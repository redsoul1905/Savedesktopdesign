#!/usr/bin/env python3
"""
SaveDesktopDesign — Sichert & restauriert das komplette KDE-Plasma-Design
(Themes, Icons, Schriften, KWin-Skripte, Plasma-Einstellungen, Kvantum,
Wallpaper, Panel-Layouts) sowie Paketlisten (pacman, AUR, Flatpak).

Für CachyOS / Arch-basierte Systeme mit KDE Plasma.
Benötigt: python-pyqt6  (sudo pacman -S python-pyqt6)
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

HOME = Path.home()
APP_NAME = "SaveDesktopDesign"
VERSION = "1.0"

# ----------------------------------------------------------------------------
# Was gesichert wird — Pfade relativ zum Home-Verzeichnis
# ----------------------------------------------------------------------------
CATEGORIES: dict[str, list[str]] = {
    "Plasma- & KWin-Einstellungen": [
        ".config/kdeglobals",
        ".config/kwinrc",
        ".config/kwinrulesrc",
        ".config/kglobalshortcutsrc",
        ".config/khotkeysrc",
        ".config/kscreenlockerrc",
        ".config/ksplashrc",
        ".config/ksmserverrc",
        ".config/krunnerrc",
        ".config/plasmarc",
        ".config/plasmashellrc",
        ".config/plasmanotifyrc",
        ".config/plasma-org.kde.plasma.desktop-appletsrc",
        ".config/kcminputrc",
        ".config/kded5rc",
        ".config/kded6rc",
        ".config/breezerc",
        ".config/oxygenrc",
        ".config/kwalletrc",
        ".config/dolphinrc",
        ".config/konsolerc",
        ".config/yakuakerc",
        ".config/spectaclerc",
        ".config/katerc",
        ".config/lattedockrc",
        ".config/latte",
        ".config/autostart",
        ".config/kde.org",
        ".config/xsettingsd",
        ".config/Trolltech.conf",
        ".config/mimeapps.list",
        ".config/touchpadrc",
        ".config/powermanagementprofilesrc",
    ],
    "GTK- & Kvantum-Design (Glass etc.)": [
        ".config/gtkrc",
        ".config/gtkrc-2.0",
        ".config/gtk-3.0",
        ".config/gtk-4.0",
        ".config/Kvantum",
        ".gtkrc-2.0",
    ],
    "Themes, Icons & Cursor": [
        ".local/share/plasma",            # Desktop-Themes, Look&Feel, Plasmoids
        ".local/share/aurorae",           # Fensterdekorationen
        ".local/share/color-schemes",
        ".local/share/icons",
        ".local/share/themes",
        ".themes",
        ".icons",
    ],
    "Schriften": [
        ".local/share/fonts",
        ".fonts",
        ".config/fontconfig",
        ".local/share/kfontinst",
    ],
    "KWin-Skripte & Effekte": [
        ".local/share/kwin",              # Skripte, Effekte, Tabbox
        ".local/share/kservices5",
        ".local/share/kservices6",
        ".local/share/knewstuff3",
    ],
    "Wallpaper & Konsole-Profile": [
        ".local/share/wallpapers",
        ".local/share/konsole",
        ".local/share/kxmlgui5",
        ".local/share/kxmlgui6",
    ],
}

PKG_CATEGORY = "Paketlisten (pacman / AUR / Flatpak)"


def gather_package_lists() -> dict[str, str]:
    """Erzeugt Paketlisten als {dateiname: inhalt}."""
    lists: dict[str, str] = {}
    cmds = {
        "pacman-explicit.txt": ["pacman", "-Qqen"],   # explizit, offizielle Repos
        "pacman-foreign.txt": ["pacman", "-Qqem"],    # AUR / fremd
    }
    for fname, cmd in cmds.items():
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if out.returncode == 0:
                lists[fname] = out.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    try:
        out = subprocess.run(
            ["flatpak", "list", "--app", "--columns=application"],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode == 0:
            lists["flatpak.txt"] = out.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return lists


# ----------------------------------------------------------------------------
# Worker-Threads
# ----------------------------------------------------------------------------
class BackupWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, dest: str, categories: list[str], with_packages: bool):
        super().__init__()
        self.dest = dest
        self.categories = categories
        self.with_packages = with_packages

    def run(self):
        try:
            paths: list[tuple[str, Path]] = []  # (kategorie, absoluter pfad)
            for cat in self.categories:
                for rel in CATEGORIES[cat]:
                    p = HOME / rel
                    if p.exists():
                        paths.append((cat, p))

            total = len(paths) + (1 if self.with_packages else 0) + 1
            done = 0

            manifest = {
                "app": APP_NAME,
                "version": VERSION,
                "created": datetime.now().isoformat(timespec="seconds"),
                "hostname": socket.gethostname(),
                "user": os.environ.get("USER", ""),
                "categories": self.categories,
                "with_packages": self.with_packages,
                "paths": [str(p.relative_to(HOME)) for _, p in paths],
            }

            with tarfile.open(self.dest, "w:gz") as tar:
                for cat, p in paths:
                    rel = p.relative_to(HOME)
                    self.log.emit(f"  + {rel}")
                    try:
                        tar.add(p, arcname=f"home/{rel}")
                    except (PermissionError, OSError) as e:
                        self.log.emit(f"  ! übersprungen ({e})")
                    done += 1
                    self.progress.emit(int(done / total * 100))

                if self.with_packages:
                    self.log.emit("  + Paketlisten erzeugen …")
                    for fname, content in gather_package_lists().items():
                        data = content.encode()
                        info = tarfile.TarInfo(f"packages/{fname}")
                        info.size = len(data)
                        info.mtime = int(datetime.now().timestamp())
                        import io
                        tar.addfile(info, io.BytesIO(data))
                    done += 1
                    self.progress.emit(int(done / total * 100))

                mdata = json.dumps(manifest, indent=2).encode()
                info = tarfile.TarInfo("manifest.json")
                info.size = len(mdata)
                info.mtime = int(datetime.now().timestamp())
                import io
                tar.addfile(info, io.BytesIO(mdata))

            self.progress.emit(100)
            size_mb = Path(self.dest).stat().st_size / 1024 / 1024
            self.finished_ok.emit(f"{self.dest} ({size_mb:.1f} MB)")
        except Exception:
            self.failed.emit(traceback.format_exc())


class RestoreWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished_ok = pyqtSignal(bool)   # True wenn Paketlisten enthalten
    failed = pyqtSignal(str)

    def __init__(self, archive: str):
        super().__init__()
        self.archive = archive

    @staticmethod
    def _extract_filter(member, path):
        """Wie tarfile.data_filter, aber Symlinks aus Icon-/Theme-Paketen
        (absolute Links) werden erlaubt — es ist das eigene Backup."""
        try:
            return tarfile.data_filter(member, path)
        except (tarfile.AbsoluteLinkError, tarfile.LinkOutsideDestinationError):
            return member  # Symlink unverändert übernehmen
        except tarfile.FilterError:
            return None    # alles andere Verdächtige überspringen

    def run(self):
        try:
            with tempfile.TemporaryDirectory(prefix="sdd-restore-") as tmp:
                tmpp = Path(tmp)
                self.log.emit("Archiv wird entpackt …")
                with tarfile.open(self.archive, "r:gz") as tar:
                    # Sicherheit: keine Pfade außerhalb des Zielordners zulassen
                    members = []
                    for m in tar.getmembers():
                        name = os.path.normpath(m.name)
                        if name.startswith("..") or os.path.isabs(name):
                            continue
                        members.append(m)
                    try:
                        tar.extractall(tmpp, members=members,
                                       filter=self._extract_filter)
                    except TypeError:  # älteres Python ohne filter-Parameter
                        tar.extractall(tmpp, members=members)
                self.progress.emit(30)

                src_home = tmpp / "home"
                if not src_home.exists():
                    self.failed.emit("Ungültiges Archiv: kein 'home/'-Ordner enthalten.")
                    return

                entries = list(src_home.iterdir())
                total = max(len(entries), 1)
                for i, entry in enumerate(entries, 1):
                    self._copy_into_home(entry, src_home)
                    self.progress.emit(30 + int(i / total * 60))

                # Paketlisten ins Home legen, damit sie nach dem Restore greifbar sind
                has_packages = False
                pkg_dir = tmpp / "packages"
                if pkg_dir.exists():
                    dest = HOME / ".savedesktopdesign-packages"
                    dest.mkdir(exist_ok=True)
                    for f in pkg_dir.iterdir():
                        shutil.copy2(f, dest / f.name)
                    has_packages = True
                    self.log.emit(f"Paketlisten gespeichert unter: {dest}")

                self.log.emit("Schrift-Cache wird aktualisiert …")
                subprocess.run(["fc-cache", "-f"], capture_output=True, timeout=300)

                self.progress.emit(100)
                self.finished_ok.emit(has_packages)
        except Exception:
            self.failed.emit(traceback.format_exc())

    def _copy_into_home(self, entry: Path, src_root: Path):
        rel = entry.relative_to(src_root)
        target = HOME / rel
        self.log.emit(f"  → {rel}")
        if entry.is_dir():
            shutil.copytree(entry, target, dirs_exist_ok=True, symlinks=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)


# ----------------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {VERSION} — KDE-Design sichern & laden")
        self.setWindowIcon(QIcon.fromTheme("preferences-desktop-theme"))
        self.resize(720, 620)
        self.worker = None

        tabs = QTabWidget()
        tabs.addTab(self._build_backup_tab(), QIcon.fromTheme("document-save"), "Sichern")
        tabs.addTab(self._build_restore_tab(), QIcon.fromTheme("document-open"), "Wiederherstellen")
        self.setCentralWidget(tabs)

    # ---------------- Backup-Tab ----------------
    def _build_backup_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        title = QLabel("Komplettes Plasma-Design + Paketlisten in eine Datei sichern")
        f = QFont(); f.setPointSize(12); f.setBold(True)
        title.setFont(f)
        lay.addWidget(title)

        box = QGroupBox("Was soll gesichert werden?")
        blay = QVBoxLayout(box)
        self.cat_checks: dict[str, QCheckBox] = {}
        for cat in CATEGORIES:
            cb = QCheckBox(cat)
            cb.setChecked(True)
            self.cat_checks[cat] = cb
            blay.addWidget(cb)
        self.pkg_check = QCheckBox(PKG_CATEGORY)
        self.pkg_check.setChecked(True)
        blay.addWidget(self.pkg_check)
        lay.addWidget(box)

        self.backup_btn = QPushButton(QIcon.fromTheme("document-save"), "  Backup erstellen …")
        self.backup_btn.setMinimumHeight(42)
        self.backup_btn.clicked.connect(self.start_backup)
        lay.addWidget(self.backup_btn)

        self.backup_progress = QProgressBar()
        lay.addWidget(self.backup_progress)

        self.backup_log = QTextEdit()
        self.backup_log.setReadOnly(True)
        lay.addWidget(self.backup_log)
        return w

    def start_backup(self):
        cats = [c for c, cb in self.cat_checks.items() if cb.isChecked()]
        if not cats and not self.pkg_check.isChecked():
            QMessageBox.warning(self, APP_NAME, "Bitte mindestens eine Kategorie auswählen.")
            return
        default = str(HOME / f"plasma-design-{datetime.now():%Y-%m-%d}.tar.gz")
        dest, _ = QFileDialog.getSaveFileName(
            self, "Backup speichern unter …", default, "Archiv (*.tar.gz)")
        if not dest:
            return
        if not dest.endswith(".tar.gz"):
            dest += ".tar.gz"

        self.backup_btn.setEnabled(False)
        self.backup_log.clear()
        self.backup_log.append("Backup wird erstellt …")
        self.worker = BackupWorker(dest, cats, self.pkg_check.isChecked())
        self.worker.log.connect(self.backup_log.append)
        self.worker.progress.connect(self.backup_progress.setValue)
        self.worker.finished_ok.connect(self._backup_done)
        self.worker.failed.connect(self._backup_fail)
        self.worker.start()

    def _backup_done(self, info: str):
        self.backup_btn.setEnabled(True)
        self.backup_log.append(f"\n✔ Fertig: {info}")
        QMessageBox.information(self, APP_NAME, f"Backup erstellt:\n{info}")

    def _backup_fail(self, err: str):
        self.backup_btn.setEnabled(True)
        self.backup_log.append(f"\n✘ Fehler:\n{err}")
        QMessageBox.critical(self, APP_NAME, "Backup fehlgeschlagen — Details im Protokoll.")

    # ---------------- Restore-Tab ----------------
    def _build_restore_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        title = QLabel("Backup-Archiv laden und Design wiederherstellen")
        f = QFont(); f.setPointSize(12); f.setBold(True)
        title.setFont(f)
        lay.addWidget(title)

        hint = QLabel(
            "1-Klick-Restore: Archiv wählen → Dateien werden zurückkopiert.\n"
            "Danach optional Pakete installieren und Plasma neu starten.")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self.restore_btn = QPushButton(QIcon.fromTheme("document-open"), "  Archiv wählen & wiederherstellen …")
        self.restore_btn.setMinimumHeight(42)
        self.restore_btn.clicked.connect(self.start_restore)
        lay.addWidget(self.restore_btn)

        self.pkg_btn = QPushButton(QIcon.fromTheme("system-software-install"), "  Pakete installieren (öffnet Terminal)")
        self.pkg_btn.setEnabled(False)
        self.pkg_btn.clicked.connect(self.install_packages)
        lay.addWidget(self.pkg_btn)

        self.plasma_btn = QPushButton(QIcon.fromTheme("system-reboot"), "  Plasma neu starten (Design anwenden)")
        self.plasma_btn.setEnabled(False)
        self.plasma_btn.clicked.connect(self.restart_plasma)
        lay.addWidget(self.plasma_btn)

        self.restore_progress = QProgressBar()
        lay.addWidget(self.restore_progress)

        self.restore_log = QTextEdit()
        self.restore_log.setReadOnly(True)
        lay.addWidget(self.restore_log)
        return w

    def start_restore(self):
        archive, _ = QFileDialog.getOpenFileName(
            self, "Backup-Archiv wählen", str(HOME), "Archiv (*.tar.gz)")
        if not archive:
            return

        # Manifest anzeigen
        info_txt = ""
        try:
            with tarfile.open(archive, "r:gz") as tar:
                mf = tar.extractfile("manifest.json")
                if mf:
                    m = json.loads(mf.read())
                    info_txt = (f"Erstellt: {m.get('created')}\n"
                                f"Rechner: {m.get('hostname')}\n"
                                f"Kategorien: {len(m.get('categories', []))}\n"
                                f"Paketlisten: {'ja' if m.get('with_packages') else 'nein'}")
        except Exception:
            pass

        msg = "Dieses Backup wiederherstellen?\nBestehende Einstellungen werden überschrieben."
        if info_txt:
            msg += f"\n\n{info_txt}"
        if QMessageBox.question(self, APP_NAME, msg) != QMessageBox.StandardButton.Yes:
            return

        self.restore_btn.setEnabled(False)
        self.restore_log.clear()
        self.worker = RestoreWorker(archive)
        self.worker.log.connect(self.restore_log.append)
        self.worker.progress.connect(self.restore_progress.setValue)
        self.worker.finished_ok.connect(self._restore_done)
        self.worker.failed.connect(self._restore_fail)
        self.worker.start()

    def _restore_done(self, has_packages: bool):
        self.restore_btn.setEnabled(True)
        self.plasma_btn.setEnabled(True)
        self.pkg_btn.setEnabled(has_packages)
        self.restore_log.append("\n✔ Design wiederhergestellt!")
        QMessageBox.information(
            self, APP_NAME,
            "Design wiederhergestellt!\n\n"
            + ("Jetzt optional Pakete installieren und " if has_packages else "")
            + "Plasma neu starten (oder ab- und anmelden), damit alles greift.")

    def _restore_fail(self, err: str):
        self.restore_btn.setEnabled(True)
        self.restore_log.append(f"\n✘ Fehler:\n{err}")
        QMessageBox.critical(self, APP_NAME, "Restore fehlgeschlagen — Details im Protokoll.")

    def install_packages(self):
        pkg_dir = HOME / ".savedesktopdesign-packages"
        script = pkg_dir / "install.sh"
        helper = shutil.which("paru") or shutil.which("yay")
        lines = [
            "#!/usr/bin/env bash",
            "set -e",
            'cd "$(dirname "$0")"',
            "echo '=== SaveDesktopDesign: Pakete installieren ==='",
        ]
        if (pkg_dir / "pacman-explicit.txt").exists():
            lines.append("echo; echo '--- Offizielle Pakete (pacman) ---'")
            lines.append("sudo pacman -S --needed - < pacman-explicit.txt || true")
        if (pkg_dir / "pacman-foreign.txt").exists():
            if helper:
                lines.append("echo; echo '--- AUR-Pakete ---'")
                lines.append(f"{Path(helper).name} -S --needed - < pacman-foreign.txt || true")
            else:
                lines.append("echo 'Kein AUR-Helper (paru/yay) gefunden — AUR-Pakete in pacman-foreign.txt'")
        if (pkg_dir / "flatpak.txt").exists():
            lines.append("echo; echo '--- Flatpaks ---'")
            lines.append("xargs -r -a flatpak.txt -I{} flatpak install -y --noninteractive flathub {} || true")
        lines.append("echo; echo 'Fertig! Fenster kann geschlossen werden.'; read -r -p 'Enter zum Beenden …'")
        script.write_text("\n".join(lines))
        script.chmod(0o755)

        term = shutil.which("konsole") or shutil.which("alacritty") or shutil.which("xterm")
        if not term:
            QMessageBox.warning(self, APP_NAME,
                                f"Kein Terminal gefunden. Bitte manuell ausführen:\n{script}")
            return
        if "konsole" in term:
            subprocess.Popen([term, "-e", "bash", str(script)])
        else:
            subprocess.Popen([term, "-e", f"bash {script}"])

    def restart_plasma(self):
        if QMessageBox.question(
                self, APP_NAME,
                "Plasma jetzt neu starten? Der Desktop ist kurz weg.") != QMessageBox.StandardButton.Yes:
            return
        subprocess.Popen(
            "kquitapp6 plasmashell 2>/dev/null || kquitapp5 plasmashell 2>/dev/null; "
            "sleep 1; (kstart plasmashell >/dev/null 2>&1 &) || (plasmashell --replace >/dev/null 2>&1 &)",
            shell=True)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
