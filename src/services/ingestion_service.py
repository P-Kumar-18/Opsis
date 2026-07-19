from data.scrape_ao3 import get_url, extract
from src.loader.load_ao3 import load_ao3
from src.recommender.embedding_generator import EmbeddingGenerator
from src.recommender.postgres_store import PostgresEmbeddingStore 

import pandas as pd

class IngestionService:
    def __init__(self, input: dict):
        self.input = input

    def id_to_url(self, fic_id: str) -> dict:
        return {
            "url": f"https://archiveofourown.org/works/{fic_id}"
        }

    def name_and_author_to_url(self, params: dict) -> dict:
        url = f"https://archiveofourown.org/works/search?work_search%5Bquery%5D={params['name']}&work_search%5Bcreators%5D={params['author']}"
        print(f"Searching for fic with name '{params['name']}' and author '{params['author']}' at URL: {url}")
        url_list = get_url(url, mode="live")

        if len(url_list) == 0:
            return {
                "error": "No fic found with the given name and author"
            }

        elif len(url_list) > 1:
            return {
                "error": (
                    "Multiple fics matched that name and author. "
                    "Please use the fic's URL or Work ID instead."
                )
            }

        return {
            "single_match": url_list[0]
        }

    def ingest(self):
        if "fic_id" in self.input:
            url_list = [self.id_to_url(self.input["fic_id"])["url"]]

        elif "name" in self.input and "author" in self.input:
            url = self.name_and_author_to_url(
                self.input
            )

            if "error" in url:
                return url

            url_list = [
                url["single_match"]
            ]


        elif "url" in self.input:
            url_list = [self.input["url"]]

        else:
            return {"error": "Invalid input. Please provide either 'fic_id', 'name' and 'author', or 'url'."}
        
        # Use the extract function to scrape the fanfiction data
        data = []

        for url in url_list:
            data_, _ = extract(url, mode="live")
            if data_ is not None:
                data.append(data_)
            else:
                print(f"Failed to extract data from URL: {url}")

        if not data:        
            return {"error": "No data extracted from the provided URL(s)"}
        
        df = pd.DataFrame(data)
        df["fic_id"] = (
            df["url"]
            .str.extract(r"/works/(\d+)")
            .astype("Int64")
        )

        print("DataFrame created from extracted data:", df)

        try:
            load_ao3(df=df)

        except Exception as e:
            print(f"Error during ingestion: {e}")
            return {"error": "An internal error occurred while processing this fic."}

        fic_id = df["fic_id"].to_numpy()
        summaries = df["summary"].fillna("").astype(str).to_list()

        store = PostgresEmbeddingStore()
        generator = EmbeddingGenerator()
        
        embeddings = generator.generate_embeddings(summaries=summaries)
        
        if embeddings is None:
            return {"error": "Failed to generate embeddings for the provided summaries"}

        for id, embedding in zip(
            fic_id,
            embeddings
        ):
            store.save_embedding(fic_id = id, embedding = embedding, model_name = generator.model_name)

        return {
            "single_item": data[0]
        }