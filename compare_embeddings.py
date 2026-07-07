from corpus_loader import CorpusLoader
from vector_db import VectorDB


class EmbeddingComparison:
	QUESTIONS = [
		{"q": "Comment s'appelle le chat bleu de Bob ?", "attendu": ["chunk_001", "chunk_200"]},
		{"q": "De quelle couleur est le chat d'Henri ?", "attendu": ["chunk_001", "chunk_022"]},
		{"q": "Qui est le maire de Villebrume ?", "attendu": ["chunk_078", "chunk_079"]},
		{"q": "Combien d'habitants compte Villebrume-les-Cuillères ?", "attendu": ["chunk_161"]},
		{"q": "Que fait un plieur de brume ?", "attendu": ["chunk_058", "chunk_066"]},
	]

	def __init__(self, models, n=3):
		self.models = models
		self.n = n
		self.chunks = CorpusLoader().load()
		self.dbs = {}

	@staticmethod
	def _slug(model_name):
		return "cmp_" + model_name.replace("/", "_").replace("-", "_")

	def _build(self):
		for model in self.models:
			print(f"[index] {model}")
			self.dbs[model] = VectorDB(
				collection_name=self._slug(model),
				chunks=self.chunks,
				embedding_model_name=model,
			)

	def run(self):
		self._build()
		scores = {model: 0 for model in self.models}
		for item in self.QUESTIONS:
			question, attendu = item["q"], set(item["attendu"])
			print("\n" + "=" * 72)
			print(f"? {question}   (attendu : {', '.join(sorted(attendu))})")
			for model in self.models:
				results = self.dbs[model].retrieve(question, n=self.n)
				hit = any(c["id"] in attendu for c in results)
				scores[model] += int(hit)
				print(f"\n  > {model}   {'HIT' if hit else 'miss'}")
				for c in results:
					mark = "*" if c["id"] in attendu else " "
					print(f"    {mark} [{c['distance']:.3f}] {c['id']}  {c['text']}")
		print("\n" + "=" * 72)
		print(f"BILAN hit@{self.n} :")
		for model in self.models:
			print(f"   {scores[model]}/{len(self.QUESTIONS)}   {model}")


if __name__ == "__main__":
	EmbeddingComparison([
		"distiluse-base-multilingual-cased-v2",
		"paraphrase-multilingual-mpnet-base-v2",
	]).run()
