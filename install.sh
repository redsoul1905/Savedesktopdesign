#!/usr/bin/env bash
# SaveDesktopDesign — Installation ins Benutzerverzeichnis
set -e

APP_DIR="$HOME/.local/share/savedesktopdesign"
BIN_DIR="$HOME/.local/bin"
DESKTOP_FILE="$HOME/.local/share/applications/savedesktopdesign.desktop"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

REPO_URL="https://github.com/redsoul1905/Savedesktopdesign.git"

if [[ "$1" == "--uninstall" ]]; then
    rm -rf "$APP_DIR"
    rm -f "$BIN_DIR/savedesktopdesign" "$DESKTOP_FILE"
    echo "SaveDesktopDesign wurde entfernt. / SaveDesktopDesign has been removed."
    exit 0
fi

if [[ "$1" == "--update" ]]; then
    echo "Updating SaveDesktopDesign ..."
    if [[ -d "$SRC_DIR/.git" ]] && command -v git >/dev/null; then
        git -C "$SRC_DIR" pull --ff-only
    else
        echo "No git repository found — downloading a fresh copy ..."
        command -v git >/dev/null || { echo "git is required for updating."; exit 1; }
        TMP_DIR="$(mktemp -d)"
        git clone --depth 1 "$REPO_URL" "$TMP_DIR/repo"
        cp -f "$TMP_DIR/repo/savedesktopdesign.py" "$TMP_DIR/repo/install.sh" "$SRC_DIR/"
        chmod +x "$SRC_DIR/install.sh"
        rm -rf "$TMP_DIR"
    fi
    exec "$SRC_DIR/install.sh"   # frisch installieren mit neuer Version
fi

# Abhängigkeit prüfen / check dependency
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "PyQt6 is missing. Install it with:"
    if command -v pacman >/dev/null; then
        echo "  sudo pacman -S python-pyqt6"
    elif command -v apt-get >/dev/null; then
        echo "  sudo apt install python3-pyqt6"
    elif command -v dnf >/dev/null; then
        echo "  sudo dnf install python3-pyqt6"
    else
        echo "  (install the PyQt6 package for your distribution)"
    fi
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
