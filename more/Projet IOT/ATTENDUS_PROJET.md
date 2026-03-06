# 📋 ATTENDUS DU PROJET

## Projet 4 : Garantir la qualité de la production d'un produit pharmaceutique (Flacons d'insuline) – Vérification

**Étudiant** : Walid
**Formation** : [À compléter]
**Date** : Mars 2026
**Encadrant** : [À compléter]

---

## 1️⃣ CAHIER DES CHARGES

### 1.1 Objectifs du projet

- ✅ Développer un **système automatisé de contrôle qualité** pour la production de flacons d'insuline
- ✅ Implémenter une **détection visuelle par intelligence artificielle** (YOLO) pour vérifier :
  - Présence de la bouteille
  - Présence et bon positionnement du bouchon
  - Présence et lisibilité de l'étiquette
  - Niveau de liquide dans le flacon
- ✅ Créer un **jumeau numérique** pour supervision temps réel
- ✅ Garantir la **traçabilité** des produits conformes et non-conformes

### 1.2 Spécifications fonctionnelles

#### Capteurs et actionneurs
- Capteur infrarouge (détection présence objet)
- Caméra Raspberry Pi + modèle YOLO
- 2 convoyeurs (moteurs DC)
- LEDs d'indication (verte = OK, rouge = défaut)
- Bouton d'arrêt d'urgence

#### Logique de contrôle (GRAFCET)
- **E0_INIT** : Initialisation du système
- **E1_MARCHE_CONV** : Démarrage convoyeur 1
- **E2_DETECTION_OBJET** : Détection flacon par capteur IR
- **E3_CONTROL_CAMERA** : Analyse visuelle par IA
- **E6_LED_ROUGE_CAMERA** : Produit non-conforme (évacuation)
- **E8_LED_VERT_CONV2** : Produit conforme (convoyeur 2)
- **E9_STOP_CONV** / **E11_STOP_CONV2** : Arrêts contrôlés

#### Protocole de communication
- **MQTT** pour IoT
- **WebSocket** pour temps réel
- **REST API** pour commandes
- **InfluxDB** pour historisation

### 1.3 Spécifications techniques

| Composant | Technologie |
|-----------|-------------|
| Microcontrôleur | ESP8266 NodeMCU |
| Ordinateur embarqué | Raspberry Pi 4 |
| Vision par ordinateur | YOLOv8 (Ultralytics) |
| Broker MQTT | Eclipse Mosquitto |
| Backend | Node.js + Express |
| Base de données temps réel | InfluxDB |
| Frontend | React + Vite |
| Design UI | Glass Morphism moderne |

### 1.4 Contraintes

- ✅ Temps de réponse < 200ms pour détection
- ✅ Taux de faux positifs < 2%
- ✅ Disponibilité système > 99%
- ✅ Interface responsive (desktop, tablet, mobile)
- ✅ Traçabilité complète des analyses
- ✅ Arrêt d'urgence fonctionnel en < 100ms

---

## 2️⃣ ARCHITECTURES TECHNIQUES / IMPLÉMENTATION

### 2.1 Architecture globale

```
┌──────────────┐
│  ESP8266     │ ──MQTT──> ┌──────────────────┐
│  - Capteur IR│           │  Raspberry Pi    │
│  - Moteurs   │           │  - Mosquitto     │
│  - LEDs      │ <─GPIO──> │  - Caméra YOLO   │
└──────────────┘           └──────────────────┘
                                    │
                                  MQTT
                                    │
                                    ▼
┌──────────────────────────────────────────────┐
│  Backend (Node.js)                           │
│  - MQTT Handler                              │
│  - WebSocket Server                          │
│  - REST API                                  │
│  - InfluxDB Writer                           │
└──────────────────────────────────────────────┘
                    │
                WebSocket
                    │
                    ▼
┌──────────────────────────────────────────────┐
│  Frontend (React)                            │
│  - Dashboard temps réel                      │
│  - Graphiques historiques                    │
│  - Contrôles à distance                      │
│  - Statistiques de production                │
└──────────────────────────────────────────────┘
```

