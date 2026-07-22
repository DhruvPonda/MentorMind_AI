const API_BASE = "http://127.0.0.1:8000";

// State
let state = {
    token: localStorage.getItem('token') || null,
    studentId: localStorage.getItem('studentId') || null,
    studentName: localStorage.getItem('studentName') || null,
    messages: []
};

// DOM Elements
const authView = document.getElementById('auth-view');
const mainView = document.getElementById('main-view');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const goRegisterBtn = document.getElementById('go-register');
const goLoginBtn = document.getElementById('go-login');
const authError = document.getElementById('auth-error');

const userNameEl = document.getElementById('user-name');
const userIdEl = document.getElementById('user-id');
const logoutBtn = document.getElementById('logout-btn');
const masteryContainer = document.getElementById('mastery-container');
const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

// Initialization
function init() {
    if (state.token) {
        showMainView();
        loadMastery();
        addMessage('assistant', `Welcome back, **${state.studentName}**! I remember our past conversations and adapt to your learning style.`);
    } else {
        showAuthView();
    }
}

// View Management
function showAuthView() {
    authView.classList.add('active');
    authView.classList.remove('hidden');
    mainView.classList.remove('active');
    mainView.classList.add('hidden');
}

function showMainView() {
    authView.classList.remove('active');
    authView.classList.add('hidden');
    mainView.classList.add('active');
    mainView.classList.remove('hidden');
    
    userNameEl.textContent = state.studentName;
    userIdEl.textContent = `ID: ${state.studentId.substring(0, 8)}...`;
}

function showError(msg) {
    authError.textContent = msg;
    authError.classList.remove('hidden');
    setTimeout(() => authError.classList.add('hidden'), 5000);
}

// Event Listeners for Auth
goRegisterBtn.addEventListener('click', (e) => {
    e.preventDefault();
    loginForm.classList.add('hidden');
    loginForm.classList.remove('active');
    registerForm.classList.remove('hidden');
    registerForm.classList.add('active');
    authError.classList.add('hidden');
});

goLoginBtn.addEventListener('click', (e) => {
    e.preventDefault();
    registerForm.classList.add('hidden');
    registerForm.classList.remove('active');
    loginForm.classList.remove('hidden');
    loginForm.classList.add('active');
    authError.classList.add('hidden');
});

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const res = await fetch(`${API_BASE}/students/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        
        if (res.ok) {
            handleAuthSuccess(data);
        } else {
            showError(data.detail || 'Login failed');
        }
    } catch (err) {
        showError('Cannot connect to backend server.');
    }
});

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters.');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/students/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();
        
        if (res.ok) {
            handleAuthSuccess(data);
        } else {
            showError(data.detail || 'Registration failed');
        }
    } catch (err) {
        showError('Cannot connect to backend server.');
    }
});

logoutBtn.addEventListener('click', () => {
    state = { token: null, studentId: null, studentName: null, messages: [] };
    localStorage.removeItem('token');
    localStorage.removeItem('studentId');
    localStorage.removeItem('studentName');
    chatContainer.innerHTML = '';
    showAuthView();
});

function handleAuthSuccess(data) {
    state.token = data.access_token;
    state.studentId = data.student_id;
    state.studentName = data.name;
    
    localStorage.setItem('token', state.token);
    localStorage.setItem('studentId', state.studentId);
    localStorage.setItem('studentName', state.studentName);
    
    chatContainer.innerHTML = '';
    showMainView();
    loadMastery();
    addMessage('assistant', `Welcome, **${state.studentName}**! I am your personal AI tutor.`);
}

// Chat functionality
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    
    sendChatMessage(text);
});

async function sendChatMessage(text) {
    chatInput.value = '';
    addMessage('user', text);
    
    const loadingId = addLoadingIndicator();
    sendBtn.disabled = true;
    
    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ question: text })
        });
        
        removeElement(loadingId);
        sendBtn.disabled = false;
        
        if (res.status === 401) {
            logoutBtn.click();
            return;
        }
        
        const data = await res.json();
        if (res.ok) {
            addMessage('assistant', data.answer, data);
            if (data.mastery_scores) {
                renderMastery(data.mastery_scores);
            }
        } else {
            addMessage('assistant', `❌ Error: ${data.detail || 'Unknown error'}`);
        }
    } catch (err) {
        removeElement(loadingId);
        sendBtn.disabled = false;
        addMessage('assistant', '❌ Cannot connect to backend server.');
    }
}

// Markdown parser (simple version)
function parseMarkdown(text) {
    let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    html = html.replace(/\n/g, '<br>');
    return html;
}

function addMessage(role, text, extraData = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🧠';
    
    const bubbleWrapper = document.createElement('div');
    bubbleWrapper.style.maxWidth = '100%';
    
    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = parseMarkdown(text);
    
    bubbleWrapper.appendChild(bubble);
    
    // Add extra components if assistant and extraData provided
    if (role === 'assistant' && extraData) {
        const extrasDiv = document.createElement('div');
        extrasDiv.className = 'msg-extras';
        
        if (extraData.quiz && extraData.quiz.length > 0) {
            extrasDiv.appendChild(createQuizElement(extraData.quiz));
        }
        
        if (extraData.report) {
            extrasDiv.appendChild(createReportElement(extraData.report));
        }
        
        if (extraData.next_topics && extraData.next_topics.length > 0) {
            extrasDiv.appendChild(createTopicsElement(extraData.next_topics, extraData.learning_path));
        }
        
        if (extrasDiv.childNodes.length > 0) {
            bubbleWrapper.appendChild(extrasDiv);
        }
    }
    
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubbleWrapper);
    
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addLoadingIndicator() {
    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = `message assistant`;
    msgDiv.id = id;
    
    msgDiv.innerHTML = `
        <div class="msg-avatar">🧠</div>
        <div class="msg-bubble">
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return id;
}

