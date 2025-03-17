# scripts/faq_scraper.py
import sys
import os
import time
import requests
from bs4 import BeautifulSoup
from supabase import create_client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simple_embed(text: str) -> list:
    """Basic embedding fallback (for MVP testing)"""
    return [len(text)] * 384  # Simple numerical representation

def update_faqs():
    try:
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials in environment variables")
        supabase = create_client(supabase_url, supabase_key)

        # Set up Selenium to fetch dynamic content from the homepage
        faq_url = "https://www.frontlett.com"
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        
        # Initialize WebDriver (ensure chromedriver is installed and in PATH)
        driver = webdriver.Chrome(options=options)
        driver.get(faq_url)
        time.sleep(5)  # Wait for the page to fully load dynamic content
        html = driver.page_source
        driver.quit()

        # Debug: print first 500 characters of fetched HTML
        print("Fetched HTML snippet:", html[:500])

        soup = BeautifulSoup(html, "html.parser")
        # Adjust this selector based on the actual structure of the FAQ section on the homepage.
        # For example, assume FAQs are within a section with class "faq-section" and each FAQ item has a class "faq-item"
        faq_items = soup.select("section.faq-section div.faq-item")
        if not faq_items:
            raise ValueError("No FAQ items found - check if the FAQ section exists or if the selectors need adjustment.")

        faqs = []
        for item in faq_items:
            try:
                # Adjust selectors below to match the actual DOM structure.
                question_el = item.select_one("h3, h4, .faq-question")
                answer_el = item.select_one("p, .faq-answer")
                if not question_el or not answer_el:
                    continue
                question = question_el.get_text(strip=True)
                answer = answer_el.get_text(strip=True)
                faqs.append({
                    "question": question,
                    "answer": answer,
                    "embedding": simple_embed(question)
                })
            except Exception as e:
                print(f"Skipping an FAQ item due to error: {str(e)}")
                continue

        if faqs:
            # Clear existing FAQs
            supabase.from_("faq_knowledge_base").delete().neq("id", "0").execute()
            # Batch insert new FAQs
            batch_size = 10
            for i in range(0, len(faqs), batch_size):
                batch = faqs[i:i+batch_size]
                supabase.from_("faq_knowledge_base").insert(batch).execute()
            print(f"Successfully updated {len(faqs)} FAQs")
        else:
            print("No FAQs found to update")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    update_faqs()
