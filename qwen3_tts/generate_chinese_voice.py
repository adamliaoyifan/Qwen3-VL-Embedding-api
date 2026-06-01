#!/usr/bin/env python3
# coding=utf-8
"""
Generate Chinese voice to WAV file using Qwen3-TTS-12Hz-1.7B-CustomVoice.

Loads the model from models/Qwen3-TTS/ and synthesizes Chinese text to speech.
"""

import argparse
import os
import sys
import time

# Allow importing qwen_tts when run from repo root (e.g. python qwen3_tts/generate_chinese_voice.py)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_QWEN_TTS_ROOT = os.path.join(_SCRIPT_DIR, "Qwen3-TTS")
if _QWEN_TTS_ROOT not in sys.path:
    sys.path.insert(0, _QWEN_TTS_ROOT)

import torch
import soundfile as sf

from qwen_tts import Qwen3TTSModel


def _default_model_path() -> str:
    """Resolve default model path: models/Qwen3-TTS/ relative to repo root."""
    repo_root = os.path.dirname(_SCRIPT_DIR)  # qwen3_tts -> repo root
    return os.path.join(repo_root, "models", "Qwen3-TTS")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Chinese voice to WAV file using Qwen3-TTS-12Hz-1.7B-CustomVoice."
    )
    parser.add_argument(
        "text",
        nargs="?",
        default="你好，世界！欢迎使用 Qwen3 语音合成。",
        help="Chinese text to synthesize (default: sample greeting).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.wav",
        help="Output WAV file path (default: output.wav).",
    )
    parser.add_argument(
        "-m",
        "--model-path",
        default=None,
        help="Path to Qwen3-TTS model (default: models/Qwen3-TTS/).",
    )
    parser.add_argument(
        "--speaker",
        default="Vivian",
        help="Speaker name, e.g. Vivian, Ryan (default: Vivian).",
    )
    parser.add_argument(
        "--instruct",
        default=None,
        help="Optional instruction for tone/emotion, e.g. 用愤怒的语气说.",
    )
    parser.add_argument(
        "--language",
        default="Chinese",
        choices=["Chinese", "Auto"],
        help="Language (default: Chinese).",
    )
    parser.add_argument(
        "--device",
        default="cuda:0",
        help="Device for inference (default: cuda:0). Use cpu for CPU-only.",
    )
    parser.add_argument(
        "--no-flash-attn",
        action="store_true",
        help="Disable FlashAttention-2 (use if not installed).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    model_path = args.model_path or _default_model_path()
    if not os.path.isdir(model_path):
        print(f"Error: Model path not found: {model_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading model from {model_path} ...")
    try:
        tts = Qwen3TTSModel.from_pretrained(
            model_path,
            device_map=args.device,
            dtype=torch.bfloat16,
            attn_implementation=None if args.no_flash_attn else "flash_attention_2",
        )
    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Generating speech: \"{args.text[:50]}{'...' if len(args.text) > 50 else ''}\"")
    try:
        if args.device.startswith("cuda"):
            torch.cuda.synchronize()
        t0 = time.time()

        wavs, sr = tts.generate_custom_voice(
            text=args.text,
            language=args.language,
            speaker=args.speaker,
            instruct=args.instruct or None,
        )

        if args.device.startswith("cuda"):
            torch.cuda.synchronize()
        t1 = time.time()
        print(f"Generation time: {t1 - t0:.3f}s")
    except Exception as e:
        print(f"Error generating speech: {e}", file=sys.stderr)
        sys.exit(1)

    out_path = args.output
    try:
        sf.write(out_path, wavs[0], sr)
        print(f"Saved WAV to {out_path} (sample rate: {sr})")
    except Exception as e:
        print(f"Error saving WAV: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
