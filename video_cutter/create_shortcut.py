import os
import sys
from win32com.client import Dispatch
import winshell

def create_shortcut():
    # Obtenir le chemin du bureau
    desktop = winshell.desktop()
    
    # Chemin complet vers le fichier batch
    path = os.path.abspath("launch.bat")
    
    # Créer le raccourci
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(os.path.join(desktop, "Video Cutter.lnk"))
    shortcut.Targetpath = path
    shortcut.WorkingDirectory = os.path.dirname(path)
    shortcut.IconLocation = sys.executable  # Utilise l'icône de Python
    shortcut.save()

if __name__ == "__main__":
    create_shortcut() 