import pandas as pd
from supabase import create_client
import os
from sentence_transformers import SentenceTransformer

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
encoder = SentenceTransformer('all-MiniLM-L6-v2')

def process_faq_data(csv_path: str):
    # Load FAQ data
    faq_df = pd.read_csv(csv_path)
    
    # Generate embeddings
    faq_df['embedding'] = faq_df['question'].apply(
        lambda x: encoder.encode(x).tolist()
    )
    
    # Create/Update table
    supabase.table('faq_knowledge_base').delete().neq('id', 0).execute()
    
    # Batch insert
    for batch in np.array_split(faq_df, 10):
        supabase.table('faq_knowledge_base').insert(
            batch.to_dict('records')
        ).execute()