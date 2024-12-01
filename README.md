# AutoDerush

AutoDerush est une application de traitement vidéo qui permet de supprimer automatiquement les silences dans les vidéos. Elle est particulièrement utile pour le montage de vidéos, les tutoriels, ou tout autre contenu où vous souhaitez éliminer les temps morts.

## Fonctionnalités

- Détection automatique des silences
- Prévisualisation en temps réel de la vidéo
- Interface graphique intuitive
- Préréglages personnalisables
- Contrôle précis des paramètres de détection
- Prévisualisation du résultat avant export

## Prérequis

- Python 3.6 ou supérieur
- FFmpeg installé et accessible dans le PATH
- Les dépendances Python listées dans `requirements.txt`

## Installation

1. Clonez ce dépôt :

```bash
git clone https://github.com/votre-username/AutoDerush.git
cd AutoDerush
```

2. Installez les dépendances :

```bash
pip install -r requirements.txt
```

3. Installez FFmpeg :
   - Windows : [Téléchargez FFmpeg](https://ffmpeg.org/download.html)
   - Linux : `sudo apt-get install ffmpeg`
   - macOS : `brew install ffmpeg`

## Utilisation

1. Lancez l'application :

```bash
python video_cutter/main.py
```

2. Sélectionnez une vidéo à traiter
3. Ajustez les paramètres selon vos besoins :
   - Seuil de détection : contrôle la sensibilité de détection des silences
   - Marge : définit la durée à conserver avant/après chaque segment
4. Utilisez les préréglages ou créez les vôtres
5. Cliquez sur "Traiter la vidéo"

## Création de l'exécutable

Pour créer un exécutable Windows :

```bash
python create_shortcut.py
```

Cela créera :
- Un exécutable dans le dossier `dist/AutoDerush`
- Un raccourci sur le bureau

## Préréglages

L'application inclut trois préréglages par défaut :
- Standard (seuil : 25, marge : 100ms)
- Agressif (seuil : 75, marge : 50ms)
- Conservateur (seuil : 15, marge : 200ms)

Vous pouvez créer et sauvegarder vos propres préréglages.

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 