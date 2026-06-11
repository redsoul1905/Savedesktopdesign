#!/usr/bin/env bash
# SaveDesktopDesign — Installation ins Benutzerverzeichnis
set -e

APP_DIR="$HOME/.local/share/savedesktopdesign"
BIN_DIR="$HOME/.local/bin"
DESKTOP_FILE="$HOME/.local/share/applications/savedesktopdesign.desktop"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ "$1" == "--uninstall" ]]; then
    rm -rf "$APP_DIR"
    rm -f "$BIN_DIR/savedesktopdesign" "$DESKTOP_FILE"
    echo "SaveDesktopDesign wurde entfernt."
    exit 0
fi

# Abhängigkeit prüfen
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "python-pyqt6 fehlt. Installation:"
    echo "  sudo pacman -S python-pyqt6"
    exit 1
fi

mkdir -p "$APP_DIR" "$BIN_DIR" "$(dirname "$DESKTOP_FILE")"
cp "$SRC_DIR/savedesktopdesign.py" "$APP_DIR/"

cat > "$BIN_DIR/savedesktopdesign" <<EOF
#!/usr/bin/env bash
exec python3 "$APP_DIR/savedesktopdesign.py" "\$@"
EOF
chmod +x "$BIN_DIR/savedesktopdesign"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=SaveDesktopDesign
Comment=KDE-Plasma-Design & Paketlisten sichern und wiederherstellen
Exec=python3 $APP_DIR/savedesktopdesign.py
Icon=preferences-desktop-theme
Terminal=false
Categories=Utility;Settings;
EOF

echo "Installiert! Du findest 'SaveDesktopDesign' im Anwendungsmenü"
echo "oder startest sie mit: savedesktopdesign"
