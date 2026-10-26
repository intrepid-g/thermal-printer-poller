#!/bin/sh
# Installs `btprint` and `thermal-poller` into ~/.local/bin, with their own venv.
set -e
D="$HOME/.local/share/thermal-printer"
SRC="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$D" "$HOME/.local/bin"
[ -d "$D/venv" ] || python3 -m venv "$D/venv"
"$D/venv/bin/pip" -q install bleak pillow
cp "$SRC/config.py" "$SRC/btprint.py" "$SRC/poller.py" "$D/"
for pair in btprint:btprint.py thermal-poller:poller.py; do
  printf '#!/bin/sh\nexec "$HOME/.local/share/thermal-printer/venv/bin/python" "$HOME/.local/share/thermal-printer/%s" "$@"\n' "${pair#*:}" > "$HOME/.local/bin/${pair%%:*}"
  chmod +x "$HOME/.local/bin/${pair%%:*}"
done
echo "installed btprint and thermal-poller in ~/.local/bin (first run asks for the printer, server URL and token)"
