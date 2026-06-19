# Stage 2 turns the user's text into a vector of numbers that captures the meaning of the sentence. Two sentences with similar meaning will
# have similar vectors even if they use different words — "I'm sad" and "feeling down and gloomy" end up close together in that space.
# We need that because KMeans clusters live in a numerical space — you can't compare raw text to cluster centroids. The embedding
# bridges that gap.

from sentence_transformers import SentenceTransformer
import joblib
import numpy as np
import pandas as pd
import torch
import faiss

# Originally planned to use bge-m3 (1024-dim, top-tier quality) but at batch_size=32 on RTX 5070
# it projected ~89 hours for 955k songs. Swapped to paraphrase-multilingual-mpnet-base-v2:
# - Still multilingual — handles non-English lyrics in the dataset
# - 768-dim vs 1024-dim, mid-tier quality, but sufficient for mood-based reranking
# - Runs in ~2-3 hours at batch_size=128 on the same hardware
# If higher quality embeddings are needed later, rerun with bge-m3 on better hardware

#  print(embedding.shape)
#  print(embedding[:5])
#  (768,)
#  [-0.04608794  0.0110431  -0.02667089 -0.02327831 -0.01315501]

# 768-dim vector: embedding for I'm feeling blah blah blah

# ------------------------------------------------------------------------------------------------------------------------------------------------ #
# Projection Layer, linear map from 768 -> 5 dims, each cluster has a centroid in 5-dim audio space and we can pair mood
# descriptions with their matching centroid

# kmeans = joblib.load('archive/kmeans_model.pkl')
# print(kmeans.cluster_centers_)
# [[0.31834384 0.88158994 0.53521369 0.02624341 0.41188698]
# [0.32282001 0.55132163 0.47843726 0.18737258 0.58193304]
# [0.28902274 0.29861373 0.4588708  0.79446589 0.47017999]
# [0.73303203 0.77351461 0.50331367 0.10270728 0.65654264]
# [0.71021773 0.5785708  0.48770265 0.59656975 0.64244961]]

# use the songs themselves. Each song has audio features AND lyrics so (sbert(lyrics), audio_features) and we train the projection layer to map
# from lyric embedding space to audio feature space.

df = pd.read_csv('archive/songs_clustered.csv')
lyrics = df['lyrics'].fillna('').tolist()

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', device=device)

embeddings = model.encode(lyrics, batch_size=128, show_progress_bar=True, normalize_embeddings=True)

print(f"Embeddings shape: {embeddings.shape}")
np.save('archive/lyrics_embeddings.npy', embeddings)

d = embeddings.shape[1]
index = faiss.IndexFlatIP(d)
index.add(embeddings.astype('float32'))
faiss.write_index(index, 'archive/lyrics_faiss.index')
print(f"FAISS index built: {index.ntotal} vectors")
