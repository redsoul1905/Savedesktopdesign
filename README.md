# SaveDesktopDesign

Backs up your **entire KDE Plasma design from A to Z into a single file** — and restores it on a new machine with one click.

Built for **CachyOS** and other Arch-based systems running KDE Plasma.

🌍 **Languages:** English · Deutsch · Français · Italiano · Español · Português · Türkçe — auto-detects your system language, switchable in the app.

## What gets backed up?

| Category | Contents |
|---|---|
| Plasma & KWin | Global themes, panel layouts, shortcuts, window rules, Krohnkite/script settings |
| GTK & Kvantum | Glass/Kvantum themes, GTK 2/3/4 configuration |
| Themes & icons | Desktop themes, look-and-feel, window decorations (Aurorae), color schemes, icons, cursors |
| Fonts | Custom fonts incl. fontconfig |
| KWin scripts & effects | Krohnkite & co. from `~/.local/share/kwin` |
| Wallpapers & more | Wallpapers, Konsole profiles |
| Package lists | pacman (explicit), AUR/foreign, Flatpak — e.g. for Rounded Corners, Force Blur, Kvantum |

> **Note:** Compiled KWin plugins (e.g. Rounded Corners) live in system directories and are reinstalled via the **package list**, not copied as files.

## Installation

```bash
sudo pacman -S --needed git python python-pyqt6
git clone https://github.com/redsoul1905/Savedesktopdesign.git
cd Savedesktopdesign
./install.sh
```

You'll then find **SaveDesktopDesign** in your application menu.

Run directly without installing:

```bash
python3 savedesktopdesign.py
```

## Usage

**Back up (old machine):**
1. Launch the app → **Back up** tab
2. Select categories (default: everything) → **Create backup**
3. Copy the resulting `.tar.gz` to a USB drive / cloud storage

**Restore (new machine):**
1. Launch the app → **Restore** tab → choose the archive
2. Click **Install packages** (opens a terminal; uses `pacman`, `paru`/`yay` and `flatpak`)
3. **Log out and back in** so KWin effects and the design fully apply

## Uninstall

```bash
./install.sh --uninstall
```

## Requirements

- Arch-based system (CachyOS, EndeavourOS, Arch …) with KDE Plasma
- Python 3.10+ and `python-pyqt6`
- Optional: `paru` or `yay` for AUR packages, `flatpak`

## License

MIT — see [LICENSE](LICENSE).
