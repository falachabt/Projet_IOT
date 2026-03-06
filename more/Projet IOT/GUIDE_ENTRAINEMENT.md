# 🎯 Guide Complet - Entraîner un Modèle YOLO Personnalisé

## Pourquoi entraîner ton propre modèle ?

Le modèle YOLO de base détecte des bouteilles mais **pas spécifiquement** :
- ✗ Bouchon fermé vs ouvert
- ✗ Type de flacon spécifique
- ✗ Niveau de remplissage précis

Avec ton propre modèle, tu obtiens **une détection sur mesure** pour ton cas d'usage !

---

## 📋 Étape 1 : Collecter des Images (30 min)

### Lancer la collecte
```bash
python collect_training_images.py
```

### Combien d'images ?
- **Minimum** : 50 images par classe = 150 images total
- **Recommandé** : 100 images par classe = 300 images total
- **Optimal** : 200+ images par classe

### Quoi photographier ?

#### 🧴 Classe 1 : `bottle` (flacon complet)
- Flacon vu de face, de côté, en angle
- Différentes positions dans l'image
- Différents éclairages

#### 🟢 Classe 2 : `cap_closed` (bouchon fermé)
- Bouchon bien vissé
- Différents angles de vue
- Gros plan + vue d'ensemble

#### 🔴 Classe 3 : `cap_open` (bouchon ouvert/absent)
- Bouchon dévissé
- Bouchon enlevé
- Flacon sans bouchon

### Conseils
- Varie les conditions (lumière, fond, position)
- Garde le même type de flacon que tu veux analyser
- Prends plusieurs photos de chaque configuration
- Utilise le crosshair vert pour centrer

---

## 🏷️ Étape 2 : Annoter les Images (1-2h)

### Méthode Recommandée : Roboflow (le plus simple) ⭐

1. **Créer un compte**
   - Va sur https://roboflow.com
   - Inscription gratuite

2. **Créer un projet**
   - Nouveau projet
   - Type: Object Detection
   - Nom: "Flacon Detector"

3. **Upload les images**
   - Upload `training_data/images/` 
   - Attends la fin du chargement

4. **Annoter**
   - Clique sur chaque image
   - Dessine des rectangles autour de :
     * La bouteille entière → label `bottle`
     * Le bouchon → label `cap_closed` ou `cap_open`
   - Fais ça pour TOUTES les images

5. **Générer le dataset**
   - "Generate" > "Version 1"
   - Split: 70% Train, 20% Valid, 10% Test
   - Preprocessing: Resize 640x640
   - Augmentation (optionnel) :
     * Flip horizontal
     * Rotation ±15°
     * Brightness ±15%

6. **Export**
   - Format: **YOLOv8**
   - Download ZIP

7. **Installer dans le projet**
   ```bash
   # Extraire le ZIP téléchargé
   # Copier le contenu dans training_data/
   ```

### Méthode Alternative : Label Studio (local)

```bash
pip install label-studio
label-studio
```

1. Ouvre http://localhost:8080
2. Crée un projet "Object Detection with Bounding Boxes"
3. Import `training_data/images/`
4. Annote avec les 3 labels
5. Export > YOLO

### Méthode Manuelle : labelImg (basique)

```bash
pip install labelImg
labelImg training_data/images/
```

- Format: YOLO
- Dessine les rectangles manuellement
- Sauvegarde crée un .txt par image

---

## 🏋️ Étape 3 : Entraîner le Modèle (1-3h selon PC)

### Structure du dataset
Vérifie que tu as cette structure :
```
training_data/
  ├── dataset.yaml
  ├── images/
  │   ├── train/
  │   │   ├── img001.jpg
  │   │   ├── img002.jpg
  │   │   └── ...
  │   └── val/
  │       ├── img050.jpg
  │       └── ...
  └── labels/
      ├── train/
      │   ├── img001.txt
      │   ├── img002.txt
      │   └── ...
      └── val/
          ├── img050.txt
          └── ...
```

### Lancer l'entraînement
```bash
python train_custom_model.py
```

### Choix du modèle
- **yolo11n.pt** (nano) : Le plus rapide, idéal pour Raspberry Pi
- **yolo11s.pt** (small) : Bon compromis
- **yolo11m.pt** (medium) : Plus précis mais plus lent

### Pendant l'entraînement
- Patience ! Peut prendre 1-3h selon ton PC
- Surveille les métriques dans le terminal
- Le modèle s'améliore progressivement

### Si erreur mémoire
Édite `train_custom_model.py` :
```python
BATCH_SIZE = 8  # au lieu de 16
IMG_SIZE = 416  # au lieu de 640
```

---

## 🚀 Étape 4 : Utiliser ton Modèle

### Récupérer le modèle entraîné
```bash
# Le meilleur modèle est ici :
training_runs/flacon_detector/weights/best.pt

# Copie-le à la racine
cp training_runs/flacon_detector/weights/best.pt ./flacon_model.pt
```

### Modifier le code
Édite `flacon_checker_v2.py` ligne 35 :
```python
# Avant:
self.model = YOLO("yolo11n.pt")

# Après:
self.model = YOLO("flacon_model.pt")
```

### Tester
```bash
python flacon_checker_v2.py
```

Maintenant ton modèle détecte **tes flacons spécifiques** avec **tes bouchons** !

---

## 📊 Évaluer les Performances

Après l'entraînement, regarde :
```
training_runs/flacon_detector/
  ├── weights/best.pt           # Ton modèle
  ├── results.png               # Graphiques de performance
  ├── confusion_matrix.png      # Matrice de confusion
  └── val_batch0_pred.jpg       # Exemples de prédictions
```

### Métriques importantes
- **mAP50** : Précision globale (objectif > 0.7)
- **Precision** : Taux de vrais positifs (objectif > 0.8)
- **Recall** : Taux de détection (objectif > 0.8)

### Si les résultats sont mauvais
1. **Collecte plus d'images** (vise 200+ par classe)
2. **Améliore les annotations** (rectangles précis)
3. **Augmente les époques** (essaye 150-200)
4. **Varie plus les conditions** de capture

---

## 🎓 Conseils Avancés

### Améliorer la précision
- Ajoute plus d'augmentations dans `train_custom_model.py`
- Utilise un modèle plus gros (yolo11m.pt)
- Augmente le nombre d'époques

### Optimiser pour Raspberry Pi
- Utilise yolo11n.pt (le plus léger)
- Réduis IMG_SIZE à 416
- Considère la quantification du modèle

### Entraîner sur GPU
Si tu as un GPU NVIDIA :
```python
# Dans train_custom_model.py
device='cuda'  # au lieu de 'cpu'
```

---

## ❓ FAQ

**Q: Combien de temps prend l'entraînement ?**
A: 1-3h sur CPU, 15-30min sur GPU

**Q: Mon PC n'est pas assez puissant ?**
A: Utilise Google Colab (gratuit avec GPU) :
https://colab.research.google.com/

**Q: Je peux entraîner sur le Raspberry Pi ?**
A: Possible mais très lent (10-20h). Mieux sur PC puis transférer le modèle.

**Q: Ça coûte de l'argent ?**
A: Non ! Tout est gratuit (Roboflow free tier, YOLO open-source)

**Q: Je peux détecter d'autres choses ?**
A: Oui ! Modifie `dataset.yaml` avec tes propres classes.

---

## 🆘 Besoin d'Aide ?

1. Vérifie que la structure du dataset est correcte
2. Regarde les exemples dans `training_data/`
3. Teste avec peu d'images d'abord (30 total)
4. Augmente progressivement

**Bon entraînement ! 🚀**
