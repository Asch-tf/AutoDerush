from PIL import Image, ImageDraw
import os

def create_logo(size=(256, 256)):
    try:
        # Créer une nouvelle image avec fond transparent
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Couleurs
        screen_color = (41, 128, 185)  # Bleu
        lightning_color = (241, 196, 15)  # Jaune
        
        # Dimensions de l'écran
        margin = size[0] // 8
        screen_left = margin
        screen_right = size[0] - margin
        screen_top = margin
        screen_bottom = size[1] - margin
        
        # Dessiner l'écran (rectangle avec coins arrondis)
        draw.rounded_rectangle(
            [screen_left, screen_top, screen_right, screen_bottom],
            radius=20,
            fill=screen_color
        )
        
        # Points pour l'éclair
        lightning_width = size[0] // 20
        center_x = size[0] // 2
        center_y = size[1] // 2
        
        # Dessiner l'éclair
        lightning_points = [
            (center_x - lightning_width*2, screen_top + margin),
            (center_x + lightning_width, center_y - lightning_width),
            (center_x - lightning_width, center_y),
            (center_x + lightning_width*2, screen_bottom - margin),
            (center_x - lightning_width, center_y + lightning_width),
            (center_x + lightning_width, center_y),
            (center_x - lightning_width*2, screen_top + margin)
        ]
        
        draw.polygon(lightning_points, fill=lightning_color)
        
        # Créer le dossier resources s'il n'existe pas
        os.makedirs('resources', exist_ok=True)
        
        # Sauvegarder d'abord en PNG puis convertir en ICO
        png_path = 'resources/temp_icon.png'
        ico_path = 'resources/icon.ico'
        
        # Sauvegarder en PNG
        image.save(png_path, format='PNG')
        
        # Convertir en ICO
        img = Image.open(png_path)
        img.save(ico_path, format='ICO', sizes=[(256, 256)])
        
        # Supprimer le fichier PNG temporaire
        os.remove(png_path)
        
        print("Logo créé avec succès!")
        
    except Exception as e:
        print(f"Erreur lors de la création du logo: {str(e)}")
        raise

if __name__ == '__main__':
    create_logo() 