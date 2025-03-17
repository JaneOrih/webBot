from app.utils.embeddings import get_embedding
from supabase import create_client
import os

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_faq_context(query: str, threshold=0.75, top_k=3):
    embedding = get_embedding(query).flatten().tolist()
    results = supabase.rpc('match_faq', {
        'query_embedding': embedding,
        'match_threshold': threshold,
        'match_count': top_k
    }).execute()
    return "\n".join([f"Q: {res['question']}\nA: {res['answer']}" for res in results.data])