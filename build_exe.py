import PyInstaller.__main__
import os

# Chemin vers l'icône
icon_path = os.path.join('resources', 'icon.ico')

# Configuration de PyInstaller
PyInstaller.__main__.run([
    'video_cutter/main.py',  # Script principal
    '--name=AutoDerush',     # Nom de l'exécutable
    '--onefile',             # Créer un seul fichier
    '--windowed',            # Mode fenêtré (pas de console)
    '--icon=' + icon_path,   # Icône de l'application
    '--add-data=resources;resources',  # Inclure les ressources
    '--clean',               # Nettoyer les fichiers temporaires
    # Ajouter les dépendances nécessaires
    '--hidden-import=librosa',
    '--hidden-import=numpy',
    '--hidden-import=soundfile',
    '--hidden-import=PyQt6',
]) 