# Qdrant — l'essentiel

## C'est quoi ?

Une **base de données de vecteurs**. Une base SQL cherche « les lignes où `nom = 'Stevi'` ». Qdrant, lui, cherche « les textes **les plus proches** de ma question ».

## Le vocabulaire (comparé à SQL)

| Qdrant | Équivalent SQL | Dans My Notebook |
|---|---|---|
| **Collection** | Table | `my_notebook` |
| **Point** | Ligne | Un chunk |
| **Vecteur** | (pas d'équivalent) | Le texte du chunk transformé en nombres |
| **Payload** | Les colonnes | `text`, `filename`, `page`, `section`, `doc_id` |

## Nos 2 vecteurs par chunk

Chaque chunk est stocké avec **deux** vecteurs :

1. **`dense`** (OpenAI, 1536 nombres) : capture le **sens**.
   « voiture » est proche de « automobile », même sans mot en commun.
2. **`bm25`** (sparse = « creux ») : capture les **mots exacts**.
   Il est bon pour « LEFT JOIN », « L2 » ou un nom propre, là où le dense peut se tromper.

« Sparse » veut dire que le vecteur ne contient que les mots présents dans le texte : 5 valeurs au lieu de 1536. L'option **IDF** donne plus de poids aux mots rares (« regularization ») qu'aux mots courants (« the »).

Combiner les deux s'appelle la **recherche hybride**. On fusionnera leurs résultats avec le RRF au ticket MNB-7.

## Le code (`backend/app/services/vector_store.py`)

```python
create_collection_if_missing(client)   # crée la "table" avec ses 2 vecteurs
index_chunks(client, chunks)           # calcule les vecteurs et enregistre (upsert)
delete_document_chunks(client, doc_id) # supprime les chunks d'un document
```

**Upsert** = insert **ou** update. Comme l'id d'un chunk est toujours le même pour un document donné, réindexer **remplace** l'ancien chunk au lieu de créer un doublon.

## Lancer et explorer

```bash
make qdrant-up                       # démarre Qdrant dans Docker
# puis ouvrir http://localhost:6333/dashboard
```

Le dashboard permet de voir la collection, les points et leurs payloads.

Dans les tests, on utilise `QdrantClient(":memory:")` : un vrai Qdrant, mais en mémoire et sans Docker.

## Pourquoi Qdrant et pas un autre ?

| Option | Pour | Contre |
|---|---|---|
| **Qdrant** (choisi) | Dense + sparse dans le même outil, dashboard, version cloud gratuite | Un service de plus à lancer |
| ChromaDB | Très simple | Pas de BM25 intégré |
| pgvector (PostgreSQL) | Tout dans une seule base | Plus de SQL à écrire pour l'hybride |
| FAISS | Ultra rapide | Simple librairie : pas de payload, pas de serveur |
