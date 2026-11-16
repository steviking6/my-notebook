# Docker — l'essentiel pour My Notebook

> Objectif : comprendre juste assez de Docker pour lancer Qdrant en local, puis déployer notre API sur Cloud Run vendredi.

## 1. Le problème que Docker résout

« Chez moi ça marche » : ton code dépend d'une version de Python, de librairies système, de variables d'env… Sur une autre machine (ou sur GCP), rien ne garantit que ce soit pareil.

Docker emballe **l'application + tout son environnement** dans une boîte standard qui tourne pareil partout.

## 2. Les 4 concepts à retenir

| Concept | Analogie | Dans notre projet |
|---|---|---|
| **Image** | La recette (figée, versionnée) | `qdrant/qdrant:v1.20.0`, plus tard `my-notebook-backend:0.1.0` |
| **Conteneur** | Le plat cuisiné à partir de la recette (une instance qui tourne) | Le Qdrant qui tourne sur ton PC |
| **Dockerfile** | Le texte de la recette, qu'on écrit soi-même | `backend/Dockerfile` (vendredi) |
| **Registry** | Le livre de recettes partagé en ligne | Docker Hub (où on récupère Qdrant), Artifact Registry sur GCP (où on poussera notre image) |

Une image donne autant de conteneurs que tu veux. Un conteneur est **jetable** : si tu le supprimes, ce qu'il contenait disparaît… sauf ce qui est stocké dans un **volume**.

## 3. Ports et volumes

- **Port** : le conteneur est isolé. `-p 6333:6333` signifie « le port 6333 de mon PC renvoie vers le port 6333 du conteneur ». C'est ce qui te permet d'ouvrir `http://localhost:6333/dashboard`.
- **Volume** : un dossier persistant géré par Docker, branché dans le conteneur. Sans volume, tes vecteurs seraient perdus à chaque redémarrage de Qdrant.

## 4. Docker Compose

Au lieu de taper de longues commandes `docker run ...`, on décrit les services dans `docker-compose.yml` :

```yaml
services:
  qdrant:
    image: qdrant/qdrant:v1.20.0   # quelle recette
    ports: ["6333:6333"]           # quel port exposer
    volumes:
      - qdrant_storage:/qdrant/storage   # où persister les données
```

Commandes utiles :

```bash
docker compose up -d        # démarre les services en arrière-plan (-d = detached)
docker compose ps           # liste ce qui tourne
docker compose logs -f qdrant   # suit les logs
docker compose down         # arrête et supprime les conteneurs (le volume reste)
docker compose down -v      # idem + supprime les volumes (repart de zéro)
```

Raccourcis du projet : `make qdrant-up` et `make qdrant-down`.

## 5. Installation (Windows + WSL2)

1. Installer **Docker Desktop** : https://www.docker.com/products/docker-desktop/
2. Dans Docker Desktop : *Settings → Resources → WSL Integration* → activer ta distro Ubuntu.
3. Redémarrer le terminal WSL, puis vérifier :
   ```bash
   docker --version
   docker run hello-world
   ```

## 6. Pourquoi Docker et pas autre chose ?

| Option | Pour | Contre |
|---|---|---|
| **Docker** (choisi) | Standard de l'industrie, exigé par Cloud Run, énorme écosystème | Docker Desktop est un peu lourd sous Windows |
| Podman | Compatible avec Docker, sans démon, open source | Moins de docs, intégration Windows moins fluide |
| Installer Qdrant « à la main » | Pas de couche en plus | Pas reproductible, et différent de la prod |
| Qdrant Cloud dès le dev | Zéro installation | Dépend d'Internet, et données de dev dans le cloud |

## 7. À venir

- **Dockerfile** du backend : couches, cache, multi-stage build, `.dockerignore`.
- **Push vers Artifact Registry**, puis Cloud Run qui exécute l'image.
