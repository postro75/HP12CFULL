#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESK="$ROOT/desktop"
DIST="$ROOT/dist"
WWW="$DESK/www"

rm -rf "$WWW"
mkdir -p "$WWW"
cp "$ROOT/index.html" "$WWW/"
cp "$ROOT/models.css" "$WWW/"
cp -R "$ROOT/hp" "$WWW/hp"
cp -R "$ROOT/assets" "$WWW/assets"

echo "→ ikona .ico"
python3 - <<'PY'
from pathlib import Path
src = Path("/Users/pawelostrowski/MY_PROJECTS/casio-kalkulator/assets/models/HP12C.png")
dst = Path("/Users/pawelostrowski/MY_PROJECTS/casio-kalkulator/desktop/icon.ico")
try:
    from PIL import Image
    im = Image.open(src).convert("RGBA")
    sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
    im.save(dst, sizes=sizes)
    print("ico", dst, dst.stat().st_size)
except Exception as e:
    print("PIL ico failed:", e)
    raise SystemExit(1)
PY

cd "$DESK"
npm install --no-fund --no-audit electron@37.2.1 >/dev/null

# electron-packager unzip of win32 is flaky here; assemble from the cached zip.
CACHE=$(find "$HOME/Library/Caches/electron" -name 'electron-v37.2.1-win32-x64.zip' | head -1)
if [[ -z "$CACHE" ]]; then
  node -e "require('electron/install.js')" 2>/dev/null || true
  npx electron --version >/dev/null
  python3 - <<'PY'
import os, urllib.request, pathlib
url = "https://github.com/electron/electron/releases/download/v37.2.1/electron-v37.2.1-win32-x64.zip"
dest = pathlib.Path.home() / "Library/Caches/electron/electron-v37.2.1-win32-x64.zip"
dest.parent.mkdir(parents=True, exist_ok=True)
if not dest.exists():
    print("download", url)
    urllib.request.urlretrieve(url, dest)
print(dest)
PY
  CACHE=$(find "$HOME/Library/Caches/electron" -name 'electron-v37.2.1-win32-x64.zip' | head -1)
fi

WIN="$DIST/HP12CFULL-win32-x64"
rm -rf "$WIN"
mkdir -p "$WIN"
unzip -q "$CACHE" -d "$WIN"
mv "$WIN/electron.exe" "$WIN/HP12CFULL.exe"
APP="$WIN/resources/app"
rm -rf "$APP"
mkdir -p "$APP/www"
cp "$DESK/main.js" "$DESK/package.json" "$APP/"
cp -R "$WWW/"* "$APP/www/"

rm -f "$DIST/HP12CFULL-win64.zip"
(cd "$DIST" && zip -qr "HP12CFULL-win64.zip" "HP12CFULL-win32-x64")
echo "OK  $WIN/HP12CFULL.exe"
echo "OK  $DIST/HP12CFULL-win64.zip"
ls -lh "$WIN/HP12CFULL.exe" "$DIST/HP12CFULL-win64.zip"
