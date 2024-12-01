import os
import sys
import subprocess
import winshell
from win32com.client import Dispatch

def create_shortcut():
    try:
        # Obtenir le chemin absolu de l'exécutable
        current_dir = os.path.dirname(os.path.abspath(__file__))
        exe_path = os.path.join(current_dir, "dist", "AutoDerush.exe")
        
        # Vérifier que l'exécutable existe
        if not os.path.exists(exe_path):
            print(f"Erreur : L'exécutable n'existe pas à {exe_path}")
            return False
            
        # Créer le raccourci
        desktop = winshell.desktop()
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(os.path.join(desktop, "AutoDerush.lnk"))
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = os.path.join(current_dir, "icon.ico")
        shortcut.save()
        
        print(f"Raccourci créé sur le bureau : {os.path.join(desktop, 'AutoDerush.lnk')}")
        return True
        
    except Exception as e:
        print(f"Erreur lors de la création du raccourci : {str(e)}")
        return False

if __name__ == "__main__":
    print("Création du raccourci...")
    if create_shortcut():
        print("Installation terminée avec succès !")
    else:
        print("Échec de la création du raccourci") 