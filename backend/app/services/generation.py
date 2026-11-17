"""Write the answer from the reranked chunks, with citations.

The chunks are numbered [1], [2]... in the prompt. The LLM must:
- answer ONLY from these sources (no outside knowledge),
- cite the number of the source after each fact, e.g. "... the noise [2].",
- say so when the sources do not contain the answer.
[n] in the answer = the n-th chunk of the list returned with it.
"""

from openai import OpenAI

from app.core.config import get_settings
from app.services.ingestion import Chunk

NO_SOURCES = "I couldn't find anything about this in your documents."

SYSTEM = """You are a study assistant. You answer a student's question using ONLY the numbered
sources from their course notes given below.

Rules:
- Use only facts found in the sources. Never add outside knowledge.
- After each fact, cite its source number in square brackets, e.g. [1] or [2][3].
- If the sources do not contain the answer, say: "{no_sources}"
- Be clear and concise. Use short paragraphs or bullet points when it helps."""


def format_sources(chunks: list[Chunk]) -> str:
    """[1] (notes.pdf, p. 3, Overfitting)\\n<text> ..."""
    blocks = []
    for n, chunk in enumerate(chunks, start=1):
        where = ", ".join(
            part
            for part in [
                chunk.filename,
                f"p. {chunk.page}" if chunk.page else None,
                chunk.section,
            ]
            if part
        )
        blocks.append(f"[{n}] ({where})\n{chunk.text}")
    return "\n\n".join(blocks)


def generate_answer(question: str, chunks: list[Chunk]) -> str:
    if not chunks:
        return NO_SOURCES  # nothing indexed or nothing found: no LLM call

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        temperature=0.2,  # low = sticks to the sources, little "creativity"
        messages=[
            {"role": "system", "content": SYSTEM.format(no_sources=NO_SOURCES)},
            {
                "role": "user",
                "content": f"Sources:\n\n{format_sources(chunks)}\n\nQuestion: {question}",
            },
        ],
    )
    return response.choices[0].message.content
