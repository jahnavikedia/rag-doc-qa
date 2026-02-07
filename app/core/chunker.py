"""Document chunking — splits text into smaller pieces for embedding."""


class Chunker:
    """Splits text into overlapping chunks at natural boundaries.

    Tries to split at the strongest boundary first:
    paragraphs → lines → sentences → words → characters
    """

    SEPARATORS = [
        "\n\n",  # Paragraph breaks
        "\n",    # Line breaks
        ". ",    # Sentence endings
        " ",     # Word boundaries
        "",      # Characters (last resort)
    ]

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[str]:
        """Split text into chunks. Main entry point."""
        if not text.strip():
            return []

        raw_chunks = self._split_text(text, self.SEPARATORS)

        # Add overlap between consecutive chunks
        if self.chunk_overlap > 0 and len(raw_chunks) > 1:
            raw_chunks = self._add_overlap(raw_chunks)

        # Clean up whitespace
        return [chunk.strip() for chunk in raw_chunks if chunk.strip()]

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text, trying each separator in order."""

        # Base case: text is small enough, no need to split
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        # Pick the current separator to try
        separator = separators[0]
        remaining_separators = separators[1:] if len(separators) > 1 else separators

        # Split the text on this separator
        if separator == "":
            pieces = list(text)  # Split into individual characters
        else:
            pieces = text.split(separator)

        # Merge pieces back together into chunks of the right size
        chunks: list[str] = []
        current = ""

        for piece in pieces:
            # Would adding this piece keep us under the limit?
            candidate = f"{current}{separator}{piece}" if current else piece

            if len(candidate) <= self.chunk_size:
                # Yes — keep building the current chunk
                current = candidate
            else:
                # No — save the current chunk and start a new one
                if current:
                    chunks.append(current)

                # If this single piece is STILL too big, recurse with
                # a finer separator (e.g., try sentences instead of paragraphs)
                if len(piece) > self.chunk_size and remaining_separators:
                    sub_chunks = self._split_text(piece, remaining_separators)
                    chunks.extend(sub_chunks)
                else:
                    current = piece

        # Don't forget the last chunk
        if current.strip():
            chunks.append(current)

        return chunks

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        """Add overlap from the end of each chunk to the start of the next."""
        overlapped: list[str] = [chunks[0]]

        for i in range(1, len(chunks)):
            prev = chunks[i - 1]

            # Grab the last N characters from the previous chunk
            overlap_text = prev[-self.chunk_overlap:]

            # Try to start at a word boundary (not mid-word)
            space_idx = overlap_text.find(" ")
            if space_idx != -1:
                overlap_text = overlap_text[space_idx + 1:]

            overlapped.append(f"{overlap_text} {chunks[i]}")

        return overlapped