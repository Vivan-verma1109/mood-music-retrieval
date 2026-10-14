# backend/Stage5Explain/explain_chain.py
# builds the chain that takes a page's retrieved lyric snippets and has Haiku write a short "why this fits" blurb per song.
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from backend.Stage5Explain.retriever import SongLyricsRetriever

_llm = None

# lazy-init so this module doesn't blow up at import time if ANTHROPIC_API_KEY isn't set yet
def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=os.getenv('ANTHROPIC_API_KEY'), max_tokens=500)
    return _llm


# turns the retrieved Documents into a plain text block Haiku can read, one song per paragraph
def _format_documents(documents):
    blocks = []
    for doc in documents:
        blocks.append(
            f"song_id: {doc.metadata['song_id']}\n"
            f"name: {doc.metadata['name']}\n"
            f"artist: {doc.metadata['artists']}\n"
            f"lyric excerpt: {doc.page_content}"
        )
    return "\n\n".join(blocks)


_PROMPT = ChatPromptTemplate.from_template(
      "You are a music recommendation assistant. The user described their mood as: \"{mood}\"\n\n"
      "Here are songs retrieved as a good match, each with a short lyric excerpt:\n\n"
      "{songs}\n\n"
      "For each song, write ONE short sentence, plain and friendly, explaining why it fits the mood, "
      "grounded in the lyric excerpt shown. Do not invent facts not shown above.\n\n"
      "Return exactly one line per song in this format:\n"
      "song_id: blurb\n\n"
      "No extra text, no headers, no numbering."
  )


def generate_blurbs(mood_text, song_ids):
    retriever = SongLyricsRetriever(song_ids = song_ids)
    documents = retriever.invoke(mood_text)
    formatted = _format_documents(documents)

    chain = _PROMPT | _get_llm()
    response = chain.invoke({"mood": mood_text, "songs": formatted})

    return _parse_blurbs(response.content)


# turns Haiku's raw "song_id: blurb" lines into an actual dict
def _parse_blurbs(text):
    blurbs = {}
    for line in text.strip().split("\n"):
        if ":" not in line:
            continue
        song_id, blurb = line.split(":", 1)
        blurbs[song_id.strip()] = blurb.strip()
    return blurbs