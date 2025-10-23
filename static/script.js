document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatWindow = document.getElementById('chat-window');

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault(); // Stop the form from submitting normally

        const userMessage = userInput.value.trim();
        if (userMessage === '') {
            return; // Don't send empty messages
        }

        // 1. Display User Message
        appendMessage(userMessage, 'user');

        // 2. Clear input
        userInput.value = '';

        // 3. Send message to Python backend API
        setTimeout(() => {
            sendMessageToBackend(userMessage);
        }, 800); // Wait for 0.8 seconds to show loading state
    });

    /**
     * Creates and appends a new message bubble to the chat window.
     * @param {string} text - The message content.
     * @param {string} sender - 'user' or 'bot'.
     */
    function appendMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(`${sender}-message`);
        
        const paragraph = document.createElement('p');
        paragraph.textContent = text;
        messageElement.appendChild(paragraph);

        chatWindow.appendChild(messageElement);
        
        // Scroll to the latest message
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    /**
     * Sends the user message to the Python backend API and handles the response.
     * @param {string} userText - The user's input text.
     */
    function sendMessageToBackend(userText) {
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('message', 'bot-message', 'typing-indicator');
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        chatWindow.appendChild(typingIndicator);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        
        // Send request to backend
        fetch('/get', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userText
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            chatWindow.removeChild(typingIndicator);
            
            // Display bot response
            appendMessage(data.response, 'bot');
        })
        .catch(error => {
            // Remove typing indicator
            chatWindow.removeChild(typingIndicator);
            
            // Display error message
            appendMessage("Sorry, I'm having trouble connecting to my brain right now. Please try again later.", 'bot');
            console.error('Error:', error);
        });
    }
});