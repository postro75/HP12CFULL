#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="HP12CFULL"
DIST="$ROOT/dist"
APP="$DIST/$APP_NAME.app"
MACOS="$APP/Contents/MacOS"
RES="$APP/Contents/Resources"
ICONSET="$DIST/AppIcon.iconset"
DMG="$DIST/$APP_NAME.dmg"
STAGE="$DIST/dmg-stage"

rm -rf "$APP" "$ICONSET" "$STAGE" "$DMG"
mkdir -p "$MACOS" "$RES" "$ICONSET"

echo "→ kompilacja (universal arm64 + x86_64)"
swiftc "$ROOT/macos/App.swift" \
  -o "$DIST/HP12CFULL.arm64" \
  -O \
  -framework Cocoa \
  -framework WebKit \
  -target arm64-apple-macosx13.0
swiftc "$ROOT/macos/App.swift" \
  -o "$DIST/HP12CFULL.x86_64" \
  -O \
  -framework Cocoa \
  -framework WebKit \
  -target x86_64-apple-macosx13.0
lipo -create -output "$MACOS/HP12CFULL" "$DIST/HP12CFULL.arm64" "$DIST/HP12CFULL.x86_64"
rm -f "$DIST/HP12CFULL.arm64" "$DIST/HP12CFULL.x86_64"

cp "$ROOT/macos/Info.plist" "$APP/Contents/Info.plist"
cp "$ROOT/index.html" "$RES/index.html"
cp "$ROOT/models.css" "$RES/models.css"
cp -R "$ROOT/hp" "$RES/hp"
cp -R "$ROOT/assets" "$RES/assets"

echo "→ ikona"
SRC="$ROOT/assets/models/HP12C.png"
if [[ ! -f "$SRC" ]]; then SRC="$ROOT/assets/casio-front.jpg"; fi
png() { sips -s format png -z "$1" "$1" "$SRC" --out "$2" >/dev/null; }
png 16  "$ICONSET/icon_16x16.png"
png 32  "$ICONSET/icon_16x16@2x.png"
png 32  "$ICONSET/icon_32x32.png"
png 64  "$ICONSET/icon_32x32@2x.png"
png 128 "$ICONSET/icon_128x128.png"
png 256 "$ICONSET/icon_128x128@2x.png"
png 256 "$ICONSET/icon_256x256.png"
png 512 "$ICONSET/icon_512x512@2x.png"
png 512 "$ICONSET/icon_512x512.png"
png 1024 "$ICONSET/icon_512x512@2x.png"
iconutil -c icns "$ICONSET" -o "$RES/AppIcon.icns"
rm -rf "$ICONSET"

printf 'APPL????' > "$APP/Contents/PkgInfo"
xattr -cr "$APP" || true
echo "→ podpis ad-hoc"
codesign --force --deep -s - "$APP" >/dev/null

mkdir -p "$HOME/Applications"
rm -rf "$HOME/Applications/$APP_NAME.app"
cp -R "$APP" "$HOME/Applications/"

echo "→ DMG"
mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create \
  -volname "$APP_NAME" \
  -srcfolder "$STAGE" \
  -ov -format UDZO \
  "$DMG" >/dev/null
rm -rf "$STAGE"

echo "OK  $APP"
echo "OK  $HOME/Applications/$APP_NAME.app"
echo "OK  $DMG"
ls -lh "$DMG" "$APP/Contents/MacOS/HP12CFULL"
