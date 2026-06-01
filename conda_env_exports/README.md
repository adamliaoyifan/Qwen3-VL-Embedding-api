# Conda Environment Exports

This folder contains reproducibility exports for the local conda environments.

## Folders

- `qwen3/`: recommended environment for Qwen3-VL embedding/API work.
- `navdp/`: secondary vision/runtime environment.

Each folder contains:

- `*.lock.yml`: full conda environment export for closest reproduction on similar machines.
- `*.history.yml`: portable conda spec based on explicitly requested packages.
- `*.pip.lock.txt`: exact pip package list from the environment.

## Recreate qwen3

```bash
conda env create -f qwen3/qwen3.lock.yml
conda activate qwen3
python -m pip install -r qwen3/qwen3.pip.lock.txt
```

Fallback for different machines if the lock file fails:

```bash
conda env create -f qwen3/qwen3.history.yml
conda activate qwen3
python -m pip install -r qwen3/qwen3.pip.lock.txt
```

## Recreate navdp

```bash
conda env create -f navdp/navdp.lock.yml
conda activate navdp
python -m pip install -r navdp/navdp.pip.lock.txt
```

Fallback for different machines if the lock file fails:

```bash
conda env create -f navdp/navdp.history.yml
conda activate navdp
python -m pip install -r navdp/navdp.pip.lock.txt
```

## Verify

```bash
python -V
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.cuda)"
```
