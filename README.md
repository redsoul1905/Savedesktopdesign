# SaveDesktopDesign

Sichert dein komplettes **KDE-Plasma-Design von A bis Z in eine einzige Datei** — und stellt es auf einem neuen Rechner mit einem Klick wieder her.

Gemacht für **CachyOS** und andere Arch-basierte Systeme mit KDE Plasma.

## Was wird gesichert?

| Kategorie | Inhalt |
|---|---|
| Plasma & KWin | Globale Designs, Panel-Layouts, Shortcuts, Fensterregeln, Krohnkite-/Skript-Einstellungen |
| GTK & Kvantum | Glass-/Kvantum-Themes, GTK 2/3/4-Konfiguration |
| Themes & Icons | Desktop-Themes, Look-and-Feel, Fensterdekorationen (Aurorae), Farbschemata, Icons, Cursor |
| Schriften | Eigene Fonts inkl. fontconfig |
| KWin-Skripte & Effekte | Krohnkite & Co. aus `~/.local/share/kwin` |
| Wallpaper & Co. | Hintergrundbilder, Konsole-Profile |
| Paketlisten | pacman (explizit), AUR/fremd, Flatpak — z. B. für Rounded Corners, Force Blur, Kvantum |

> **Hinweis:** Kompilierte KWin-Plugins (z. B. Rounded Corners) liegen in Systemordnern und werden über die **Paketliste** nachinstalliert, nicht als Dateien kopiert.

## Installation

```bash
sudo pacman -S --needed git python python-pyqt6
git clone https://github.com/DEIN-BENUTZERNAME/savedesktopdesign.git
cd savedesktopdesign
./install.sh
```

Danach findest du **SaveDesktopDesign** im Anwendungsmenü.

Ohne Installation direkt starten:

```bash
python3 savedesktopdesign.py
```

## Benutzung

**Sichern (alter Rechner):**
1. App starten → Tab **Sichern**
2. Kategorien auswählen (Standard: alles) → **Backup erstellen**
3. Die erzeugte `.tar.gz` auf USB-Stick / Cloud kopieren

**Wiederherstellen (neuer Rechner):**
1. App starten → Tab **Wiederherstellen** → Archiv wählen
2. **Pakete installieren** klicken (öffnet Terminal; nutzt `pacman`, `paru`/`yay` und `flatpak`)
3. **Ab- und wieder anmelden**, damit KWin-Effekte und Design vollständig greifen

## Deinstallation

```bash
./install.sh --uninstall
```

## Voraussetzungen

- Arch-basiertes System (CachyOS, EndeavourOS, Arch …) mit KDE Plasma
- Python 3.10+ und `python-pyqt6`
- Optional: `paru` oder `yay` für AUR-Pakete, `flatpak`

## Lizenz

MIT — siehe [LICENSE](LICENSE).
