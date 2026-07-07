import csv

from config import CORPUS_PATH


class CorpusLoader:
	def __init__(self, path=CORPUS_PATH):
		self.path = path

	def load(self):
		chunks = []
		with open(self.path, newline="", encoding="utf-8") as file:
			for row in csv.DictReader(file):
				text = (row.get("text") or "").strip()
				if not text:
					continue
				chunks.append({
					"id": (row.get("id") or f"chunk-{len(chunks)}").strip(),
					"text": text,
					"source": (row.get("source") or "inconnue").strip(),
					"categorie": (row.get("categorie") or "inconnue").strip(),
				})
		if not chunks:
			raise ValueError(f"Corpus vide ou illisible : {self.path}")
		return chunks
