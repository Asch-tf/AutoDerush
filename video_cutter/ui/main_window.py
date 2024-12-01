import os
import sys
import json
import logging
import subprocess
import cv2
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                          QPushButton, QLabel, QFileDialog, QSlider, QSpinBox,
                          QProgressBar, QMessageBox, QLineEdit, QComboBox,
                          QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap

def format_duration(seconds):
    """Formate une durée en secondes en format HH:MM:SS"""
    return str(timedelta(seconds=int(seconds)))

# Ajouter le dossier parent au path pour permettre les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from video_cutter.audio_analyzer import AudioAnalyzer

def open_folder(path):
    """Ouvre un dossier dans l'explorateur de fichiers"""
    if os.path.exists(path):
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', path])
        else:  # Linux
            subprocess.run(['xdg-open', path])

class ProcessThread(QThread):
    """Thread pour le traitement de la vidéo"""
    progress = pyqtSignal(str, int)  # Message et pourcentage
    finished = pyqtSignal(bool, str)
    
    def __init__(self, video_path, threshold, margin, output_path):
        QThread.__init__(self)
        self.video_path = video_path
        self.threshold = threshold
        self.margin = margin
        self.output_path = output_path
        self.analyzer = AudioAnalyzer()
        
    def run(self):
        try:
            # Initialiser l'analyseur
            self.analyzer.set_threshold(self.threshold)
            self.analyzer.set_margin(self.margin)
            
            # Extraire l'audio
            self.progress.emit("Extraction de l'audio...", 10)
            audio_data, sample_rate = self.analyzer.extract_audio(self.video_path)
            
            # Détecter les segments
            self.progress.emit("Analyse audio et détection des segments...", 40)
            segments = self.analyzer.detect_speech_segments(audio_data, sample_rate)
            
            if not segments:
                self.finished.emit(False, "Aucun segment de parole n'a été détecté. Essayez d'ajuster le seuil de détection.")
                return
            
            # Exporter les segments
            self.progress.emit("Export de la vidéo...", 70)
            output_dir = os.path.dirname(self.output_path)
            output_name = os.path.basename(self.output_path)
            self.analyzer.export_segments(self.video_path, segments, output_dir, output_name)
            
            self.progress.emit("Finalisation...", 95)
            self.finished.emit(True, f"Traitement terminé avec succès !\nLa vidéo sans les blancs a été enregistrée sous :\n{self.output_path}")
            
        except Exception as e:
            self.finished.emit(False, f"Erreur lors du traitement : {str(e)}")

