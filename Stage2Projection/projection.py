# Stage 2 turns the user's text into a vector of numbers that captures the meaning of the sentence. Two sentences with similar meaning will
# have similar vectors even if they use different words — "I'm sad" and "feeling down and gloomy" end up close together in that space.
# We need that because KMeans clusters live in a numerical space — you can't compare raw text to cluster centroids. The embedding
# bridges that gap.

from sentence_transformers import SentenceTransformer
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