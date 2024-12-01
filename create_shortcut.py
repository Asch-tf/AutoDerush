import os
import sys
import subprocess
import winshell
from win32com.client import Dispatch
from pathlib import Path

def create_executable():
    """Crée l'exécutable avec PyInstaller"""
    try:
        # Installer PyInstaller si nécessaire
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        
        # Créer l'exécutable
        subprocess.run(["pyinstaller", "AutoDerush.spec"], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la création de l'exécutable : {e}")
        return False

def create_desktop_shortcut():
    """Crée un raccourci sur le bureau"""
    try:
        # Chemin de l'exécutable
        exe_path = os.path.abspath(os.path.join("dist", "AutoDerush", "AutoDerush.exe"))
        if not os.path.exists(exe_path):
            print(f"L'exécutable n'existe pas : {exe_path}")
            return False
        
        # Chemin du bureau
        desktop = Path(winshell.desktop())
        shortcut_path = os.path.join(desktop, "AutoDerush.lnk")
        
        # Créer le raccourci
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()
        
        print(f"Raccourci créé sur le bureau : {shortcut_path}")
        return True
        
    except Exception as e:
        print(f"Erreur lors de la création du raccourci : {e}")
        return False

def main():
    # Créer l'exécutable
    print("Création de l'exécutable...")
    if not create_executable():
        print("Échec de la création de l'exécutable")
        return
    
    # Créer le raccourci
    print("Création du raccourci sur le bureau...")
    if not create_desktop_shortcut():
        print("Échec de la création du raccourci")
        return
    
    print("Installation terminée avec succès !")

if __name__ == "__main__":
    main() 