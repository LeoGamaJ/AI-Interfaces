// scripts.js

document.addEventListener("DOMContentLoaded", () => {
    const messagesContainer = document.getElementById('messagesContainer');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const configForm = document.getElementById('configForm');

    function appendMessage(message, isUser, citations = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;

        if (!isUser) {
            // Remover referências numéricas como [1][2][5] do texto
            message = removeNumericReferences(message);

            // Processar o Markdown e citar links
            message = renderMarkdown(message);
            if (citations.length > 0) {
                message = linkifyCitations(message, citations);
            }
        }
        messageDiv.innerHTML = message;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    function removeNumericReferences(text) {
        // Remove padrões de referências numéricas [n] onde n é um número entre colchetes
        return text.replace(/\[\d+\]/g, '');
    }

    function renderMarkdown(text) {
        const converter = new showdown.Converter();
        return converter.makeHtml(text);
    }

    function linkifyCitations(text, citations) {
        citations.forEach(citation => {
            const regex = new RegExp(`\\[${citation.index}\\]`, 'g');
            const link = `<a href="${citation.url}" target="_blank">[${citation.index}]</a>`;
            text = text.replace(regex, link);
        });
        return text;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;

        appendMessage(message, true);
        messageInput.value = '';

        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            const data = await response.json();
            if (data.error) {
                appendMessage(`Erro: ${data.error}`, false);
            } else {
                appendMessage(data.content, false, data.citations);
            }
        } catch (error) {
            appendMessage(`Erro ao enviar mensagem: ${error.message}`, false);
        }
    });

    configForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(configForm);
        const config = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/update_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config),
            });

            const data = await response.json();
            if (data.status === 'success') {
                alert('Configurações atualizadas com sucesso!');
            } else {
                alert(`Erro ao atualizar configurações: ${data.message}`);
            }
        } catch (error) {
            alert(`Erro ao atualizar configurações: ${error.message}`);
        }
    });

    window.toggleConfig = function() {
        const configCollapse = document.getElementById('configCollapse');
        const bsCollapse = new bootstrap.Collapse(configCollapse, {
            toggle: false
        });
        bsCollapse.toggle();
    }

    window.clearHistory = async function() {
        if (!confirm('Tem certeza que deseja limpar o histórico?')) return;

        try {
            const response = await fetch('/clear_history', {
                method: 'POST',
            });
            const data = await response.json();
            if (data.status === 'success') {
                messagesContainer.innerHTML = '';
                alert('Histórico limpo com sucesso!');
            }
        } catch (error) {
            alert(`Erro ao limpar histórico: ${error.message}`);
        }
    }

    window.saveConversation = async function() {
        try {
            const response = await fetch('/save_conversation', {
                method: 'POST',
            });
            const data = await response.json();
            if (data.status === 'success') {
                alert(`Conversa salva com sucesso! Arquivo: ${data.filename}`);
            }
        } catch (error) {
            alert(`Erro ao salvar conversa: ${error.message}`);
        }
    }
});