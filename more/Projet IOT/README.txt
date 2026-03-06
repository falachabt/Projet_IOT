# Flacon Checker - Controle Qualite

Application de controle qualite automatise pour flacons avec vision par ordinateur.

## Installation

1. Double-cliquez sur `install.bat`
2. Attendez la fin de l'installation (~2-3 minutes)

## Test rapide

Double-cliquez sur `test.bat` pour faire un test avec votre webcam !
L'image sera sauvegardee dans le dossier `output/`

## Utilisation manuelle

Activez l'environnement virtuel:
```
venv\Scripts\activate
```

### Mode demo (avec webcam Windows)
```
python flacon_checker.py --demo --headless
```

### Mode production (avec Picamera2 sur Raspberry Pi)
```
python flacon_checker.py --headless --continuous --interval 10
```

### Mode avec affichage visuel
```
python flacon_checker.py --demo
```

## Structure

```
Projet_IOT/
├── flacon_checker.py    # Script principal
├── requirements.txt     # Dependances Python
├── install.bat         # Script d'installation
├── test.bat            # Test rapide
├── run.bat             # Lancement en continu
├── venv/               # Environnement virtuel Python
└── output/             # Images capturees
```

## Configuration

Modifiez dans `flacon_checker.py`:
- MIN_FILL_PERCENT = 80  # Niveau minimum (%)
- MAX_FILL_PERCENT = 105 # Niveau maximum (%)

## Resultats

Les images sont nommees:
- 20260119_173108_OK.jpg     (flacon valide)
- 20260119_173108_REJET.jpg  (flacon rejete)

Status inclus dans le nom du fichier pour faciliter le tri!
