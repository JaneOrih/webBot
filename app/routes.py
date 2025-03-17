from flask import Blueprint, request, jsonify, render_template
from flask_caching import Cache
from supabase import create_client
from groq import Groq
from app.utils.embeddings import get_embedding
from app.utils.faq_processor import get_faq_context
import os
import datetime
import numpy as np

bp = Blueprint('main', __name__)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Initialize clients
def init_clients(app):
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None
    app.config['supabase'] = supabase
    app.config['groq_client'] = groq_client
    cache.init_app(app)

@bp.route('/')
def home():
    return render_template('chat.html')

@bp.route('/api/chat', methods=['POST'])
def chat_handler():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id', f'sess-{datetime.datetime.now().timestamp()}')

    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    # 1. Check for human handoff
    if any(trigger in user_message.lower() for trigger in ['human', 'agent', 'representative']):
        log_conversation(session_id, user_message, None, True)
        return jsonify({'response': 'Connecting you to a human agent...', 'handoff': True})

    # 2. Cache check
    cached_response = cache.get(user_message)
    if cached_response:
        return jsonify({'response': cached_response, 'source': 'cache'})

    # 3. FAQ Context Retrieval
    faq_context = get_faq_context(user_message)
    system_prompt = build_system_prompt(faq_context)

    # 4. Generate Response
    try:
        response = generate_groq_response(system_prompt, user_message)
        cache.set(user_message, response)
        log_conversation(session_id, user_message, response)
        return jsonify({'response': response, 'source': 'model'})
    except Exception as e:
        log_conversation(session_id, user_message, str(e), is_error=True)
        return jsonify({'response': 'Apologies, I'm having technical difficulties. Please try again.', 'error': True})

def build_system_prompt(faq_context):
    base_prompt = """You are Frontlett's AI assistant specializing in:
- Web/Mobile Development (React, Django, Flutter)
- Digital Marketing Strategies
- UI/UX Design Services"""
    
    if faq_context:
        return f"{base_prompt}\n\nFAQ CONTEXT:\n{faq_context}"
    return base_prompt

def generate_groq_response(system_prompt, user_message):
    client = current_app.config['groq_client']
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ],
        temperature=0.3,
        max_tokens=150
    )
    return response.choices[0].message.content

def log_conversation(session_id, user_message, bot_response, is_handoff=False, is_error=False):
    supabase = current_app.config['supabase']
    supabase.table('conversations').insert({
        'session_id': session_id,
        'user_message': user_message,
        'bot_response': bot_response,
        'is_handoff': is_handoff,
        'is_error': is_error
    }).execute()