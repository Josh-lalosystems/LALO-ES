# Copyright (c) 2025 LALO AI LLC. All rights reserved.
#
# Simple in-memory vector store for demo purposes.
# Uses TF-IDF to embed text and cosine similarity to retrieve closest matches.
# In production, replace with FAISS / Chroma / Weaviate for persistence & scale.

from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class VectorStore:
    def __init__(self):
        self.documents: List[str] = []
        self.vectorizer = TfidfVectorizer()
        self.doc_vectors = None

    def add_document(self, doc: str):
        """Add a new document to the store."""
        self.documents.append(doc)
        self.doc_vectors = self.vectorizer.fit_transform(self.documents)

    def query(self, text: str, top_k: int = 1) -> List[Tuple[str, float]]:
        """
        Retrieve top_k most similar documents.
        Returns list of (document, similarity_score).
        """
        if not self.documents:
            return []

        query_vec = self.vectorizer.transform([text])
        similarities = cosine_similarity(query_vec, self.doc_vectors).flatten()
        ranked_indices = similarities.argsort()[::-1][:top_k]
        results = [(self.documents[i], float(similarities[i])) for i in ranked_indices]
        return results


# Example usage for standalone testing
if __name__ == "__main__":
    vs = VectorStore()
    vs.add_document("Sample marketing report for Q2 high margin shoes.")
    vs.add_document("Production report for low margin items.")
    vs.add_document("Financial summary and sales trends for footwear.")

    query = "high margin shoes Q2"
    matches = vs.query(query, top_k=2)
    print("Query:", query)
    print("Matches:", matches)
