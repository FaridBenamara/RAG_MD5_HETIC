from config import LLM_MODEL, RAG_PROMPT_SYSTEM, N_RESULTS, DISTANCE_THRESHOLD
from agent import Agent
from moderator_agent import ModeratorAgent
from vector_db import VectorDB


class RAGAgent(Agent):
	def __init__(self, use_moderator=True, distance_threshold=DISTANCE_THRESHOLD):
		super().__init__()
		self.db = VectorDB.load_or_create()
		self.moderator = ModeratorAgent() if use_moderator else None
		self.system_template = Agent.read_file(RAG_PROMPT_SYSTEM)
		self.distance_threshold = distance_threshold

	def _build_system_prompt(self, chunks):
		blocks = []
		for i, c in enumerate(chunks, start=1):
			blocks.append(
				f"[{i}] (source: {c['source']} | catégorie: {c['categorie']} | "
				f"distance: {c['distance']:.3f})\n{c['text']}"
			)
		chunks_block = "\n\n".join(blocks) if blocks else "(aucun extrait)"
		return self.system_template.replace("{{Chunks}}", chunks_block)

	def answer_question(self, question):
		# modération d'abord : si injection, on ne contacte jamais le LLM principal
		moderation = None
		if self.moderator is not None:
			moderation = self.moderator.moderate(question)
			if moderation["is_prompt_injection"]:
				return {
					"answer": "Requête refusée : tentative de prompt injection détectée.",
					"refused": True,
					"moderation": moderation,
					"chunks": [],
					"warning": None,
				}

		chunks = self.db.retrieve(question, n=N_RESULTS)

		warning = None
		if (self.distance_threshold is not None and chunks
				and chunks[0]["distance"] > self.distance_threshold):
			warning = (
				f"Meilleur extrait éloigné (distance {chunks[0]['distance']:.3f} > "
				f"{self.distance_threshold}) : réponse peu fiable."
			)

		completion = self.client.chat.completions.create(
			messages=[
				{"role": "system", "content": self._build_system_prompt(chunks)},
				{"role": "user", "content": question},
			],
			model=LLM_MODEL,
			temperature=0.2,
		)

		return {
			"answer": completion.choices[0].message.content,
			"refused": False,
			"moderation": moderation,
			"chunks": chunks,
			"warning": warning,
		}
