# Production Checklist - GL3E Manager

## 1) Variables .env obligatoires
- `DEBUG=false`
- `SECRET_KEY` fort (long, aléatoire)
- `DATABASE_URL` pointe vers la vraie base prod
- `CORS_ORIGINS` liste exacte des domaines frontend (ex: `https://stephanezoa.online`)
- `ALLOWED_HOSTS` liste exacte des hosts (ex: `stephanezoa.online,www.stephanezoa.online`)
- `FORCE_SECURE_COOKIES=true` (HTTPS obligatoire)
- SMTP/SMS/Twilio/mTarget correctement renseignés

## 2) Commande de démarrage recommandée
- Installer dépendances: `pip install -r requirements.txt`
- Lancer avec workers: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`

## 3) Reverse proxy (Nginx/Caddy)
- Activer HTTPS (certificat valide)
- Redirection HTTP -> HTTPS
- `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`
- `proxy_set_header X-Forwarded-Proto https;`

## 4) Sécurité applicative
- CORS restreint (pas `*` en prod)
- Cookies admin `Secure` + `HttpOnly`
- `ALLOWED_HOSTS` restreint
- Rotation des logs active (`logs/`)

## 5) Vérifications avant go-live
- Test complet flow étudiant (OTP email + OTP SMS)
- Test export PDF étudiant/admin et ZIP global
- Vérifier création de logs:
  - `logs/endpoints/*.log`
  - `logs/errors/app_errors.log`
  - `logs/services/*.log`
- Vérifier santé: `GET /health`

## 6) Post-déploiement
- Mettre un superviseur (systemd/supervisor)
- Mettre sauvegarde DB quotidienne
- Monitorer erreurs SMTP/SMS et latence endpoints
