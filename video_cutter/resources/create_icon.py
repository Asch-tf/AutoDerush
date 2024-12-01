from PIL import Image, ImageDraw
import os

def create_icon():
    # Taille de l'icône
    size = (256, 256)
    
    # Créer une nouvelle image avec fond transparent
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Couleurs
    primary_color = (42, 130, 218)  # Bleu
    secondary_color = (255, 255, 255)  # Blanc
    
    # Dessiner le fond circulaire
    padding = 20
    draw.ellipse([padding, padding, size[0]-padding, size[1]-padding], fill=primary_color)
    
    # Dessiner le symbole de ciseaux stylisé
    points = [
        (90, 90),   # Point de départ
        (166, 166), # Point central
        (90, 166),  # Point bas
        (166, 90),  # Point haut
    ]
    
    # Dessiner les lignes
    line_width = 12
    draw.line(points[:2], fill=secondary_color, width=line_width)
    draw.line(points[2:], fill=secondary_color, width=line_width)
    
    # Dessiner les cercles aux extrémités
    circle_radius = 8
    for point in points:
        x, y = point
        draw.ellipse([x-circle_radius, y-circle_radius, x+circle_radius, y+circle_radius], 
                    fill=secondary_color)
    
    # Sauvegarder l'image
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
    image.save(icon_path, 'PNG')
    
    # Convertir en ICO
    ico_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    image.save(ico_path, format='ICO', sizes=[(256, 256)])
    
    print(f"Icône créée : {ico_path}")

if __name__ == "__main__":
    create_icon() 