### 2.2 Architecture matérielle (ESP8266)

**Pinout utilisé** :
- **D1** : Capteur IR (détection objet)
- **D7/D8** : Moteur 1 (L298N IN1/IN2)
- **D3/D4** : Moteur 2 (L298N IN3/IN4)
- **D0** : LED verte
- **D2** : LED rouge

**Topics MQTT publiés** :
- `esp8266/capteurs/distance` - État capteur IR
- `esp8266/actionneurs/moteur1` - État moteur 1
- `esp8266/actionneurs/moteur2` - État moteur 2
- `esp8266/actionneurs/led_vert_conv` - LED verte
- `esp8266/actionneurs/led_rouge_camera` - LED rouge
- `esp8266/systeme/etat` - État GRAFCET complet
- `esp8266/boutons/marche` - Bouton marche
- `esp8266/systeme/urgence` - Arrêt d'urgence

**Topics MQTT souscrits** :
- `esp8266/commandes/#` - Commandes générales
- `esp8266/boutons/marche/cmd` - Bouton virtuel marche
- `esp8266/boutons/urgence/cmd` - Bouton virtuel urgence
- `raspberry/camera/resultat` - Résultat analyse caméra

### 2.3 Architecture logicielle (Raspberry Pi)

**Script de détection YOLO** :
- Capture image via Raspberry Pi Camera
- Analyse avec modèle YOLOv8 entraîné
- Détection multi-classes :
  - Classe "bottle" (bouteille)
  - Classe "cap" (bouchon)
  - Classe "label" (étiquette)
- Score de confiance pour chaque détection
- Publication résultat sur MQTT

**Format message caméra** :
```json
{
  "status": "OK" | "KO" | "ERREUR",
  "bottle": {
    "detected": true,
    "confidence": 0.95
  },
  "cap": {
    "detected": true,
    "confidence": 0.92
  },
  "label": {
    "detected": true,
    "confidence": 0.88
  },
  "elapsed_ms": 145.5,
  "timestamp": "2026-03-05T10:30:00Z"
}
```

### 2.4 Architecture backend (Node.js)

**Modules principaux** :
1. **mqtt-handler.js** : Connexion broker, souscription topics, parsing messages
2. **influxdb.js** : Écriture données historiques
3. **routes/control.js** : API REST pour commandes
4. **websocket.js** : Broadcast temps réel vers frontend

**État global système** :
```javascript
global.systemState = {
  ultrason: { distance_cm, flacon_detecte, timestamp },
  moteur: { etat, vitesse, timestamp },
  leds: { verte, rouge, timestamp },
  urgence: { active, timestamp },
  boutons: { bouton_marche, bouton_urgence },
  camera: { status, bouteille_detectee, bouchon_present, ... },
  statistics: { total_analyses, analyses_ok, analyses_ko, taux_ok_pourcent }
}
```

### 2.5 Architecture frontend (React)

**Composants React** :
- `App.jsx` : Conteneur principal, gestion WebSocket
- `Dashboard.jsx` : Layout grille 3 lignes
- `SensorCard.jsx` : Affichage capteurs génériques
- `GrafcetStatus.jsx` : État du système GRAFCET
- `CameraFeed.jsx` : Résultats analyse visuelle
- `MotorControl.jsx` : Commande moteurs
- `LEDIndicator.jsx` : État et contrôle LEDs
- `ButtonControl.jsx` : Boutons virtuels MQTT
- `HistoryChart.jsx` : Graphiques historiques

**Design System** :
- Glass morphism (fond blur + transparence)
- Gradients animés multicolores
- Effets 3D au hover (élévation, rotation)
- Bordures RGB animées
- Palette : Indigo → Violet → Rose → Or
- Animations fluides (cubic-bezier)

---

## 3️⃣ PLANNING PRÉVISIONNEL

