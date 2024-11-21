import os
import json
from typing import List, Dict, Optional, Union
from datetime import datetime
import requests
from dotenv import load_dotenv

class PerplexityChat:
    """
    Classe para interagir com a API da Perplexity AI.
    """
    
    def __init__(self):
        """
        Inicializa a classe PerplexityChat carregando as variáveis de ambiente 
        e configurando os parâmetros padrões.
        """
        load_dotenv()
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY não encontrada no arquivo .env")
        
        self.url = 'https://api.perplexity.ai/chat/completions'
        self.conversation_history: List[Dict[str, str]] = []
        
        self.available_models = [
            'llama-3.1-sonar-small-128k-chat',
            'llama-3.1-sonar-large-128k-chat',
            'llama-3.1-sonar-small-128k-online',
            'llama-3.1-sonar-large-128k-online',
            'llama-3.1-sonar-huge-128k-online'
        ]
        
        # Configurações padrão
        self.current_config: Dict[str, Union[str, float, int, bool, None]] = {
            'model': 'llama-3.1-sonar-small-128k-online',
            'temperature': 0.2,
            'top_p': 0.9,
            'top_k': 0,
            'max_tokens': None,
            'presence_penalty': 0,
            'frequency_penalty': 1,
            'return_citations': True,
            'return_related_questions': False,
            'search_recency_filter': None,
            'language': 'pt-br'  # Idioma padrão
        }

        # Mensagens do sistema para cada idioma
        self.system_messages = {
            'pt-br': "Você é um assistente prestativo. Responda sempre em português do Brasil de forma clara e natural.",
            'en': "You are a helpful assistant. Always respond in English in a clear and natural way."
        }
    
    def create_headers(self) -> Dict[str, str]:
        """
        Cria os cabeçalhos necessários para a requisição à API.

        Returns:
            Dict[str, str]: Cabeçalhos HTTP.
        """
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_request_body(self, messages: List[Dict[str, str]]) -> Dict:
        """
        Cria o corpo da requisição para enviar à API com base nas mensagens.

        Args:
            messages (List[Dict[str, str]]): Histórico de mensagens da conversa.

        Returns:
            Dict: Corpo da requisição formatado.
        """
        # Adiciona a mensagem do sistema no início da conversa
        system_message = {
            "role": "system",
            "content": self.system_messages.get(self.current_config['language'], self.system_messages['en'])
        }
        
        full_messages = [system_message] + messages

        body = {
            "model": self.current_config['model'],
            "messages": full_messages,
            "temperature": self.current_config['temperature'],
            "top_p": self.current_config['top_p'],
            "top_k": self.current_config['top_k'],
            "presence_penalty": self.current_config['presence_penalty'],
            "frequency_penalty": self.current_config['frequency_penalty'],
            "return_citations": self.current_config['return_citations'],
            "return_related_questions": self.current_config['return_related_questions']
        }

        if self.current_config['max_tokens'] is not None:
            body["max_tokens"] = self.current_config['max_tokens']
            
        if self.current_config['search_recency_filter']:
            body["search_recency_filter"] = self.current_config['search_recency_filter']

        return body
    
    def send_message(self, message: str) -> Dict[str, Union[str, List[Dict[str, Union[int, str]]], None]]:
        """
        Envia uma mensagem para a API da Perplexity e retorna a resposta.

        Args:
            message (str): A mensagem do usuário.

        Returns:
            Dict: Contém o conteúdo da resposta e citações, se houver.
        """
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            response = requests.post(
                self.url,
                headers=self.create_headers(),
                data=json.dumps(self.create_request_body(self.conversation_history))
            )
            
            response.raise_for_status()
            result = response.json()
            
            assistant_message = result['choices'][0]['message']
            self.conversation_history.append(assistant_message)

            # Adaptar as citações para incluir índice e URL
            citations = []
            for idx, citation in enumerate(assistant_message.get('citations', []), start=1):
                # Ajustar conforme a estrutura real de 'citation'
                citations.append({"index": idx, "url": citation})
            
            return {
                'content': assistant_message.get('content', ''),
                'citations': citations or None
            }
        
        except requests.exceptions.RequestException as e:
            # Log de erro pode ser aprimorado conforme necessário
            error_msg = f"Erro na requisição: {str(e)}"
            return {'error': error_msg}
    
    def save_conversation(self, filename: Optional[str] = None) -> str:
        """
        Salva o histórico da conversa em um arquivo JSON.

        Args:
            filename (Optional[str]): Nome do arquivo. Se None, usa timestamp.

        Returns:
            str: Mensagem indicando onde a conversa foi salva.
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'conversation_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
        
        return f"Conversa salva em {filename}"
    
    def clear_conversation(self) -> str:
        """
        Limpa o histórico da conversa.

        Returns:
            str: Mensagem de confirmação.
        """
        self.conversation_history = []
        return "Histórico de conversa limpo"
    
    def get_current_config(self) -> Dict[str, Union[str, float, int, bool, None]]:
        """
        Retorna a configuração atual do chat.

        Returns:
            Dict: Configurações atuais.
        """
        return self.current_config.copy()
    
    def update_config(self, new_config: Dict[str, Union[str, float, int, bool, None]]) -> Dict[str, Union[str, float, int, bool, None]]:
        """
        Atualiza as configurações do chat com base no dicionário fornecido.

        Args:
            new_config (Dict): Novas configurações a serem atualizadas.

        Returns:
            Dict: Configurações atualizadas.
        """
        for key, value in new_config.items():
            if key in self.current_config:
                if key == 'language' and value not in self.system_messages:
                    continue  # Ignora idiomas não suportados
                self.current_config[key] = value
        return self.get_current_config()
    
    def get_available_languages(self) -> List[str]:
        """
        Retorna a lista de idiomas disponíveis.

        Returns:
            List[str]: Idiomas disponíveis.
        """
        return list(self.system_messages.keys())
    
    def get_available_models(self) -> List[str]:
        """
        Retorna a lista de modelos disponíveis.

        Returns:
            List[str]: Modelos disponíveis.
        """
        return self.available_models.copy()