import sys
import shutil
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

# Ajouter le dossier parent au path pour permettre les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from video_cutter.ui.main_window import MainWindow

def show_error(title, message):
    """Affiche une boîte de dialogue d'erreur"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.exec()

def check_ffmpeg():
    """Vérifie si FFmpeg est disponible dans le système"""
    try:
        if not shutil.which('ffmpeg'):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("FFmpeg n'est pas installé ou n'est pas dans le PATH du système")
            msg.setInformativeText("Veuillez installer FFmpeg pour utiliser cette application.\n"
                                "Vous pouvez le télécharger sur : https://ffmpeg.org/download.html")
            msg.setWindowTitle("Erreur - FFmpeg manquant")
            msg.exec()
            return False
        return True
    except Exception as e:
        show_error("Erreur FFmpeg", f"Erreur lors de la vérification de FFmpeg : {str(e)}")
        return False

def main():
    # Créer l'application Qt
    app = QApplication(sys.argv)
    
    # Configurer le style
    app.setStyle("Fusion")
    
    # Vérifier FFmpeg
    if not check_ffmpeg():
        return
    
    # Créer et afficher la fenêtre principale
    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    
    # Démarrer l'application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
