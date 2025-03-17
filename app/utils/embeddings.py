# Description: This file contains the code to generate embeddings for the text data using the SentenceTransformer library.
from sentence_transformers import SentenceTransformer
import numpy as np

encoder = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> np.ndarray:
    return encoder.encode(text).reshape(1, -1)