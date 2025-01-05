import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Optional, Union
from datetime import datetime
import json

class OpenAIChat:
    def __init__(self):
        # Tenta carregar as variáveis de ambiente
        load_dotenv()
        
        # Tenta obter a API key primeiro do ambiente, depois do .env
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        # Se não encontrar a API key, orienta o usuário
        if not self.api_key:
            print("API Key não encontrada. Por favor, siga os passos abaixo:")
            print("1. Crie um arquivo .env na raiz do projeto")
            print("2. Adicione sua API key no formato: OPENAI_API_KEY=sua_chave_aqui")
            print("3. Reinicie o script")
            raise ValueError("OPENAI_API_KEY não encontrada")
            
        # Inicializa o cliente OpenAI
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            print(f"Erro ao inicializar cliente OpenAI: {str(e)}")
            raise
            
        # Histórico de conversas
        self.conversation_history: List[Dict[str, str]] = []
        
        # Modelos disponíveis
        self.available_models = [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4',
            'gpt-4-turbo',
            'gpt-3.5-turbo',
            'o1-preview',
            'o1-mini'
        ]
        
        # Configurações padrão
        self.current_config = {
            'model': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'top_p': 1.0,
            'max_tokens': None,
            'presence_penalty': 0,
            'frequency_penalty': 0,
            'stream': True,
            'language': 'pt-br'
        }

        # Mensagens do sistema para cada idioma
        self.system_messages = {
            'pt-br': "Você é um assistente prestativo. Responda sempre em português do Brasil de forma clara e natural.",
            'en': "You are a helpful assistant. Always respond in English in a clear and natural way."
        }

    def create_chat_params(self, messages: List[Dict[str, str]]) -> Dict:
        """Cria os parâmetros para a chamada da API."""
        system_message = {
            "role": "system",
            "content": self.system_messages[self.current_config['language']]
        }
        
        full_messages = [system_message] + messages

        params = {
            "model": self.current_config['model'],
            "messages": full_messages,
            "temperature": self.current_config['temperature'],
            "top_p": self.current_config['top_p'],
            "presence_penalty": self.current_config['presence_penalty'],
            "frequency_penalty": self.current_config['frequency_penalty'],
            "stream": self.current_config['stream']
        }

        if self.current_config['max_tokens'] is not None:
            params["max_tokens"] = self.current_config['max_tokens']

        return params

    def send_message(self, message: str) -> Dict:
        """Envia uma mensagem para a API e retorna a resposta."""
        try:
            # Adiciona a mensagem do usuário ao histórico
            self.conversation_history.append({"role": "user", "content": message})
            
            # Cria a stream de chat
            stream = self.client.chat.completions.create(
                **self.create_chat_params(self.conversation_history)
            )
            
            response_content = ""
            
            # Processa a resposta
            if self.current_config['stream']:
                print("\nAssistente: " if self.current_config['language'] == 'pt-br' else "\nAssistant: ", end="")
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        response_content += content
                print()
            else:
                response_content = stream.choices[0].message.content
                
            # Adiciona a resposta ao histórico
            self.conversation_history.append({
                "role": "assistant",
                "content": response_content
            })

            return {
                'content': response_content,
                'citations': []
            }

        except Exception as e:
            error_msg = "Erro na requisição" if self.current_config['language'] == 'pt-br' else "Request error"
            print(f"{error_msg}: {str(e)}")
            return {'error': str(e)}

    def save_conversation(self, filename: Optional[str] = None) -> None:
        """Salva a conversa em um arquivo JSON."""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'conversation_{timestamp}.json'
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            
            save_msg = "Conversa salva em" if self.current_config['language'] == 'pt-br' else "Conversation saved to"
            print(f"{save_msg} {filename}")
        except Exception as e:
            error_msg = "Erro ao salvar conversa" if self.current_config['language'] == 'pt-br' else "Error saving conversation"
            print(f"{error_msg}: {str(e)}")

    def clear_conversation(self) -> None:
        """Limpa o histórico da conversa."""
        self.conversation_history = []
        clear_msg = "Histórico de conversa limpo" if self.current_config['language'] == 'pt-br' else "Conversation history cleared"
        print(clear_msg)

    def show_current_config(self):
        """Mostra as configurações atuais."""
        title = "\nConfigurações atuais:" if self.current_config['language'] == 'pt-br' else "\nCurrent settings:"
        print(title)
        for key, value in self.current_config.items():
            print(f"{key}: {value}")

    def configure_settings(self):
        """Interface para configurar os parâmetros do chat."""
        try:
            is_ptbr = self.current_config['language'] == 'pt-br'
            
            print("\n=== " + ("Configuração do Chat" if is_ptbr else "Chat Configuration") + " ===")
            print("Pressione Enter para manter o valor atual" if is_ptbr else "Press Enter to keep current value")
            
            # Configuração de idioma
            print("\n" + ("Idiomas disponíveis:" if is_ptbr else "Available languages:"))
            print("1. Português (pt-br)\n2. English (en)")
            lang_choice = input("Escolha o idioma (1-2)" if is_ptbr else "Choose language (1-2): ")
            if lang_choice == '1':
                self.current_config['language'] = 'pt-br'
            elif lang_choice == '2':
                self.current_config['language'] = 'en'
            
            is_ptbr = self.current_config['language'] == 'pt-br'

            # Configuração do modelo
            print(f"\n" + ("Modelos disponíveis:" if is_ptbr else "Available models:"))
            for idx, model in enumerate(self.available_models, 1):
                print(f"{idx}. {model}")
            model_prompt = "Escolha o número do modelo" if is_ptbr else "Choose model number"
            model_choice = input(f"{model_prompt} (atual: {self.current_config['model']}): ")
            if model_choice.isdigit() and 1 <= int(model_choice) <= len(self.available_models):
                self.current_config['model'] = self.available_models[int(model_choice)-1]

            # Configuração de temperatura
            temp_prompt = "Temperature (0-2)" if is_ptbr else "Temperature (0-2)"
            temp = input(f"{temp_prompt} (atual: {self.current_config['temperature']}): ")
            if temp:
                self.current_config['temperature'] = float(temp)

            # Configuração de top_p
            top_p = input(f"Top P (0-1) (atual: {self.current_config['top_p']}): ")
            if top_p:
                self.current_config['top_p'] = float(top_p)

            # Configuração de max_tokens
            tokens_prompt = "Max Tokens" if is_ptbr else "Max Tokens"
            max_tokens = input(f"{tokens_prompt} (atual: {self.current_config['max_tokens']}): ")
            if max_tokens:
                self.current_config['max_tokens'] = int(max_tokens) if max_tokens.lower() != 'none' else None

            # Configuração de streaming
            stream_prompt = "Usar streaming (true/false)" if is_ptbr else "Use streaming (true/false)"
            stream = input(f"{stream_prompt} (atual: {self.current_config['stream']}): ")
            if stream.lower() in ['true', 'false']:
                self.current_config['stream'] = stream.lower() == 'true'

            print("\n" + ("Configurações atualizadas!" if is_ptbr else "Settings updated!"))
            self.show_current_config()
        except Exception as e:
            error_msg = "Erro ao configurar" if is_ptbr else "Configuration error"
            print(f"{error_msg}: {str(e)}")

