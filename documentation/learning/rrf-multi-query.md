# Multi-query + RRF — l'essentiel

## Le problème

Un étudiant demande : *« Why does my model work on train but not on test? »*.
Son cours, lui, parle d'**overfitting**. Les mots ne correspondent pas, donc la recherche peut rater le bon passage.

## 1. Multi-query : poser la question plusieurs fois

Le LLM reformule la question avec d'autres mots :

```
1. Why does my model work on train but not on test?   (originale, toujours gardée)
2. What causes poor generalization to unseen data?
3. What is overfitting in machine learning?
4. How do models perform on training vs test sets?
```

Plus de formulations, donc plus de chances de tomber sur les bons mots du cours.

## 2. Recherche hybride : 2 recherches par formulation

Pour chaque formulation :
- une recherche **dense**, par le sens ;
- une recherche **BM25**, par les mots exacts.

4 formulations × 2 recherches = **8 classements** différents.

## 3. RRF : fusionner les 8 classements

**Reciprocal Rank Fusion** : chaque classement donne `1 / (60 + rang)` points à chaque chunk qu'il contient.

Exemple avec 2 classements :

| Chunk | Classement 1 | Classement 2 | Score RRF |
|---|---|---|---|
| A | 1er | absent | 1/61 = 0,0164 |
| **B** | 2e | 1er | 1/62 + 1/61 = **0,0325** |
| C | absent | 2e | 1/62 = 0,0161 |

**B gagne** : il est bien classé **partout**. Le RRF récompense l'accord entre les recherches.

Pourquoi utiliser les **rangs** et pas les scores ? Les scores dense (entre 0 et 1) et BM25 (entre 0 et 20 environ) ne sont pas sur la même échelle, alors qu'un rang est toujours comparable.

Pourquoi **60** ? C'est la valeur du papier d'origine (Cormack et al., 2009). Elle réduit l'écart entre le 1er et le 2e : un seul classement ne peut pas tout décider.

## 4. Le slider d'efficacité

| Niveau | Formulations | Résultats par classement | Chunks gardés après RRF |
|---|---|---|---|
| 1 Fast | 1 (aucun appel au LLM) | 10 | 20 |
| 2 Light | 3 | 10 | 25 |
| 3 Balanced (défaut) | 4 | 15 | 30 |
| 4 Deep | 6 | 20 | 40 |
| 5 Exhaustive | 8 | 25 | 50 |

**Règle** : plus le niveau est haut, plus on trouve de bons passages, mais plus c'est **lent** et **cher** (plus d'appels à OpenAI et à Qdrant).

Code : `backend/app/services/retrieval.py`, dictionnaire `LEVELS`.

## Alternatives

| Option | Pour | Contre |
|---|---|---|
| **RRF codé nous-mêmes** (choisi) | 10 lignes, on comprend tout, on fusionne autant de classements qu'on veut | – |
| RRF intégré à Qdrant (`Fusion.RRF`) | Une seule requête | Fusionne dense + BM25 pour UNE formulation, pas nos N formulations |
| Moyenne pondérée des scores | Simple | Il faut normaliser les échelles, c'est fragile |
| HyDE (le LLM écrit une fausse réponse, qu'on cherche ensuite) | Très bon sur les questions vagues | Un appel LLM plus long, et des hallucinations possibles |
