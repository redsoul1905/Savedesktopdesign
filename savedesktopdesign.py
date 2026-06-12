#!/usr/bin/env python3
"""
SaveDesktopDesign — Sichert & restauriert das komplette KDE-Plasma-Design
(Themes, Icons, Schriften, KWin-Skripte, Plasma-Einstellungen, Kvantum,
Wallpaper, Panel-Layouts) sowie Paketlisten (pacman, AUR, Flatpak).

Für KDE Plasma auf Arch-basierten Systemen (CachyOS, EndeavourOS …),
Ubuntu/Debian (apt) und Fedora (dnf).
Benötigt PyQt6:  Arch: python-pyqt6 | Ubuntu/Fedora: python3-pyqt6

Sprachen: Deutsch, English, Français, Italiano, Español, Português, Türkçe
"""

import io
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

from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QProgressBar, QPushButton, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

HOME = Path.home()
APP_NAME = "SaveDesktopDesign"
VERSION = "1.3"

# ----------------------------------------------------------------------------
# Übersetzungen / Translations
# ----------------------------------------------------------------------------
LANG_NAMES = {
    "de": "Deutsch", "en": "English", "fr": "Français", "it": "Italiano",
    "es": "Español", "pt": "Português", "tr": "Türkçe",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "de": {
        "app_subtitle": "KDE-Design sichern & laden",
        "lang_label": "Sprache:",
        "tab_backup": "Sichern",
        "tab_restore": "Wiederherstellen",
        "backup_title": "Komplettes Plasma-Design + Paketlisten in eine Datei sichern",
        "choose_box": "Was soll gesichert werden?",
        "cat_plasma": "Plasma- & KWin-Einstellungen",
        "cat_gtk": "GTK- & Kvantum-Design (Glass etc.)",
        "cat_themes": "Themes, Icons & Cursor",
        "cat_fonts": "Schriften",
        "cat_kwin": "KWin-Skripte & Effekte",
        "cat_wallpaper": "Wallpaper & Konsole-Profile",
        "cat_packages": "Paketlisten (pacman / AUR / Flatpak)",
        "btn_backup": "  Backup erstellen …",
        "msg_select_one": "Bitte mindestens eine Kategorie auswählen.",
        "dlg_save": "Backup speichern unter …",
        "dlg_open": "Backup-Archiv wählen",
        "dlg_archive_filter": "Archiv (*.tar.gz)",
        "log_creating": "Backup wird erstellt …",
        "log_pkg_creating": "  + Paketlisten erzeugen …",
        "log_skipped": "  ! übersprungen",
        "done_prefix": "\n✔ Fertig: ",
        "msg_backup_done": "Backup erstellt:",
        "err_prefix": "\n✘ Fehler:\n",
        "msg_backup_failed": "Backup fehlgeschlagen — Details im Protokoll.",
        "restore_title": "Backup-Archiv laden und Design wiederherstellen",
        "restore_hint": "1-Klick-Restore: Archiv wählen → Dateien werden zurückkopiert.\n"
                        "Danach optional Pakete installieren und Plasma neu starten.",
        "btn_restore": "  Archiv wählen & wiederherstellen …",
        "btn_packages": "  Pakete installieren (öffnet Terminal)",
        "btn_plasma": "  Plasma neu starten (Design anwenden)",
        "mf_created": "Erstellt", "mf_host": "Rechner",
        "mf_categories": "Kategorien", "mf_packages": "Paketlisten",
        "yes": "ja", "no": "nein",
        "msg_confirm_restore": "Dieses Backup wiederherstellen?\nBestehende Einstellungen werden überschrieben.",
        "log_extracting": "Archiv wird entpackt …",
        "err_invalid_archive": "Ungültiges Archiv: kein 'home/'-Ordner enthalten.",
        "log_pkglists_saved": "Paketlisten gespeichert unter: ",
        "log_fontcache": "Schrift-Cache wird aktualisiert …",
        "log_kwin_reload": "KWin-Einstellungen werden neu geladen …",
        "log_restored": "\n✔ Design wiederhergestellt!",
        "msg_restored_pkg": "Design wiederhergestellt!\n\nJetzt optional Pakete installieren und Plasma neu starten (oder ab- und anmelden), damit alles greift.",
        "msg_restored": "Design wiederhergestellt!\n\nPlasma neu starten (oder ab- und anmelden), damit alles greift.",
        "msg_restore_failed": "Restore fehlgeschlagen — Details im Protokoll.",
        "msg_no_terminal": "Kein Terminal gefunden. Bitte manuell ausführen:\n",
        "msg_confirm_plasma": "Plasma jetzt neu starten? Der Desktop ist kurz weg.",
    },
    "en": {
        "app_subtitle": "Back up & restore your KDE design",
        "lang_label": "Language:",
        "tab_backup": "Back up",
        "tab_restore": "Restore",
        "backup_title": "Back up your complete Plasma design + package lists into one file",
        "choose_box": "What should be backed up?",
        "cat_plasma": "Plasma & KWin settings",
        "cat_gtk": "GTK & Kvantum design (Glass etc.)",
        "cat_themes": "Themes, icons & cursors",
        "cat_fonts": "Fonts",
        "cat_kwin": "KWin scripts & effects",
        "cat_wallpaper": "Wallpapers & Konsole profiles",
        "cat_packages": "Package lists (pacman / AUR / Flatpak)",
        "btn_backup": "  Create backup …",
        "msg_select_one": "Please select at least one category.",
        "dlg_save": "Save backup as …",
        "dlg_open": "Choose backup archive",
        "dlg_archive_filter": "Archive (*.tar.gz)",
        "log_creating": "Creating backup …",
        "log_pkg_creating": "  + Generating package lists …",
        "log_skipped": "  ! skipped",
        "done_prefix": "\n✔ Done: ",
        "msg_backup_done": "Backup created:",
        "err_prefix": "\n✘ Error:\n",
        "msg_backup_failed": "Backup failed — see log for details.",
        "restore_title": "Load a backup archive and restore your design",
        "restore_hint": "One-click restore: pick the archive → files are copied back.\n"
                        "Then optionally install packages and restart Plasma.",
        "btn_restore": "  Choose archive & restore …",
        "btn_packages": "  Install packages (opens a terminal)",
        "btn_plasma": "  Restart Plasma (apply design)",
        "mf_created": "Created", "mf_host": "Computer",
        "mf_categories": "Categories", "mf_packages": "Package lists",
        "yes": "yes", "no": "no",
        "msg_confirm_restore": "Restore this backup?\nExisting settings will be overwritten.",
        "log_extracting": "Extracting archive …",
        "err_invalid_archive": "Invalid archive: no 'home/' folder found.",
        "log_pkglists_saved": "Package lists saved to: ",
        "log_fontcache": "Updating font cache …",
        "log_kwin_reload": "Reloading KWin settings …",
        "log_restored": "\n✔ Design restored!",
        "msg_restored_pkg": "Design restored!\n\nOptionally install the packages now, then restart Plasma (or log out and back in) so everything takes effect.",
        "msg_restored": "Design restored!\n\nRestart Plasma (or log out and back in) so everything takes effect.",
        "msg_restore_failed": "Restore failed — see log for details.",
        "msg_no_terminal": "No terminal found. Please run manually:\n",
        "msg_confirm_plasma": "Restart Plasma now? The desktop will disappear briefly.",
    },
    "fr": {
        "app_subtitle": "Sauvegarder et restaurer votre design KDE",
        "lang_label": "Langue :",
        "tab_backup": "Sauvegarder",
        "tab_restore": "Restaurer",
        "backup_title": "Sauvegarder l'ensemble du design Plasma + listes de paquets dans un seul fichier",
        "choose_box": "Que faut-il sauvegarder ?",
        "cat_plasma": "Paramètres Plasma & KWin",
        "cat_gtk": "Design GTK & Kvantum (Glass, etc.)",
        "cat_themes": "Thèmes, icônes et curseurs",
        "cat_fonts": "Polices",
        "cat_kwin": "Scripts et effets KWin",
        "cat_wallpaper": "Fonds d'écran et profils Konsole",
        "cat_packages": "Listes de paquets (pacman / AUR / Flatpak)",
        "btn_backup": "  Créer une sauvegarde …",
        "msg_select_one": "Veuillez sélectionner au moins une catégorie.",
        "dlg_save": "Enregistrer la sauvegarde sous …",
        "dlg_open": "Choisir l'archive de sauvegarde",
        "dlg_archive_filter": "Archive (*.tar.gz)",
        "log_creating": "Création de la sauvegarde …",
        "log_pkg_creating": "  + Génération des listes de paquets …",
        "log_skipped": "  ! ignoré",
        "done_prefix": "\n✔ Terminé : ",
        "msg_backup_done": "Sauvegarde créée :",
        "err_prefix": "\n✘ Erreur :\n",
        "msg_backup_failed": "Échec de la sauvegarde — détails dans le journal.",
        "restore_title": "Charger une archive et restaurer le design",
        "restore_hint": "Restauration en un clic : choisissez l'archive → les fichiers sont recopiés.\n"
                        "Ensuite, installez éventuellement les paquets et redémarrez Plasma.",
        "btn_restore": "  Choisir l'archive et restaurer …",
        "btn_packages": "  Installer les paquets (ouvre un terminal)",
        "btn_plasma": "  Redémarrer Plasma (appliquer le design)",
        "mf_created": "Créée", "mf_host": "Ordinateur",
        "mf_categories": "Catégories", "mf_packages": "Listes de paquets",
        "yes": "oui", "no": "non",
        "msg_confirm_restore": "Restaurer cette sauvegarde ?\nLes paramètres existants seront écrasés.",
        "log_extracting": "Extraction de l'archive …",
        "err_invalid_archive": "Archive non valide : aucun dossier « home/ ».",
        "log_pkglists_saved": "Listes de paquets enregistrées dans : ",
        "log_fontcache": "Mise à jour du cache des polices …",
        "log_kwin_reload": "Rechargement des paramètres KWin …",
        "log_restored": "\n✔ Design restauré !",
        "msg_restored_pkg": "Design restauré !\n\nInstallez éventuellement les paquets, puis redémarrez Plasma (ou déconnectez-vous et reconnectez-vous) pour tout appliquer.",
        "msg_restored": "Design restauré !\n\nRedémarrez Plasma (ou déconnectez-vous et reconnectez-vous) pour tout appliquer.",
        "msg_restore_failed": "Échec de la restauration — détails dans le journal.",
        "msg_no_terminal": "Aucun terminal trouvé. Veuillez exécuter manuellement :\n",
        "msg_confirm_plasma": "Redémarrer Plasma maintenant ? Le bureau disparaîtra brièvement.",
    },
    "it": {
        "app_subtitle": "Salva e ripristina il tuo design KDE",
        "lang_label": "Lingua:",
        "tab_backup": "Salva",
        "tab_restore": "Ripristina",
        "backup_title": "Salva l'intero design Plasma + elenchi dei pacchetti in un unico file",
        "choose_box": "Cosa salvare?",
        "cat_plasma": "Impostazioni Plasma e KWin",
        "cat_gtk": "Design GTK e Kvantum (Glass ecc.)",
        "cat_themes": "Temi, icone e cursori",
        "cat_fonts": "Caratteri",
        "cat_kwin": "Script ed effetti KWin",
        "cat_wallpaper": "Sfondi e profili Konsole",
        "cat_packages": "Elenchi dei pacchetti (pacman / AUR / Flatpak)",
        "btn_backup": "  Crea backup …",
        "msg_select_one": "Seleziona almeno una categoria.",
        "dlg_save": "Salva il backup come …",
        "dlg_open": "Scegli l'archivio di backup",
        "dlg_archive_filter": "Archivio (*.tar.gz)",
        "log_creating": "Creazione del backup …",
        "log_pkg_creating": "  + Generazione elenchi pacchetti …",
        "log_skipped": "  ! saltato",
        "done_prefix": "\n✔ Fatto: ",
        "msg_backup_done": "Backup creato:",
        "err_prefix": "\n✘ Errore:\n",
        "msg_backup_failed": "Backup non riuscito — dettagli nel registro.",
        "restore_title": "Carica un archivio di backup e ripristina il design",
        "restore_hint": "Ripristino con un clic: scegli l'archivio → i file vengono ricopiati.\n"
                        "Poi, se vuoi, installa i pacchetti e riavvia Plasma.",
        "btn_restore": "  Scegli archivio e ripristina …",
        "btn_packages": "  Installa i pacchetti (apre un terminale)",
        "btn_plasma": "  Riavvia Plasma (applica il design)",
        "mf_created": "Creato", "mf_host": "Computer",
        "mf_categories": "Categorie", "mf_packages": "Elenchi pacchetti",
        "yes": "sì", "no": "no",
        "msg_confirm_restore": "Ripristinare questo backup?\nLe impostazioni esistenti verranno sovrascritte.",
        "log_extracting": "Estrazione dell'archivio …",
        "err_invalid_archive": "Archivio non valido: cartella 'home/' mancante.",
        "log_pkglists_saved": "Elenchi pacchetti salvati in: ",
        "log_fontcache": "Aggiornamento della cache dei caratteri …",
        "log_kwin_reload": "Ricaricamento delle impostazioni KWin …",
        "log_restored": "\n✔ Design ripristinato!",
        "msg_restored_pkg": "Design ripristinato!\n\nSe vuoi, installa ora i pacchetti, poi riavvia Plasma (o esci e rientra) per applicare tutto.",
        "msg_restored": "Design ripristinato!\n\nRiavvia Plasma (o esci e rientra) per applicare tutto.",
        "msg_restore_failed": "Ripristino non riuscito — dettagli nel registro.",
        "msg_no_terminal": "Nessun terminale trovato. Esegui manualmente:\n",
        "msg_confirm_plasma": "Riavviare Plasma adesso? Il desktop sparirà per un momento.",
    },
    "es": {
        "app_subtitle": "Guardar y restaurar tu diseño KDE",
        "lang_label": "Idioma:",
        "tab_backup": "Guardar",
        "tab_restore": "Restaurar",
        "backup_title": "Guarda todo el diseño de Plasma + listas de paquetes en un solo archivo",
        "choose_box": "¿Qué se debe guardar?",
        "cat_plasma": "Ajustes de Plasma y KWin",
        "cat_gtk": "Diseño GTK y Kvantum (Glass, etc.)",
        "cat_themes": "Temas, iconos y cursores",
        "cat_fonts": "Fuentes",
        "cat_kwin": "Scripts y efectos de KWin",
        "cat_wallpaper": "Fondos de pantalla y perfiles de Konsole",
        "cat_packages": "Listas de paquetes (pacman / AUR / Flatpak)",
        "btn_backup": "  Crear copia de seguridad …",
        "msg_select_one": "Selecciona al menos una categoría.",
        "dlg_save": "Guardar copia de seguridad como …",
        "dlg_open": "Elegir archivo de copia de seguridad",
        "dlg_archive_filter": "Archivo (*.tar.gz)",
        "log_creating": "Creando la copia de seguridad …",
        "log_pkg_creating": "  + Generando listas de paquetes …",
        "log_skipped": "  ! omitido",
        "done_prefix": "\n✔ Listo: ",
        "msg_backup_done": "Copia de seguridad creada:",
        "err_prefix": "\n✘ Error:\n",
        "msg_backup_failed": "La copia de seguridad falló — detalles en el registro.",
        "restore_title": "Cargar un archivo de copia y restaurar el diseño",
        "restore_hint": "Restauración con un clic: elige el archivo → los archivos se copian de vuelta.\n"
                        "Después, opcionalmente instala los paquetes y reinicia Plasma.",
        "btn_restore": "  Elegir archivo y restaurar …",
        "btn_packages": "  Instalar paquetes (abre una terminal)",
        "btn_plasma": "  Reiniciar Plasma (aplicar el diseño)",
        "mf_created": "Creado", "mf_host": "Equipo",
        "mf_categories": "Categorías", "mf_packages": "Listas de paquetes",
        "yes": "sí", "no": "no",
        "msg_confirm_restore": "¿Restaurar esta copia de seguridad?\nSe sobrescribirán los ajustes actuales.",
        "log_extracting": "Extrayendo el archivo …",
        "err_invalid_archive": "Archivo no válido: no contiene la carpeta 'home/'.",
        "log_pkglists_saved": "Listas de paquetes guardadas en: ",
        "log_fontcache": "Actualizando la caché de fuentes …",
        "log_kwin_reload": "Recargando los ajustes de KWin …",
        "log_restored": "\n✔ ¡Diseño restaurado!",
        "msg_restored_pkg": "¡Diseño restaurado!\n\nOpcionalmente instala ahora los paquetes y reinicia Plasma (o cierra y vuelve a iniciar sesión) para que todo surta efecto.",
        "msg_restored": "¡Diseño restaurado!\n\nReinicia Plasma (o cierra y vuelve a iniciar sesión) para que todo surta efecto.",
        "msg_restore_failed": "La restauración falló — detalles en el registro.",
        "msg_no_terminal": "No se encontró ninguna terminal. Ejecuta manualmente:\n",
        "msg_confirm_plasma": "¿Reiniciar Plasma ahora? El escritorio desaparecerá un momento.",
    },
    "pt": {
        "app_subtitle": "Salvar e restaurar seu design KDE",
        "lang_label": "Idioma:",
        "tab_backup": "Salvar",
        "tab_restore": "Restaurar",
        "backup_title": "Salve todo o design do Plasma + listas de pacotes em um único arquivo",
        "choose_box": "O que deve ser salvo?",
        "cat_plasma": "Configurações do Plasma e KWin",
        "cat_gtk": "Design GTK e Kvantum (Glass etc.)",
        "cat_themes": "Temas, ícones e cursores",
        "cat_fonts": "Fontes",
        "cat_kwin": "Scripts e efeitos do KWin",
        "cat_wallpaper": "Papéis de parede e perfis do Konsole",
        "cat_packages": "Listas de pacotes (pacman / AUR / Flatpak)",
        "btn_backup": "  Criar backup …",
        "msg_select_one": "Selecione pelo menos uma categoria.",
        "dlg_save": "Salvar backup como …",
        "dlg_open": "Escolher arquivo de backup",
        "dlg_archive_filter": "Arquivo (*.tar.gz)",
        "log_creating": "Criando o backup …",
        "log_pkg_creating": "  + Gerando listas de pacotes …",
        "log_skipped": "  ! ignorado",
        "done_prefix": "\n✔ Concluído: ",
        "msg_backup_done": "Backup criado:",
        "err_prefix": "\n✘ Erro:\n",
        "msg_backup_failed": "Falha no backup — detalhes no registro.",
        "restore_title": "Carregar um arquivo de backup e restaurar o design",
        "restore_hint": "Restauração com um clique: escolha o arquivo → os arquivos são copiados de volta.\n"
                        "Depois, opcionalmente instale os pacotes e reinicie o Plasma.",
        "btn_restore": "  Escolher arquivo e restaurar …",
        "btn_packages": "  Instalar pacotes (abre um terminal)",
        "btn_plasma": "  Reiniciar o Plasma (aplicar o design)",
        "mf_created": "Criado", "mf_host": "Computador",
        "mf_categories": "Categorias", "mf_packages": "Listas de pacotes",
        "yes": "sim", "no": "não",
        "msg_confirm_restore": "Restaurar este backup?\nAs configurações existentes serão substituídas.",
        "log_extracting": "Extraindo o arquivo …",
        "err_invalid_archive": "Arquivo inválido: pasta 'home/' não encontrada.",
        "log_pkglists_saved": "Listas de pacotes salvas em: ",
        "log_fontcache": "Atualizando o cache de fontes …",
        "log_kwin_reload": "Recarregando as configurações do KWin …",
        "log_restored": "\n✔ Design restaurado!",
        "msg_restored_pkg": "Design restaurado!\n\nOpcionalmente instale os pacotes agora e reinicie o Plasma (ou saia e entre novamente) para aplicar tudo.",
        "msg_restored": "Design restaurado!\n\nReinicie o Plasma (ou saia e entre novamente) para aplicar tudo.",
        "msg_restore_failed": "Falha na restauração — detalhes no registro.",
        "msg_no_terminal": "Nenhum terminal encontrado. Execute manualmente:\n",
        "msg_confirm_plasma": "Reiniciar o Plasma agora? A área de trabalho sumirá por um instante.",
    },
    "tr": {
        "app_subtitle": "KDE tasarımınızı yedekleyin ve geri yükleyin",
        "lang_label": "Dil:",
        "tab_backup": "Yedekle",
        "tab_restore": "Geri Yükle",
        "backup_title": "Tüm Plasma tasarımını + paket listelerini tek dosyada yedekleyin",
        "choose_box": "Neler yedeklensin?",
        "cat_plasma": "Plasma ve KWin ayarları",
        "cat_gtk": "GTK ve Kvantum tasarımı (Glass vb.)",
        "cat_themes": "Temalar, simgeler ve imleçler",
        "cat_fonts": "Yazı tipleri",
        "cat_kwin": "KWin betikleri ve efektleri",
        "cat_wallpaper": "Duvar kâğıtları ve Konsole profilleri",
        "cat_packages": "Paket listeleri (pacman / AUR / Flatpak)",
        "btn_backup": "  Yedek oluştur …",
        "msg_select_one": "Lütfen en az bir kategori seçin.",
        "dlg_save": "Yedeği farklı kaydet …",
        "dlg_open": "Yedek arşivini seç",
        "dlg_archive_filter": "Arşiv (*.tar.gz)",
        "log_creating": "Yedek oluşturuluyor …",
        "log_pkg_creating": "  + Paket listeleri oluşturuluyor …",
        "log_skipped": "  ! atlandı",
        "done_prefix": "\n✔ Tamamlandı: ",
        "msg_backup_done": "Yedek oluşturuldu:",
        "err_prefix": "\n✘ Hata:\n",
        "msg_backup_failed": "Yedekleme başarısız — ayrıntılar günlükte.",
        "restore_title": "Yedek arşivini yükleyin ve tasarımı geri getirin",
        "restore_hint": "Tek tıkla geri yükleme: arşivi seçin → dosyalar geri kopyalanır.\n"
                        "Ardından isteğe bağlı paketleri kurun ve Plasma'yı yeniden başlatın.",
        "btn_restore": "  Arşiv seç ve geri yükle …",
        "btn_packages": "  Paketleri kur (terminal açılır)",
        "btn_plasma": "  Plasma'yı yeniden başlat (tasarımı uygula)",
        "mf_created": "Oluşturulma", "mf_host": "Bilgisayar",
        "mf_categories": "Kategoriler", "mf_packages": "Paket listeleri",
        "yes": "evet", "no": "hayır",
        "msg_confirm_restore": "Bu yedek geri yüklensin mi?\nMevcut ayarların üzerine yazılacak.",
        "log_extracting": "Arşiv çıkarılıyor …",
        "err_invalid_archive": "Geçersiz arşiv: 'home/' klasörü yok.",
        "log_pkglists_saved": "Paket listeleri şuraya kaydedildi: ",
        "log_fontcache": "Yazı tipi önbelleği güncelleniyor …",
        "log_kwin_reload": "KWin ayarları yeniden yükleniyor …",
        "log_restored": "\n✔ Tasarım geri yüklendi!",
        "msg_restored_pkg": "Tasarım geri yüklendi!\n\nİsterseniz şimdi paketleri kurun, ardından her şeyin etkinleşmesi için Plasma'yı yeniden başlatın (veya oturumu kapatıp açın).",
        "msg_restored": "Tasarım geri yüklendi!\n\nHer şeyin etkinleşmesi için Plasma'yı yeniden başlatın (veya oturumu kapatıp açın).",
        "msg_restore_failed": "Geri yükleme başarısız — ayrıntılar günlükte.",
        "msg_no_terminal": "Terminal bulunamadı. Lütfen elle çalıştırın:\n",
        "msg_confirm_plasma": "Plasma şimdi yeniden başlatılsın mı? Masaüstü kısa süreliğine kaybolur.",
    },
}