def run_chat():
    """Função principal que executa o chat."""
    chat = None
    try:
        chat = OpenAIChat()
        is_ptbr = chat.current_config['language'] == 'pt-br'
        
        # Mostra as instruções iniciais
        print("\n=== OpenAI Chat ===")
        print("Comandos disponíveis:" if is_ptbr else "Available commands:")
        print("'config' - " + ("Configurar parâmetros do chat" if is_ptbr else "Configure chat parameters"))
        print("'settings' - " + ("Mostrar configurações atuais" if is_ptbr else "Show current settings"))
        print("'save' - " + ("Salvar conversa" if is_ptbr else "Save conversation"))
        print("'clear' - " + ("Limpar histórico" if is_ptbr else "Clear history"))
        print("'exit' - " + ("Sair" if is_ptbr else "Exit"))
        print("=" * 30)

        # Loop principal do chat
        while True:
            try:
                is_ptbr = chat.current_config['language'] == 'pt-br'
                prompt = "\nVocê: " if is_ptbr else "\nYou: "
                user_input = input(prompt).strip()
                
                # Processa comandos especiais
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'save':
                    chat.save_conversation()
                    continue
                elif user_input.lower() == 'clear':
                    chat.clear_conversation()
                    continue
                elif user_input.lower() == 'config':
                    chat.configure_settings()
                    continue
                elif user_input.lower() == 'settings':
                    chat.show_current_config()
                    continue
                elif not user_input:
                    continue

                # Envia mensagem para a API
                response = chat.send_message(user_input)

                if 'error' in response:
                    error_msg = "Erro" if is_ptbr else "Error"
                    print(f"\n{error_msg}: {response['error']}")
                    continue

                if not chat.current_config['stream']:
                    assistant_msg = "Assistente" if is_ptbr else "Assistant"
                    print(f"\n{assistant_msg}:", response['content'])

            except KeyboardInterrupt:
                print("\nEncerrando o chat...")
                break
            except Exception as e:
                error_msg = "Erro durante a execução" if is_ptbr else "Runtime error"
                print(f"{error_msg}: {str(e)}")
                continue

    except Exception as e:
        # Tratamento de erro inicial
        if chat:
            error_msg = "Erro ao iniciar o chat" if chat.current_config['language'] == 'pt-br' else "Error starting chat"
        else:
            error_msg = "Erro ao iniciar o chat"
        print(f"{error_msg}: {str(e)}")

if __name__ == '__main__':
    run_chat()