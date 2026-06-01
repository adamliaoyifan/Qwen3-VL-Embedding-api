"""Standalone Visual Place Recognition (VPR) embedding server.

Supports multiple VPR backends: DINOv2, CosPlace, EigenPlaces.
Provides a single /v1/embed endpoint that returns L2-normalized embeddings.

Usage:
    # Default: EigenPlaces (recommended for place recognition)
    python -m api.vpr_server --model eigenplaces --port 8890

    # CosPlace
    python -m api.vpr_server --model cosplace --port 8890

    # DINOv2 (original, less viewpoint-robust)
    python -m api.vpr_server --model dinov2 --port 8890

    # Custom backbone/dim for CosPlace/EigenPlaces
    python -m api.vpr_server --model eigenplaces --backbone ResNet50 --dim 2048 --port 8890
"""

import argparse
import io
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
import torch
import torchvision.transforms as T
import uvicorn
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vpr_server")

# Global state
vpr_model = None
vpr_transform = None
vpr_device = "cpu"
vpr_model_name = "unknown"
vpr_dim = 0
API_KEY: Optional[str] = None


# ---------------------------------------------------------------------------
# Model loaders
# ---------------------------------------------------------------------------

def load_dinov2(backbone: str = "dinov2_vits14"):
    """Load DINOv2 from torch hub."""
    global vpr_model, vpr_transform, vpr_device, vpr_model_name, vpr_dim
    vpr_device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[DINOv2] Loading {backbone} on {vpr_device} ...")

    vpr_model = torch.hub.load("facebookresearch/dinov2", backbone)
    vpr_model = vpr_model.eval().to(vpr_device)
    vpr_transform = T.Compose([
        T.Resize(256, interpolation=T.InterpolationMode.BICUBIC),
        T.CenterCrop(224),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    # Probe output dim
    with torch.no_grad():
        dummy = torch.randn(1, 3, 224, 224, device=vpr_device)
        vpr_dim = vpr_model(dummy).shape[-1]
    vpr_model_name = backbone
    logger.info(f"[DINOv2] Loaded. dim={vpr_dim}")


def load_cosplace(backbone: str = "ResNet18", dim: int = 512):
    """Load CosPlace from torch hub (gmberton/CosPlace)."""
    global vpr_model, vpr_transform, vpr_device, vpr_model_name, vpr_dim
    vpr_device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[CosPlace] Loading backbone={backbone} dim={dim} on {vpr_device} ...")

    vpr_model = torch.hub.load(
        "gmberton/cosplace", "get_trained_model",
        backbone=backbone, fc_output_dim=dim,
    )
    vpr_model = vpr_model.eval().to(vpr_device)
    vpr_transform = T.Compose([
        T.Resize((512, 512), interpolation=T.InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    vpr_dim = dim
    vpr_model_name = f"cosplace_{backbone}_{dim}"
    logger.info(f"[CosPlace] Loaded. dim={vpr_dim}")


def load_eigenplaces(backbone: str = "ResNet18", dim: int = 512):
    """Load EigenPlaces from torch hub (gmberton/EigenPlaces)."""
    global vpr_model, vpr_transform, vpr_device, vpr_model_name, vpr_dim
    vpr_device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[EigenPlaces] Loading backbone={backbone} dim={dim} on {vpr_device} ...")

    vpr_model = torch.hub.load(
        "gmberton/eigenplaces", "get_trained_model",
        backbone=backbone, fc_output_dim=dim,
    )
    vpr_model = vpr_model.eval().to(vpr_device)
    vpr_transform = T.Compose([
        T.Resize((512, 512), interpolation=T.InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    vpr_dim = dim
    vpr_model_name = f"eigenplaces_{backbone}_{dim}"
    logger.info(f"[EigenPlaces] Loaded. dim={vpr_dim}")


# ---------------------------------------------------------------------------
# CLI argument parsing (needed before lifespan for model selection)
# ---------------------------------------------------------------------------

_cli_args = None


def parse_args():
    parser = argparse.ArgumentParser(description="VPR Embedding Server")
    parser.add_argument("--model", type=str, default="eigenplaces",
                        choices=["dinov2", "cosplace", "eigenplaces"],
                        help="VPR model to use (default: eigenplaces)")
    parser.add_argument("--backbone", type=str, default="ResNet18",
                        help="Backbone for CosPlace/EigenPlaces (default: ResNet18)")
    parser.add_argument("--dim", type=int, default=512,
                        help="Output dimension for CosPlace/EigenPlaces (default: 512)")
    parser.add_argument("--port", type=int, default=8890,
                        help="Server port (default: 8890)")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="Server host (default: 0.0.0.0)")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

# API密钥验证依赖
async def verify_api_key(api_key: Optional[str] = Query(None, description="API key for authentication")):
    global API_KEY
    if API_KEY is None:
        logger.warning("API_KEY not configured - allowing request without authentication")
        return
    if api_key is None:
        logger.warning("API key required but not provided in request")
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide api_key as a query parameter."
        )
    if api_key != API_KEY:
        logger.warning("Invalid API key attempt from client")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Please provide a valid api_key query parameter."
        )
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cli_args, API_KEY
    # 加载API密钥
    API_KEY = os.environ.get("API_KEY")
    if API_KEY:
        logger.info("API key authentication enabled")
    else:
        logger.warning("API_KEY not set - service will be unprotected! Set API_KEY environment variable to enable authentication.")

    args = _cli_args
    try:
        if args.model == "dinov2":
            load_dinov2()
        elif args.model == "cosplace":
            load_cosplace(backbone=args.backbone, dim=args.dim)
        elif args.model == "eigenplaces":
            load_eigenplaces(backbone=args.backbone, dim=args.dim)
    except Exception as e:
        logger.error(f"Failed to load VPR model: {e}")
        raise
    logger.info(f"VPR server ready: model={vpr_model_name} dim={vpr_dim}")
    yield


app = FastAPI(title="VPR Embedding Server", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": vpr_model_name,
        "dim": vpr_dim,
        "device": vpr_device,
    }


@app.post("/v1/embed")
async def embed(image: UploadFile = File(...), _: None = Depends(verify_api_key)):
    """Compute VPR embedding for an uploaded image.

    Returns JSON: {"status": "success", "embedding": [...], "model": "...", "dim": N}
    """
    if vpr_model is None:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": "VPR model not loaded"},
        )

    t0 = time.monotonic()
    try:
        img_bytes = await image.read()
        pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        tensor = vpr_transform(pil_img).unsqueeze(0).to(vpr_device)

        with torch.no_grad():
            emb = vpr_model(tensor).squeeze(0).cpu().numpy()

        # L2 normalize
        norm = np.linalg.norm(emb)
        if norm > 1e-6:
            emb = emb / norm

        elapsed_ms = (time.monotonic() - t0) * 1000
        return {
            "status": "success",
            "embedding": emb.tolist(),
            "model": vpr_model_name,
            "dim": int(emb.shape[0]),
            "elapsed_ms": round(elapsed_ms, 1),
        }
    except Exception as e:
        logger.error(f"Embed error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)},
        )


def main():
    global _cli_args
    _cli_args = parse_args()
    uvicorn.run(
        app,
        host=_cli_args.host,
        port=_cli_args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
