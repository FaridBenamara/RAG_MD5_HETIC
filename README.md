# Mon premier RAG — M2 MD5

Un RAG minimal mais complet, en POO :
**ChromaDB** (base vectorielle) + **sentence-transformers** (embeddings) +
**Groq** (LLM) + **agent modérateur** (anti prompt-injection).

Base de connaissances : un corpus de 200 faits absurdes (`data/05_corpus_rag.csv`)
sur le village imaginaire de *Villebrume-les-Cuillères*. Ces faits n'existent nulle
part : si le système répond juste, c'est forcément grâce au *retrieval*, pas à la
mémoire du modèle.

---

## Démarrage

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate   |   macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # puis collez votre clé Groq (console.groq.com) dans .env

python main.py              # indexation (1re fois) + tests de la section 6
python main.py --retrieve   # seulement la récupération, sans clé API
python compare_embeddings.py  # « aller plus loin » : comparaison de 2 embeddings
```

---

## Architecture (POO)

```
config.py               constantes (modèles, chemins) — un seul endroit
agent.py                Agent          : classe de base, détient le client Groq + read_file
moderator_agent.py      ModeratorAgent(Agent)   Brique 2 — détection de prompt injection
rag_agent.py            RAGAgent(Agent)         Brique 3 — orchestration du pipeline
vector_db.py            VectorDB                Brique 1 — ChromaDB persistée
corpus_loader.py        CorpusLoader            lecture du CSV
compare_embeddings.py   EmbeddingComparison     bonus « aller plus loin »
main.py                 démonstration de bout en bout
prompts/                prompts système (retravaillables sans toucher au code)
data/05_corpus_rag.csv  corpus : id, text, source, categorie
```

Un **`Agent`** de base porte le client Groq et `read_file` ; les agents
spécialisés en héritent. `VectorDB` et `CorpusLoader` ne sont pas des agents LLM :
`RAGAgent` les **compose** (composition plutôt qu'héritage).

---

## Choix des modèles (`config.py`)

| Rôle | Modèle | Pourquoi |
|---|---|---|
| Embedding | `distiluse-base-multilingual-cased-v2` | multilingue, léger, corpus FR |
| LLM | `llama-3.3-70b-versatile` | production Groq, multilingue, mode JSON |
| Modérateur | `openai/gpt-oss-safeguard-20b` | famille *safeguard*, suit une politique + sortie JSON |

> Note : l'ancien modérateur `meta-llama/llama-guard-4-12b` a été arrêté par Groq
> le 05/03/2026 → on utilise son successeur `gpt-oss-safeguard-20b`. Repli JSON
> universel si besoin : `llama-3.1-8b-instant`.

**Détail malin :** le nom du modèle d'embedding est **gravé dans les métadonnées de
la collection**. Au rechargement, `VectorDB` relit ce nom-là et charge CE modèle —
pas celui, peut-être différent, de la config du jour. Bug évité : encoder la base
avec un modèle et interroger avec un autre → des vecteurs incomparables et un
*retrieval* silencieusement faux, très dur à diagnostiquer.

---

## Les 3 briques

1. **`VectorDB`** — s'aiguille dans son constructeur : recharge la base si elle
   existe, la crée si on fournit des chunks, refuse sinon. Encode avec
   normalisation (similarité cosinus), retrouve les k plus proches voisins.
2. **`ModeratorAgent`** — avant tout, demande à un modèle de sécurité si la
   question est une injection, et renvoie `{"is_prompt_injection": bool, "reason": ...}`.
3. **`RAGAgent`** — pipeline : **modération d'abord** (sécurité), puis récupération
   des 3 chunks, remplissage du prompt à trous `{{Chunks}}`, appel LLM.

---

## Réponses aux questions du TP (section 6)

1. **Qui intercepte l'entrée piégée, et quand ?** Le `ModeratorAgent`, **en tout
   premier**, avant toute récupération ou appel au LLM principal
   (`RAGAgent.answer_question`, étape 1). Si injection → refus immédiat, le LLM
   principal n'est jamais contacté.
2. **Sans modérateur ?** Testé au cas `[5]` de `main.py` (`use_moderator=False`) :
   l'instruction « oublie ton contexte » atteint directement le LLM générateur et
   peut détourner sa réponse. Le modérateur est la garde à l'entrée.
3. **Hors corpus (« capitale du Japon ») ?** La règle 3 du prompt impose de dire
   qu'on ne sait pas. Pour durcir : baisser la température, insister « si l'info
   n'est pas dans les extraits, réponds exactement : je ne sais pas », et utiliser
   le **seuil de distance** ci-dessous.
4. **Affirmation fausse (« le chat d'Henri est vert ? »)** La règle 4 impose de
   signaler la contradiction ; le corpus contient `chunk_022` (« n'a jamais été
   vert : il est et a toujours été bleu »), ce qui déclenche le comportement.

**Pourquoi un modèle dédié plutôt qu'une consigne dans le prompt du RAG ?** Le RAG
voit la question dans le même message que ses instructions : une injection peut les
détourner. Le modérateur ne fait *que* classer, avec son propre prompt : rien à
détourner. Séparation des responsabilités.

---

## Pour aller plus loin (implémenté)

- **Vrai corpus** : 200 chunks (`data/05_corpus_rag.csv`) avec `source` et `categorie`.
- **Sources + scores** : chaque réponse liste ses chunks (id + distance) ; le prompt
  système reçoit aussi source, catégorie et distance par extrait.
- **Seuil de distance** (`DISTANCE_THRESHOLD = 0.6`) : si le meilleur chunk dépasse
  le seuil, `RAGAgent` ajoute un avertissement.
  **Calibrage :** lancez `python main.py --retrieve` et regardez la distance du
  meilleur chunk pour des questions *dans* le corpus (typiquement basse) vs *hors*
  corpus (plus haute) ; placez le seuil entre les deux nuages. Distance cosinus :
  0 = identique, 2 = opposé.
- **Comparaison d'embeddings** : `compare_embeddings.py` indexe le corpus avec deux
  modèles, pose les 5 questions et affiche un score `hit@3`.

---

## Workflow git

| Branche | Rôle | Règle |
|---|---|---|
| `main` | version stable, démontrable | jamais de commit direct ; ne reçoit que des **merges depuis `dev`**, **taggés** (`v0.1.0`…) |
| `dev` | intégration | pas de commit direct ; reçoit les `feature/*` par **PR** |
| `feature/*` | une fonctionnalité | créée depuis `dev`, commits petits, supprimée après merge |

Seule exception : le **commit racine** (vide) sur `main` — un dépôt a besoin d'une
racine. Ensuite `main` est gelée.
