#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="CASIO SL-300"
DIST="$ROOT/dist"
APP="$DIST/$APP_NAME.app"
MACOS="$APP/Contents/MacOS"
RES="$APP/Contents/Resources"
ICONSET="$DIST/AppIcon.iconset"

rm -rf "$APP" "$ICONSET"
mkdir -p "$MACOS" "$RES" "$ICONSET"

echo "→ kompilacja"
swiftc "$ROOT/macos/App.swift" \
  -o "$MACOS/CasioSL300" \
  -O \
  -framework Cocoa \
  -framework WebKit \
  -target arm64-apple-macosx13.0

cp "$ROOT/macos/Info.plist" "$APP/Contents/Info.plist"
cp "$ROOT/index.html" "$RES/index.html"
cp "$ROOT/models.css" "$RES/models.css"
cp -R "$ROOT/hp" "$RES/hp"
cp -R "$ROOT/assets" "$RES/assets"

echo "→ ikona"
SRC="$ROOT/assets/casio-front.jpg"
png() { sips -s format png -z "$1" "$1" "$SRC" --out "$2" >/dev/null; }
png 16  "$ICONSET/icon_16x16.png"
png 32  "$ICONSET/icon_16x16@2x.png"
png 32  "$ICONSET/icon_32x32.png"
png 64  "$ICONSET/icon_32x32@2x.png"
png 128 "$ICONSET/icon_128x128.png"
png 256 "$ICONSET/icon_128x128@2x.png"
png 256 "$ICONSET/icon_256x256.png"
png 512 "$ICONSET/icon_256x256@2x.png"
png 512 "$ICONSET/icon_512x512.png"
png 1024 "$ICONSET/icon_512x512@2x.png"
iconutil -c icns "$ICONSET" -o "$RES/AppIcon.icns"
rm -rf "$ICONSET"

cat > "$APP/Contents/PkgInfo" <<'EOF'
APPL????
EOF

xattr -cr "$APP" || true
echo "→ podpis ad-hoc"
codesign --force --deep -s - "$APP" >/dev/null

mkdir -p "$HOME/Applications"
rm -rf "$HOME/Applications/$APP_NAME.app"
cp -R "$APP" "$HOME/Applications/"

echo "OK  $APP"
echo "OK  $HOME/Applications/$APP_NAME.app"
