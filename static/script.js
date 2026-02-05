document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatContainer = document.getElementById('chat-container');
    const welcomeMessage = document.querySelector('.welcome-message');
    const themeToggle = document.getElementById('theme-toggle');

    let isWaiting = false;

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        themeToggle.textContent = newTheme === 'light' ? '☀️' : '🌙';
    });

    // Suggestion Chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            userInput.value = chip.textContent;
            handleSubmit();
        });
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleSubmit();
    });

    async function handleSubmit() {
        const query = userInput.value.trim();
        if (!query || isWaiting) return;

        // Hide welcome message on first chat
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }

        // Add User Message
        addMessage(query, 'user');
        userInput.value = '';
        isWaiting = true;

        // Show Loading State (temporary bot message)
        const loadingId = addMessage('Thinking...', 'bot', true);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            // Remove loading message
            removeMessage(loadingId);

            // Add Bot Message with Sources and Metrics
            addMessage(data.answer, 'bot', false, data.sources, {
                accuracy: data.accuracy,
                precision: data.precision,
                confidence: data.confidence
            });

        } catch (error) {
            console.error('Error:', error);
            removeMessage(loadingId);
            addMessage('Sorry, something went wrong. Please try again.', 'bot');
        } finally {
            isWaiting = false;
        }
    }

    function addMessage(text, sender, isLoading = false, sources = [], metrics = null) {
        const msgWrapper = document.createElement('div');
        msgWrapper.classList.add('message-wrapper', `${sender}-wrapper`);
        if (isLoading) msgWrapper.id = `msg-${Date.now()}`;

        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', `${sender}-message`);

        // Convert newlines to <br> for bot messages
        const formattedText = text.replace(/\n/g, '<br>');

        let htmlContent = `<div class="message-content">${formattedText}</div>`;

        if (sources && sources.length > 0) {
            htmlContent += `<div class="source-container"><div class="source-title">References:</div>`;
            const uniqueSources = [...new Set(sources.map(s => s.source))];
            uniqueSources.forEach(src => {
                const filename = src.split('/').pop().split('\\').pop();
                htmlContent += `<a href="/files/${filename}" target="_blank" class="source-link">📄 ${filename}</a>`;
            });
            htmlContent += `</div>`;
        }

        msgDiv.innerHTML = htmlContent;
        msgWrapper.appendChild(msgDiv);

        // Add Metrics on the right side
        if (metrics && sender === 'bot') {
            const metricsDiv = document.createElement('div');
            metricsDiv.classList.add('metrics-panel');

            const getScoreClass = (val) => val > 0.8 ? 'score-high' : (val > 0.5 ? 'score-med' : 'score-low');

            metricsDiv.innerHTML = `
                <div class="metric-item">
                    <span class="metric-label">Accuracy</span>
                    <span class="metric-value ${getScoreClass(metrics.accuracy)}">${(metrics.accuracy * 100).toFixed(0)}%</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Precision</span>
                    <span class="metric-value ${getScoreClass(metrics.precision)}">${(metrics.precision * 100).toFixed(0)}%</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Confidence</span>
                    <span class="metric-value ${getScoreClass(metrics.confidence)}">${(metrics.confidence * 100).toFixed(0)}%</span>
                </div>
            `;
            msgWrapper.appendChild(metricsDiv);
        }

        chatContainer.appendChild(msgWrapper);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        return msgWrapper.id;
    }

    function removeMessage(id) {
        const msg = document.getElementById(id);
        if (msg) msg.remove();
    }
});