### Phase 1 : Conception (Semaine 1-2)
- ✅ Analyse des besoins
- ✅ Schéma architecture globale
- ✅ Choix technologies (ESP8266, Raspberry Pi, MQTT, React)
- ✅ Définition protocoles communication

### Phase 2 : Développement matériel (Semaine 3-4)
- ✅ Câblage ESP8266 + capteurs/actionneurs
- ✅ Configuration Raspberry Pi + caméra
- ✅ Tests unitaires capteurs
- ✅ Calibration capteur IR

### Phase 3 : Développement logiciel embarqué (Semaine 4-5)
- ✅ Programmation GRAFCET sur ESP8266
- ✅ Intégration MQTT (PubSubClient)
- ✅ Gestion boutons virtuels
- ✅ Tests intégration ESP8266 ↔ MQTT

### Phase 4 : Intelligence artificielle (Semaine 5-6)
- ✅ Collecte dataset images (bouteilles, bouchons, étiquettes)
- ✅ Annotation images (LabelImg, Roboflow)
- ✅ Entraînement modèle YOLOv8
- ✅ Optimisation pour Raspberry Pi
- ✅ Script Python détection temps réel

### Phase 5 : Backend (Semaine 6-7)
- ✅ Setup Node.js + Express
- ✅ MQTT handler avec souscription topics
- ✅ WebSocket server (temps réel)
- ✅ API REST (commandes moteur, LEDs)
- ✅ Intégration InfluxDB
- ✅ Calcul statistiques

### Phase 6 : Frontend (Semaine 7-8)
- ✅ Setup React + Vite
- ✅ Création composants (Dashboard, Cards, Charts)
- ✅ Connexion WebSocket
- ✅ Design system premium (glass morphism)
- ✅ Animations et effets visuels
- ✅ Responsive design

### Phase 7 : Tests et optimisation (Semaine 9)
- ⏳ Tests de bout en bout
- ⏳ Optimisation performances
- ⏳ Correction bugs
- ⏳ Tests de charge
- ⏳ Documentation utilisateur

### Phase 8 : Finalisation (Semaine 10)
- ⏳ Rédaction rapport technique
- ⏳ Préparation présentation
- ⏳ Démo système complet
- ⏳ Livraison finale

---

## 4️⃣ RAPPORT TECHNIQUE

### 4.1 Structure du rapport

1. **Introduction**
   - Contexte industriel
   - Problématique qualité pharmaceutique
   - Objectifs du projet

2. **Analyse et conception**
   - Cahier des charges détaillé
   - Choix technologiques justifiés
   - Architecture système (schémas, diagrammes)
   - GRAFCET détaillé

3. **Implémentation**
   - Développement ESP8266 (code, explications)
   - Développement Raspberry Pi (YOLO, MQTT)
   - Backend Node.js (architecture, API)
   - Frontend React (composants, design)

4. **Tests et validation**
   - Tests unitaires par composant
   - Tests d'intégration
   - Validation performances
   - Mesures (temps réponse, taux erreur)

5. **Résultats**
   - Captures d'écran interface
   - Statistiques de détection
   - Graphiques performances
   - Analyse critique

6. **Conclusion et perspectives**
   - Bilan objectifs atteints
   - Difficultés rencontrées
   - Améliorations futures
   - Apprentissages

### 4.2 Annexes

- Code source complet (GitHub)
- Schémas électriques
- Diagrammes UML
- Documentation API
- Manuel utilisateur
- Guides de démarrage

---

## 5️⃣ PRÉSENTATION FINALE

### 5.1 Format

- **Durée** : 15-20 minutes + 10 minutes questions
- **Support** : PowerPoint / Google Slides
- **Démo live** : Système en fonctionnement réel

### 5.2 Contenu de la présentation

**Slide 1 : Page de titre**
- Titre projet
- Nom étudiant
- Date

**Slides 2-3 : Contexte et problématique**
- Industrie pharmaceutique
- Importance contrôle qualité
- Enjeux réglementaires

**Slides 4-5 : Objectifs et cahier des charges**
- Objectifs fonctionnels
- Contraintes techniques
- Spécifications

