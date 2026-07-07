import { useState } from "react";

function ModerationBadge({ moderation }) {
	if (!moderation) return null;
	const injection = moderation.is_prompt_injection;
	return (
		<div className={`badge ${injection ? "badge-danger" : "badge-ok"}`}>
			{injection ? "Injection détectée" : "Modération : ok"}
			{moderation.reason && <span className="badge-reason"> — {moderation.reason}</span>}
		</div>
	);
}

function SourceList({ chunks }) {
	if (!chunks || chunks.length === 0) return null;
	return (
		<div className="sources">
			<h3>Extraits utilisés</h3>
			<ul>
				{chunks.map((c) => (
					<li key={c.id}>
						<span className="distance">[{c.distance.toFixed(3)}]</span>{" "}
						<span className="source-tag">({c.source})</span> {c.text}
					</li>
				))}
			</ul>
		</div>
	);
}

export default function App() {
	const [question, setQuestion] = useState("");
	const [loading, setLoading] = useState(false);
	const [result, setResult] = useState(null);
	const [error, setError] = useState(null);

	async function handleSubmit(e) {
		e.preventDefault();
		if (!question.trim()) return;
		setLoading(true);
		setError(null);
		setResult(null);
		try {
			const res = await fetch("/api/ask", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ question }),
			});
			if (!res.ok) throw new Error(`Erreur API (${res.status})`);
			setResult(await res.json());
		} catch (err) {
			setError(err.message);
		} finally {
			setLoading(false);
		}
	}

	return (
		<main className="app">
			<h1>Mon premier RAG</h1>
			<p className="subtitle">Villebrume-les-Cuillères — corpus absurde, M2 MD5</p>

			<form onSubmit={handleSubmit} className="ask-form">
				<input
					type="text"
					value={question}
					onChange={(e) => setQuestion(e.target.value)}
					placeholder="Comment s'appelle le chat bleu de Bob ?"
				/>
				<button type="submit" disabled={loading}>
					{loading ? "..." : "Demander"}
				</button>
			</form>

			{error && <div className="badge badge-danger">{error}</div>}

			{result && (
				<div className="result">
					<ModerationBadge moderation={result.moderation} />

					{result.warning && <div className="badge badge-warning">{result.warning}</div>}

					<div className={`answer ${result.refused ? "answer-refused" : ""}`}>
						{result.answer}
					</div>

					<SourceList chunks={result.chunks} />
				</div>
			)}
		</main>
	);
}
