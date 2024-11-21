# app.py
from flask import Flask, render_template, request, jsonify
from perplexity_chat import PerplexityChat
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializa o chat como uma variável global
chat = PerplexityChat()

@app.route('/')
def index():
    """
    Rota principal que renderiza a página inicial do chat.
    Passa os modelos disponíveis e a configuração atual para o frontend.
    """
    return render_template(
        'index.html',
        models=chat.get_available_models(),
        config=chat.get_current_config(),
        languages=chat.get_available_languages()
    )

@app.route('/send_message', methods=['POST'])
def send_message():
    """
    Recebe uma mensagem do usuário, envia para a API da Perplexity e retorna a resposta.
    """
    data = request.get_json()
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Mensagem vazia'}), 400

    response = chat.send_message(message)

    if 'error' in response:
        return jsonify({'error': response['error']}), 500

    return jsonify(response), 200

@app.route('/update_config', methods=['POST'])
def update_config():
    """
    Atualiza as configurações do chat com base nos dados recebidos do frontend.
    """
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Nenhuma configuração fornecida.'}), 400

    try:
        # Preparar novo_config com os dados recebidos
        new_config = {}

        # Atualização de idioma
        language = data.get('language')
        if language and language in chat.get_available_languages():
            new_config['language'] = language

        # Atualização de modelo
        model = data.get('model')
        if model and model in chat.get_available_models():
            new_config['model'] = model

        # Atualização de temperature
        temperature = data.get('temperature')
        if temperature is not None:
            temperature = float(temperature)
            if 0 <= temperature <= 2:
                new_config['temperature'] = temperature

        # Atualização de top_p
        top_p = data.get('top_p')
        if top_p is not None:
            top_p = float(top_p)
            if 0 <= top_p <= 1:
                new_config['top_p'] = top_p

        # Atualização de top_k
        top_k = data.get('top_k')
        if top_k is not None:
            top_k = int(top_k)
            if top_k >= 0:
                new_config['top_k'] = top_k

        # Atualização de max_tokens
        max_tokens = data.get('max_tokens')
        if max_tokens is not None:
            if isinstance(max_tokens, int) and max_tokens > 0:
                new_config['max_tokens'] = max_tokens
            elif isinstance(max_tokens, str) and max_tokens.lower() == 'none':
                new_config['max_tokens'] = None

        # Atualização de presence_penalty
        presence_penalty = data.get('presence_penalty')
        if presence_penalty is not None:
            presence_penalty = float(presence_penalty)
            new_config['presence_penalty'] = presence_penalty

        # Atualização de frequency_penalty
        frequency_penalty = data.get('frequency_penalty')
        if frequency_penalty is not None:
            frequency_penalty = float(frequency_penalty)
            new_config['frequency_penalty'] = frequency_penalty

        # Atualização de return_citations
        return_citations = data.get('return_citations')
        if return_citations is not None:
            if isinstance(return_citations, bool):
                new_config['return_citations'] = return_citations
            elif isinstance(return_citations, str):
                new_config['return_citations'] = return_citations.lower() == 'true'

        # Atualização de return_related_questions
        return_related_questions = data.get('return_related_questions')
        if return_related_questions is not None:
            if isinstance(return_related_questions, bool):
                new_config['return_related_questions'] = return_related_questions
            elif isinstance(return_related_questions, str):
                new_config['return_related_questions'] = return_related_questions.lower() == 'true'

        # Atualização de search_recency_filter
        search_recency_filter = data.get('search_recency_filter')
        if search_recency_filter is not None:
            valid_filters = ['month', 'week', 'day', 'hour', None]
            if search_recency_filter in valid_filters or search_recency_filter.lower() == 'none':
                new_config['search_recency_filter'] = search_recency_filter.lower() if search_recency_filter.lower() != 'none' else None

        # Atualizar a configuração no chat
        updated_config = chat.update_config(new_config)

        return jsonify({'status': 'success', 'config': updated_config}), 200

    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Erro ao atualizar a configuração.'}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """
    Limpa o histórico de conversas.
    """
    try:
        message = chat.clear_conversation()
        return jsonify({'status': 'success', 'message': message}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Erro ao limpar o histórico.'}), 500

@app.route('/save_conversation', methods=['POST'])
def save_conversation():
    """
    Salva o histórico de conversas em um arquivo JSON.
    """
    try:
        filename = None
        data = request.get_json()
        if data and 'filename' in data:
            filename = data['filename']

        message = chat.save_conversation(filename)
        return jsonify({'status': 'success', 'message': message, 'filename': filename}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Erro ao salvar a conversa.'}), 500

@app.route('/get_config', methods=['GET'])
def get_config():
    """
    Retorna a configuração atual do chat.
    """
    try:
        config = chat.get_current_config()
        return jsonify({'status': 'success', 'config': config}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Erro ao obter configuração.'}), 500

@app.route('/get_available_languages', methods=['GET'])
def get_available_languages():
    """
    Retorna a lista de idiomas disponíveis.
    """
    try:
        languages = chat.get_available_languages()
        return jsonify({'status': 'success', 'languages': languages}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Erro ao obter idiomas disponíveis.'}), 500

@app.route('/get_available_models', methods=['GET'])
def get_available_models():
    """
    Retorna a lista de modelos disponíveis.
    """
    try:
        models = chat.get_available_models()
        return jsonify({'status': 'success', 'models': models}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Erro ao obter modelos disponíveis.'}), 500

if __name__ == '__main__':
    app.run(debug=True)