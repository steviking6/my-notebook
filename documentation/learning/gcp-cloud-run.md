# GCP Cloud Run — l'essentiel

## L'idée

Cloud Run fait tourner **une image Docker** derrière une URL HTTPS. Pas de serveur à gérer :
- 0 requête → 0 instance → **0 €** (*scale to zero*) ;
- beaucoup de requêtes → Cloud Run lance plus d'instances (on plafonne à 2).

Inconvénient : le **cold start**. La première requête après une pause attend que l'instance démarre (quelques secondes, plus si l'image est grosse).

## Les briques utilisées

| Brique GCP | Rôle | Dans notre projet |
|---|---|---|
| **Cloud Build** | Construit l'image Docker dans le cloud | `gcloud builds submit backend` |
| **Artifact Registry** | Stocke les images (le « Docker Hub » privé) | dépôt `my-notebook` |
| **Cloud Run** | Fait tourner les images | `my-notebook-backend`, `my-notebook-frontend` |
| **Secret Manager** | Stocke les secrets, injectés en variables d'env | clés OpenAI, Qdrant, `app-api-key` |
| **Cloud Storage (GCS)** | Stocke les fichiers uploadés | bucket monté comme un dossier `/mnt/uploads` |
| **Service accounts** | L'« identité » de chaque service, avec le minimum de droits | le front ne peut lire que `app-api-key` |

Qdrant n'est pas sur GCP : on utilise **Qdrant Cloud** (offre gratuite, 1 Go).

## Pourquoi monter le bucket comme un dossier ?

Le disque d'une instance Cloud Run est **effacé** à chaque redémarrage. Les uploads doivent donc vivre ailleurs.

| Option | Pour | Contre |
|---|---|---|
| **Bucket monté (Cloud Storage FUSE)** (choisi) | Zéro code : notre `LocalStorage` écrit dans `/mnt/uploads` comme en local | Plus lent qu'un vrai disque (OK pour quelques fichiers) |
| Client `google-cloud-storage` dans le code | Contrôle fin | Une 2e implémentation du stockage à écrire et tester |
| Base de données pour les métadonnées | Requêtes, concurrence | Surdimensionné pour le MVP |

## Sécurité : qui peut dépenser nos crédits OpenAI ?

```
navigateur ──> front (public) ──/api + X-API-Key──> backend (public, mais protégé par la clé)
```

- La clé `APP_API_KEY` n'existe que côté serveur (proxy Next.js) : elle n'est **jamais** envoyée au navigateur.
- Limite : quiconque ouvre le front peut poser des questions. Pour le MVP, on plafonne :
  `--max-instances 2` + **budget mensuel dans le dashboard OpenAI** + alerte de budget GCP.
- Vraie solution (v2) : authentification des utilisateurs.

## Déployer

```bash
# une fois
gcloud auth login
export PROJECT_ID=... QDRANT_URL=... OPENAI_API_KEY=... QDRANT_API_KEY=...
./deploy/setup.sh

# à chaque version
./deploy/deploy.sh
```

## Alternatives

| Option | Pour | Contre |
|---|---|---|
| **Cloud Run** (choisi) | Serverless, scale to zero, juste une image Docker | Cold start |
| Vercel (front) + Cloud Run (back) | Vercel est fait pour Next.js | Deux plateformes à gérer |
| GKE (Kubernetes) | Contrôle total | Beaucoup trop complexe et cher pour ce projet |
| Une VM (Compute Engine) | Simple à comprendre | Payante 24h/24, mises à jour à gérer soi-même |
