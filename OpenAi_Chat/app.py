from flask import Flask, render_template, request, jsonify, session
from openai_chat import OpenAIChat
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializa o chat como uma variável global
chat = None
try:
    chat = OpenAIChat()
except Exception as e:
    print(f"Erro ao inicializar o chat: {str(e)}")

@app.route('/')
def index():
    """Rota principal que renderiza a página inicial."""
    if not chat:
        return render_template('error.html', 
                             error="Erro ao inicializar o chat. Verifique sua API key no arquivo .env")
    
    if 'conversation_history' not in session:
        session['conversation_history'] = []
        
    return render_template('index.html', 
                         models=chat.available_models,
                         config=chat.current_config)

@app.route('/send_message', methods=['POST'])
def send_message():
    """Endpoint para enviar mensagens para o chat."""
    if not chat:
        return jsonify({'error': 'Chat não inicializado'})
    
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Mensagem vazia'})
    
    try:
        response = chat.send_message(message)
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/update_config', methods=['POST'])
def update_config():
    """Endpoint para atualizar as configurações do chat."""
    if not chat:
        return jsonify({'error': 'Chat não inicializado'})
    
    try:
        new_config = request.json
        
        # Validação e conversão dos tipos de dados
        if 'temperature' in new_config:
            new_config['temperature'] = float(new_config['temperature'])
        if 'top_p' in new_config:
            new_config['top_p'] = float(new_config['top_p'])
        if 'max_tokens' in new_config:
            new_config['max_tokens'] = int(new_config['max_tokens']) if new_config['max_tokens'] else None
        if 'stream' in new_config:
            new_config['stream'] = new_config['stream'].lower() == 'true'
            
        # Atualiza a configuração
        chat.current_config.update(new_config)
        
        return jsonify({
            'status': 'success',
            'config': chat.current_config
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Endpoint para limpar o histórico de conversas."""
    if not chat:
        return jsonify({'error': 'Chat não inicializado'})
    
    try:
        chat.clear_conversation()
        session['conversation_history'] = []
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/save_conversation', methods=['POST'])
def save_conversation():
    """Endpoint para salvar a conversa em arquivo."""
    if not chat:
        return jsonify({'error': 'Chat não inicializado'})
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'conversation_{timestamp}.json'
        chat.save_conversation(filename)
        return jsonify({
            'status': 'success',
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)