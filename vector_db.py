import chromadb
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, CHROMA_PATH, COLLECTION_NAME, N_RESULTS


class VectorDB:
	def __init__(self, persist_path=CHROMA_PATH, collection_name=COLLECTION_NAME,
			chunks=None, embedding_model_name=EMBEDDING_MODEL):
		self.persist_path = persist_path
		self.collection_name = collection_name
		self.client = chromadb.PersistentClient(path=persist_path)

		existing = [
			c.name if hasattr(c, "name") else c
			for c in self.client.list_collections()
		]

		if collection_name in existing:
			self._load(collection_name)
		elif chunks:
			self._create(collection_name, chunks, embedding_model_name)
		else:
			raise ValueError(
				f"Collection « {collection_name} » absente et aucun chunk fourni."
			)

	def _create(self, collection_name, chunks, embedding_model_name):
		self.embedding_model_name = embedding_model_name
		self.model = SentenceTransformer(embedding_model_name)

		# on stocke le modèle d'embedding dans les métadonnées pour le relire au rechargement
		self.collection = self.client.create_collection(
			name=collection_name,
			metadata={
				"embedding_model": embedding_model_name,
				"hnsw:space": "cosine",
			},
		)

		texts = [c["text"] for c in chunks]
		self.collection.add(
			ids=[c["id"] for c in chunks],
			documents=texts,
			embeddings=self._encode(texts),
			metadatas=[
				{"source": c.get("source", "inconnue"),
					"categorie": c.get("categorie", "inconnue")}
				for c in chunks
			],
		)

	def _load(self, collection_name):
		self.collection = self.client.get_collection(collection_name)
		meta = self.collection.metadata or {}
		self.embedding_model_name = meta.get("embedding_model", EMBEDDING_MODEL)
		self.model = SentenceTransformer(self.embedding_model_name)

	def _encode(self, texts):
		vectors = self.model.encode(
			list(texts),
			batch_size=32,
			normalize_embeddings=True,
			show_progress_bar=False,
		)
		return vectors.tolist()

	def retrieve(self, question, n=N_RESULTS):
		result = self.collection.query(
			query_embeddings=self._encode([question]),
			n_results=n,
		)
		return [
			{
				"id": _id,
				"text": doc,
				"source": meta.get("source"),
				"categorie": meta.get("categorie"),
				"distance": dist,
			}
			for _id, doc, meta, dist in zip(
				result["ids"][0],
				result["documents"][0],
				result["metadatas"][0],
				result["distances"][0],
			)
		]

	def count(self):
		return self.collection.count()
