# GL3E Project Assignment System

Système d'attribution aléatoire de projets Java EE pour la classe GL3E de l'Institut Africain d'Informatique.

## Fonctionnalités

- ✅ Attribution aléatoire de 70 projets à 83 étudiants
- ✅ Vérification OTP par email (SMTP) ou SMS (mTarget + Twilio fallback)
- ✅ Validation téléphone camerounais uniquement
- ✅ Dashboard administrateur avec statistiques
- ✅ Logs d'activité détaillés
- ✅ Export PDF des attributions
- ✅ Page publique de consultation des projets attribués
- ✅ Interface mobile-first avec animations
- ✅ Déploiement avec SSL (Nginx + Certbot)

## Installation

### Prérequis

- Python 3.10+
- pip
- virtualenv (recommandé)

### Étapes d'installation

1. **Cloner ou télécharger le projet**

```bash
cd /Users/tech/.gemini/antigravity/scratch/gl3e-project-assignment
```

2. **Créer un environnement virtuel**

```bash
python3 -m venv venv
source venv/bin/activate  # Sur macOS/Linux
# ou
venv\Scripts\activate  # Sur Windows
```

3. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

4. **Configurer les variables d'environnement**

Le fichier `.env` est déjà configuré avec les credentials fournis. Vérifiez et modifiez si nécessaire.

5. **Initialiser la base de données**

```bash
python init_db.py
```

Cela va créer la base de données SQLite et charger:
- 83 étudiants GL3E
- 70 projets Java EE
- Utilisateur admin (username: admin, password: admin123)

6. **Lancer l'application**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **Accéder à l'application**

- Interface étudiant: http://localhost:8000
- Dashboard admin: http://localhost:8000/admin
- API Documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Utilisation

### Pour les étudiants

1. Aller sur la page d'accueil
2. Sélectionner votre nom dans la liste
3. Entrer votre email OU numéro de téléphone camerounais
4. Cliquer sur "Me donner un thème"
5. Recevoir le code OTP par email ou SMS
6. Entrer le code OTP
7. Recevoir votre projet attribué

### Pour l'administrateur

1. Aller sur http://localhost:8000/admin
2. Se connecter (admin / admin123)
3. Consulter le dashboard avec:
   - Statistiques globales
   - Liste des attributions
   - Barre de recherche
   - Logs d'activité
4. Exporter en PDF si nécessaire

## Déploiement en Production

### 1. Préparer le serveur

```bash
# Copier le projet sur le serveur
scp -r gl3e-project-assignment user@stephanezoa.online:/var/www/

# Se connecter au serveur
ssh user@stephanezoa.online
cd /var/www/gl3e-project-assignment
```

### 2. Installer les dépendances

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
```

### 3. Configurer systemd

```bash
sudo cp deploy/gl3e-assignment.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gl3e-assignment
sudo systemctl start gl3e-assignment
sudo systemctl status gl3e-assignment
```

### 4. Configurer Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/stephanezoa.online
sudo ln -s /etc/nginx/sites-available/stephanezoa.online /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Installer SSL avec Certbot

```bash
sudo certbot --nginx -d stephanezoa.online -d www.stephanezoa.online
```

## Structure du Projet

```
gl3e-project-assignment/
├── app/
│   ├── models/          # Modèles SQLAlchemy
│   ├── services/        # Services (email, SMS, OTP, etc.)
│   ├── routers/         # Routes API
│   ├── utils/           # Utilitaires
│   ├── config.py        # Configuration
│   ├── database.py      # Setup base de données
│   └── main.py          # Application FastAPI
├── static/              # Fichiers statiques (CSS, JS, images)
├── templates/           # Templates HTML
├── deploy/              # Fichiers de déploiement
├── init_db.py           # Script d'initialisation
├── requirements.txt     # Dépendances Python
└── .env                 # Variables d'environnement
```

## Technologies Utilisées

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Email**: aiosmtplib (SMTP)
- **SMS**: mTarget API (primary), Twilio (fallback)
- **PDF**: ReportLab
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Déploiement**: systemd, Nginx, Certbot

## Support

Pour toute question ou problème, contactez l'administration GL3E.

## Licence

© 2024 Institut Africain d'Informatique - GL3E
