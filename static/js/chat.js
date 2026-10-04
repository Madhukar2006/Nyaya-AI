/**
 * NyayaAI - Dedicated Chat Interface Script
 * Handles real-time legal assistant interactions, markdown rendering, suggestion chips, and history.
 */

let currentConversationId = window.NYAYA_CONV_ID || null;
let currentUsername = window.NYAYA_USERNAME || 'User';
let isSending = false;

document.addEventListener('DOMContentLoaded', function() {
    const metaEl = document.getElementById('chat-metadata');
    if (metaEl) {
        const rawConvId = metaEl.getAttribute('data-conv-id');
        if (rawConvId && rawConvId !== 'None' && rawConvId !== '') {
            currentConversationId = rawConvId;
        }
        currentUsername = metaEl.getAttribute('data-username') || currentUsername;
    }

    const messagesArea = document.getElementById('messages-area');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const charCounter = document.getElementById('char-counter');
    const welcomeScreen = document.getElementById('welcome-screen');
    const typingIndicator = document.getElementById('typing-indicator');
    const newChatBtn = document.getElementById('new-chat-btn');
    const toggleConvDrawer = document.getElementById('toggle-conv-drawer');
    const convSidebar = document.getElementById('chat-history-sidebar');

    // Auto-scroll on initial load
    scrollToBottom();

    // Load recent conversations into sidebar
    loadSidebarConversations();

    // Toggle inner history drawer on mobile / small screens
    if (toggleConvDrawer && convSidebar) {
        toggleConvDrawer.addEventListener('click', () => {
            convSidebar.classList.toggle('drawer-open');
        });
    }

    // Auto-expanding textarea & character counter
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            const newHeight = Math.min(this.scrollHeight, 180);
            this.style.height = (newHeight > 42 ? newHeight : 42) + 'px';

            const len = this.value.length;
            if (charCounter) {
                charCounter.textContent = `${len} / 4000`;
                if (len > 3800) {
                    charCounter.classList.add('char-limit-near');
                } else {
                    charCounter.classList.remove('char-limit-near');
                }
            }
        });

        // Submit on Enter (Shift+Enter for newline)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitUserMessage();
            }
        });
    }

    // Send button click
    if (sendBtn) {
        sendBtn.addEventListener('click', function(e) {
            e.preventDefault();
            submitUserMessage();
        });
    }

    // Clickable Suggestion Chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', function() {
            const prompt = this.getAttribute('data-prompt');
            if (messageInput && prompt) {
                messageInput.value = prompt;
                messageInput.focus();
                messageInput.dispatchEvent(new Event('input'));
                submitUserMessage();
            }
        });
    });

    // New Chat Button
    if (newChatBtn) {
        newChatBtn.addEventListener('click', function(e) {
            e.preventDefault();
            startFreshChat();
        });
    }

    // Copy response buttons (for pre-rendered messages)
    initCopyButtons();

    function submitUserMessage() {
        if (isSending) return;
        const text = messageInput.value.trim();
        if (!text) return;

        // Hide empty state if visible
        if (welcomeScreen) {
            welcomeScreen.style.display = 'none';
            welcomeScreen.classList.add('is-hidden');
        }

        // Render user message bubble
        appendMessageBubble('user', text, getFormattedTime());

        // Reset input
        messageInput.value = '';
        messageInput.style.height = '42px';
        if (charCounter) charCounter.textContent = '0 / 4000';

        // Show typing indicator & set loading state
        setLoadingState(true);
        scrollToBottom();

        // Send to Flask API
        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                conversation_id: currentConversationId
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(errData.error || 'Server error');
                });
            }
            return response.json();
        })
        .then(data => {
            setLoadingState(false);
            if (data.conversation_id) {
                currentConversationId = data.conversation_id;
                // Update URL if starting a fresh conversation
                if (window.history.pushState && !window.location.pathname.includes(`/chat/${currentConversationId}`)) {
                    window.history.pushState({}, '', `/chat/${currentConversationId}`);
                }
                loadSidebarConversations();
            }

            appendMessageBubble('assistant', data.response, getFormattedTime());
            scrollToBottom();
        })
        .catch(err => {
            setLoadingState(false);
            appendMessageBubble('assistant', '⚠️ ' + (err.message || 'Unable to connect to the legal AI service. Please try again.'), getFormattedTime(), true);
            scrollToBottom();
            if (window.showToast) {
                window.showToast(err.message || 'Error receiving AI response', 'error');
            }
        });
    }

    function appendMessageBubble(role, content, timeStr, isError = false) {
        const msgId = 'msg-' + Date.now();
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper message-${role}${isError ? ' message-error-bubble' : ''}`;

        if (role === 'assistant') {
            const aiAvatar = document.createElement('div');
            aiAvatar.className = 'message-avatar-ai';
            aiAvatar.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="3" x2="12" y2="21"></line><path d="M4 7l8-4 8 4"></path><path d="M4 11a4 4 0 0 0 8 0"></path><path d="M12 11a4 4 0 0 0 8 0"></path><line x1="6" y1="18" x2="18" y2="18"></line></svg>`;
            wrapper.appendChild(aiAvatar);
        }

        const bubbleContainer = document.createElement('div');
        bubbleContainer.className = 'message-bubble-container';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.id = msgId;

        if (role === 'assistant' && !isError) {
            bubble.innerHTML = formatMarkdown(content);
        } else {
            bubble.textContent = content;
        }
        bubbleContainer.appendChild(bubble);

        const metaBar = document.createElement('div');
        metaBar.className = 'message-meta-bar';

        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-timestamp';
        timeSpan.textContent = timeStr;
        metaBar.appendChild(timeSpan);

        if (role === 'assistant' && !isError) {
            const actions = document.createElement('div');
            actions.className = 'message-actions';

            const copyBtn = document.createElement('button');
            copyBtn.type = 'button';
            copyBtn.className = 'btn-msg-action btn-copy';
            copyBtn.title = 'Copy answer';
            copyBtn.innerHTML = `
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                <span>Copy</span>
            `;
            copyBtn.addEventListener('click', () => {
                copyTextToClipboard(content, copyBtn);
            });
            actions.appendChild(copyBtn);
            metaBar.appendChild(actions);
        }

        bubbleContainer.appendChild(metaBar);
        wrapper.appendChild(bubbleContainer);

        if (role === 'user') {
            const userAvatar = document.createElement('div');
            userAvatar.className = 'message-avatar-user';
            userAvatar.textContent = (currentUsername[0] || 'U').toUpperCase();
            wrapper.appendChild(userAvatar);
        }

        // Insert before typing indicator
        if (typingIndicator && typingIndicator.parentNode === messagesArea) {
            messagesArea.insertBefore(wrapper, typingIndicator);
        } else {
            messagesArea.appendChild(wrapper);
        }
    }

    function setLoadingState(loading) {
        isSending = loading;
        if (sendBtn) {
            sendBtn.disabled = loading;
        }
        if (typingIndicator) {
            typingIndicator.style.display = loading ? 'flex' : 'none';
        }
    }

    function scrollToBottom() {
        if (messagesArea) {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    }

    function getFormattedTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function startFreshChat() {
        currentConversationId = null;
        if (window.history.pushState) {
            window.history.pushState({}, '', '/chat');
        }

        // Remove existing messages except typing indicator and welcome screen
        const messageElements = messagesArea.querySelectorAll('.message-wrapper:not(#typing-indicator)');
        messageElements.forEach(el => el.remove());

        if (welcomeScreen) {
            welcomeScreen.style.display = 'flex';
            welcomeScreen.classList.remove('is-hidden');
        }
        if (messageInput) {
            messageInput.value = '';
            messageInput.focus();
        }
        highlightActiveSidebarConv(null);
    }

    function loadSidebarConversations() {
        const listContainer = document.getElementById('sidebar-conv-list');
        if (!listContainer) return;

        fetch('/api/conversations')
        .then(res => res.json())
        .then(data => {
            const convs = data.conversations || [];
            if (convs.length === 0) {
                listContainer.innerHTML = '<div class="sidebar-empty-state">No past conversations</div>';
                return;
            }

            listContainer.innerHTML = '';
            convs.forEach(c => {
                const item = document.createElement('a');
                item.href = `/chat/${c.id}`;
                item.className = `sidebar-conv-item${currentConversationId && String(currentConversationId) === String(c.id) ? ' active-conv' : ''}`;
                item.setAttribute('data-conv-id', c.id);

                item.innerHTML = `
                    <div class="conv-item-left">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                        <span class="conv-item-title">${escapeHtml(c.title || 'Conversation')}</span>
                    </div>
                `;
                listContainer.appendChild(item);
            });
        })
        .catch(() => {
            const loadingState = document.getElementById('sidebar-loading');
            if (loadingState) loadingState.textContent = 'Past chats';
        });
    }

    function highlightActiveSidebarConv(convId) {
        document.querySelectorAll('.sidebar-conv-item').forEach(item => {
            if (convId && item.getAttribute('data-conv-id') === String(convId)) {
                item.classList.add('active-conv');
            } else {
                item.classList.remove('active-conv');
            }
        });
    }

    function initCopyButtons() {
        document.querySelectorAll('.btn-copy').forEach(btn => {
            btn.addEventListener('click', function() {
                const targetId = this.dataset.target;
                const targetElem = document.getElementById(targetId);
                if (targetElem) {
                    copyTextToClipboard(targetElem.innerText || targetElem.textContent, this);
                }
            });
        });
    }

    function copyTextToClipboard(text, btnElement) {
        if (!navigator.clipboard) {
            const temp = document.createElement('textarea');
            temp.value = text;
            document.body.appendChild(temp);
            temp.select();
            document.execCommand('copy');
            document.body.removeChild(temp);
            showCopiedFeedback(btnElement);
            return;
        }

        navigator.clipboard.writeText(text).then(() => {
            showCopiedFeedback(btnElement);
        }).catch(() => {
            if (window.showToast) window.showToast('Failed to copy text', 'error');
        });
    }

    function showCopiedFeedback(btnElement) {
        const origHtml = btnElement.innerHTML;
        btnElement.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <span style="color:#059669; font-weight:600;">Copied!</span>
        `;
        setTimeout(() => {
            btnElement.innerHTML = origHtml;
        }, 2000);
    }
});

/**
 * Format markdown text into clean semantic HTML
 */
function formatMarkdown(text) {
    if (!text) return '';

    // Split text into lines for block-level parsing
    let lines = text.split('\n');
    let html = '';
    let inList = false;
    let listType = ''; // 'ul' or 'ol'

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];

        // Check for disclaimer line
        if (line.includes('⚖️ NyayaAI provides general legal information only') || line.includes('⚖️ NyayaAI provides general legal information')) {
            if (inList) { html += `</${listType}>`; inList = false; }
            html += `<div class="message-disclaimer-box"><span class="disclaimer-badge">Disclaimer</span>${escapeHtml(line)}</div>`;
            continue;
        }

        // Headings
        if (line.startsWith('### ')) {
            if (inList) { html += `</${listType}>`; inList = false; }
            html += `<h4>${inlineFormat(line.slice(4))}</h4>`;
            continue;
        } else if (line.startsWith('## ')) {
            if (inList) { html += `</${listType}>`; inList = false; }
            html += `<h3>${inlineFormat(line.slice(3))}</h3>`;
            continue;
        } else if (line.startsWith('# ')) {
            if (inList) { html += `</${listType}>`; inList = false; }
            html += `<h3>${inlineFormat(line.slice(2))}</h3>`;
            continue;
        }

        // Numbered list (e.g. "1. ")
        const numMatch = line.match(/^(\d+)\.\s+(.+)$/);
        if (numMatch) {
            if (!inList || listType !== 'ol') {
                if (inList) html += `</${listType}>`;
                html += '<ol class="chat-ol">';
                inList = true;
                listType = 'ol';
            }
            html += `<li>${inlineFormat(numMatch[2])}</li>`;
            continue;
        }

        // Unordered bullet list (e.g. "- ", "* ", "• ")
        const bulletMatch = line.match(/^[-*•]\s+(.+)$/);
        if (bulletMatch) {
            if (!inList || listType !== 'ul') {
                if (inList) html += `</${listType}>`;
                html += '<ul class="chat-ul">';
                inList = true;
                listType = 'ul';
            }
            html += `<li>${inlineFormat(bulletMatch[1])}</li>`;
            continue;
        }

        // Regular line
        if (inList) {
            html += `</${listType}>`;
            inList = false;
        }

        const trimmed = line.trim();
        if (trimmed.length === 0) {
            html += '<div class="paragraph-gap"></div>';
        } else {
            html += `<p>${inlineFormat(trimmed)}</p>`;
        }
    }

    if (inList) {
        html += `</${listType}>`;
    }

    return html;
}

function inlineFormat(text) {
    let safe = escapeHtml(text);
    // Bold: **text**
    safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic: *text*
    safe = safe.replace(/(^|[^*])\*([^*]+?)\*([^*]|$)/g, '$1<em>$2</em>$3');
    // Inline code: `code`
    safe = safe.replace(/`([^`]+)`/g, '<code>$1</code>');
    return safe;
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
