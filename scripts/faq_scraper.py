# scripts/faq_scraper.py
import sys
import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from supabase import create_client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simple_embed(text: str) -> list:
    """Basic embedding fallback (for MVP testing)"""
    return [len(text)] * 384

def update_faqs():
    try:
        # Load environment variables for Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials in environment variables")

        supabase = create_client(supabase_url, supabase_key)

        # Configure Selenium / ChromeDriver
        faq_home_url = "https://www.frontlett.com"
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        # Initialize driver
        driver = webdriver.Chrome(options=options)
        driver.get(faq_home_url)
        time.sleep(5)  # Let the homepage load

        # 1) Attempt to find the FAQ link by link text (adjust text as needed)
        # For example, if the top nav has a link <a href="#">FAQ</a>
        try:
            faq_link = driver.find_element(By.LINK_TEXT, "FAQ")
            faq_link.click()
            time.sleep(5)  # Wait for FAQ content to load
        except NoSuchElementException:
            print("Could not find a link with text 'FAQ'. Trying partial link or other selectors.")
            # Optionally try partial link text or a different approach:
            # faq_link = driver.find_element(By.PARTIAL_LINK_TEXT, "FAQ")
            # faq_link.click()
            # time.sleep(5)

        # Now the page should have the FAQ content
        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "html.parser")

        # Print snippet to verify we have the FAQ in the HTML
        print("Fetched HTML snippet:", soup.prettify()[:500])

        # 2) Select the FAQ elements
        # Inspect the actual DOM to identify the correct container or classes
        # Example placeholders:
        # e.g. <div class="faq-item"> <h3>Question</h3> <p>Answer</p> </div>
        faq_items = soup.select("div.faq-item")
        if not faq_items:
            raise ValueError("No FAQ items found - adjust the selectors to match the actual page structure.")

        faqs = []
        for item in faq_items:
            try:
                # Example placeholders for question/answer
                question_el = item.select_one("h3, h4, .faq-question")
                answer_el = item.select_one("p, .faq-answer")

                # If either is missing, skip
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
                print(f"Skipping item due to error: {str(e)}")
                continue

        if faqs:
            # Clear existing FAQs
            supabase.table("faq_knowledge_base").delete().neq("id", "0").execute()

            # Batch-insert new data
            batch_size = 10
            for i in range(0, len(faqs), batch_size):
                batch = faqs[i : i + batch_size]
                supabase.table("faq_knowledge_base").insert(batch).execute()

            print(f"Successfully updated {len(faqs)} FAQs")
        else:
            print("No FAQs found to update")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    update_faqs()
