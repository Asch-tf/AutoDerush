from datetime import datetime
import time
from plyer import notification
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from tkcalendar import Calendar

class AppRappels(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Smart Reminder")
        self.geometry("1000x700")
        
        # Initialisation du style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Police par défaut pour l'application
        default_font = ('Calibri', 11)
        title_font = ('Calibri', 12, 'bold')
        button_font = ('Calibri', 11, 'bold')
        
        self.option_add('*Font', default_font)
        self.option_add('*TButton*Font', button_font)
        self.option_add('*TLabel*Font', default_font)
        
        # Initialisation du thème
        self.current_theme = "light"
        
        # Définition des palettes de couleurs
        self.color_themes = {
            "light": {
                "primary": "#4361ee",
                "secondary": "#3f37c9",
                "accent": "#4895ef",
                "success": "#4cc9f0",
                "background": "#f8f9fa",
                "sidebar": "#1a1a2e",
                "text_light": "#ffffff",
                "text_dark": "#212529",
                "input_bg": "#ffffff",
                "border": "#e9ecef",
                "list_bg": "#ffffff",
                "tab_bg": "#ffffff",
                "tab_selected": "#4361ee",
                "date_entry_bg": "#ffffff",
                "date_entry_fg": "#212529",
                "date_selected_bg": "#4361ee",
                "date_selected_fg": "#ffffff"
            },
            "dark": {
                "primary": "#3498db",
                "secondary": "#2980b9",
                "accent": "#34495e",
                "success": "#27ae60",
                "background": "#1a1a2e",
                "sidebar": "#0f0f1a",
                "text_light": "#ffffff",
                "text_dark": "#ecf0f1",
                "input_bg": "#2d2d3f",
                "border": "#2d3436",
                "list_bg": "#242438",
                "tab_bg": "#1a1a2e",
                "tab_selected": "#3498db",
                "date_entry_bg": "#2d2d3f",
                "date_entry_fg": "#ffffff",
                "date_selected_bg": "#3498db",
                "date_selected_fg": "#ffffff"
            }
        }
        
        # Initialisation des couleurs avec le thème actuel
        self.colors = self.color_themes[self.current_theme]
        
        # Création du gestionnaire
        self.gestionnaire = GestionnaireRappels()
        
        # Création des onglets
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")
        
        # Onglet Ajouter
        self.tab_ajouter = ttk.Frame(self.notebook)
        self.creer_onglet_ajouter()
        
        # Onglet Liste
        self.tab_liste = ttk.Frame(self.notebook)
        self.creer_onglet_liste()
        
        self.notebook.add(self.tab_ajouter, text="Ajouter un rappel")
        self.notebook.add(self.tab_liste, text="Liste des rappels")
        
        # Création du bouton de thème
        self.theme_button = tk.Button(
            self,
            text="🌙 Mode sombre",
            command=self.toggle_theme,
            bg="#4361ee",
            fg="white",
            font=('Helvetica', 10),
            relief="flat",
            width=20
        )
        self.theme_button.pack(side="bottom", padx=10, pady=10)
        
        # Démarrer la vérification périodique des rappels
        self.verifier_rappels()
        
        # Ajouter un gestionnaire d'événement pour le redimensionnement
        self.bind('<Configure>', self.on_resize)

    def creer_onglet_ajouter(self):
        # Frame pour le formulaire
        form_frame = ttk.Frame(self.tab_ajouter)
        form_frame.pack(padx=30, pady=30, fill='both', expand=True)
        
        # Styles des polices
        title_font = ('Calibri', 12, 'bold')
        label_font = ('Calibri', 11)
        
        # Titre de la section
        section_title = ttk.Label(form_frame, text="Nouveau Rappel", font=('Calibri', 16, 'bold'))
        section_title.pack(pady=(0, 20), anchor='w')
        
        # Titre
        titre_frame = ttk.Frame(form_frame)
        titre_frame.pack(fill='x', pady=10)
        self.titre_label = ttk.Label(titre_frame, text="Titre:", font=label_font)
        self.titre_label.pack(side='left', padx=(0, 10))
        self.titre_entry = ttk.Entry(titre_frame, font=label_font)
        self.titre_entry.pack(side='left', fill='x', expand=True)
        
        # Message
        message_frame = ttk.Frame(form_frame)
        message_frame.pack(fill='x', pady=10)
        self.message_label = ttk.Label(message_frame, text="Message:", font=label_font)
        self.message_label.pack(side='left', padx=(0, 10))
        self.message_entry = ttk.Entry(message_frame, font=label_font)
        self.message_entry.pack(side='left', fill='x', expand=True)
        
        # Date et Heure
        datetime_frame = ttk.Frame(form_frame)
        datetime_frame.pack(fill='x', pady=10)
        
        # Date
        self.date_frame = ttk.Frame(datetime_frame)
        self.date_frame.pack(side='left', padx=(0, 30))
        self.date_label = ttk.Label(self.date_frame, text="Date:", font=('Calibri', 11))
        self.date_label.pack(side='left', padx=(0, 10))
        
        # Configuration du style pour le DateEntry
        date_style = {'background': self.colors["date_entry_bg"],
                     'foreground': self.colors["date_entry_fg"],
                     'borderwidth': 1,
                     'relief': "solid",
                     'font': ('Calibri', 11),
                     'selectbackground': self.colors["date_selected_bg"],
                     'selectforeground': self.colors["date_selected_fg"],
                     'fieldbackground': self.colors["date_entry_bg"]}
        
        self.date_entry = DateEntry(self.date_frame, width=12, 
                                  **date_style,
                                  headersbackground=self.colors["input_bg"],
                                  headersforeground=self.colors["text_light"],
                                  normalbackground=self.colors["input_bg"],
                                  normalforeground=self.colors["text_light"],
                                  weekendbackground=self.colors["input_bg"],
                                  weekendforeground=self.colors["text_light"],
                                  othermonthbackground=self.colors["background"],
                                  othermonthforeground=self.colors["text_dark"])
        
        # Configuration supplémentaire du DateEntry
        self.date_entry._top_cal.configure(background=self.colors["input_bg"])
        for w in self.date_entry._top_cal.winfo_children():
            if isinstance(w, tk.Entry):
                w.configure(background=self.colors["date_entry_bg"],
                          foreground=self.colors["date_entry_fg"],
                          insertbackground=self.colors["date_entry_fg"])
        
        self.date_entry.pack(side='left')
        
        # Heure
        heure_frame = ttk.Frame(datetime_frame)
        heure_frame.pack(side='left')
        self.heure_label = ttk.Label(heure_frame, text="Heure:", font=label_font)
        self.heure_label.pack(side='left', padx=(0, 10))
        
        time_frame = ttk.Frame(heure_frame)
        time_frame.pack(side='left')
        
        self.heure_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        
        self.heure_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=2,
                                      textvariable=self.heure_var, format="%02.0f",
                                      font=label_font)
        self.heure_spinbox.pack(side='left')
        
        ttk.Label(time_frame, text=":", font=label_font).pack(side='left', padx=2)
        
        self.minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=2,
                                       textvariable=self.minute_var, format="%02.0f",
                                       font=label_font)
        self.minute_spinbox.pack(side='left')
        
        # Bouton Ajouter
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=30)
        self.bouton_ajouter = ttk.Button(button_frame,
                                      text="Ajouter le rappel",
                                      command=self.ajouter_rappel,
                                      style='Accent.TButton')
        self.bouton_ajouter.pack()

    def creer_onglet_liste(self):
        # Frame principal
        main_frame = ttk.Frame(self.tab_liste)
        main_frame.pack(padx=30, pady=30, fill='both', expand=True)
        
        # Titre de la section
        section_title = ttk.Label(main_frame, text="Liste des Rappels", font=('Calibri', 16, 'bold'))
        section_title.pack(pady=(0, 20), anchor='w')
        
        # Création du Treeview avec style personnalisé
        self.tree = ttk.Treeview(main_frame, columns=("Titre", "Message", "Date"), show="headings",
                                style="Custom.Treeview")
        
        # Configuration des colonnes
        self.tree.heading("Titre", text="Titre")
        self.tree.heading("Message", text="Message")
        self.tree.heading("Date", text="Date")
        
        # Ajustement des colonnes
        self.tree.column("Titre", width=200)
        self.tree.column("Message", width=400)
        self.tree.column("Date", width=150)
        
        self.tree.pack(pady=10, fill='both', expand=True)
        
        # Frame pour les boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20, fill='x')
        
        # Boutons avec espacement
        ttk.Button(button_frame, text="Rafraîchir", 
                  command=self.rafraichir_liste,
                  style='Secondary.TButton').pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Supprimer le rappel sélectionné",
                  command=self.supprimer_rappel,
                  style='Secondary.TButton').pack(side='left', padx=5)
        
        self.rafraichir_liste()

    def ajouter_rappel(self):
        titre = self.titre_entry.get()
        message = self.message_entry.get()
        date = self.date_entry.get_date()
        heure = self.heure_var.get()
        minute = self.minute_var.get()
        
        if not titre or not message:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
            
        date_str = f"{date.strftime('%d/%m/%Y')} {heure}:{minute}"
        
        try:
            self.gestionnaire.ajouter_rappel_gui(titre, message, date_str)
            messagebox.showinfo("Succès", "Rappel ajouté avec succès!")
            self.rafraichir_liste()
            
            # Réinitialiser les champs
            self.titre_entry.delete(0, tk.END)
            self.message_entry.delete(0, tk.END)
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))

    def rafraichir_liste(self):
        # Effacer la liste actuelle
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Remplir avec les rappels actuels
        for rappel in self.gestionnaire.rappels:
            self.tree.insert("", tk.END, values=(
                rappel["titre"],
                rappel["message"],
                rappel["date"]
            ))

    def supprimer_rappel(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un rappel à supprimer")
            return
            
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce rappel?"):
            item = self.tree.item(selection[0])
            date_rappel = item['values'][2]
            self.gestionnaire.supprimer_rappel(date_rappel)
            self.rafraichir_liste()

    def verifier_rappels(self):
        self.gestionnaire.verifier_rappels()
        self.after(60000, self.verifier_rappels)  # Vérifier toutes les minutes

    def ouvrir_calendrier(self):
        # Création de la fenêtre popup
        top = tk.Toplevel(self)
        top.title("Sélectionner une date")
        
        # Rendre la fenêtre modale
        top.transient(self)
        top.grab_set()
        
        # Style pour la fenêtre popup
        top.configure(bg=self.colors["background"])
        
        # Création du calendrier avec style
        cal = Calendar(top, 
                      selectmode='day',
                      year=datetime.now().year,
                      month=datetime.now().month,
                      day=datetime.now().day,
                      locale='fr_FR')  # Simplifié pour éviter les conflits
        cal.pack(padx=20, pady=20)
        
        # Frame pour le bouton
        btn_frame = ttk.Frame(top, style="Main.TFrame")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def set_date():
            try:
                selected = cal.selection_get()
                formatted_date = selected.strftime("%d/%m/%Y")
                self.selected_date.set(formatted_date)
                top.destroy()
            except:
                messagebox.showerror("Erreur", "Veuillez sélectionner une date")
        
        # Bouton de validation stylisé
        ttk.Button(btn_frame, 
                  text="✓ Valider", 
                  style="Primary.TButton",
                  command=set_date).pack(pady=5)
        
        # Centrer la fenêtre popup
        top.update_idletasks()
        width = top.winfo_width()
        height = top.winfo_height()
        x = (self.winfo_width() // 2) - (width // 2) + self.winfo_x()
        y = (self.winfo_height() // 2) - (height // 2) + self.winfo_y()
        top.geometry(f"+{x}+{y}")

    def create_layout(self):
        # Créer un frame pour le bouton en bas
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side="bottom", fill="x")
        
        # Bouton de thème simple en bas à gauche
        self.theme_button = tk.Button(
            bottom_frame,
            text="🌙 Mode sombre",
            command=self.toggle_theme,
            bg="#4361ee",
            fg="white",
            font=('Helvetica', 10),
            relief="flat",
            width=20
        )
        self.theme_button.pack(side="left", padx=10, pady=10)
        
        # Création de la sidebar
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo et titre dans la sidebar
        ttk.Label(self.sidebar,
                 text="Smart Reminder",
                 font=('Helvetica', 16, 'bold'),
                 foreground=self.colors["text_light"],
                 background=self.colors["sidebar"]).pack(pady=20)
        
        # Zone principale
        self.main_frame = ttk.Frame(self, style="Main.TFrame")
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        # Création des onglets
        self.notebook = ttk.Notebook(self.main_frame)
        
        # Onglet Ajouter
        self.tab_ajouter = ttk.Frame(self.notebook, style="Main.TFrame")
        self.creer_onglet_ajouter()
        
        # Onglet Liste
        self.tab_liste = ttk.Frame(self.notebook, style="Main.TFrame")
        self.creer_onglet_liste()
        
        self.notebook.add(self.tab_ajouter, text="Ajouter un rappel")
        self.notebook.add(self.tab_liste, text="Liste des rappels")
        self.notebook.pack(expand=True, fill="both")

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.colors = self.color_themes[self.current_theme]
        
        # Mettre à jour le texte du bouton
        self.theme_button.configure(
            text="☀️ Mode clair" if self.current_theme == "dark" else "🌙 Mode sombre",
            bg=self.colors["primary"],
            fg=self.colors["text_light"]
        )
        
        # Configurer les styles ttk
        style = self.style
        
        # Style général
        style.configure(".",
                       background=self.colors["background"],
                       foreground=self.colors["text_dark"])
        
        # Style pour les onglets
        style.configure("TNotebook",
                       background=self.colors["tab_bg"],
                       borderwidth=0)
        
        style.configure("TNotebook.Tab",
                       background=self.colors["tab_bg"],
                       foreground=self.colors["text_dark"],
                       padding=[10, 5],
                       borderwidth=0)
        
        style.map("TNotebook.Tab",
                 background=[("selected", self.colors["tab_selected"])],
                 foreground=[("selected", self.colors["text_light"])])
        
        # Style pour les boutons
        style.configure("TButton",
                       background=self.colors["primary"],
                       foreground=self.colors["text_light"],
                       padding=(10, 5))
        
        style.configure("Accent.TButton",
                       background=self.colors["accent"],
                       foreground=self.colors["text_light"],
                       padding=(20, 10))
        
        style.configure("Secondary.TButton",
                       background=self.colors["secondary"],
                       foreground=self.colors["text_light"],
                       padding=(10, 5))
        
        # Style pour les entrées
        style.configure("TEntry",
                       fieldbackground=self.colors["input_bg"],
                       foreground=self.colors["text_dark"],
                       borderwidth=1,
                       relief="solid")
        
        # Style pour les Spinbox
        style.configure("TSpinbox",
                       fieldbackground=self.colors["input_bg"],
                       foreground=self.colors["text_dark"],
                       selectbackground=self.colors["primary"],
                       selectforeground=self.colors["text_light"],
                       arrowcolor=self.colors["text_dark"])
        
        # Mettre à jour le style du DateEntry et son calendrier
        self.date_entry.configure(
            background=self.colors["date_entry_bg"],
            foreground=self.colors["date_entry_fg"],
            selectbackground=self.colors["date_selected_bg"],
            selectforeground=self.colors["date_selected_fg"],
            borderwidth=1,
            relief="solid"
        )
        
        # Configuration du style du calendrier
        style.configure('Calendar.TFrame', 
                       background=self.colors["input_bg"])
        style.configure('Calendar.TLabel', 
                       background=self.colors["input_bg"],
                       foreground=self.colors["text_light"])
        style.configure('Calendar.TButton', 
                       background=self.colors["input_bg"],
                       foreground=self.colors["text_light"])
        
        # Recréer le DateEntry pour appliquer les nouveaux styles
        old_date = self.date_entry.get_date()
        self.date_entry.destroy()
        
        # Configuration du style pour le nouveau DateEntry
        date_style = {'background': self.colors["date_entry_bg"],
                     'foreground': self.colors["date_entry_fg"],
                     'borderwidth': 1,
                     'relief': "solid",
                     'font': ('Calibri', 11),
                     'selectbackground': self.colors["date_selected_bg"],
                     'selectforeground': self.colors["date_selected_fg"],
                     'fieldbackground': self.colors["date_entry_bg"]}
        
        self.date_entry = DateEntry(self.date_frame, width=12,
                                  **date_style,
                                  headersbackground=self.colors["input_bg"],
                                  headersforeground=self.colors["text_light"],
                                  normalbackground=self.colors["input_bg"],
                                  normalforeground=self.colors["text_light"],
                                  weekendbackground=self.colors["input_bg"],
                                  weekendforeground=self.colors["text_light"],
                                  othermonthbackground=self.colors["background"],
                                  othermonthforeground=self.colors["text_dark"])
        
        # Configuration supplémentaire du DateEntry
        self.date_entry._top_cal.configure(background=self.colors["input_bg"])
        for w in self.date_entry._top_cal.winfo_children():
            if isinstance(w, tk.Entry):
                w.configure(background=self.colors["date_entry_bg"],
                          foreground=self.colors["date_entry_fg"],
                          insertbackground=self.colors["date_entry_fg"])
        
        self.date_entry.pack(side='left')
        self.date_entry.set_date(old_date)
        
        # Style pour le Treeview
        style.configure("Custom.Treeview",
                       background=self.colors["list_bg"],
                       fieldbackground=self.colors["list_bg"],
                       foreground=self.colors["text_dark"],
                       rowheight=30,
                       font=('Calibri', 11))
        
        style.configure("Custom.Treeview.Heading",
                       background=self.colors["primary"],
                       foreground=self.colors["text_light"],
                       font=('Calibri', 11, 'bold'),
                       padding=(10, 5))
        
        # Mettre à jour la fenêtre principale
        self.configure(bg=self.colors["background"])
        
        # Mettre à jour les spinbox
        self.heure_spinbox.configure(style="TSpinbox")
        self.minute_spinbox.configure(style="TSpinbox")
        
        self.update_idletasks()

    def on_resize(self, event):
        if hasattr(self, 'theme_button'):
            self.theme_button.place(x=10, y=self.winfo_height() - 40)

class GestionnaireRappels:
    def __init__(self):
        self.fichier_rappels = "rappels.json"
        self.rappels = self.charger_rappels()

    def charger_rappels(self):
        if os.path.exists(self.fichier_rappels):
            with open(self.fichier_rappels, 'r') as f:
                return json.load(f)
        return []

    def sauvegarder_rappels(self):
        with open(self.fichier_rappels, 'w') as f:
            json.dump(self.rappels, f)

    def ajouter_rappel_gui(self, titre, message, date_str):
        try:
            date_rappel = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            
            rappel = {
                "titre": titre,
                "message": message,
                "date": date_rappel.strftime("%d/%m/%Y %H:%M")
            }
            
            self.rappels.append(rappel)
            self.sauvegarder_rappels()
        except ValueError:
            raise ValueError("Format de date invalide!")

    def supprimer_rappel(self, date_str):
        self.rappels = [r for r in self.rappels if r["date"] != date_str]
        self.sauvegarder_rappels()

    def verifier_rappels(self):
        maintenant = datetime.now()
        rappels_a_supprimer = []

        for rappel in self.rappels:
            date_rappel = datetime.strptime(rappel["date"], "%d/%m/%Y %H:%M")
            if date_rappel <= maintenant:
                self.envoyer_notification(rappel["titre"], rappel["message"])
                rappels_a_supprimer.append(rappel)

        for rappel in rappels_a_supprimer:
            self.rappels.remove(rappel)
        self.sauvegarder_rappels()

    def envoyer_notification(self, titre, message):
        notification.notify(
            title=titre,
            message=message,
            app_icon=None,
            timeout=10,
        )

if __name__ == "__main__":
    app = AppRappels()
    app.mainloop()  