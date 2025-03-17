import os
from dotenv import load_dotenv
from app.utils.db import get_supabase
from app.utils.faq_data import faqs

load_dotenv()

def populate_faqs():
    supabase = get_supabase()
    
    # Clear existing FAQs
    supabase.table('faq_knowledge').delete().neq('id', '0').execute()
    
    # Insert new FAQs
    for faq in faqs:
        supabase.table('faq_knowledge').insert(faq).execute()
    
    print(f"Successfully inserted {len(faqs)} FAQs")

if __name__ == "__main__":
    populate_faqs()