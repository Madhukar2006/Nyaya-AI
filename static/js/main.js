// NyayaAI - Main JavaScript

// State
let currentConversationId = null; // Will be set from template
let isLoading = false;

// DOM references
let messagesArea, messageInput, sendBtn, charCounter, welcomeScreen, loadingIndicator;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize DOM refs
    messagesArea = document.getElementById('messages-area');
    messageInput = document.getElementById('message-input');
    sendBtn = document.getElementById('send-btn');
    charCounter = document.getElementById('char-counter');
    welcomeScreen = document.getElementById('welcome-screen');
    loadingIndicator = document.getElementById('loading-indicator');
    
    // Read initial conversation ID from data attribute
    const convData = document.getElementById('conv-data');
    if (convData) {
        currentConversationId = convData.dataset.convId || null;
        if (currentConversationId === '' || currentConversationId === 'None') {
            currentConversationId = null;
        }
    }
    
    // Check if we already have messages
    checkWelcomeScreen();
    scrollToBottom();
    
    // Event listeners
    if (messageInput) {
        messageInput.addEventListener('input', onInputChange);
        messageInput.addEventListener('keydown', onKeyDown);
    }
    
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // Suggestion buttons
    document.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const text = this.dataset.text;
            if (messageInput) {
                messageInput.value = text;
                messageInput.focus();
                onInputChange();
            }
        });
    });
    
    // New chat button
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', startNewChat);
    }
    
    // Mobile nav hamburger
    const hamburger = document.getElementById('hamburger-btn');
    const mobileNav = document.getElementById('mobile-nav');
    if (hamburger && mobileNav) {
        hamburger.addEventListener('click', function() {
            mobileNav.classList.toggle('open');
        });
    }
    
    // Flash message close buttons
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.alert').remove();
        });
    });
    
    // Auto-hide flash messages
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(el => el.remove());
    }, 5000);
});

function onInputChange() {
    const len = messageInput.value.length;
    if (charCounter) charCounter.textContent = len + ' / 2000';
    if (len > 2000) messageInput.value = messageInput.value.substring(0, 2000);
}

function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function sendMessage() {
    if (isLoading) return;
    const text = messageInput.value.trim();
    if (!text) return;
    
    // Add user message to UI
    appendMessage('user', text, getCurrentTime());
    messageInput.value = '';
    onInputChange();
    hideWelcomeScreen();
    showLoading();
    scrollToBottom();
    
    // Send to API
    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: text,
            conversation_id: currentConversationId
        })
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.error) {
            appendMessage('assistant', 'Sorry, an error occurred: ' + data.error, getCurrentTime(), true);
        } else {
            currentConversationId = data.conversation_id;
            appendMessage('assistant', data.response, getCurrentTime());
        }
        scrollToBottom();
    })
    .catch(err => {
        hideLoading();
        appendMessage('assistant', 'Sorry, the AI service is temporarily unavailable. Please try again later.', getCurrentTime(), true);
        scrollToBottom();
    });
}

function appendMessage(role, content, timestamp, isError = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role === 'user' ? 'message-user' : 'message-ai'}${isError ? ' message-error' : ''}`;
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.innerHTML = formatMessage(content);
    
    const metaDiv = document.createElement('div');
    metaDiv.className = 'message-meta';
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = timestamp;
    metaDiv.appendChild(timeSpan);
    
    if (role === 'assistant' && !isError) {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.innerHTML = '📋 Copy';
        copyBtn.title = 'Copy response';
        copyBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(content).then(() => {
                copyBtn.innerHTML = '✅ Copied!';
                setTimeout(() => { copyBtn.innerHTML = '📋 Copy'; }, 2000);
            });
        });
        metaDiv.appendChild(copyBtn);
    }
    
    msgDiv.appendChild(bubbleDiv);
    msgDiv.appendChild(metaDiv);
    
    if (messagesArea) messagesArea.appendChild(msgDiv);
}

function formatMessage(text) {
    // Basic formatting
    let escaped = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
    escaped = escaped.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    escaped = escaped.replace(/\n/g, '<br>');
    return escaped;
}

function showLoading() {
    isLoading = true;
    if (sendBtn) sendBtn.disabled = true;
    if (loadingIndicator) loadingIndicator.style.display = 'flex';
}

function hideLoading() {
    isLoading = false;
    if (sendBtn) sendBtn.disabled = false;
    if (loadingIndicator) loadingIndicator.style.display = 'none';
}

function scrollToBottom() {
    if (messagesArea) messagesArea.scrollTop = messagesArea.scrollHeight;
}

function checkWelcomeScreen() {
    const messages = messagesArea ? messagesArea.querySelectorAll('.message') : [];
    if (messages.length === 0) {
        showWelcomeScreen();
    } else {
        hideWelcomeScreen();
    }
}

function showWelcomeScreen() {
    if (welcomeScreen) welcomeScreen.style.display = 'flex';
}

function hideWelcomeScreen() {
    if (welcomeScreen) welcomeScreen.style.display = 'none';
}

function startNewChat() {
    currentConversationId = null;
    if (messagesArea) messagesArea.innerHTML = '';
    checkWelcomeScreen();
    if (messageInput) messageInput.focus();
}

function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function deleteConversation(convId) {
    if (!confirm('Delete this conversation?')) return;
    fetch(`/api/conversation/delete/${convId}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const row = document.getElementById(`conv-${convId}`);
            if (row) row.remove();
            
            const list = document.getElementById('conversation-list');
            if (list && list.children.length === 0) {
                const empty = document.getElementById('empty-state');
                if (empty) empty.style.display = 'block';
            }
        }
    })
    .catch(() => alert('Failed to delete conversation.'));
}
