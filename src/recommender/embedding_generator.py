import numpy as np

from src.recommender.embedding_store import EmbeddingStore


class EmbeddingGenerator:

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        print("DEBUG: About to import SentenceTransformer", flush=True)

        from sentence_transformers import SentenceTransformer

        print("DEBUG: SentenceTransformer imported", flush=True)

        self.model_name = model_name

        print("DEBUG: About to load embedding model", flush=True)

        self.model = SentenceTransformer(model_name)

        print("DEBUG: Embedding model loaded", flush=True)

    def generate_embeddings(
        self,
        summaries: list[str],
    ) -> np.ndarray:

        print("DEBUG: Starting embedding generation", flush=True)

        embeddings = self.model.encode(
            summaries,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        print("DEBUG: Embedding generation completed", flush=True)
        
        return embeddings.astype(
            np.float32
        )

    def generate_and_store(
        self,
        fic_ids: np.ndarray,
        summaries: list[str],
        store: EmbeddingStore,
    ) -> None:

        embeddings = self.generate_embeddings(summaries)

        store.save_embeddings(
            fic_ids=fic_ids,
            embeddings=embeddings,
            model_name=self.model_name,
        )