from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class RetrievalHit:
    id: str
    title: str
    content: str
    score: float


class RetrievalService:
    def __init__(self, docs):
        self.docs = docs
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        corpus = [f"{d.title} {d.content}" for d in docs]
        self.matrix = self.vectorizer.fit_transform(corpus) if corpus else None

    def search(self, query: str, k: int = 4) -> list[RetrievalHit]:
        if not self.docs or self.matrix is None:
            return []
        q = self.vectorizer.transform([query])
        scores = cosine_similarity(q, self.matrix)[0]
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        hits = []
        for idx, score in ranked[:k]:
            if score <= 0:
                continue
            d = self.docs[idx]
            if d.unsafe:  # never surface adversarial documents
                continue
            hits.append(RetrievalHit(d.id, d.title, d.content, float(score)))
        return hits
