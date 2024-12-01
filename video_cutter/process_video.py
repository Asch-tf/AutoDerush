import sys
import os
import json
from audio_analyzer import AudioAnalyzer
import logging
import traceback

def setup_logging():
    """Configure le logging pour le processus de traitement"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def process_video(input_data):
    """Traite la vidéo avec les paramètres donnés"""
    try:
        logging.info("Début du traitement de la vidéo")
        logging.info(f"Données d'entrée : {input_data}")
        
        # Extraire les paramètres
        video_path = input_data['video_path']
        threshold = input_data['threshold']
        margin = input_data['margin']
        output_path = input_data['output_path']
        
        logging.info(f"Chemin de la vidéo : {video_path}")
        logging.info(f"Seuil : {threshold}")
        logging.info(f"Marge : {margin}")
        logging.info(f"Chemin de sortie : {output_path}")
        
        # Initialiser l'analyseur
        logging.info("Initialisation de l'analyseur audio")
        analyzer = AudioAnalyzer()
        analyzer.set_threshold(threshold)
        analyzer.set_margin(margin)
        
        # Extraire l'audio
        logging.info("Extraction de l'audio")
        audio_data, sample_rate = analyzer.extract_audio(video_path)
        logging.info(f"Audio extrait : {len(audio_data)} échantillons, {sample_rate}Hz")
        
        # Détecter les segments
        logging.info("Détection des segments")
        segments = analyzer.detect_speech_segments(audio_data, sample_rate)
        logging.info(f"Segments détectés : {len(segments) if segments else 0}")
        
        if not segments:
            logging.warning("Aucun segment détecté")
            return {
                'success': False,
                'message': "Aucun segment de parole n'a été détecté. Essayez d'ajuster le seuil de détection."
            }
        
        # Exporter les segments
        logging.info("Export des segments")
        output_dir = os.path.dirname(output_path)
        output_name = os.path.basename(output_path)
        logging.info(f"Dossier de sortie : {output_dir}")
        logging.info(f"Nom du fichier : {output_name}")
        
        analyzer.export_segments(video_path, segments, output_dir, output_name)
        logging.info("Export terminé avec succès")
        
        return {
            'success': True,
            'message': f"Traitement terminé avec succès !\nLa vidéo sans les blancs a été enregistrée sous :\n{output_path}"
        }
        
    except Exception as e:
        error_msg = f"Erreur lors du traitement : {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }

if __name__ == '__main__':
    # Configurer le logging
    setup_logging()
    
    try:
        logging.info("Démarrage du processus de traitement")
        
        # Lire les données d'entrée depuis stdin
        input_text = sys.stdin.read()
        logging.info(f"Données reçues : {input_text}")
        
        input_data = json.loads(input_text)
        logging.info("Données JSON décodées avec succès")
        
        # Traiter la vidéo
        result = process_video(input_data)
        logging.info(f"Résultat du traitement : {result}")
        
        # Écrire le résultat sur stdout
        output_text = json.dumps(result)
        print(output_text)
        logging.info("Résultat envoyé avec succès")
        
    except Exception as e:
        error_msg = f"Erreur fatale : {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        print(json.dumps({
            'success': False,
            'message': error_msg
        })) 