function removeElement(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Extra Components Renderers
function createQuizElement(quizData) {
    const container = document.createElement('div');
    container.className = 'quiz-container';
    container.innerHTML = `<h4>📝 Quiz Time</h4>`;
    
    quizData.forEach((q, i) => {
        const qDiv = document.createElement('div');
        qDiv.className = 'quiz-question';
        qDiv.innerHTML = `<strong>Q${i+1}. ${q.question}</strong><br><br>`;
        
        let selectedOption = null;
        
        q.options.forEach(opt => {
            const optDiv = document.createElement('div');
            optDiv.className = 'quiz-option';
            optDiv.textContent = opt;
            optDiv.onclick = () => {
                // deselect others
                Array.from(qDiv.querySelectorAll('.quiz-option')).forEach(el => el.classList.remove('selected'));
                optDiv.classList.add('selected');
                selectedOption = opt;
            };
            qDiv.appendChild(optDiv);
        });
        
        const checkBtn = document.createElement('button');
        checkBtn.className = 'check-btn';
        checkBtn.textContent = 'Check Answer';
        checkBtn.style.marginTop = '10px';
        
        const resultSpan = document.createElement('span');
        resultSpan.style.marginLeft = '10px';
        
        checkBtn.onclick = () => {
            if (!selectedOption) return;
            const options = Array.from(qDiv.querySelectorAll('.quiz-option'));
            options.forEach(el => {
                if (el.textContent === q.correct_answer) {
                    el.classList.add('correct');
                } else if (el.textContent === selectedOption && selectedOption !== q.correct_answer) {
                    el.classList.add('incorrect');
                }
                el.style.pointerEvents = 'none'; // disable clicks
            });
            checkBtn.style.display = 'none';
        };
        
        qDiv.appendChild(checkBtn);
        container.appendChild(qDiv);
        if (i < quizData.length - 1) {
            container.appendChild(document.createElement('hr'));
            container.lastChild.style.margin = '16px 0';
            container.lastChild.style.borderColor = 'var(--glass-border)';
        }
    });
    
    return container;
}

function createReportElement(reportText) {
    const container = document.createElement('div');
    container.className = 'report-container';
    container.innerHTML = `<h4>📊 Progress Report</h4>`;
    const content = document.createElement('div');
    content.innerHTML = parseMarkdown(reportText);
    container.appendChild(content);
    return container;
}

function createTopicsElement(nextTopics, learningPath) {
    const container = document.createElement('div');
    container.className = 'topics-container';
    container.innerHTML = `<h4>🗺️ Recommended Next Topics</h4>`;
    
    const ul = document.createElement('ul');
    ul.className = 'topics-list';
    
    if (learningPath && learningPath.length > 0) {
        learningPath.forEach(step => {
            const li = document.createElement('li');
            const icon = step.prerequisite_met ? '✅' : '⚠️';
            li.innerHTML = `${icon} <strong>${step.topic}</strong> — ${step.reason}`;
            ul.appendChild(li);
        });
    } else {
        nextTopics.forEach(topic => {
            const li = document.createElement('li');
            li.innerHTML = `📚 <strong>${topic}</strong>`;
            ul.appendChild(li);
        });
    }
    
    container.appendChild(ul);
    return container;
}

// Mastery Dashboard
async function loadMastery() {
    try {
        const res = await fetch(`${API_BASE}/students/me/mastery`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (res.ok) {
            const data = await res.json();
            renderMastery(data.mastery_scores);
        }
    } catch (e) {
        console.error('Failed to load mastery', e);
    }
}

function renderMastery(scoresObj) {
    masteryContainer.innerHTML = '';
    const entries = Object.entries(scoresObj).sort((a, b) => b[1].score - a[1].score);
    
    if (entries.length === 0) {
        masteryContainer.innerHTML = `<p style="font-size: 13px; color: var(--text-muted); text-align: center;">No mastery data yet. Start chatting!</p>`;
        return;
    }
    
    entries.forEach(([topic, info]) => {
        const score = info.score;
        let color = 'var(--danger)';
        let icon = '🔴';
        if (score >= 0.7) { color = 'var(--success)'; icon = '🟢'; }
        else if (score >= 0.4) { color = 'var(--warning)'; icon = '🟡'; }
        
        const item = document.createElement('div');
        item.className = 'mastery-item';
        
        const percent = Math.round(score * 100);
        
        item.innerHTML = `
            <div class="mastery-header">
                <span>${icon} ${topic}</span>
                <span>${percent}%</span>
            </div>
            <div class="progress-bg">
                <div class="progress-fill" style="width: ${percent}%; background-color: ${color}"></div>
            </div>
        `;
        masteryContainer.appendChild(item);
    });
}

// Quick Actions
document.getElementById('btn-quiz').onclick = () => sendChatMessage("Quiz me on my weakest topic");
document.getElementById('btn-report').onclick = () => sendChatMessage("Generate my progress report");
document.getElementById('btn-plan').onclick = () => sendChatMessage("What should I study next?");
document.getElementById('btn-refresh').onclick = () => loadMastery();

// Start
init();
