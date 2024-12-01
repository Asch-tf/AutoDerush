import numpy as np
import os
import subprocess
import tempfile
import logging
import traceback
import wave

# Pour masquer la fenêtre de commande sous Windows
startupinfo = None
if os.name == 'nt':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

class AudioAnalyzer:
    def __init__(self):
        self.threshold = 0.02
        self.margin_ms = 100  # Marge par défaut en millisecondes
        logging.info("AudioAnalyzer initialisé")
        
    def set_threshold(self, value):
        """Met à jour le seuil de détection"""
        try:
            # Convertir la valeur du slider (1-100) en un multiplicateur (0.1-2.0)
            self.threshold = 0.1 + (value / 50.0)
            logging.info(f"Seuil mis à jour : {self.threshold}")
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour du seuil : {str(e)}")
            logging.error(traceback.format_exc())
            raise
        
    def set_margin(self, value_ms):
        """Met à jour la marge temporelle"""
        try:
            self.margin_ms = value_ms
            logging.info(f"Marge mise à jour : {self.margin_ms}ms")
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour de la marge : {str(e)}")
            logging.error(traceback.format_exc())
            raise
        
    def extract_audio(self, video_path):
        """Extrait l'audio d'une vidéo"""
        try:
            logging.info("=== Début de l'extraction audio ===")
            
            # Convertir en chemin absolu et normaliser
            video_path = os.path.abspath(os.path.normpath(video_path))
            logging.info(f"Chemin de la vidéo : {video_path}")
            
            if not os.path.exists(video_path):
                error_msg = f"Le fichier vidéo n'existe pas : {video_path}"
                logging.error(error_msg)
                raise FileNotFoundError(error_msg)
                
            # Créer un fichier audio temporaire dans le dossier temp du système
            temp_dir = tempfile.gettempdir()
            temp_audio = os.path.join(temp_dir, 'temp_audio.wav')
            logging.info(f"Fichier audio temporaire : {temp_audio}")
            
            # S'assurer que ffmpeg est disponible
            try:
                logging.info("Vérification de FFmpeg...")
                result = subprocess.run(['ffmpeg', '-version'], 
                    capture_output=True, 
                    text=True, 
                    check=True,
                    startupinfo=startupinfo)
                logging.info(f"Version de FFmpeg : {result.stdout.split('\\n')[0]}")
            except subprocess.CalledProcessError as e:
                error_msg = "FFmpeg n'est pas installé ou n'est pas accessible"
                logging.error(error_msg)
                logging.error(f"Erreur FFmpeg : {e.stderr}")
                raise Exception(error_msg)
            
            # Extraire l'audio avec ffmpeg
            logging.info("Extraction de l'audio avec FFmpeg...")
            command = [
                'ffmpeg',
                '-y',  # Écraser le fichier existant
                '-i', video_path,
                '-vn',  # Pas de vidéo
                '-acodec', 'pcm_s16le',  # Codec audio
                '-ar', '44100',  # Taux d'échantillonnage
                '-ac', '1',  # Mono
                temp_audio
            ]
            
            logging.info(f"Commande FFmpeg : {' '.join(command)}")
            
            try:
                result = subprocess.run(command, 
                    capture_output=True, 
                    text=True, 
                    check=True,
                    startupinfo=startupinfo)
                logging.info("Extraction audio terminée")
            except subprocess.CalledProcessError as e:
                error_msg = f"Erreur lors de l'extraction audio : {e.stderr}"
                logging.error(error_msg)
                raise Exception(error_msg)
            
            if not os.path.exists(temp_audio):
                error_msg = "Le fichier audio temporaire n'a pas été créé"
                logging.error(error_msg)
                raise Exception(error_msg)
            
            # Charger l'audio
            logging.info("Chargement de l'audio...")
            try:
                with wave.open(temp_audio, 'rb') as wav_file:
                    # Obtenir les paramètres du fichier
                    sample_rate = wav_file.getframerate()
                    n_frames = wav_file.getnframes()
                    
                    # Lire les données audio
                    audio_bytes = wav_file.readframes(n_frames)
                    
                    # Convertir les bytes en tableau numpy
                    audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                    
                    # Normaliser entre -1 et 1
                    audio_data = audio_data.astype(np.float32) / 32768.0
                    
                    logging.info(f"Audio chargé : {len(audio_data)} échantillons, {sample_rate}Hz")
                    return audio_data, sample_rate
            except Exception as e:
                error_msg = f"Erreur lors du chargement audio : {str(e)}"
                logging.error(error_msg)
                logging.error(traceback.format_exc())
                raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Erreur lors de l'extraction audio : {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            raise Exception(error_msg)
        finally:
            # Nettoyer le fichier temporaire
            try:
                if 'temp_audio' in locals() and os.path.exists(temp_audio):
                    os.remove(temp_audio)
                    logging.info("Fichier temporaire supprimé")
            except Exception as e:
                logging.error(f"Erreur lors de la suppression du fichier temporaire : {str(e)}")
            logging.info("=== Fin de l'extraction audio ===")
            
    def detect_speech_segments(self, audio_data, sample_rate):
        """Détecte les segments avec de la parole et optimise les transitions"""
        try:
            logging.info("Début de la détection des segments de parole")
            
            # Conversion en mono si stéréo
            if len(audio_data.shape) > 1:
                logging.info("Conversion du signal stéréo en mono")
                audio_data = np.mean(audio_data, axis=1)
            
            # Calcul de l'énergie du signal
            logging.info("Calcul de l'énergie du signal")
            try:
                # Utiliser la valeur absolue du signal comme énergie
                energy = np.abs(audio_data)
                energy_mean = np.mean(energy)
                energy_std = np.std(energy)
                # Le seuil est maintenant basé sur la moyenne et l'écart-type
                energy_threshold = energy_mean + (energy_std * self.threshold)
                logging.info(f"Statistiques du signal :")
                logging.info(f"- Énergie moyenne : {energy_mean}")
                logging.info(f"- Écart-type : {energy_std}")
                logging.info(f"- Seuil calculé : {energy_threshold}")
                logging.info(f"- Multiplicateur utilisé : {self.threshold}")
            except Exception as e:
                error_msg = f"Erreur lors du calcul de l'énergie : {str(e)}"
                logging.error(error_msg)
                logging.error(traceback.format_exc())
                raise Exception(error_msg)
            
            # Détection des segments parlés
            raw_segments = []
            is_speech = False
            start_time = 0
            end_time = 0
            speech_samples = 0
            total_samples = len(energy)
            
            # Détecter les segments avec une fenêtre glissante pour réduire le bruit
            window_size = int(sample_rate * 0.05)  # fenêtre de 50ms
            for i in range(0, len(energy), window_size):
                # Calculer la moyenne d'énergie sur la fenêtre
                window_end = min(i + window_size, len(energy))
                window_energy = np.mean(energy[i:window_end])
                
                if window_energy > energy_threshold and not is_speech:
                    is_speech = True
                    start_time = i
                    speech_samples += window_size
                elif window_energy > energy_threshold and is_speech:
                    speech_samples += window_size
                elif window_energy <= energy_threshold and is_speech:
                    is_speech = False
                    end_time = i
                    if (end_time - start_time) > sample_rate * 0.1:  # Ignorer les segments < 100ms
                        raw_segments.append((start_time / sample_rate, end_time / sample_rate))
            
            # Gérer le dernier segment si nécessaire
            if is_speech:
                end_time = len(audio_data)
                if (end_time - start_time) > sample_rate * 0.1:
                    raw_segments.append((start_time / sample_rate, end_time / sample_rate))
            
            # Fusionner les segments proches
            if raw_segments:
                merged_segments = [raw_segments[0]]
                min_gap = 0.3  # 300ms de gap minimum entre les segments
                
                for i in range(1, len(raw_segments)):
                    current_start, current_end = raw_segments[i]
                    last_start, last_end = merged_segments[-1]
                    
                    if current_start - last_end < min_gap:
                        # Fusionner les segments
                        merged_segments[-1] = (last_start, current_end)
                    else:
                        merged_segments.append((current_start, current_end))
                
                raw_segments = merged_segments
            
            # Logs des statistiques de détection
            logging.info(f"Statistiques de détection :")
            logging.info(f"- Nombre total d'échantillons : {total_samples}")
            logging.info(f"- Échantillons avec parole : {speech_samples}")
            logging.info(f"- Pourcentage de parole : {(speech_samples/total_samples)*100:.2f}%")
            logging.info(f"- Nombre de segments bruts : {len(raw_segments)}")
            
            if not raw_segments:
                logging.warning("Aucun segment détecté - ajustez le seuil de détection")
                return []
            
            # Optimisation des segments
            optimized_segments = []
            margin_time = self.margin_ms / 1000.0
            
            # Traiter le premier segment
            current_segment = list(raw_segments[0])
            
            # Fusionner les segments proches
            for i in range(1, len(raw_segments)):
                next_start, next_end = raw_segments[i]
                
                # Si les segments se chevauchent avec les marges
                if (current_segment[1] + margin_time) >= (next_start - margin_time):
                    # Fusionner les segments
                    current_segment[1] = next_end
                else:
                    # Ajouter le segment avec les marges
                    optimized_segments.append((
                        max(0, current_segment[0] - margin_time),
                        min(len(audio_data) / sample_rate, current_segment[1] + margin_time)
                    ))
                    current_segment = [next_start, next_end]
            
            # Ajouter le dernier segment
            optimized_segments.append((
                max(0, current_segment[0] - margin_time),
                min(len(audio_data) / sample_rate, current_segment[1] + margin_time)
            ))
            
            logging.info(f"Segments détectés : {len(optimized_segments)}")
            return optimized_segments
            
        except Exception as e:
            error_msg = f"Erreur lors de la détection des segments : {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            raise Exception(error_msg)
            
    def export_segments(self, video_path, segments, output_dir, output_filename="video_sans_blancs.mp4"):
        """Exporte les segments de vidéo sélectionnés"""
        try:
            logging.info("Export de la vidéo sans les blancs :")
            logging.info(f"Vidéo source : {video_path}")
            logging.info(f"Dossier de sortie : {output_dir}")
            
            # Créer le dossier de sortie s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Préparer le fichier de sortie
            output_path = os.path.join(output_dir, output_filename)
            
            # Construire le filtre complexe pour FFmpeg
            filter_parts = []
            for i, (start, end) in enumerate(segments):
                # Ajouter les filtres vidéo
                filter_parts.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];")
            
            for i, (start, end) in enumerate(segments):
                # Ajouter les filtres audio
                filter_parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}];")
            
            # Ajouter la concaténation vidéo
            concat_video = ''.join(f'[v{i}]' for i in range(len(segments)))
            filter_parts.append(f"{concat_video}concat=n={len(segments)}:v=1:a=0[outv];")
            
            # Ajouter la concaténation audio
            concat_audio = ''.join(f'[a{i}]' for i in range(len(segments)))
            filter_parts.append(f"{concat_audio}concat=n={len(segments)}:v=0:a=1[outa]")
            
            filter_complex = ''.join(filter_parts)
            
            # Préparer la commande FFmpeg
            command = [
                'ffmpeg',
                '-y',  # Écraser le fichier existant
                '-i', video_path,
                '-filter_complex', filter_complex,
                '-map', '[outv]',
                '-map', '[outa]',
                '-c:v', 'libx264',  # Utiliser le codec H.264 pour la vidéo
                '-preset', 'fast',   # Préréglage de compression rapide
                '-c:a', 'aac',       # Utiliser le codec AAC pour l'audio
                '-b:a', '192k',      # Bitrate audio de 192k
                output_path
            ]
            
            logging.info("Lancement de la commande FFmpeg")
            logging.info(f"Commande : {' '.join(command)}")
            
            # Exécuter FFmpeg
            try:
                result = subprocess.run(command, 
                    capture_output=True, 
                    text=True, 
                    check=True,
                    startupinfo=startupinfo)
                logging.info("Export terminé avec succès")
                logging.info(f"Sortie FFmpeg : {result.stdout}")
                if result.stderr:
                    logging.info(f"Messages FFmpeg : {result.stderr}")
            except subprocess.CalledProcessError as e:
                error_msg = f"Erreur FFmpeg : {e.stderr}"
                logging.error(error_msg)
                raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Erreur lors de l'export : {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            raise Exception(error_msg)
