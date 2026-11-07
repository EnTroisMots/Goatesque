# 🔥 PyroSentinel - Système de Surveillance Incendie & Cartographie Tactique

PyroSentinel est une solution complète de surveillance d'incendies en temps réel et de rejouage historique. Le système combine un backend Python FastAPI, une base de données SQLite pour l'archivage, des communications WebSockets pour la diffusion des alertes immédiates, et des interfaces frontend interactives basées sur Leaflet.js et Tailwind CSS.

---

## 🚀 Guide d'Installation et de Démarrage Rapide

### 1. Installation des dépendances

Ouvrez un terminal à la racine du projet et exécutez la commande suivante :

```bash
pip install fastapi uvicorn
```

---

### 2. Lancement du serveur Backend

Démarrez le serveur FastAPI avec la commande :

```bash
uvicorn main:app --reload
```

> **Note :** Le serveur démarrera sur `http://127.0.0.1:8000`. La base de données SQLite (`pyrosentinel.db`) sera automatiquement créée au premier lancement.

---

### 3. Tester l'API avec Swagger UI

Ouvrez votre navigateur web à l'adresse [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) : vous y découvrirez une page interactive où vous pourrez tester l'envoi de fausses mesures et voir votre base de données SQLite se remplir en direct !

---

### 4. Lancer le simulateur de données (Optionnel, ça sert pas a grand chose mis a par pour faire des copier coller de test et les mettre dans Swagger UI)

Pour générer et envoyer automatiquement des données de test (balises et alertes) au backend, ouvrez un deuxième terminal et lancez :

```bash
python simulateur.py
```

---

### 5. Comment lancer le site (Frontend)

Aucune configuration complexe n'est requise pour ouvrir les interfaces graphiques :

1. **Tableau de bord en Temps Réel (`index.html`) :**
   * Double-cliquez simplement sur le fichier `index.html` pour l'ouvrir dans votre navigateur web (Chrome, Firefox, Edge, etc.).
   * Vous y verrez la carte en temps réel avec la dernière position connue de vos balises et le flux d'alertes WebSocket.

2. **Interface Historique & Rembobinage (`history.html`) :**
   * Double-cliquez sur `history.html` (ou cliquez sur le bouton **📜 Historique** depuis la page principale).
   * Vous accéderez à la carte plein écran avec filtres par date/heure et le tableau escamotable.

> 💡 *Astuce : Si vous préférez passer par un serveur web local pour ouvrir vos pages HTML, lancez `python -m http.server 8080` dans votre terminal et ouvrez `http://localhost:8080/index.html`.*

---

## 📂 Structure des fichiers

```text
📂 PyroSentinel/
│
├── 📄 main.py            # Backend FastAPI (API REST, WebSockets, gestion SQLite)
├── 📄 simulateur.py      # Générateur/simulateur de données de balises
├── 📄 index.html         # Dashboard en temps réel (Carte active & flux d'alertes)
├── 📄 history.html       # Interface d'historique (Time Machine, carte plein écran, filtres)
└── 📄 README.md          # Documentation du projet
```