#!/usr/bin/env bash
# One-time: fetch Hecate (scrollprize/hecate, MIT) into ./hecate and install its requirements into .inkenv
set -euo pipefail; cd "$(dirname "$0")"
.inkenv/bin/hf download scrollprize/hecate hecate.py requirements.txt hecate_9.6um.pth --local-dir hecate
cat hecate/requirements.txt
uv pip install -p .inkenv -r hecate/requirements.txt
echo "hecate ready"
