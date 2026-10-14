# backend/Stage5Explain/retriever.py
# LangChain retriever that scores a page's songs against the mood query using their lyrics,
# so the generation chain gets ranked, grounded lyric snippets instead of raw unordered lyrics.
import numpy as np
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from backend.Stage4Fusion.loader import df, model


def chunk_lyrics(lyrics, chunk_size=40):
    words = " ".join(lyrics.split()).split(" ")
    if len(words) <= chunk_size:
        return [" ".join(words)]
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


class SongLyricsRetriever(BaseRetriever):
    song_ids: list[str]

    def _get_relevant_documents(self, query, *, run_manager=None):
        query_emb = model.encode([query], normalize_embeddings=True).astype('float32')[0]

        documents = []
        for song_id in self.song_ids:
            row = df.loc[int(song_id)]
            chunks = chunk_lyrics(row['lyrics'])
            chunk_embs = model.encode(chunks, normalize_embeddings=True).astype('float32')
            sims = chunk_embs @ query_emb
            best = chunks[int(np.argmax(sims))]

            documents.append(Document(
                page_content=best,
                metadata={"name": row['name'], "artists": row['artists'], "song_id": song_id},
            ))
        return documents