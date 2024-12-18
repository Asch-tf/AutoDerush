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
                          QInputDialog, QGroupBox)
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

class LoadingIndicator(QWidget):
    """Widget d'indication de chargement"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Indicateur animé
        self.spinner = QLabel()
        self.spinner.setFixedSize(16, 16)
        self.spinner.setStyleSheet("QLabel { color: #2196F3; font-size: 14px; font-weight: bold; }")
        layout.addWidget(self.spinner)
        
        # Texte explicatif
        self.text = QLabel("Calcul en cours...")
        self.text.setStyleSheet("QLabel { color: #2196F3; font-weight: bold; }")
        layout.addWidget(self.text)
        
        # Configuration du timer pour l'animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_text)
        self.angle = 0
        self.spinner.setText("◐")
        
        # Fond coloré pour plus de visibilité
        self.setStyleSheet("""
            LoadingIndicator {
                background-color: #E3F2FD;
                border: 1px solid #2196F3;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        self.hide()

    def rotate_text(self):
        """Change le caractère pour créer une animation de rotation"""
        symbols = ["◐", "◓", "◑", "◒"]
        self.angle = (self.angle + 1) % 4
        self.spinner.setText(symbols[self.angle])

    def start(self):
        """Démarre l'animation"""
        self.show()
        self.timer.start(100)

    def stop(self):
        """Arrête l'animation"""
        self.timer.stop()
        self.hide()

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
        self.loading_preset = False
        self.estimate_timer = QTimer()
        self.estimate_timer.setSingleShot(True)
        self.estimate_timer.setInterval(500)  # Délai de 500ms
        self.estimate_timer.timeout.connect(self.delayed_estimate)
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
        self.setMinimumWidth(800)  # Augmentation de la largeur minimale
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Création d'un layout horizontal pour diviser l'écran en deux colonnes
        content_layout = QHBoxLayout()
        
        # Colonne de gauche (60% de la largeur)
        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 10, 0)  # Marge à droite pour séparer les colonnes
        
        # Groupe Sélection de la vidéo
        video_group = QGroupBox("Sélection de la vidéo")
        video_layout = QVBoxLayout(video_group)
        
        select_button = QPushButton("Sélectionner une vidéo")
        select_button.setToolTip("Cliquez pour choisir la vidéo à traiter")
        select_button.clicked.connect(self.select_video)
        video_layout.addWidget(select_button)
        
        self.video_label = QLabel("Aucune vidéo sélectionnée")
        self.video_label.setStyleSheet("font-weight: bold;")
        video_layout.addWidget(self.video_label)
        
        # Informations de durée
        duration_layout = QHBoxLayout()
        self.duration_label = QLabel("Durée : --:--:--")
        self.estimated_duration_label = QLabel("Durée estimée : --:--:--")
        duration_layout.addWidget(self.duration_label)
        duration_layout.addWidget(self.estimated_duration_label)
        video_layout.addLayout(duration_layout)
        
        left_column.addWidget(video_group)
        
        # Groupe Prévisualisation
        preview_group = QGroupBox("Prévisualisation")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(480, 270)  # Format 16:9
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("QLabel { background-color: black; border: 1px solid #666; }")
        preview_layout.addWidget(self.preview_label)
        
        left_column.addWidget(preview_group)
        
        # Colonne de droite (40% de la largeur)
        right_column = QVBoxLayout()
        right_column.setContentsMargins(10, 0, 0, 0)  # Marge à gauche pour séparer les colonnes
        
        # Groupe Paramètres
        params_group = QGroupBox("Paramètres de détection")
        params_layout = QVBoxLayout(params_group)
        
        # Préréglages avec indicateur de chargement
        presets_layout = QVBoxLayout()  # Changé en VBoxLayout pour meilleure organisation
        presets_header = QHBoxLayout()
        presets_header.addWidget(QLabel("Préréglages :"))
        
        self.presets_combo = QComboBox()
        self.presets_combo.addItems(self.presets.keys())
        self.presets_combo.currentTextChanged.connect(self.on_preset_changed)
        presets_header.addWidget(self.presets_combo, 1)
        presets_layout.addLayout(presets_header)
        
        # Indicateur de chargement en dessous du combo
        self.loading_indicator = LoadingIndicator()
        presets_layout.addWidget(self.loading_indicator)
        
        # Boutons de préréglages
        preset_buttons_layout = QHBoxLayout()
        save_preset_button = QPushButton("Sauvegarder")
        save_preset_button.setToolTip("Sauvegarder les paramètres actuels comme nouveau préréglage")
        save_preset_button.clicked.connect(self.save_current_preset)
        delete_preset_button = QPushButton("Supprimer")
        delete_preset_button.setToolTip("Supprimer le préréglage sélectionné")
        delete_preset_button.clicked.connect(self.delete_preset)
        preset_buttons_layout.addWidget(save_preset_button)
        preset_buttons_layout.addWidget(delete_preset_button)
        presets_layout.addLayout(preset_buttons_layout)
        
        params_layout.addLayout(presets_layout)
        params_layout.addSpacing(10)
        
        # Seuil de détection
        threshold_layout = QVBoxLayout()
        threshold_label = QLabel("Seuil de détection :")
        threshold_label.setToolTip("Plus le seuil est élevé, plus les silences détectés seront courts")
        threshold_layout.addWidget(threshold_label)
        
        threshold_control = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(1)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(25)
        self.threshold_slider.valueChanged.connect(self.update_threshold_label)
        self.threshold_slider.valueChanged.connect(self.schedule_estimate)
        
        self.threshold_label = QLabel("25")
        threshold_control.addWidget(self.threshold_slider)
        threshold_control.addWidget(self.threshold_label)
        threshold_layout.addLayout(threshold_control)
        params_layout.addLayout(threshold_layout)
        
        # Marge temporelle
        margin_layout = QVBoxLayout()
        margin_label = QLabel("Marge temporelle (ms) :")
        margin_label.setToolTip("Marge à conserver avant et après chaque segment de parole")
        margin_layout.addWidget(margin_label)
        
        self.margin_spinbox = QSpinBox()
        self.margin_spinbox.setMinimum(0)
        self.margin_spinbox.setMaximum(1000)
        self.margin_spinbox.setValue(100)
        self.margin_spinbox.valueChanged.connect(self.schedule_estimate)
        margin_layout.addWidget(self.margin_spinbox)
        params_layout.addLayout(margin_layout)
        
        right_column.addWidget(params_group)
        
        # Groupe Export
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        # Dossier de sortie
        output_dir_layout = QHBoxLayout()
        self.output_dir_path = QLineEdit()
        self.output_dir_path.setReadOnly(True)
        self.output_dir_path.setPlaceholderText("Dossier de destination")
        output_dir_layout.addWidget(self.output_dir_path)
        
        select_dir_button = QPushButton("...")
        select_dir_button.setToolTip("Sélectionner le dossier de destination")
        select_dir_button.setMaximumWidth(30)
        select_dir_button.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(select_dir_button)
        
        open_dir_button = QPushButton("Ouvrir")
        open_dir_button.setToolTip("Ouvrir le dossier de destination")
        open_dir_button.setMaximumWidth(60)
        open_dir_button.clicked.connect(lambda: open_folder(self.output_dir_path.text()))
        output_dir_layout.addWidget(open_dir_button)
        
        export_layout.addLayout(output_dir_layout)
        
        # Nom du fichier
        self.output_name_edit = QLineEdit()
        self.output_name_edit.setPlaceholderText("nom_de_la_video.mp4")
        export_layout.addWidget(self.output_name_edit)
        
        right_column.addWidget(export_group)
        
        # Groupe Progression
        progress_group = QGroupBox("Progression")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        progress_layout.addWidget(self.status_label)
        
        right_column.addWidget(progress_group)
        
        # Bouton de traitement
        self.process_button = QPushButton("Traiter la vidéo")
        self.process_button.setToolTip("Lancer le traitement de la vidéo avec les paramètres actuels")
        self.process_button.clicked.connect(self.process_video)
        self.process_button.setEnabled(False)
        self.process_button.setMinimumHeight(40)
        self.process_button.setStyleSheet("QPushButton { font-weight: bold; }")
        right_column.addWidget(self.process_button)
        
        # Ajout des colonnes au layout principal
        content_layout.addLayout(left_column, 60)
        content_layout.addLayout(right_column, 40)
        main_layout.addLayout(content_layout)
        
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
        
    def on_preset_changed(self, preset_name):
        """Gère le changement de préréglage avec indication visuelle"""
        if not self.loading_preset and preset_name in self.presets:
            self.loading_preset = True
            self.loading_indicator.start()
            self.presets_combo.setEnabled(False)
            
            # Arrêter toute estimation en cours
            self.estimate_timer.stop()
            
            # Utiliser QTimer pour permettre à l'interface de se mettre à jour
            QTimer.singleShot(100, lambda: self.apply_preset(preset_name))

    def apply_preset(self, preset_name):
        """Applique le préréglage sélectionné"""
        try:
            preset = self.presets[preset_name]
            # Désactiver temporairement les connexions pour éviter les estimations multiples
            self.threshold_slider.valueChanged.disconnect(self.schedule_estimate)
            self.margin_spinbox.valueChanged.disconnect(self.schedule_estimate)
            
            self.threshold_slider.setValue(preset["threshold"])
            self.margin_spinbox.setValue(preset["margin"])
            
            # Rétablir les connexions
            self.threshold_slider.valueChanged.connect(self.schedule_estimate)
            self.margin_spinbox.valueChanged.connect(self.schedule_estimate)
            
            self.estimate_duration()
            logging.info(f"Préréglage chargé : {preset_name}")
        finally:
            self.loading_preset = False
            self.loading_indicator.stop()
            self.presets_combo.setEnabled(True)

    def load_preset(self, preset_name):
        """Charge un préréglage initial"""
        if preset_name in self.presets:
            self.presets_combo.setCurrentText(preset_name)  # Cela déclenchera on_preset_changed

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

    def schedule_estimate(self):
        """Programme une estimation différée"""
        if not self.loading_preset:  # Ne pas programmer si on charge un préréglage
            self.loading_indicator.start()
            self.estimate_timer.start()

    def delayed_estimate(self):
        """Effectue l'estimation après le délai"""
        self.estimate_duration()
        self.loading_indicator.stop()