**Slides 6-8 : Architecture et technologies**
- Schéma architecture globale
- Technologies choisies
- Justifications

**Slides 9-11 : Implémentation**
- ESP8266 + GRAFCET
- Raspberry Pi + YOLO
- Backend + Frontend

**Slide 12 : Démo live** 🎥
- Montrer système en action
- Détection objet
- Analyse caméra OK/KO
- Interface temps réel
- Statistiques

**Slides 13-14 : Résultats et performances**
- Taux de détection
- Temps de réponse
- Captures d'écran interface
- Graphiques statistiques

**Slide 15 : Difficultés et solutions**
- Problèmes rencontrés
- Solutions apportées
- Apprentissages

**Slide 16 : Perspectives et améliorations**
- Évolutions possibles
- Intégration ERP
- Machine learning avancé

**Slide 17 : Conclusion**
- Bilan projet
- Compétences acquises
- Remerciements

**Slide 18 : Questions**

### 5.3 Conseils pour la présentation

- ✅ Parler clairement et lentement
- ✅ Regarder l'auditoire
- ✅ Éviter lecture des slides
- ✅ Préparer la démo (tests avant)
- ✅ Prévoir plan B si problème technique
- ✅ Anticiper questions techniques
- ✅ Montrer passion et maîtrise du sujet

---

## 📊 LIVRABLES ATTENDUS

### Livrables obligatoires

1. ✅ **Code source complet**
   - Repository GitHub
   - Code ESP8266 (Arduino/C++)
   - Code Raspberry Pi (Python)
   - Code Backend (Node.js)
   - Code Frontend (React)
   - Fichiers configuration

2. ✅ **Documentation technique**
   - README.md complet
   - Guide d'installation
   - Guide de démarrage
   - Documentation API
   - Schémas électriques
   - Architecture système

3. ⏳ **Rapport technique**
   - Format PDF
   - 30-50 pages
   - Schémas et captures
   - Analyse détaillée
   - Bibliographie

4. ⏳ **Présentation**
   - Support PowerPoint/PDF
   - 15-20 slides
   - Démonstration vidéo (backup)

5. ✅ **Système fonctionnel**
   - Prototype opérationnel
   - Tests validés
   - Démonstration live

### Livrables bonus

- 📹 Vidéo démo complète (YouTube)
- 📚 Manuel utilisateur illustré
- 🧪 Dataset d'entraînement YOLO
- 📈 Dashboard analytics avancé
- 🔧 Scripts de déploiement automatisé

---

## ✅ CRITÈRES D'ÉVALUATION

### Aspects techniques (40%)
- Maîtrise des technologies IoT
- Qualité du code (lisibilité, organisation)
- Architecture système robuste
- Performances et optimisation

### Fonctionnalités (30%)
- Respect cahier des charges
- Système complet et opérationnel
- Intégration composants
- Fiabilité détection IA

### Documentation (15%)
- Clarté rapport technique
- Qualité schémas et diagrammes
- Guides utilisateur
- Code commenté

### Présentation (15%)
- Clarté de l'exposé
- Qualité supports visuels
- Démo live réussie
- Réponses aux questions

---

## 📅 DATES CLÉS

| Jalons | Date limite | Statut |
|--------|-------------|--------|
| Cahier des charges | [Date] | ✅ Terminé |
| Prototype matériel | [Date] | ✅ Terminé |
| Backend fonctionnel | [Date] | ✅ Terminé |
| Frontend complet | [Date] | ✅ Terminé |
| Tests finaux | [Date] | ⏳ En cours |
| Rapport technique | [Date] | ⏳ À faire |
| Présentation finale | [Date] | ⏳ À faire |

---

## 📞 CONTACTS

**Étudiant** : Walid
**Email** : [À compléter]
**GitHub** : [À compléter]

**Encadrant** : [À compléter]
**Email** : [À compléter]

---

**Document créé le** : 05/03/2026
**Dernière mise à jour** : 05/03/2026
**Version** : 1.0
