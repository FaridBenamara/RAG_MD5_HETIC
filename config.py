from pathlib import Path

ROOT = Path(__file__).resolve().parent

EMBEDDING_MODEL = "distiluse-base-multilingual-cased-v2"
LLM_MODEL = "llama-3.3-70b-versatile"
# successeur de llama-guard-4-12b (arrêté par Groq le 05/03/2026)
MODERATOR_MODEL = "openai/gpt-oss-safeguard-20b"

CHROMA_PATH = str(ROOT / "chroma_db")
COLLECTION_NAME = "corpus_absurde"
N_RESULTS = 3
DISTANCE_THRESHOLD = 0.6

CORPUS_PATH = str(ROOT / "data" / "05_corpus_rag.csv")
MODERATOR_PROMPT_SYSTEM = str(ROOT / "prompts" / "moderator_prompt_system.txt")
RAG_PROMPT_SYSTEM = str(ROOT / "prompts" / "rag_prompt_system.txt")
