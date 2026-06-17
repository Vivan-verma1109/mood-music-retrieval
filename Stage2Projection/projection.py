# Stage 2 turns the user's text into a vector of numbers that captures the meaning of the sentence. Two sentences with similar meaning will
# have similar vectors even if they use different words — "I'm sad" and "feeling down and gloomy" end up close together in that space.
# We need that because KMeans clusters live in a numerical space — you can't compare raw text to cluster centroids. The embedding
# bridges that gap.