import numpy as np
import pandas as pd
import faiss

df = pd.read_csv('archive/songs_clustered.csv')
embeddings = np.load('archive/lyrics_embeddings.npy').astype('float32')

# case-insensitive dedup on name + artists
df_lower = df[['name', 'artists']].apply(lambda col: col.str.lower().str.strip())
keep_mask = ~df_lower.duplicated(keep='first')
keep_idx = np.where(keep_mask.values)[0]

df_dedup = df[keep_mask].reset_index(drop=True)
embeddings_dedup = embeddings[keep_idx]

df_dedup.to_csv('archive/songs_clustered.csv', index=False)
np.save('archive/lyrics_embeddings.npy', embeddings_dedup)

index = faiss.IndexFlatIP(embeddings_dedup.shape[1])
index.add(embeddings_dedup)
faiss.write_index(index, 'archive/lyrics_faiss.index')

print(f"Before: {len(df)} | After: {len(df_dedup)} | Removed: {len(df) - len(df_dedup)}")