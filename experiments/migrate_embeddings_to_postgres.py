from src.recommender.pickle_store import (
    PickleEmbeddingStore
)

from src.recommender.postgres_store import (
    PostgresEmbeddingStore
)


def main():

    old_store = (
        PickleEmbeddingStore()
    )

    new_store = (
        PostgresEmbeddingStore()
    )

    fic_ids, embeddings = (
        old_store.get_all_embeddings()
    )

    print(
        f"Found {len(fic_ids)} "
        f"embeddings to migrate."
    )

    new_store.save_embeddings(
        fic_ids=fic_ids,
        embeddings=embeddings,
        model_name=old_store.model_name,
    )

    new_fic_ids, new_embeddings = (
        new_store.get_all_embeddings()
    )

    print(
        f"PostgreSQL now contains "
        f"{len(new_fic_ids)} embeddings."
    )

    if (
        len(fic_ids)
        != len(new_fic_ids)
    ):
        raise RuntimeError(
            "Migration verification failed: "
            "embedding counts do not match."
        )

    print(
        "Migration completed successfully."
    )


if __name__ == "__main__":
    main()