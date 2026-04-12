// Configure Marked for better math/code rendering
if (window.marked) {
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false
    });
}

const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages');
const sendBtn = document.getElementById('send-btn');
const backendInfo = document.getElementById('backend-info');

const imageInput = document.getElementById('image-input');
const imagePreviewContainer = document.getElementById('image-preview-container');
const imageNameSpan = document.getElementById('image-name');
let selectedImageBase64 = null;

imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
            selectedImageBase64 = event.target.result;
            imageNameSpan.textContent = `📎 ${file.name}`;
            imagePreviewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
});

function clearImage() {
    selectedImageBase64 = null;
    imageInput.value = '';
    imagePreviewContainer.style.display = 'none';
}

// Handle chat submissions
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message && !selectedImageBase64) return;

    // Add user message to UI
    let displayMsg = message;
    if (selectedImageBase64) {
        displayMsg += message ? '\n\n' : '';
        displayMsg += `*(Sent an image for analysis)*`;
    }
    
    appendMessage('user', '🧑 STUDENt', displayMsg);
    
    const payload = { message: message };
    if (selectedImageBase64) {
        payload.image = selectedImageBase64;
    }

    userInput.value = '';
    clearImage();
    
    // Show typing indicator
    const typingId = appendTypingIndicator();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        removeTypingIndicator(typingId);
        
        if (data.response) {
            appendMessage('assistant', data.label || '🌟 UDENE COMPANION', data.response);
            if (data.backend) {
                backendInfo.textContent = `${data.backend} (${data.model || 'cloud'})`;
            }
            // Update streak counter if present
            if (data.streak !== undefined) {
                const streakEl = document.getElementById('current-streak');
                if (streakEl) streakEl.textContent = data.streak;
            }

            // Show badge notifications
            if (data.new_badges && data.new_badges.length > 0) {
                data.new_badges.forEach(badge => {
                    showBadgeNotification(badge);
                });
            }
        } else if (data.error) {
            appendMessage('assistant', '⚠️ ERROR', `Sorry, something went wrong: ${data.error}`);
        }
    } catch (err) {
        removeTypingIndicator(typingId);
        appendMessage('assistant', '⚠️ ERROR', `Connection failed: ${err.message}`);
    }
});

function showBadgeNotification(badgeName) {
    const toast = document.createElement('div');
    toast.className = 'badge-toast';
    toast.innerHTML = `
        <div class="toast-icon">✨</div>
        <div class="toast-body">
            <strong>Badge Unlocked!</strong>
            <div>${badgeName}</div>
        </div>
    `;
    document.body.appendChild(toast);
    
    // Animate in and out
    setTimeout(() => toast.classList.add('visible'), 100);
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}

function appendMessage(role, label, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    
    const labelDiv = document.createElement('div');
    labelDiv.className = 'message-label';
    labelDiv.textContent = label;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // For assistant messages, render markdown if 'marked' is available
    if (role === 'assistant' && window.marked) {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }
    
    msgDiv.appendChild(labelDiv);
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'message assistant-message typing';
    typingDiv.innerHTML = '<div class="message-content">Thinking...</div>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function setInput(text) {
    userInput.value = text;
    userInput.focus();
}

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    const targetSection = document.getElementById(`${sectionId}-section`);
    if (targetSection) targetSection.classList.add('active');
    
    // Find button that matches
    const navBtns = document.querySelectorAll('.nav-item');
    navBtns.forEach(btn => {
        // Match by sectionId link in JS or hidden data attribute ideally,
        // but for now let's use the text mapping
        const text = btn.textContent.toLowerCase();
        if ((sectionId === 'chat' && text.includes('chat')) ||
            (sectionId === 'report' && text.includes('performance')) ||
            (sectionId === 'curriculum' && text.includes('curriculum'))) {
            btn.classList.add('active');
        }
    });
}

function clearChat() {
    chatMessages.innerHTML = '';
    appendMessage('assistant', '🌟 UDENE COMPANION', 'History cleared. What should we learn next?');
}

async function loadReport() {
    showSection('report');
    const container = document.getElementById('report-content');
    container.innerHTML = 'Analyzing your performance...';
    
    try {
        const resp = await fetch('/report');
        const data = await resp.json();
        container.innerHTML = marked.parse(data.report);
    } catch (err) {
        container.innerHTML = `<p class="error">Failed to load report: ${err.message}</p>`;
    }
}

async function loadCurriculum() {
    showSection('curriculum');
    const container = document.getElementById('curriculum-content');
    container.innerHTML = 'Mapping your journey...';
    
    try {
        const resp = await fetch('/curriculum');
        const data = await resp.json();
        container.innerHTML = marked.parse(data.curriculum);
    } catch (err) {
        container.innerHTML = `<p class="error">Failed to load curriculum: ${err.message}</p>`;
    }
}
