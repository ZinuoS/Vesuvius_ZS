#!/usr/bin/env bash
# One-time: slim ink-inference environment on Apple Silicon (MPS). No C++ build.
set -euo pipefail; cd "$(dirname "$0")"
command -v uv >/dev/null || { curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"; }
if [ ! -d villa ]; then
  git clone --depth 1 --filter=blob:none --sparse https://github.com/ScrollPrize/villa.git villa
  git -C villa sparse-checkout set vesuvius
fi
echo "villa @ $(git -C villa rev-parse --short HEAD)" | tee ink_env.txt
uv venv .inkenv --python 3.14
uv pip install -p .inkenv torch numpy "zarr>=2.18.7,<4" "numcodecs>=0.15.1,<0.17" fsspec s3fs aiohttp \
  requests pillow pyyaml pynrrd tifffile einops fvcore timm huggingface_hub scipy scikit-image imageio imagecodecs
.inkenv/bin/python -c "import torch; print('torch', torch.__version__, '| mps:', torch.backends.mps.is_available())" | tee -a ink_env.txt
.inkenv/bin/hf download scrollprize/ink_9um hybrid_3d2d-seed42/step-075000.pth --local-dir checkpoints/ink_9um
echo "setup done"
