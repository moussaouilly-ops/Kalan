# Plateforme e-learning — Fondation backend (Django + DRF)

Squelette backend d'une plateforme d'apprentissage en ligne inspirée d'Udemy,
adaptée au contexte ouest-africain (paiement mobile money, FCFA, français).

## Structure du projet

```
edutech/
├── config/          # Réglages Django, urls racine, wsgi/asgi
├── accounts/        # Utilisateurs (étudiant/formateur/admin), auth, vérification e-mail
├── courses/         # Catégories, cours, chapitres, leçons, inscriptions, progression, notes
├── payments/        # Paiements mobile money (Orange/Moov/Wave/Coris), abonnements, reversements
├── quizzes/         # Quiz, questions, tentatives, correction auto, certificats
├── reviews/         # Avis et commentaires notés sur les cours
├── messaging/       # Messagerie étudiant ↔ formateur
├── affiliates/      # Système d'affiliation (liens, clics, commissions)
├── core/            # Fonctions transverses (recherche, utilitaires)
├── requirements.txt
└── .env.example
```

## Ce qui est fait dans cette étape

- **Modèles de données complets** pour les 10 fonctionnalités demandées (16 apps
  Django, ~35 modèles), avec UUID comme clé primaire, index sur les champs de
  filtrage fréquents, et contraintes d'unicité cohérentes (ex: un seul avis par
  étudiant et par cours).
- **Utilisateur personnalisé** (`accounts.User`) : connexion par e-mail, 3 rôles
  (étudiant / formateur / administrateur), profil formateur séparé.
- **Configuration Django** prête pour la production : PostgreSQL, DRF avec
  authentification JWT (SimpleJWT + blacklist des tokens), CORS, pagination,
  throttling, i18n en français, fuseau horaire Afrique/Ouagadougou.
- **Django Admin** enregistré pour toutes les apps — utilisable immédiatement
  pour créer des catégories, valider des cours, gérer les paiements, etc.
- **Migrations générées et validées** (`makemigrations` s'exécute sans erreur).
- Emplacement des URLs (`urls.py`) posé pour chaque app, prêt à recevoir les
  vues DRF à l'étape suivante.

## Ce qui reste à construire (prochaines étapes suggérées)

1. **Sérialiseurs + ViewSets DRF** pour accounts, courses, payments... (CRUD complet)
2. **Endpoints d'authentification** : inscription, connexion, refresh JWT,
   réinitialisation de mot de passe par e-mail
3. **Intégration réelle des paiements mobile money** : chaque opérateur a sa
   propre API (webhooks de confirmation, formats de requête différents) — à
   implémenter un par un, en sandbox avant la production
4. **Recherche avancée** : PostgreSQL full-text search ou moteur dédié (Meilisearch/Elasticsearch)
5. **Stockage cloud des vidéos** (S3-compatible) + transcodage (ex: via une file
   de tâches Celery pour compresser/générer les miniatures)
6. **Frontend** React (ou Flutter) consommant l'API REST
7. **Tests automatisés** (pytest-django) sur les modèles et endpoints critiques

## Démarrage local

```bash
cp .env.example .env          # renseigner les valeurs
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

L'administration est accessible sur `/admin/`.
