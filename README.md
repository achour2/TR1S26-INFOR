# TravelHub

TravelHub est une application Web Django de planification de voyages. Les données sont enregistrées dans PostgreSQL et manipulées avec l’ORM Django.

## Structure

- `travelhub` : tableau de bord et configuration centrale du projet.
- `compte` : profil de l’utilisateur connecté.
- `voyage` : création, consultation, modification, suppression, filtrage et tri des voyages.
- `destination` : gestion des destinations liées à un voyage.
- `activite` : consultation et gestion des activités liées à une destination.
- `travail1_ti` : paramètres et routes globales de Django.

Les modèles de domaine se trouvent actuellement dans `travelhub/models.py` : un voyage peut avoir plusieurs destinations, une destination plusieurs activités, et un voyage plusieurs participants (utilisateurs Django). Les contraintes du modèle protègent notamment l’ordre des dates et les coûts non négatifs. Les changements de schéma sont gérés par les migrations.

## Prérequis

- Python 3.13 ou plus récent
- PostgreSQL
- `uv` (recommandé) ou `pip`
- pgAdmin est facultatif; il peut servir à créer la base et à consulter les tables.

## Installation sous Windows / PowerShell

À la racine du projet :

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
uv sync
```

Pour installer avec pip plutôt qu’uv :

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Les versions et dépendances principales sont déclarées dans `pyproject.toml`, verrouillées dans `uv.lock` et également listées dans `requirements.txt`. Les stubs DRF sont optionnels pour le développement : `uv sync --extra dev`.

## PostgreSQL

Dans PostgreSQL ou pgAdmin, créez une base `travelhub` et un utilisateur PostgreSQL autorisé à s’y connecter. Configurez ensuite les variables d’environnement dans la session PowerShell avant de lancer Django :

```powershell
$env:DB_NAME = "travelhub"
$env:DB_USER = "traveluser"
$env:DB_PASSWORD = "votre-mot-de-passe-postgresql"
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DJANGO_SECRET_KEY = "remplacez-par-une-cle-secrete"
$env:DJANGO_DEBUG = "true"
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1"
```

Les paramètres PostgreSQL et Django peuvent ainsi être définis séparément pour chaque environnement. Ne réutilisez pas la clé de développement en production; désactivez `DJANGO_DEBUG` et définissez `DJANGO_ALLOWED_HOSTS` pour le serveur déployé.

## Initialiser et démarrer

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ouvrez `http://127.0.0.1:8000/`. La racine redirige vers le tableau de bord TravelHub; la connexion est requise pour accéder aux voyages et aux données associées.

Les migrations ajoutent ou font évoluer le schéma. Après récupération de changements qui comprennent une migration, exécutez `python manage.py migrate`.

## API REST, GraphQL et administration

Après `python manage.py migrate`, créez un compte administrateur avec `python manage.py createsuperuser`. Django Admin est disponible sur `/admin/` et permet de rechercher et filtrer les utilisateurs, voyages, destinations et activités, ainsi que de gérer les participants.

L'API REST versionnée est disponible sous `/api/v1/` : `voyages/`, `destinations/` et `activites/` prennent en charge les opérations CRUD. Les listes acceptent `search`, `ordering` et des filtres propres à chaque ressource. Les résultats sont paginés à 20 éléments. Les écritures sont réservées au créateur; les lectures sont limitées aux voyages dont l'utilisateur est participant. Les participants d'un voyage peuvent être consultés et gérés via `/api/v1/voyages/<id>/participants/` par son créateur.

Obtenez une paire de jetons JWT avec `POST /api/token/` et les champs `username` et `password`, puis envoyez `Authorization: Bearer <access>` aux endpoints protégés. Renouvelez un jeton avec `POST /api/token/refresh/`. La documentation Swagger interactive est disponible sur `/api/docs/` et le schéma OpenAPI sur `/api/schema/`.

GraphiQL est disponible sur `/graphql/`. L'interface peut être consultée sans connexion; les requêtes et mutations exigent un JWT, à saisir dans son éditeur d'en-têtes : `{"Authorization": "Bearer <access>"}`. Le schéma permet de consulter et manipuler les voyages, destinations et activités associés à l'utilisateur.

Configurez `CORS_ALLOWED_ORIGINS` en liste séparée par des virgules uniquement si un client web hébergé sur une autre origine doit appeler `/api/` ou `/graphql/`. Par défaut, aucune origine externe n'est autorisée.

## Services externes des destinations

La page de détail d'une destination interroge les services depuis Django. Open-Meteo géocode la ville et le pays, puis fournit les prévisions disponibles pour le séjour (conditions, températures, précipitations et vent). Le code pays retourné par le géocodage est ensuite utilisé dans une requête Countries GraphQL pour obtenir le nom du pays, sa capitale, son continent, sa monnaie et ses langues. Les valeurs calculées restent des informations d'enrichissement affichées à côté des données PostgreSQL.

Les services sont publics et ne nécessitent pas de clé pour cet usage. Si une destination n'est pas reconnue, si la période est en dehors de la fenêtre de prévision ou si un service est indisponible, la page affiche un message et conserve les informations locales du séjour.

## Vérification du compte par courriel

À l'inscription, le compte reste inactif jusqu'à la saisie du code reçu par courriel. Le code est à usage unique, expire après 10 minutes par défaut et est limité à cinq tentatives. Les modifications du profil, du mot de passe et la suppression du compte attendent également la confirmation du code envoyé à l'adresse concernée. En développement, Django affiche le message et son code dans le terminal. Le code n'est pas stocké en clair.

Sans configuration SMTP, Django affiche les codes dans le terminal pour le développement. Pour envoyer les courriels avec Gmail, copiez `.env.example` vers `.env`, remplacez les valeurs par celles de votre compte puis redémarrez le serveur :

```powershell
Copy-Item .env.example .env
```

Pour Gmail, `EMAIL_HOST_PASSWORD` doit être un mot de passe d'application Google, et non le mot de passe normal du compte. Le fichier `.env` est ignoré par Git : ne partagez pas son contenu. Redémarrez `runserver` après toute modification de ce fichier. Si un serveur SMTP est configuré sans identifiant ou mot de passe, Django signale l'erreur au démarrage au lieu d'afficher les codes dans le terminal.
