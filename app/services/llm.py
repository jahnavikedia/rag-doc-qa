"""LLM service — generates answers using Ollama (local, free).

Ollama runs a local server at localhost:11434 and serves
models like Llama 3.2. Our code sends HTTP requests to it.
"""

import ollama

from app.config import settings

# This instruction tells the LLM how to behave
SYSTEM_PROMPT = """You are a precise, helpful document assistant. Answer the user's question based ONLY on the provided context chunks. Follow these rules:

1. If the context contains the answer, provide it clearly and concisely.
2. If the context partially answers the question, state what you can answer and what's missing.
3. If the context does NOT contain the answer, say "I don't have enough information in the provided documents to answer this question."
4. Never fabricate information not present in the context.
5. When possible, reference which chunk(s) support your answer.
6. Keep answers focused — no unnecessary preamble."""


class LLMService:
    """Generates answers using a local Ollama model."""

    def __init__(self, model: str | None = None, base_url: str | None = None):
        self.model = model or settings.ollama_model
        self.base_url = base_url or settings.ollama_base_url
        self.client = ollama.Client(host=self.base_url)

        # Verify Ollama is running and model is available
        try:
            self.client.show(self.model)
            print(f"✅ LLM ready: {self.model} via Ollama")
        except Exception as exc:
            print(f"⚠️  Could not connect to Ollama: {exc}")
            print(f"   Make sure Ollama is running and '{self.model}' is pulled.")

    def generate(self, question: str, context_chunks: list[str]) -> str:
        """Generate an answer given a question and context chunks.

        This is the core RAG generation step. We build a prompt that
        includes the retrieved chunks and the question, then send it
        to the LLM with a system prompt that constrains it to only
        use the provided context.

        Args:
            question: The user's question.
            context_chunks: List of relevant text chunks from vector search.

        Returns:
            The generated answer string.
        """
        # Build the user prompt with context
        user_prompt = self._build_prompt(question, context_chunks)

        # Call Ollama
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        return response["message"]["content"]

    def generate_stream(self, question: str, context_chunks: list[str]):
        """Stream an answer token by token.

        Same as generate(), but yields tokens as they're produced
        instead of waiting for the full response. This lets the
        frontend show text appearing in real-time.

        Args:
            question: The user's question.
            context_chunks: List of relevant text chunks.

        Yields:
            Individual tokens (strings) as they're generated.
        """
        user_prompt = self._build_prompt(question, context_chunks)

        stream = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )

        for chunk in stream:
            token = chunk["message"]["content"]
            if token:
                yield token

    def _build_prompt(self, question: str, context_chunks: list[str]) -> str:
        """Build the user prompt with numbered context chunks.

        Format:
            Context from documents:

            [Chunk 1]
            The refund policy allows...

            ---

            [Chunk 2]
            Employees receive 20 days...

            ---

            Question: What is the refund policy?

            Answer based only on the context above:
        """
        context_section = "\n\n---\n\n".join(
            f"[Chunk {i + 1}]\n{chunk}" for i, chunk in enumerate(context_chunks)
        )

        return f"""Context from documents:

{context_section}

---

Question: {question}

Answer based only on the context above:"""