class VideoPreviewThread(QThread):
    """Thread pour la prévisualisation de la vidéo"""
    frame_ready = pyqtSignal(QImage)
    duration_ready = pyqtSignal(float, float)  # Durée originale, durée estimée
    
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.running = True
        
    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = int(1000 / fps)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # Émettre la durée originale
        self.duration_ready.emit(duration, 0)  # La durée estimée sera mise à jour plus tard
        
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                # Convertir BGR en RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                
                # Redimensionner pour la prévisualisation (max 320x240)
                scale = min(320/w, 240/h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                rgb_frame = cv2.resize(rgb_frame, (new_w, new_h))
                
                # Convertir en QImage
                bytes_per_line = ch * new_w
                qt_image = QImage(rgb_frame.data, new_w, new_h, bytes_per_line, QImage.Format.Format_RGB888)
                
                self.frame_ready.emit(qt_image)
                self.msleep(frame_delay)
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Retour au début
                
        cap.release()
        
    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.load_presets()
        self.init_ui()
        self.setup_tooltips()
        self.preview_thread = None
        self.original_duration = 0
        self.analyzer = AudioAnalyzer()
        logging.info("Application démarrée")
        
    def setup_logging(self):
        """Configure le système de logging"""
        log_dir = os.path.join(os.path.expanduser("~"), "AutoDerush_logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info("Système de logging initialisé")

    def get_presets_file(self):
        """Retourne le chemin du fichier de préréglages"""
        presets_dir = os.path.join(os.path.expanduser("~"), "AutoDerush_config")
        os.makedirs(presets_dir, exist_ok=True)
        return os.path.join(presets_dir, "presets.json")

    def load_presets(self):
        """Charge les préréglages depuis le fichier"""
        try:
            presets_file = self.get_presets_file()
            if os.path.exists(presets_file):
                with open(presets_file, 'r', encoding='utf-8') as f:
                    self.presets = json.load(f)
            else:
                self.presets = {
                    "Standard": {"threshold": 25, "margin": 100},
                    "Agressif": {"threshold": 75, "margin": 50},
                    "Conservateur": {"threshold": 15, "margin": 200}
                }
                self.save_presets()  # Sauvegarder les préréglages par défaut
        except Exception as e:
            logging.error(f"Erreur lors du chargement des préréglages : {str(e)}")
            self.presets = {}

    def save_presets(self):
        """Sauvegarde les préréglages dans le fichier"""
        try:
            presets_file = self.get_presets_file()
            with open(presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, indent=4)
            logging.info("Préréglages sauvegardés")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des préréglages : {str(e)}")

    def setup_tooltips(self):
        """Configure les tooltips explicatifs"""
        self.threshold_slider.setToolTip(
            "Ajustez ce curseur pour modifier la sensibilité de détection des silences.\n"
            "Plus la valeur est élevée, plus les silences détectés seront courts."
        )
        
        self.margin_spinbox.setToolTip(
            "Définit la marge en millisecondes à conserver avant et après chaque segment de parole.\n"
            "Augmentez cette valeur si les transitions semblent trop brusques."
        )
        
        self.output_name_edit.setToolTip(
            "Entrez le nom souhaité pour le fichier de sortie.\n"
            "L'extension .mp4 sera automatiquement ajoutée si nécessaire."
        )
        
        self.presets_combo.setToolTip(
            "Sélectionnez un préréglage pour charger des paramètres prédéfinis"
        )

    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("AutoDerush")
        self.setMinimumWidth(600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Sélection de la vidéo et prévisualisation
        video_preview_layout = QHBoxLayout()
        
        # Zone de gauche (sélection vidéo)
        video_select_layout = QVBoxLayout()
        self.video_label = QLabel("Aucune vidéo sélectionnée")
        video_select_layout.addWidget(self.video_label)
        
        select_button = QPushButton("Sélectionner une vidéo")
        select_button.setToolTip("Cliquez pour choisir la vidéo à traiter")
        select_button.clicked.connect(self.select_video)
        video_select_layout.addWidget(select_button)
        
        # Informations de durée
        self.duration_label = QLabel("Durée : --:--:--")
        video_select_layout.addWidget(self.duration_label)
        self.estimated_duration_label = QLabel("Durée estimée : --:--:--")
        video_select_layout.addWidget(self.estimated_duration_label)
        
        video_preview_layout.addLayout(video_select_layout)
        
        # Zone de droite (prévisualisation)
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(320, 240)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("QLabel { background-color: black; }")
        preview_layout.addWidget(self.preview_label)
        
        video_preview_layout.addLayout(preview_layout)
        layout.addLayout(video_preview_layout)
        
        # Sélection du dossier de sortie
        output_dir_layout = QHBoxLayout()
        self.output_dir_label = QLabel("Dossier de sortie :")
        output_dir_layout.addWidget(self.output_dir_label)
        
        self.output_dir_path = QLineEdit()
        self.output_dir_path.setReadOnly(True)
        self.output_dir_path.setToolTip("Chemin du dossier où sera enregistrée la vidéo traitée")
        output_dir_layout.addWidget(self.output_dir_path)
        
        select_dir_button = QPushButton("Choisir")
        select_dir_button.setToolTip("Cliquez pour sélectionner le dossier de destination")
        select_dir_button.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(select_dir_button)
        
        open_dir_button = QPushButton("Ouvrir")
        open_dir_button.setToolTip("Ouvrir le dossier de destination dans l'explorateur")
        open_dir_button.clicked.connect(lambda: open_folder(self.output_dir_path.text()))
        output_dir_layout.addWidget(open_dir_button)
        
        layout.addLayout(output_dir_layout)
        
        # Nom du fichier de sortie
        output_name_layout = QHBoxLayout()
        output_name_layout.addWidget(QLabel("Nom du fichier de sortie :"))
        
        self.output_name_edit = QLineEdit()
        self.output_name_edit.setPlaceholderText("nom_de_la_video.mp4")
        output_name_layout.addWidget(self.output_name_edit)
        layout.addLayout(output_name_layout)
        
        # Gestion des préréglages
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Préréglages :"))
        
        self.presets_combo = QComboBox()
        self.presets_combo.addItems(self.presets.keys())
        self.presets_combo.currentTextChanged.connect(self.load_preset)
        presets_layout.addWidget(self.presets_combo)
        
        save_preset_button = QPushButton("Sauvegarder")
        save_preset_button.setToolTip("Sauvegarder les paramètres actuels comme nouveau préréglage")
        save_preset_button.clicked.connect(self.save_current_preset)
        presets_layout.addWidget(save_preset_button)
        
        delete_preset_button = QPushButton("Supprimer")
        delete_preset_button.setToolTip("Supprimer le préréglage sélectionné")
        delete_preset_button.clicked.connect(self.delete_preset)
        presets_layout.addWidget(delete_preset_button)
        
        layout.addLayout(presets_layout)
        
        # Seuil de détection
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Seuil de détection :"))
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(1)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(25)  # Valeur par défaut
        threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel("25")  # Valeur par défaut
        threshold_layout.addWidget(self.threshold_label)
        layout.addLayout(threshold_layout)
        
        self.threshold_slider.valueChanged.connect(self.update_threshold_label)
        self.threshold_slider.valueChanged.connect(self.estimate_duration)
        
        # Marge temporelle
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Marge (ms) :"))
        
        self.margin_spinbox = QSpinBox()
        self.margin_spinbox.setMinimum(0)
        self.margin_spinbox.setMaximum(1000)
        self.margin_spinbox.setValue(100)
        self.margin_spinbox.valueChanged.connect(self.estimate_duration)
        margin_layout.addWidget(self.margin_spinbox)
        layout.addLayout(margin_layout)
        
        # Zone de progression
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)
        
        # Label pour le statut détaillé
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_container)
        
        # Bouton de traitement
        self.process_button = QPushButton("Traiter la vidéo")
        self.process_button.setToolTip("Lancer le traitement de la vidéo avec les paramètres actuels")
        self.process_button.clicked.connect(self.process_video)
        self.process_button.setEnabled(False)
        layout.addWidget(self.process_button)
        
        # Variables de classe
        self.video_path = None
        self.process_thread = None

        # Charger le préréglage par défaut après l'initialisation de l'interface
        QTimer.singleShot(100, lambda: self.load_preset("Standard"))

    def select_video(self):
        """Ouvre un dialogue pour sélectionner une vidéo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une vidéo",
            "",
            "Fichiers vidéo (*.mp4 *.avi *.mkv *.mov);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            self.video_path = file_path
            self.video_label.setText(os.path.basename(file_path))
            self.process_button.setEnabled(True)
            
            # Mettre à jour le dossier de sortie par défaut
            self.output_dir_path.setText(os.path.dirname(file_path))
            
            # Suggérer un nom de fichier de sortie
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.output_name_edit.setText(f"{base_name}_sans_blancs.mp4")
            
            # Démarrer la prévisualisation
            self.start_preview(file_path)
            
            # Estimer la durée avec les paramètres actuels
            QTimer.singleShot(1000, self.estimate_duration)  # Attendre 1 seconde pour laisser le temps à la prévisualisation de s'initialiser
            
            logging.info(f"Vidéo sélectionnée : {file_path}")
            
    def select_output_dir(self):
        """Ouvre un dialogue pour sélectionner le dossier de sortie"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier de sortie",
            self.output_dir_path.text() or ""
        )
        
        if dir_path:
            self.output_dir_path.setText(dir_path)
            logging.info(f"Dossier de sortie sélectionné : {dir_path}")
            
    def update_threshold_label(self, value):
        """Met à jour l'affichage de la valeur du seuil"""
        self.threshold_label.setText(str(value))
        
    def process_video(self):
        """Lance le traitement de la vidéo"""
        try:
            # Vérifier que tous les champs sont remplis
            if not self.video_path:
                self.show_error("Erreur", "Veuillez sélectionner une vidéo à traiter.")
                return
                
            if not self.output_dir_path.text():
                self.show_error("Erreur", "Veuillez sélectionner un dossier de sortie.")
                return
                
            if not self.output_name_edit.text():
                self.show_error("Erreur", "Veuillez spécifier un nom pour le fichier de sortie.")
                return
            
            # Désactiver les contrôles
            self.process_button.setEnabled(False)
            self.progress_bar.show()
            self.status_label.show()
            self.progress_bar.setValue(0)
            self.status_label.setText("Préparation...")
            
            # Préparer le chemin de sortie
            output_path = os.path.join(self.output_dir_path.text(), self.output_name_edit.text())
            
            logging.info("Début du traitement de la vidéo")
            logging.info(f"Fichier vidéo : {self.video_path}")
            logging.info(f"Fichier de sortie : {output_path}")
            logging.info(f"Seuil : {self.threshold_slider.value()}")
            logging.info(f"Marge : {self.margin_spinbox.value()}")
            
            # Créer et démarrer le thread de traitement
            self.process_thread = ProcessThread(
                self.video_path,
                self.threshold_slider.value(),
                self.margin_spinbox.value(),
                output_path
            )
            
            self.process_thread.progress.connect(self.update_progress)
            self.process_thread.finished.connect(self.process_finished)
            self.process_thread.start()
            
        except Exception as e:
            self.show_error("Erreur", f"Erreur lors du lancement du traitement : {str(e)}")
            self.process_button.setEnabled(True)
            self.progress_bar.hide()
            self.status_label.hide()
            
    def update_progress(self, message, percent):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        
    def process_finished(self, success, message):
        """Gère la fin du traitement"""
        self.process_button.setEnabled(True)
        self.progress_bar.hide()
        self.status_label.hide()
        
        if success:
            QMessageBox.information(self, "Succès", message)
        else:
            self.show_error("Erreur", message)
            
    def show_error(self, title, message):
        """Affiche une boîte de dialogue d'erreur"""
        QMessageBox.critical(self, title, message)
        
    def load_preset(self, preset_name):
        """Charge un préréglage"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            self.threshold_slider.setValue(preset["threshold"])
            self.margin_spinbox.setValue(preset["margin"])
            self.estimate_duration()  # Estimer la durée après le chargement du préréglage
            logging.info(f"Préréglage chargé : {preset_name}")
            
    def save_current_preset(self):
        """Sauvegarde les paramètres actuels comme nouveau préréglage"""
        name, ok = QInputDialog.getText(
            self,
            "Sauvegarder le préréglage",
            "Nom du préréglage :",
            QLineEdit.EchoMode.Normal
        )
        
        if ok and name:
            # Vérifier si le préréglage existe déjà
            if name in self.presets:
                reply = QMessageBox.question(
                    self,
                    "Confirmer l'écrasement",
                    f"Le préréglage '{name}' existe déjà. Voulez-vous l'écraser ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    return
            
            # Sauvegarder le préréglage
            self.presets[name] = {
                "threshold": self.threshold_slider.value(),
                "margin": self.margin_spinbox.value()
            }
            
            # Mettre à jour la liste des préréglages
            current_preset = self.presets_combo.currentText()
            self.presets_combo.clear()
            self.presets_combo.addItems(self.presets.keys())
            if name == current_preset:
                self.presets_combo.setCurrentText(name)
            
            # Sauvegarder dans le fichier
            self.save_presets()
            logging.info(f"Nouveau préréglage sauvegardé : {name}")
            
    def delete_preset(self):
        """Supprime le préréglage sélectionné"""
        preset_name = self.presets_combo.currentText()
        
        # Empêcher la suppression des préréglages par défaut
        if preset_name in ["Standard", "Agressif", "Conservateur"]:
            QMessageBox.warning(
                self,
                "Suppression impossible",
                "Les préréglages par défaut ne peuvent pas être supprimés."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer le préréglage '{preset_name}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.presets[preset_name]
            self.presets_combo.removeItem(self.presets_combo.currentIndex())
            self.save_presets()
            logging.info(f"Préréglage supprimé : {preset_name}")

    def start_preview(self, video_path):
        """Démarre la prévisualisation de la vidéo"""
        if self.preview_thread is not None:
            self.preview_thread.stop()
            
        self.preview_thread = VideoPreviewThread(video_path)
        self.preview_thread.frame_ready.connect(self.update_preview)
        self.preview_thread.duration_ready.connect(self.update_durations)
        self.preview_thread.start()
        
    def update_preview(self, image):
        """Met à jour l'image de prévisualisation"""
        self.preview_label.setPixmap(QPixmap.fromImage(image))
        
    def update_durations(self, original_duration, estimated_duration):
        """Met à jour l'affichage des durées"""
        self.original_duration = original_duration
        self.duration_label.setText(f"Durée : {format_duration(original_duration)}")
        if estimated_duration > 0:
            self.estimated_duration_label.setText(f"Durée estimée : {format_duration(estimated_duration)}")
            reduction = ((original_duration - estimated_duration) / original_duration) * 100
            self.estimated_duration_label.setToolTip(f"Réduction de {reduction:.1f}%")
        
    def estimate_duration(self):
        """Estime la durée finale en fonction des paramètres actuels"""
        if hasattr(self, 'video_path') and self.video_path:
            try:
                # Configurer l'analyseur avec les paramètres actuels
                self.analyzer.set_threshold(self.threshold_slider.value())
                self.analyzer.set_margin(self.margin_spinbox.value())
                
                # Extraire l'audio et analyser
                audio_data, sample_rate = self.analyzer.extract_audio(self.video_path)
                segments = self.analyzer.detect_speech_segments(audio_data, sample_rate)
                
                if segments:
                    # Calculer la durée totale des segments
                    total_duration = sum((end - start) for start, end in segments)
                    # Mettre à jour l'affichage
                    self.update_durations(self.original_duration, total_duration)
                else:
                    self.estimated_duration_label.setText("Durée estimée : 00:00:00")
                    self.estimated_duration_label.setToolTip("Aucun segment détecté")
                    
            except Exception as e:
                logging.error(f"Erreur lors de l'estimation de la durée : {str(e)}")
                self.estimated_duration_label.setText("Durée estimée : --:--:--")
                self.estimated_duration_label.setToolTip("Erreur lors de l'estimation")

    def closeEvent(self, event):
        """Gestionnaire d'événement de fermeture de la fenêtre"""
        if self.preview_thread is not None:
            self.preview_thread.stop()
        event.accept()
