import sys
import os
from dotenv import load_dotenv

# Add the root of the project to the sys.path so that 'app' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.db import get_supabase
from app.utils.faq_data import faqs

load_dotenv()

def populate_faqs():
    """Populate the Supabase database with FAQ data."""
    supabase = get_supabase()

    # Clear existing FAQs (if any)
    supabase.table('faq_knowledge').delete().neq('id', '0').execute()

    # Insert new FAQs into the database
    for faq in faqs:
        supabase.table('faq_knowledge').insert(faq).execute()

    print(f"Successfully inserted {len(faqs)} FAQs")

if __name__ == "__main__":
    populate_faqs()
