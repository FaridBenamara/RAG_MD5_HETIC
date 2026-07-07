import os

from dotenv import load_dotenv
from groq import Groq


class Agent:
	def __init__(self):
		load_dotenv()
		api_key = os.environ.get("GROQ_API_KEY")
		if not api_key:
			raise RuntimeError("GROQ_API_KEY manquante (voir .env.example).")
		self.client = Groq(api_key=api_key)

	@staticmethod
	def read_file(path):
		with open(path, encoding="utf-8") as file:
			return file.read()
