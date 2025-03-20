from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.utils.model import chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, MessagesState
from app.utils.db import get_supabase
import os
import sys

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# System prompt used for general queries
SYSTEM_PROMPT = """You are Frontlett's customer service chatbot.
Use the FAQ knowledge base to provide accurate and concise answers to customer questions.
If the question is not directly found in the FAQ, provide a summary of Frontlett's business model, highlighting key services and functionalities.
Include a link to the support section if you do not have answers to the question (https://www.frontlett.com/support) if further details are needed."""

# FastAPI app initialization
app = FastAPI()

# Request model for user input
class MessageRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"message": "Chatbot is working"}

@app.post("/chat")
async def chat(request: MessageRequest):
    user_input = request.message.strip().lower()

    if not user_input:
        raise HTTPException(status_code=400, detail="Message is required")

    supabase = get_supabase()

    # Check if the query is a general inquiry about what Frontlett does.
    if "what do you do" in user_input or "what is frontlett" in user_input:
        # Retrieve all FAQs as context for a business summary
        all_faq_response = supabase.table('faq_knowledge').select('question, answer').execute()
        all_faq_data = all_faq_response.data or []
        faq_context = "\n".join(
            [f"Q: {faq['question']}\nA: {faq['answer']}" for faq in all_faq_data]
        )
        # Build a system prompt that instructs the model to summarize Frontlett's business model
        business_summary_prompt = (
            "Based on the following FAQ information, provide a concise summary of what Frontlett does, "
            "highlighting our collaborative 'Virtualting' work model, key services, and core functionalities. "
            "Include a link to our support page (https://www.frontlett.com/support) for more details.\n"
        )
        combined_context = business_summary_prompt + faq_context
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("system", combined_context),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
    else:
        # For more specific queries, try to retrieve matching FAQs
        response = supabase.table('faq_knowledge') \
                           .select('question, answer') \
                           .ilike('question', f'%{user_input}%') \
                           .limit(3) \
                           .execute()
        faq_data = response.data

        if faq_data:
            faq_context = "\n".join(
                [f"Q: {faq['question']}\nA: {faq['answer']}" for faq in faq_data]
            )
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPT),
                    ("system", faq_context),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
        else:
            # If no FAQs match, fall back to including all FAQs as context
            all_faq_response = supabase.table('faq_knowledge').select('question, answer').execute()
            all_faq_data = all_faq_response.data or []
            faq_context = "\n".join(
                [f"Q: {faq['question']}\nA: {faq['answer']}" for faq in all_faq_data]
            )
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPT),
                    ("system", faq_context),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )

    # Initialize LangChain workflow
    workflow = StateGraph(state_schema=MessagesState)
    
    def call_model(state: MessagesState):
        # Generate the prompt for the model using the current state
        prompt = prompt_template.invoke(state)
        
        model= chat_model()
        response = model.invoke(prompt)
        return {"messages": response}

    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)
    memory = MemorySaver()
    compiled_app = workflow.compile(checkpointer=memory)

    # Pass the user input as the initial message
    output = compiled_app.invoke({"messages": [user_input]}, {"configurable": {"thread_id": "abc345"}})

    # Extract the 'content' from the response (from the last message)
    if "messages" in output and len(output["messages"]) > 0:
        # Access the 'content' from the last message (AIMessage object)
        response_data = output["messages"][-1]
        
        # Directly access the content of the AIMessage object
        if hasattr(response_data, 'content'):
            bot_response = response_data.content
        else:
            bot_response = "No content available"
    else:
        bot_response = "You can speak to a customer care on +234704440000222"


    return {"response": bot_response}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app/routes:app", host="0.0.0.0", port=8080, reload=True)
