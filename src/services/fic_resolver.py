from src.loader.database import get_connection


class FicResolver:
    """Service class for resolving fanfiction records from ID, URL, or author metadata."""

    def __init__(self, input: dict):
        self.input = input

    def resolve_from_id(self):
        """Fetch fic record directly using primary key ID."""
        fic_id = self.input["fic_id"]

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM fics WHERE fic_id = %s", (fic_id,))
                result = cur.fetchone()

                if result:
                    return dict(zip([desc[0] for desc in cur.description], result))

                return {"error": f"No fic found with id: {fic_id}"}

    def resolve_from_url(self):
        """Fetch fic record matching canonical AO3 URL."""
        url = f"{self.input['url']}?view_adult=true"

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM fics WHERE url = %s", (url,))
                result = cur.fetchone()

                if result:
                    return dict(zip([desc[0] for desc in cur.description], result))

                return {"error": f"No fic found with url: {url}"}

    def resolve_from_name_author(self):
        """Fetch fic record using work name and formatted author path."""
        name = self.input["name"]
        author = f"/users/{self.input['author']}/pseuds/{self.input['author']}"

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM fics WHERE name = %s AND author = %s", (name, author))
                result = cur.fetchone()

                if result:
                    return dict(zip([desc[0] for desc in cur.description], result))

                return {"error": "No fic found with exact name and author"}

    def resolve(self):
        """Dispatch resolution based on payload structure and validate parameters."""
        if len(self.input) == 1:
            if "fic_id" in self.input:
                try:
                    int(self.input["fic_id"])
                except (ValueError, TypeError):
                    return {"error": "Invalid 'fic_id' value. It must be a numeric string."}

                return self.resolve_from_id()

            elif "url" in self.input:
                url = self.input["url"]

                if url.startswith("http://") or url.startswith("https://"):
                    if "/chapters/" in url:
                        self.input["url"] = url.split("/chapters/")[0]

                    return self.resolve_from_url()

                return {"error": "Invalid 'url' value. It must be a valid HTTP or HTTPS URL."}

        elif len(self.input) == 2 and "name" in self.input and "author" in self.input:
            if self.input["name"].strip() and self.input["author"].strip():
                return self.resolve_from_name_author()

        return {"error": "Invalid input. Please provide either an 'id', a 'url', or both 'name' and 'author'."}