#!/usr/bin/env bash
# ORCD/Engaging one-time setup. Run INSIDE an interactive GPU session (so torch sees CUDA when you verify at the end).
# Creates ~/vesuvius with a sparse villa clone, a uv venv (Python 3.14, CUDA torch) and the released checkpoints.
set -euo pipefail
W=${VESUVIUS_HOME:-$HOME/vesuvius}; mkdir -p "$W"; cd "$W"
command -v uv >/dev/null || { curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"; }
if [ ! -d villa ]; then
  git clone --depth 1 --filter=blob:none --sparse https://github.com/ScrollPrize/villa.git villa
  git -C villa sparse-checkout set vesuvius ink-detection
fi
echo "villa @ $(git -C villa rev-parse --short HEAD)" | tee env.txt
uv venv .venv --python 3.14
# CUDA 12.8 wheels; torch<2.13 per the villa warning about VRAM
uv pip install -p .venv "torch<2.13" --index-url https://download.pytorch.org/whl/cu128
uv pip install -p .venv numpy "zarr>=2.18.7,<4" "numcodecs>=0.15.1,<0.17" fsspec s3fs aiohttp requests pillow pyyaml pynrrd \
  tifffile imagecodecs einops fvcore timm huggingface_hub scipy scikit-image imageio tqdm pandas
.venv/bin/python -c "import torch; print('torch', torch.__version__, '| cuda:', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-')" | tee -a env.txt
mkdir -p checkpoints
.venv/bin/hf download scrollprize/ink_9um hybrid_3d2d-seed42/step-075000.pth --local-dir checkpoints/ink_9um
.venv/bin/hf download scrollprize/hecate hecate.py requirements.txt hecate_9.6um.pth --local-dir checkpoints/hecate
echo "setup done: $W"
