"""API HTTP pour le frontend Vite : expose RAGAgent via FastAPI.

	uvicorn api:app --reload --port 8000

RAGAgent est instancié une seule fois au démarrage (le modèle d'embedding et
la base ChromaDB sont coûteux à charger) et réutilisé pour chaque requête.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_agent import RAGAgent

app = FastAPI(title="Mon premier RAG - API")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173"],
	allow_methods=["*"],
	allow_headers=["*"],
)

rag = RAGAgent()


class Question(BaseModel):
	question: str


@app.get("/health")
def health():
	return {"status": "ok", "chunks_indexes": rag.db.count()}


@app.post("/ask")
def ask(payload: Question):
	return rag.answer_question(payload.question)
