"""
rag/prompting.py — Prompt builder for the generation step.

Constructs a generation prompt in Argentinian Spanish that includes
retrieved context, instructs the LLM to stay within that context,
and embeds citation metadata.

FR-003: retrieved content must be included.
FR-004: answer in natural Argentinian Spanish.
FR-005: citation metadata available.
FR-008: LLM must not invent claims outside retrieved context.
"""
from __future__ import annotations

from rag.domain.fragments import SearchResult

_SYSTEM_TEMPLATE = """\
Eres un asistente institucional de la Universidad Tecnológica Nacional (UTN) \
que responde únicamente en español.

Responde la pregunta del usuario utilizando EXCLUSIVAMENTE la información del \
contexto institucional proporcionado a continuación. No inventes datos, fechas \
ni procedimientos que no estén respaldados por el contexto. Si la información \
no está en el contexto, no la incluyas en tu respuesta.

Sé breve y directo: respondé en no más de 2 oraciones.

Contexto institucional:
{context}

Pregunta: {question}

Respuesta (en español argentino, basada únicamente en el contexto):"""


class PromptBuilder:
    """Builds the LLM generation prompt from a question and retrieved results."""

    def build(self, question: str, results: list[SearchResult]) -> str:
        """Return the full generation prompt string.

        Parameters
        ----------
        question:
            The user's natural-language question.
        results:
            Retrieved SearchResult objects; must be non-empty.

        Raises
        ------
        ValueError
            When results is empty (no context to ground the answer).
        """
        if not results:
            raise ValueError(
                "Cannot build a generation prompt without retrieved results. "
                "Use the refusal path when context is insufficient."
            )

        context_blocks = []
        for i, result in enumerate(results, start=1):
            url = result.metadata.get("url", "")
            title = result.metadata.get("title", "")
            # The text field is not always available in SearchResult (it comes
            # from the vector store fetch).  Use metadata text if stored, or
            # a placeholder that the service layer may enrich.
            text = result.metadata.get("text", "")
            header = f"[Fuente {i}]"
            if title:
                header += f" {title}"
            if url:
                header += f" ({url})"
            block = f"{header}\n{text}" if text else header
            context_blocks.append(block)

        context = "\n\n".join(context_blocks)
        return _SYSTEM_TEMPLATE.format(context=context, question=question)
    