import numpy as np
import pandas as pd
import faiss

df = pd.read_csv('archive/songs_clustered.csv')
embeddings = np.load('archive/lyrics_embeddings.npy').astype('float32')
X_scaled = np.load('archive/X_scaled.npy').astype('float32')

# case-insensitive dedup on name + artists
def lowercase_and_strip(col):
    return col.str.lower().str.strip()

df_lower = df[['name', 'artists']].apply(lowercase_and_strip)

# a True/False array the same length as the dataframe. True = keep this row, False = it's a duplicate. So df[keep_mask] gives you only the rows marked True.
# keep_mask ends up as: True for the first time a song appears, False for every repeat.
keep_mask = ~df_lower.duplicated(keep='first')


#  np.where(keep_mask)[0] returns the row numbers where keep_mask is True — so if songs 0, 2, 5 were kept and song 1, 3, 4 were dupes, keep_idx = [0, 2, 5].                          
keep_idx = np.where(keep_mask.values)[0]

# After filtering, the dataframe still has the original row numbers (0, 5, 8...). reset_index(drop=True) renumbers them 0, 1, 2... so they stay in sync with the embeddings array, which also got renumbered 0, 1, 2 when you filtered it.
df_dedup = df[keep_mask].reset_index(drop=True)

#  Then embeddings[keep_idx] pulls just those rows out of the embedding matrix. Same songs, same order, just with the dupes removed.
#  embeddings[i] is a 768-number vector representing the meaning of song i's lyrics. The whole matrix is just 845k of those stacked on top of each other
embeddings_dedup = embeddings[keep_idx]
X_scaled_dedup = X_scaled[keep_idx]

df_dedup.to_csv('archive/songs_clustered.csv', index=False)
np.save('archive/lyrics_embeddings.npy', embeddings_dedup)
np.save('archive/X_scaled.npy', X_scaled_dedup)

# IndexFlatIP = brute-force cosine similarity search (IP = inner product, works as cosine sim since vectors are normalized)
index = faiss.IndexFlatIP(embeddings_dedup.shape[1])  # 768 = width of each embedding vector
index.add(embeddings_dedup)  # load all 845k vectors into the index
faiss.write_index(index, 'archive/lyrics_faiss.index')  # save to disk so fusion.py can load it

print(f"Before: {len(df)} | After: {len(df_dedup)} | Removed: {len(df) - len(df_dedup)}")