_current_lang = "de"


def T(key: str) -> str:
    """Übersetzten Text für die aktuelle Sprache liefern."""
    return TRANSLATIONS.get(_current_lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key))


def detect_language(settings: QSettings) -> str:
    saved = settings.value("language", "")
    if saved in TRANSLATIONS:
        return saved
    env = (os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES")
           or os.environ.get("LANG") or "en")[:2].lower()
    return env if env in TRANSLATIONS else "en"


# ----------------------------------------------------------------------------
# Was gesichert wird — Pfade relativ zum Home-Verzeichnis
# (Schlüssel = stabile IDs, Anzeigename kommt aus den Übersetzungen)
# ----------------------------------------------------------------------------
CATEGORIES: dict[str, list[str]] = {
    "cat_plasma": [
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
    "cat_gtk": [
        ".config/gtkrc",
        ".config/gtkrc-2.0",
        ".config/gtk-3.0",
        ".config/gtk-4.0",
        ".config/Kvantum",
        ".gtkrc-2.0",
    ],
    "cat_themes": [
        ".local/share/plasma",            # Desktop-Themes, Look&Feel, Plasmoids
        ".local/share/aurorae",           # Fensterdekorationen
        ".local/share/color-schemes",
        ".local/share/icons",
        ".local/share/themes",
        ".themes",
        ".icons",
    ],
    "cat_fonts": [
        ".local/share/fonts",
        ".fonts",
        ".config/fontconfig",
        ".local/share/kfontinst",
    ],
    "cat_kwin": [
        ".local/share/kwin",              # Skripte, Effekte, Tabbox
        ".local/share/kservices5",
        ".local/share/kservices6",
        ".local/share/knewstuff3",
    ],
    "cat_wallpaper": [
        ".local/share/wallpapers",
        ".local/share/konsole",
        ".local/share/kxmlgui5",
        ".local/share/kxmlgui6",
    ],
}


def _run_cmd(cmd: list[str], timeout: int = 120) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return out.stdout if out.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def gather_package_lists() -> dict[str, str]:
    """Erzeugt Paketlisten als {dateiname: inhalt} — pacman, apt, dnf, flatpak."""
    lists: dict[str, str] = {}

    if shutil.which("pacman"):
        for fname, cmd in {
            "pacman-explicit.txt": ["pacman", "-Qqen"],   # explizit, offizielle Repos
            "pacman-foreign.txt": ["pacman", "-Qqem"],    # AUR / fremd
        }.items():
            out = _run_cmd(cmd)
            if out:
                lists[fname] = out

    if shutil.which("apt-mark"):                          # Ubuntu / Debian
        out = _run_cmd(["apt-mark", "showmanual"])
        if out:
            lists["apt-manual.txt"] = out

    if shutil.which("dnf"):                               # Fedora
        out = (_run_cmd(["dnf", "repoquery", "--userinstalled",
                         "--queryformat", "%{name}\n"], 300)
               or _run_cmd(["dnf", "repoquery", "--userinstalled"], 300))
        if out:
            # Duplikate entfernen, leere Zeilen filtern
            names = sorted({l.strip() for l in out.splitlines() if l.strip()})
            lists["dnf-packages.txt"] = "\n".join(names) + "\n"

    if shutil.which("flatpak"):
        out = _run_cmd(["flatpak", "list", "--app", "--columns=application"])
        if out:
            lists["flatpak.txt"] = out

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
                        self.log.emit(f"{T('log_skipped')} ({e})")
                    done += 1
                    self.progress.emit(int(done / total * 100))

                if self.with_packages:
                    self.log.emit(T("log_pkg_creating"))
                    for fname, content in gather_package_lists().items():
                        data = content.encode()
                        info = tarfile.TarInfo(f"packages/{fname}")
                        info.size = len(data)
                        info.mtime = int(datetime.now().timestamp())
                        tar.addfile(info, io.BytesIO(data))
                    done += 1
                    self.progress.emit(int(done / total * 100))

                mdata = json.dumps(manifest, indent=2).encode()
                info = tarfile.TarInfo("manifest.json")
                info.size = len(mdata)
                info.mtime = int(datetime.now().timestamp())
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
                self.log.emit(T("log_extracting"))
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
                    self.failed.emit(T("err_invalid_archive"))
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
                    self.log.emit(T("log_pkglists_saved") + str(dest))

                self.log.emit(T("log_fontcache"))
                subprocess.run(["fc-cache", "-f"], capture_output=True, timeout=300)

                # KWin & Co. zwingen, die restaurierten Configs sofort zu laden —
                # sonst überschreibt die laufende Sitzung sie beim Abmelden wieder
                self.log.emit(T("log_kwin_reload"))
                for qdbus in ("qdbus6", "qdbus", "qdbus-qt6", "qdbus-qt5"):
                    if shutil.which(qdbus):
                        subprocess.run([qdbus, "org.kde.KWin", "/KWin", "reconfigure"],
                                       capture_output=True, timeout=30)
                        break
                for sycoca in ("kbuildsycoca6", "kbuildsycoca5"):
                    if shutil.which(sycoca):
                        subprocess.run([sycoca], capture_output=True, timeout=120)
                        break

                self.progress.emit(100)
                self.finished_ok.emit(has_packages)
        except Exception:
            self.failed.emit(traceback.format_exc())

    def _copy_into_home(self, entry: Path, src_root: Path):
        rel = entry.relative_to(src_root)
        target = HOME / rel
        self.log.emit(f"  → {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        self._merge(entry, target)

    def _remove_existing(self, dst: Path):
        """Vorhandenes Ziel (Datei, Symlink oder Ordner) entfernen."""
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink()

    def _merge(self, src: Path, dst: Path):
        """Rekursives Kopieren, das vorhandene Dateien/Symlinks ersetzt.
        Einzelne Fehler werden protokolliert, brechen aber nicht alles ab."""
        try:
            if src.is_symlink():
                link = os.readlink(src)
                if os.path.lexists(dst):
                    self._remove_existing(dst)
                os.symlink(link, dst)
            elif src.is_dir():
                if os.path.lexists(dst) and not (dst.is_dir() and not dst.is_symlink()):
                    self._remove_existing(dst)
                dst.mkdir(parents=True, exist_ok=True)
                for child in src.iterdir():
                    self._merge(child, dst / child.name)
            else:
                if os.path.lexists(dst):
                    self._remove_existing(dst)
                shutil.copy2(src, dst)
        except OSError as e:
            self.log.emit(f"{T('log_skipped')} {dst} ({e})")


# ----------------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        global _current_lang
        self.settings = QSettings(APP_NAME, APP_NAME)
        _current_lang = detect_language(self.settings)
        self.setWindowIcon(QIcon.fromTheme("preferences-desktop-theme"))
        self.resize(720, 660)
        self.worker = None
        self._build_ui()

    # ---------------- UI-Aufbau (bei Sprachwechsel neu) ----------------
    def _build_ui(self):
        self.setWindowTitle(f"{APP_NAME} {VERSION} — {T('app_subtitle')}")

        root = QWidget()
        root_lay = QVBoxLayout(root)

        # Sprachauswahl oben rechts
        lang_lay = QHBoxLayout()
        lang_lay.addStretch()
        lang_lay.addWidget(QLabel(T("lang_label")))
        self.lang_combo = QComboBox()
        for code, name in LANG_NAMES.items():
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(list(LANG_NAMES).index(_current_lang))
        self.lang_combo.currentIndexChanged.connect(self._change_language)
        lang_lay.addWidget(self.lang_combo)
        root_lay.addLayout(lang_lay)

        tabs = QTabWidget()
        tabs.addTab(self._build_backup_tab(), QIcon.fromTheme("document-save"), T("tab_backup"))
        tabs.addTab(self._build_restore_tab(), QIcon.fromTheme("document-open"), T("tab_restore"))
        root_lay.addWidget(tabs)
        self.setCentralWidget(root)

    def _change_language(self):
        global _current_lang
        code = self.lang_combo.currentData()
        if code and code != _current_lang:
            _current_lang = code
            self.settings.setValue("language", code)
            self._build_ui()

    # ---------------- Backup-Tab ----------------
    def _build_backup_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        title = QLabel(T("backup_title"))
        f = QFont(); f.setPointSize(12); f.setBold(True)
        title.setFont(f)
        title.setWordWrap(True)
        lay.addWidget(title)

        box = QGroupBox(T("choose_box"))
        blay = QVBoxLayout(box)
        self.cat_checks: dict[str, QCheckBox] = {}
        for cat_id in CATEGORIES:
            cb = QCheckBox(T(cat_id))
            cb.setChecked(True)
            self.cat_checks[cat_id] = cb
            blay.addWidget(cb)
        self.pkg_check = QCheckBox(T("cat_packages"))
        self.pkg_check.setChecked(True)
        blay.addWidget(self.pkg_check)
        lay.addWidget(box)

        self.backup_btn = QPushButton(QIcon.fromTheme("document-save"), T("btn_backup"))
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
            QMessageBox.warning(self, APP_NAME, T("msg_select_one"))
            return
        default = str(HOME / f"plasma-design-{datetime.now():%Y-%m-%d}.tar.gz")
        dest, _ = QFileDialog.getSaveFileName(
            self, T("dlg_save"), default, T("dlg_archive_filter"))
        if not dest:
            return
        if not dest.endswith(".tar.gz"):
            dest += ".tar.gz"

        self.backup_btn.setEnabled(False)
        self.backup_log.clear()
        self.backup_log.append(T("log_creating"))
        self.worker = BackupWorker(dest, cats, self.pkg_check.isChecked())
        self.worker.log.connect(self.backup_log.append)
        self.worker.progress.connect(self.backup_progress.setValue)
        self.worker.finished_ok.connect(self._backup_done)
        self.worker.failed.connect(self._backup_fail)
        self.worker.start()

    def _backup_done(self, info: str):
        self.backup_btn.setEnabled(True)
        self.backup_log.append(T("done_prefix") + info)
        QMessageBox.information(self, APP_NAME, f"{T('msg_backup_done')}\n{info}")

    def _backup_fail(self, err: str):
        self.backup_btn.setEnabled(True)
        self.backup_log.append(T("err_prefix") + err)
        QMessageBox.critical(self, APP_NAME, T("msg_backup_failed"))

    # ---------------- Restore-Tab ----------------
    def _build_restore_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        title = QLabel(T("restore_title"))
        f = QFont(); f.setPointSize(12); f.setBold(True)
        title.setFont(f)
        title.setWordWrap(True)
        lay.addWidget(title)

        hint = QLabel(T("restore_hint"))
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self.restore_btn = QPushButton(QIcon.fromTheme("document-open"), T("btn_restore"))
        self.restore_btn.setMinimumHeight(42)
        self.restore_btn.clicked.connect(self.start_restore)
        lay.addWidget(self.restore_btn)

        self.pkg_btn = QPushButton(QIcon.fromTheme("system-software-install"), T("btn_packages"))
        self.pkg_btn.setEnabled(False)
        self.pkg_btn.clicked.connect(self.install_packages)
        lay.addWidget(self.pkg_btn)

        self.plasma_btn = QPushButton(QIcon.fromTheme("system-reboot"), T("btn_plasma"))
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
            self, T("dlg_open"), str(HOME), T("dlg_archive_filter"))
        if not archive:
            return

        # Manifest anzeigen
        info_txt = ""
        try:
            with tarfile.open(archive, "r:gz") as tar:
                mf = tar.extractfile("manifest.json")
                if mf:
                    m = json.loads(mf.read())
                    info_txt = (f"{T('mf_created')}: {m.get('created')}\n"
                                f"{T('mf_host')}: {m.get('hostname')}\n"
                                f"{T('mf_categories')}: {len(m.get('categories', []))}\n"
                                f"{T('mf_packages')}: "
                                f"{T('yes') if m.get('with_packages') else T('no')}")
        except Exception:
            pass

        msg = T("msg_confirm_restore")
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
        self.restore_log.append(T("log_restored"))
        QMessageBox.information(
            self, APP_NAME,
            T("msg_restored_pkg") if has_packages else T("msg_restored"))

    def _restore_fail(self, err: str):
        self.restore_btn.setEnabled(True)
        self.restore_log.append(T("err_prefix") + err)
        QMessageBox.critical(self, APP_NAME, T("msg_restore_failed"))

    def install_packages(self):
        pkg_dir = HOME / ".savedesktopdesign-packages"
        script = pkg_dir / "install.sh"
        lines = [
            "#!/usr/bin/env bash",
            "set -e",
            'cd "$(dirname "$0")"',
            "echo '=== SaveDesktopDesign ==='",
        ]
        # --- Arch / CachyOS ---
        if (pkg_dir / "pacman-explicit.txt").exists():
            if shutil.which("pacman"):
                lines.append("echo; echo '--- pacman ---'")
                lines.append("sudo pacman -S --needed - < pacman-explicit.txt || true")
            else:
                lines.append("echo 'pacman list found, but this is not an Arch system — skipping.'")
        if (pkg_dir / "pacman-foreign.txt").exists() and shutil.which("pacman"):
            lines += [
                "echo; echo '--- AUR ---'",
                # AUR-Helper automatisch nachinstallieren, falls keiner da ist
                "if ! command -v paru >/dev/null 2>&1 && ! command -v yay >/dev/null 2>&1; then",
                "  echo 'No AUR helper found - installing paru ...'",
                "  sudo pacman -S --needed --noconfirm base-devel git",
                "  rm -rf /tmp/sdd-paru",
                "  git clone https://aur.archlinux.org/paru-bin.git /tmp/sdd-paru",
                "  (cd /tmp/sdd-paru && makepkg -si --noconfirm) || echo 'paru installation failed'",
                "fi",
                'AURHELPER="$(command -v paru || command -v yay || true)"',
                'if [ -n "$AURHELPER" ]; then',
                '  "$AURHELPER" -S --needed - < pacman-foreign.txt || true',
                "else",
                "  echo 'Skipping AUR packages (no helper available) - see pacman-foreign.txt'",
                "fi",
            ]
        # --- Ubuntu / Debian ---
        if (pkg_dir / "apt-manual.txt").exists():
            if shutil.which("apt-get"):
                lines.append("echo; echo '--- apt ---'")
                lines.append("sudo apt-get update")
                lines.append("xargs -r -a apt-manual.txt sudo apt-get install -y --ignore-missing || true")
            else:
                lines.append("echo 'apt list found, but apt is not available — skipping.'")
        # --- Fedora ---
        if (pkg_dir / "dnf-packages.txt").exists():
            if shutil.which("dnf"):
                lines.append("echo; echo '--- dnf ---'")
                lines.append("xargs -r -a dnf-packages.txt sudo dnf install -y --skip-broken || "
                             "xargs -r -a dnf-packages.txt sudo dnf install -y || true")
            else:
                lines.append("echo 'dnf list found, but dnf is not available — skipping.'")
        # --- Flatpak (alle Distros) ---
        if (pkg_dir / "flatpak.txt").exists():
            if shutil.which("flatpak"):
                lines.append("echo; echo '--- Flatpak ---'")
                lines.append("xargs -r -a flatpak.txt -I{} flatpak install -y --noninteractive flathub {} || true")
            else:
                lines.append("echo 'flatpak list found, but flatpak is not installed — skipping.'")
        lines.append("echo; echo 'Done!'; read -r -p 'Enter …'")
        script.write_text("\n".join(lines))
        script.chmod(0o755)

        term = (shutil.which("konsole") or shutil.which("gnome-terminal")
                or shutil.which("xfce4-terminal") or shutil.which("alacritty")
                or shutil.which("xterm"))
        if not term:
            QMessageBox.warning(self, APP_NAME, T("msg_no_terminal") + str(script))
            return
        if "konsole" in term:
            subprocess.Popen([term, "-e", "bash", str(script)])
        elif "gnome-terminal" in term:
            subprocess.Popen([term, "--", "bash", str(script)])
        else:
            subprocess.Popen([term, "-e", f"bash {script}"])

    def restart_plasma(self):
        if QMessageBox.question(
                self, APP_NAME, T("msg_confirm_plasma")) != QMessageBox.StandardButton.Yes:
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
