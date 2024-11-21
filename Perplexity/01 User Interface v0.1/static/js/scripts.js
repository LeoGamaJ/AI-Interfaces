// scripts.js

document.addEventListener("DOMContentLoaded", () => {
    // Element References
    const messagesContainer = document.getElementById('messagesContainer');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const configForm = document.getElementById('configForm');

    // Verify that all necessary elements are present
    if (!messagesContainer || !chatForm || !messageInput || !configForm) {
        console.error('One or more essential elements are missing from the DOM.');
        return;
    }

    // Automatically adjust the height of the message input field
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = `${messageInput.scrollHeight}px`;
    });

    // Submit the chat form when Enter is pressed without Shift
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevent adding a new line
            chatForm.dispatchEvent(new Event('submit')); // Trigger form submission
        }
    });

    /**
     * Appends a message to the chat container.
     * @param {string} message - The message content.
     * @param {boolean} isUser - Indicates if the message is from the user.
     * @param {Array} citations - Optional citations associated with the message.
     */
    function appendMessage(message, isUser, citations = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        // Ensure message is a string to prevent errors
        message = message || '';

        if (!isUser) {
            message = removeNumericReferences(message);
            message = renderMarkdown(message);

            if (citations.length > 0) {
                message = linkifyCitations(message, citations);
            }
        } else {
            // For user messages, escape HTML to prevent XSS
            message = escapeHTML(message);
        }

        messageDiv.innerHTML = message;

        // Append the message to the container
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Add copy buttons to code blocks if present
        messageDiv.querySelectorAll('pre').forEach(pre => {
            // Ensure a copy button isn't already present
            if (!pre.nextElementSibling || !pre.nextElementSibling.classList.contains('copy-button')) {
                const copyButton = document.createElement('button');
                copyButton.className = 'copy-button btn btn-secondary btn-sm';
                copyButton.style.marginTop = '5px';
                copyButton.innerText = 'Copy';
                copyButton.type = 'button'; // Prevent form submission on click

                copyButton.onclick = () => {
                    navigator.clipboard.writeText(pre.innerText).then(() => {
                        showToast(getLocalizedString('code_copied'), 'success');
                    }).catch(err => {
                        showToast(`${getLocalizedString('copy_error')}: ${err}`, 'error');
                    });
                };

                pre.parentNode.insertBefore(copyButton, pre.nextSibling);
            }
        });

        // Highlight all code blocks within the new message
        messageDiv.querySelectorAll('pre code').forEach((block) => {
            if (hljs) {
                hljs.highlightElement(block);
            } else {
                console.warn('Highlight.js não está carregado.');
            }
        });
    }

    /**
     * Removes numeric references (e.g., [1], [2]) from the text.
     * @param {string} text - The input text.
     * @returns {string} - The cleaned text.
     */
    function removeNumericReferences(text) {
        return text.replace(/\[\d+\]/g, '');
    }

    /**
     * Converts Markdown text to HTML.
     * @param {string} text - The Markdown text.
     * @returns {string} - The converted HTML.
     */
    function renderMarkdown(text) {
        if (window.showdown) {
            const converter = new showdown.Converter();
            return converter.makeHtml(text);
        } else {
            console.warn('Showdown.js não está carregado.');
            return text;
        }
    }

    /**
     * Converts citation placeholders in the text to clickable links.
     * @param {string} text - The text containing citation placeholders.
     * @param {Array} citations - Array of citation objects with index and url.
     * @returns {string} - The text with clickable citation links.
     */
    function linkifyCitations(text, citations) {
        citations.forEach(citation => {
            const regex = new RegExp(`\\[${citation.index}\\]`, 'g');
            const link = `<a href="${citation.url}" target="_blank">[${citation.index}]</a>`;
            text = text.replace(regex, link);
        });
        return text;
    }

    /**
     * Escapes HTML characters to prevent XSS attacks.
     * @param {string} text - The input text.
     * @returns {string} - The escaped text.
     */
    function escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Displays a toast notification.
     * @param {string} message - The message to display.
     * @param {string} type - The type of toast ('success' or 'error').
     */
    function showToast(message, type) {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            console.error('Container for toasts (.toast-container) not found.');
            return;
        }

        const toastDiv = document.createElement('div');
        toastDiv.className = `custom-toast toast-${type}`;

        const toastIcon = document.createElement('i');
        toastIcon.className = `bi ${type === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'} toast-icon`;

        const toastMessage = document.createElement('span');
        toastMessage.innerText = message;

        toastDiv.appendChild(toastIcon);
        toastDiv.appendChild(toastMessage);

        toastContainer.appendChild(toastDiv);

        // Automatically remove the toast after 3 seconds
        setTimeout(() => {
            toastDiv.classList.add('fade-out');
            toastDiv.addEventListener('animationend', () => {
                toastDiv.remove();
            });
        }, 3000);
    }

    /**
     * Handles the submission of the chat form.
     */
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;

        // Append the user's message to the chat
        appendMessage(message, true);
        messageInput.value = '';
        messageInput.style.height = 'auto'; // Reset the height of the input field

        // Optionally, show a typing indicator
        appendTypingIndicator();

        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            const data = await response.json();
            // Remove the typing indicator
            removeTypingIndicator();

            if (data.error) {
                appendMessage(`${getLocalizedString('error_prefix')} ${data.error}`, false);
                showToast(`${getLocalizedString('error_prefix')} ${data.error}`, 'error');
            } else {
                const content = data.content || '';
                const citations = data.citations || [];
                appendMessage(content, false, citations);
                showToast(getLocalizedString('message_sent'), 'success');
            }
        } catch (error) {
            // Remove the typing indicator
            removeTypingIndicator();
            appendMessage(`${getLocalizedString('send_error')} ${error.message}`, false);
            showToast(`${getLocalizedString('send_error')} ${error.message}`, 'error');
            console.error('Erro ao enviar mensagem:', error);
        }
    });

    /**
     * Handles the submission of the configuration form.
     */
    configForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(configForm);
        const config = {};

        // Convert FormData entries to key-value pairs
        formData.forEach((value, key) => {
            if (key === 'return_citations' || key === 'return_related_questions' ||
                key === 'presence_penalty' || key === 'frequency_penalty') {
                config[key] = value === 'on' ? true : false;
            } else {
                config[key] = value;
            }
        });

        // Handle 'max_tokens' which can be empty
        if (config.max_tokens === '') {
            config.max_tokens = null;
        } else {
            config.max_tokens = parseInt(config.max_tokens, 10);
        }

        // Handle numeric fields
        if (config.temperature !== undefined && config.temperature !== null) {
            config.temperature = parseFloat(config.temperature);
        }

        if (config.top_p !== undefined && config.top_p !== null) {
            config.top_p = parseFloat(config.top_p);
        }

        if (config.top_k !== undefined && config.top_k !== null) {
            config.top_k = parseInt(config.top_k, 10);
        }

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
                showToast(getLocalizedString('config_success'), 'success');
                // Optionally, reload the page to apply new settings
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                showToast(`${getLocalizedString('config_error')}: ${data.message}`, 'error');
                console.error('Erro ao atualizar configurações:', data.message);
            }
        } catch (error) {
            showToast(`${getLocalizedString('config_error')}: ${error.message}`, 'error');
            console.error('Erro ao atualizar configurações:', error);
        }
    });

    /**
     * Toggles the configuration panel.
     */
    window.toggleConfig = function() {
        const configCollapse = document.getElementById('configCollapse');
        if (configCollapse) {
            const bsCollapse = new bootstrap.Collapse(configCollapse, {
                toggle: false
            });
            bsCollapse.toggle();
        } else {
            console.error('Elemento #configCollapse não encontrado.');
        }
    }

    /**
     * Clears the chat history.
     */
    window.clearHistory = async function() {
        const confirmation = confirm(getLocalizedString('confirm_clear_history'));
        if (!confirmation) return;

        try {
            const response = await fetch('/clear_history', {
                method: 'POST',
            });
            const data = await response.json();
            if (data.status === 'success') {
                messagesContainer.innerHTML = '';
                showToast(getLocalizedString('history_cleared'), 'success');
            } else {
                showToast(`${getLocalizedString('clear_error')}: ${data.message}`, 'error');
                console.error('Erro ao limpar histórico:', data.message);
            }
        } catch (error) {
            showToast(`${getLocalizedString('clear_error')}: ${error.message}`, 'error');
            console.error('Erro ao limpar histórico:', error);
        }
    }

    /**
     * Saves the current conversation.
     */
    window.saveConversation = async function() {
        const filename = prompt(getLocalizedString('prompt_save_conversation'));
        if (!filename) return;

        try {
            const response = await fetch('/save_conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename }),
            });
            const data = await response.json();
            if (data.status === 'success') {
                showToast(`${getLocalizedString('conversation_saved')} ${data.filename}`, 'success');
            } else {
                showToast(`${getLocalizedString('save_error')}: ${data.message}`, 'error');
                console.error('Erro ao salvar conversa:', data.message);
            }
        } catch (error) {
            showToast(`${getLocalizedString('save_error')}: ${error.message}`, 'error');
            console.error('Erro ao salvar conversa:', error);
        }
    }

    /**
     * Appends a typing indicator to the chat.
     */
    function appendTypingIndicator() {
        if (document.getElementById('typingIndicator')) return; // Prevent multiple indicators

        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typingDiv.appendChild(dot);
        }

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Removes the typing indicator from the chat.
     */
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    /**
     * Retrieves localized strings based on the current language.
     * @param {string} key - The key for the desired string.
     * @returns {string} - The localized string.
     */
    function getLocalizedString(key) {
        const language = document.documentElement.lang || 'pt-br';
        const strings = {
            'pt-br': {
                'confirm_clear_history': 'Tem certeza que deseja limpar o histórico?',
                'prompt_save_conversation': 'Digite o nome do arquivo para salvar a conversa:',
                'code_copied': 'Código copiado para a área de transferência!',
                'copy_error': 'Erro ao copiar código',
                'message_sent': 'Mensagem enviada com sucesso!',
                'send_error': 'Erro ao enviar mensagem:',
                'config_success': 'Configurações atualizadas com sucesso!',
                'config_error': 'Erro ao atualizar configurações',
                'history_cleared': 'Histórico limpo com sucesso!',
                'clear_error': 'Erro ao limpar histórico',
                'conversation_saved': 'Conversa salva com sucesso! Arquivo:',
                'save_error': 'Erro ao salvar conversa',
            },
            'en': {
                'confirm_clear_history': 'Are you sure you want to clear the history?',
                'prompt_save_conversation': 'Enter the filename to save the conversation:',
                'code_copied': 'Code copied to clipboard!',
                'copy_error': 'Error copying code',
                'message_sent': 'Message sent successfully!',
                'send_error': 'Error sending message:',
                'config_success': 'Settings updated successfully!',
                'config_error': 'Error updating settings',
                'history_cleared': 'History cleared successfully!',
                'clear_error': 'Error clearing history',
                'conversation_saved': 'Conversation saved successfully! File:',
                'save_error': 'Error saving conversation',
            }
        };

        return strings[language] ? strings[language][key] || key : key;
    }
});