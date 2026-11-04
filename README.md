# Anonymia (Projet info 2A, ENSAI, équipe 21)

Application de caviardage de données personnelles dans des documents administratifs.
Deux détecteurs travaillent en parallèle : des expressions régulières pour les formats fixes
(NIR, IBAN, e-mail, téléphone...) et un LLM pour les formats libres (noms, adresses, lieux...).
L'API est écrite avec FastAPI, l'interface avec Streamlit.

## Prérequis

- un service VS Code Python sur Onyxia (SSPCloud), avec ce dépôt cloné dans `~/work` ;
- un service PostgreSQL lancé sur Onyxia ;
- une clé personnelle pour l'API LLM de SSPCloud.

## Configuration

Copier le modèle de configuration, puis le compléter :

```bash
cp .env.example .env
```

Le fichier `.env` (jamais versionné) doit contenir :

| Variable | Valeur |
|---|---|
| `LLM_BASE_URL` | `https://llm.lab.sspcloud.fr/api` |
| `SSPCLOUD_API_KEY` | votre clé personnelle |
| `LLM_MODEL` | `gemma4-26b-moe` |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | voir le README du service PostgreSQL sur Onyxia |
| `POSTGRES_SCHEMA` | un nom au choix, par exemple `anonymia` |

## Installation

Depuis la racine du dépôt :

```bash
uv sync --project backend --all-extras
```

## Lancer l'API

```bash
uv run --project backend uvicorn main:app --app-dir backend/src --port 5000 --root-path /proxy/5000
```

L'option `--root-path /proxy/5000` est nécessaire sur Onyxia : sans elle, la page de documentation
ne se charge pas (« Failed to load API definition »).

La documentation interactive est ensuite accessible depuis l'onglet **Ports** de VS Code (port 5000),
en ajoutant `/docs` à l'adresse. À la première utilisation, appeler `GET /reset_database`
pour créer les tables et les comptes de test.

## Lancer l'interface

Dans un second terminal, l'API tournant toujours dans le premier :

```bash
cd frontend
uv run --project ../backend streamlit run app.py --server.port 8501
```

L'interface est accessible depuis l'onglet **Ports** de VS Code (port 8501).

## Comptes de test

| E-mail | Mot de passe | Rôle |
|---|---|---|
| `a@a.com` | `a` | Utilisateur |
| `b@b.com` | à demander au groupe | Administrateur |

## Lancer les tests

```bash
uv run --project backend pytest backend/tests -v
```

## Avertissement

Aucun détecteur n'a un rappel de 100 % : des données personnelles peuvent ne pas être détectées.
Une relecture humaine reste obligatoire avant toute diffusion d'un document caviardé.