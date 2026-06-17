# Stage 2 turns the user's text into a vector of numbers that captures the meaning of the sentence. Two sentences with similar meaning will
# have similar vectors even if they use different words — "I'm sad" and "feeling down and gloomy" end up close together in that space.
# We need that because KMeans clusters live in a numerical space — you can't compare raw text to cluster centroids. The embedding
# bridges that gap.

from sentence_transformers import SentenceTransformer
import joblib
import numpy as np

# Multilingual — handles non-English lyrics since our dataset is multilingual
# Free and local — no API costs, runs on your machine
# High quality — one of the best open-source sentence embedding models currently
# Benchmarkable:  Kaggle dataset's pre-computed embeddings used bge-m3
model = SentenceTransformer('BAAI/bge-m3')

query = "I'm feeling melancholic and introspective"
query = "I'm feeling melancholic and introspective"
embedding = model.encode(query)

#  print(embedding.shape)
#  print(embedding[:5])
#  (1024,)                                                                                                                              
#  [-0.04608794  0.0110431  -0.02667089 -0.02327831 -0.01315501] 

# 1024-dim vector: embedding for I'm feeling blah blah blah

# ------------------------------------------------------------------------------------------------------------------------------------------------ #
# Projection Layer, linear map from 1024 -> 5 dims, each cluster has a centrioid in 5-dim aduio space and we can pair mood
# descriptions with their matching centroid

kmeans = joblib.load('archive/kmeans_model.pkl')
print(kmeans.cluster_centers_)
# [[0.31834384 0.88158994 0.53521369 0.02624341 0.41188698]
# [0.32282001 0.55132163 0.47843726 0.18737258 0.58193304]
# [0.28902274 0.29861373 0.4588708  0.79446589 0.47017999]
# [0.73303203 0.77351461 0.50331367 0.10270728 0.65654264]
# [0.71021773 0.5785708  0.48770265 0.59656975 0.64244961]]

# use the songs themselves. Each song has audio features AND lyrics so (sbert(lyrics), audio_features) and we train the projection layer to map
# from lyric embedding space to audio feature space.