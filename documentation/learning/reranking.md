# Reranking — l'essentiel

## Le problème

Après le RRF, on a ~30 candidats. Il n'y en a qu'une partie de vraiment utiles, et on ne veut donner au LLM que les ~6 meilleurs : moins de bruit, moins de tokens, une meilleure réponse.

Or la recherche (dense + BM25) compare la question et chaque chunk **séparément** : deux vecteurs, une distance. Elle est rapide, mais approximative.

## L'idée : un juge qui lit les deux ensemble

| | Bi-encoder (la recherche) | Cross-encoder (le reranker) |
|---|---|---|
| Entrée | question → vecteur, chunk → vecteur | `[question + chunk]` lus **ensemble** |
| Vitesse | Très rapide (les vecteurs des chunks sont pré-calculés) | Lent : un passage du modèle par chunk |
| Précision | Moyenne | Bonne : le modèle voit si le chunk **répond** vraiment |
| Usage | Fouiller toute la collection | Re-trier ~30 candidats |

D'où le pipeline en entonnoir : **chercher large** (recherche + RRF), puis **trier fin** (reranker).

## Nos deux rerankers

| Niveau | Reranker | Comment |
|---|---|---|
| 1 à 4 | **FlashRank** (`ms-marco-MiniLM-L-12-v2`) | Petit cross-encoder ONNX, sur CPU, gratuit, ~100 ms. Téléchargé une fois dans `data/models/` |
| 5 | **LLM OpenAI** | Un seul appel : « voici 50 passages numérotés, rends les numéros des 10 meilleurs », en JSON |

On reranke avec la question **originale** : les reformulations ont seulement servi à chercher.

On ne fait pas confiance aveuglément au LLM : `pick()` ignore les numéros invalides et les doublons, et complète dans l'ordre du RRF s'il en rend trop peu.

Code : `backend/app/services/reranking.py`.

## Alternatives

| Option | Pour | Contre |
|---|---|---|
| **FlashRank** (choisi) | Gratuit, local, rapide, pas de clé API | Modèle entraîné sur de l'anglais (MS MARCO) |
| Cohere Rerank / Voyage / Jina (API) | Très bons, multilingues | Payant, une API et une clé de plus |
| `bge-reranker` via sentence-transformers | Meilleur que MiniLM | Utilise torch : image Docker plus lourde, plus lent sur CPU |
| **LLM comme juge** (niveau 5) | Comprend les questions subtiles | Lent, payant, sortie à valider |
| Pas de reranking | Simple | On envoie plus de bruit au LLM |
