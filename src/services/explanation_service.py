from groq import Groq
import json


class ExplanationService:
    """Generate natural-language explanations for Opsis recommendations using Groq."""

    def __init__(self):
        self.client = Groq()
        self.model = "openai/gpt-oss-20b"

    def generate_explanations(self, source: dict, recommendations: list[dict]) -> list[str]:
        prompt = self._build_prompt(source, recommendations)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            reasoning_effort="low",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "recommendation_explanations",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "explanations": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "minItems": 10,
                                "maxItems": 10
                            }
                        },
                        "required": ["explanations"],
                        "additionalProperties": False
                    }
                }
            },
        )

        return self._parse_response(
            response,
            expected_count=len(recommendations)
        )

    @staticmethod
    def _system_prompt():
        return """You are the explanation engine for Opsis, an AI-powered fanfiction recommendation system.

            The recommendations have already been selected by Opsis using semantic similarity between fanfiction works.

            Your task is NOT to generate, rank, or judge recommendations.

            Your task is ONLY to explain why each recommended work is a good match for someone who enjoyed the source work.

            You will receive:

            • One SOURCE fanfiction.
            • A list of RECOMMENDED fanfictions in a fixed order.

            Each work may include:

            - title
            - summary
            - fandom(s)
            - relationship(s)
            - character(s)
            - archive warnings
            - freeform tags
            - kudos
            - bookmarks
            - hits

            Base every explanation only on the supplied information.

            Prioritize similarities in this order:

            1. Shared themes and central ideas.
            2. Character dynamics and relationships.
            3. Emotional tone.
            4. Narrative style or pacing.
            5. Shared fandoms or settings.
            6. Relevant warnings or freeform tags.
            7. Popularity metrics only as supporting evidence.

            Popularity should never be the primary reason for a recommendation.

            Good:
            "A community favorite that expands on the same emotionally complex mentor-student relationship."

            Bad:
            "It has lots of kudos."

            Requirements:

            - Produce exactly one explanation for every recommendation.
            - Preserve the exact order.
            - Each explanation should be between 20 and 60 words.
            - Use varied sentence structures.
            - Sound like a knowledgeable fanfiction reader.
            - Avoid generic phrases such as:
            - "If you liked..."
            - "You'll love..."
            - "Fans of..."
            - Do not invent details not supported by the input.
            - If information is limited, write a conservative explanation instead of guessing.
            - Make each explanation distinct rather than repeating the same reasoning.

            Return ONLY valid JSON in this format:

            {
            "explanations": [
                "...",
                "...",
                "...",
                "...",
                "...",
                "...",
                "...",
                "...",
                "...",
                "..."
            ]
            }"""

    def _build_prompt(self, source: dict, recommendations: list[dict]) -> str:
        """Build the user prompt containing the source fic and recommendations."""

        sections = ["""Below is the source fanfiction followed by the recommended fanfictions.

        Generate exactly one explanation for each recommendation, preserving the order.

        Return only the required JSON object.
        
        ================================================================================="""]

        sections.append("SOURCE\n")
        sections.append(self._format_fic(source))

        for index, fic in enumerate(recommendations, start=1):
            sections.append("\n" + "-" * 60)
            sections.append(f"\nRECOMMENDATION {index}\n")
            sections.append(self._format_fic(fic))

        return "\n".join(sections)

    def _format_fic(self, fic: dict) -> str:
        """Format relevant fic metadata for explanation generation."""

        def join(values):
            if not values:
                return "None"

            if isinstance(values, list):
                return ", ".join(str(v) for v in values)

            return str(values)

        return f"""Title: {fic.get("name", "")}
    Summary: {fic.get("summary", "")}
    Fandoms: {join(fic.get("fandom"))}
    Relationships: {join(fic.get("relationship"))}
    Freeform Tags: {join(fic.get("freeform"))}
    Kudos: {fic.get("kudos", 0)}
    Bookmarks: {fic.get("bookmarks", 0)}
    Hits: {fic.get("hits", 0)}"""

    def _parse_response(self, response, expected_count: int) -> list[str]:
        """Parse and validate the LLM response."""

        try:
            data = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            raise ValueError("Groq returned invalid JSON.") from e

        explanations = data.get("explanations")

        if not isinstance(explanations, list):
            raise ValueError("Missing 'explanations' array in Groq response.")

        if len(explanations) != expected_count:
            raise ValueError(
                f"Expected {expected_count} explanations but received {len(explanations)}."
            )

        return explanations