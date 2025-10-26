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
     * Return formatted timestamp (HH:MM AM/PM).
     */
    function formatTimestamp() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

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

        // Timestamp
        const timestamp = document.createElement('span');
        timestamp.classList.add('timestamp');
        timestamp.textContent = formatTimestamp();
        messageElement.appendChild(timestamp);

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

    function setBotResponse(response, type = "normal") {
        let botHtml;
        
        if (type === "inappropriate") {
            botHtml = '<p class="botText warning"><span>' + response + '</span></p>';
        } else {
            botHtml = '<p class="botText"><span>' + response + '</span></p>';
        }
        
        $("#chatbox").append(botHtml);
        document.getElementById("chat-bar-bottom").scrollIntoView(true);
    }

    /*
      Robustly find the chat input and send button (matches common ids used in many templates).
      Adjust the id strings below if your index.html uses different ids.
    */
    function getInputElement() {
        return document.getElementById('userInput')
            || document.getElementById('textInput')
            || document.querySelector('#chat-bar-bottom input[type="text"]')
            || document.querySelector('#chat-bar-bottom textarea')
            || document.querySelector('input[type="text"]');
    }

    function getSendButton() {
        return document.getElementById('sendButton')
            || document.getElementById('send')
            || document.querySelector('#chat-bar-bottom button')
            || document.querySelector('button[type="submit"]');
    }

    function disableInput() {
        const input = getInputElement();
        const btn = getSendButton();
        if (input) {
            input.disabled = true;
            input.dataset.origPlaceholder = input.placeholder || '';
            input.placeholder = 'Waiting for bot response...';
        }
        if (btn) btn.disabled = true;
    }

    function enableInput() {
        const input = getInputElement();
        const btn = getSendButton();
        if (input) {
            input.disabled = false;
            input.placeholder = input.dataset.origPlaceholder || '';
            try { input.focus(); } catch (e) {}
        }
        if (btn) btn.disabled = false;
    }

    // Prevent sending while disabled (handles Enter key)
    document.addEventListener('keydown', function (e) {
        const input = getInputElement();
        if (!input) return;
        if ((e.key === 'Enter' || e.keyCode === 13) && input.disabled) {
            e.preventDefault();
        }
    }, true);

    // Replace your existing getHardResponse / request-sending logic with this pattern
    function getHardResponse(userText) {
        // disable input while request is in-flight
        disableInput();

        let xhr = new XMLHttpRequest();
        xhr.open("POST", "/get", true);
        xhr.setRequestHeader("Content-Type", "application/json");

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                try {
                    if (xhr.status === 200) {
                        let response = JSON.parse(xhr.responseText);
                        // expected response format: { response: "text", status: "success" }
                        setBotResponse(response.response);
                    } else if (xhr.status === 401) {
                        setBotResponse("Authentication failed. Please check API key.", "error");
                    } else {
                        setBotResponse("Error: Unable to connect to the server", "error");
                    }
                } catch (err) {
                    setBotResponse("Error: Invalid server response", "error");
                } finally {
                    // re-enable input after bot has responded / error handled
                    enableInput();
                }
            }
        };

        xhr.onerror = function () {
            setBotResponse("Network error. Please try again.", "error");
            enableInput();
        };

        xhr.send(JSON.stringify({
            message: userText
            // include api_key here if your frontend sends one
            // , api_key: "codec_technologies_2023"
        }));
    }
});