from flask import Blueprint, request, jsonify
from app.utils.db import get_supabase

bp = Blueprint('chat', __name__)

@bp.route('/chat', methods=['POST'])
def handle_chat():
    data = request.get_json()
    user_input = data.get('message', '').strip().lower()
    
    if not user_input:
        return jsonify({"error": "Empty message"}), 400
    
    supabase = get_supabase()
    
    # Search for matching FAQ
    response = supabase.table('faq_knowledge') \
                     .select('answer') \
                     .ilike('question', f'%{user_input}%') \
                     .limit(1) \
                     .execute()
    
    if response.data:
        return jsonify({"response": response.data[0]['answer']})
    else:
        return jsonify({"response": "Please contact our support team at support@frontlett.com for further assistance."})