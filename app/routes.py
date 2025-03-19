from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from utils.model import chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, MessagesState
from utils.db import get_supabase
import os

load_dotenv()

SYSTEM_PROMPT = """You are Frontlett's customer service chatbot. 
Use the FAQ knowledge base to provide answers to customer questions. 
If the question is not in the FAQ, provide a fallback response like 'Please contact our support team at support@frontlett.com or visit [URL] for more information.'"""

app = FastAPI()

class MessageRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: MessageRequest):
    user_input = request.message.strip().lower()

    if not user_input:
        raise HTTPException(status_code=400, detail="Message is required")

    supabase = get_supabase()

    # Search for matching FAQ
    response = supabase.table('faq_knowledge') \
                        .select('question, answer') \
                        .ilike('question', f'%{user_input}%') \
                        .limit(3) \
                        .execute()

    faq_data = response.data

    if faq_data:
        # Attach the FAQ data as placeholders in the prompt
        faq_context = "\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in faq_data])
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("system", faq_context),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
    else:
        # If no FAQ is found, use fallback URL
        faq_context = "No relevant FAQ found. Please visit [https://www.frontlett.com/support] for more information."
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

    # Add the model to the workflow, connecting it to the start point
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    memory = MemorySaver()

    compiled_app = workflow.compile(checkpointer=memory)

    output = compiled_app.invoke({"messages": [user_input]}, {"configurable": {"thread_id": "abc345"}})

    if "messages" in output and len(output["messages"]) > 0:
        bot_response = output["messages"][-1]['content']
    else:
        bot_response = "No response from the model."

    return {"response": bot_response}

# Start FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.routes:app", host="0.0.0.0", port=6000, reload=True)
