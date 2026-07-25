const page = document.body.dataset.page || '';
const themeButtons = Array.from(document.querySelectorAll('.theme-toggle'));
const mobileToggle = document.querySelector('.mobile-menu-toggle');
const navList = document.querySelector('.nav-list');
const backToTop = document.querySelector('.back-to-top');
const loadingScreen = document.getElementById('loading-screen');

function toggleMobileMenu() {
    if (!navList) return;
    navList.classList.toggle('show');
}

function closeMobileMenuOnClick(event) {
    if (!navList || !mobileToggle) return;
    if (!navList.contains(event.target) && !mobileToggle.contains(event.target)) {
        navList.classList.remove('show');
    }
}

function setTheme() {
    const saved = localStorage.getItem('ingres-theme');
    if (saved === 'light') {
        document.body.classList.remove('dark-mode');
    } else {
        document.body.classList.add('dark-mode');
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const current = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    localStorage.setItem('ingres-theme', current);
}

function initNavigation() {
    if (!mobileToggle) return;
    mobileToggle.addEventListener('click', toggleMobileMenu);
    document.addEventListener('click', closeMobileMenuOnClick);
}

function initThemeToggle() {
    setTheme();
    themeButtons.forEach((button) => {
        button.addEventListener('click', toggleTheme);
    });
}

function initScrollReveal() {
    document.querySelectorAll('.fade-up').forEach((section) => {
        const rect = section.getBoundingClientRect();
        if (rect.top < window.innerHeight - 80) {
            section.classList.add('show');
        }
    });
}

function showTopButton() {
    if (!backToTop) return;
    if (window.scrollY > 380) {
        backToTop.classList.add('show');
    } else {
        backToTop.classList.remove('show');
    }
}

function initBackToTop() {
    if (!backToTop) return;
    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

function hideLoader() {
    if (!loadingScreen) return;
    window.addEventListener('load', () => {
        loadingScreen.style.opacity = '0';
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 350);
    });
}

function initButtonEffect() {
    document.querySelectorAll('.button, .button--ghost, .card-button').forEach((button) => {
        button.addEventListener('click', function (event) {
            const circle = document.createElement('span');
            circle.className = 'ripple';
            const rect = button.getBoundingClientRect();
            circle.style.left = `${event.clientX - rect.left}px`;
            circle.style.top = `${event.clientY - rect.top}px`;
            this.appendChild(circle);
            setTimeout(() => circle.remove(), 600);
        });
    });
}

function initLoginForm() {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return;
    const passwordToggle = document.getElementById('passwordToggle');
    const passwordInput = document.getElementById('password');
    const loginMessage = document.getElementById('loginMessage');
    loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const username = loginForm.querySelector('#username').value.trim();
        const password = passwordInput.value.trim();
        loginMessage.textContent = '';
        if (!username || !password) {
            loginMessage.textContent = 'Please fill in both username and password.';
            return;
        }
        loginMessage.textContent = 'Login successful. Redirecting...';
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 750);
    });

    if (!passwordToggle) return;
    passwordToggle.addEventListener('click', () => {
        passwordInput.type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordToggle.textContent = passwordInput.type === 'password' ? 'Show' : 'Hide';
    });
}

function initContactForm() {
    const contactForm = document.getElementById('contactForm');
    if (!contactForm) return;
    const contactMessage = document.getElementById('contactMessage');
    contactForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const name = contactForm.querySelector('#contactName').value.trim();
        const email = contactForm.querySelector('#contactEmail').value.trim();
        const subject = contactForm.querySelector('#contactSubject').value.trim();
        const message = contactForm.querySelector('#contactMessageField').value.trim();
        contactMessage.textContent = '';
        if (!name || !email || !subject || !message) {
            contactMessage.textContent = 'Please complete all fields before sending.';
            return;
        }
        if (!email.includes('@') || !email.includes('.')) {
            contactMessage.textContent = 'Enter a valid email address.';
            return;
        }
        contactMessage.textContent = 'Message sent successfully. Thank you!';
        contactForm.reset();
    });
}

function initChatbot() {
    if (page !== 'chatbot') return;
    const chatForm = document.getElementById('chatForm');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const clearChat = document.getElementById('clearChat');
    const voiceButton = document.getElementById('voiceButton');
    const responses = [
        'Sure, I can help you with that request.',
        'Here is the information you need about INGRES.',
        'I am processing your question. One moment, please.',
        'The AI assistant can answer FAQs and provide guidance.',
        'This platform supports multilingual queries and secure login.',
    ];

    function sendMessage(role, text) {
        const row = document.createElement('div');
        row.className = `message-row ${role}`;
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = text;
        row.appendChild(bubble);
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTyping() {
        const row = document.createElement('div');
        row.className = 'message-row';
        row.dataset.typing = 'true';
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = '<span class="typing-indicator"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></span>';
        row.appendChild(bubble);
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return row;
    }

    chatForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;
        sendMessage('user', message);
        chatInput.value = '';
        const typingRow = showTyping();
        setTimeout(() => {
            typingRow.remove();
            sendMessage('bot', responses[Math.floor(Math.random() * responses.length)]);
        }, 900 + Math.random() * 800);
    });

    clearChat.addEventListener('click', () => {
        chatMessages.innerHTML = '';
        sendMessage('bot', 'The chat has been cleared. Ask another question when you are ready.');
    });

    voiceButton.addEventListener('click', () => {
        const reminder = document.createElement('div');
        reminder.className = 'status-box';
        reminder.textContent = 'Voice input will be available in a future update. Please type your question now.';
        chatForm.appendChild(reminder);
        setTimeout(() => reminder.remove(), 4200);
    });
}

function initDashboard() {
    if (page !== 'dashboard') return;
    document.querySelectorAll('[data-count]').forEach((element) => {
        const target = Number(element.dataset.count);
        let current = 0;
        const step = Math.max(1, Math.floor(target / 80));
        const interval = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(interval);
            }
            element.textContent = current.toLocaleString();
        }, 16);
    });

    document.querySelectorAll('.progress-fill').forEach((fill) => {
        const percent = fill.dataset.value || '0';
        setTimeout(() => {
            fill.style.width = `${percent}%`;
        }, 120);
    });

    const pieCanvas = document.getElementById('pieChart');
    if (pieCanvas && pieCanvas.getContext) {
        const ctx = pieCanvas.getContext('2d');
        const data = [45, 30, 15, 10];
        const colors = ['#7c3aed', '#38bdf8', '#a78bfa', '#818cf8'];
        let start = -0.5 * Math.PI;
        const total = data.reduce((sum, value) => sum + value, 0);
        data.forEach((value, index) => {
            const slice = (value / total) * Math.PI * 2;
            ctx.beginPath();
            ctx.moveTo(150, 150);
            ctx.arc(150, 150, 110, start, start + slice);
            ctx.closePath();
            ctx.fillStyle = colors[index];
            ctx.fill();
            start += slice;
        });
        ctx.beginPath();
        ctx.arc(150, 150, 60, 0, Math.PI * 2);
        ctx.fillStyle = '#050816';
        ctx.fill();
    }

    const barCanvas = document.getElementById('barChart');
    if (barCanvas && barCanvas.getContext) {
        const ctx = barCanvas.getContext('2d');
        const values = [68, 80, 54, 91, 76];
        const labels = ['Engagement', 'Retention', 'Accuracy', 'Growth', 'NPS'];
        const chartHeight = 260;
        const chartWidth = 500;
        const padding = 40;
        const max = Math.max(...values) * 1.1;
        const barWidth = (chartWidth - padding * 2) / values.length - 18;
        ctx.clearRect(0, 0, chartWidth, chartHeight);
        values.forEach((value, index) => {
            const x = padding + index * (barWidth + 18);
            const barHeight = (value / max) * (chartHeight - padding * 2);
            ctx.fillStyle = '#38bdf8';
            ctx.fillRect(x, chartHeight - padding - barHeight, barWidth, barHeight);
            ctx.fillStyle = '#dbeafe';
            ctx.font = '600 13px Inter, system-ui';
            ctx.fillText(`${value}%`, x, chartHeight - padding - barHeight - 12);
            ctx.fillStyle = '#94a3b8';
            ctx.font = '500 11px Inter, system-ui';
            ctx.fillText(labels[index], x, chartHeight - padding + 20);
        });
        ctx.strokeStyle = 'rgba(255,255,255,0.12)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, chartHeight - padding);
        ctx.lineTo(chartWidth - padding, chartHeight - padding);
        ctx.stroke();
    }
}

function activateCurrentLink() {
    const path = window.location.pathname.split('/').pop() || 'index.html';
    const activeLink = document.querySelector(`.nav-list a[href="${path}"]`);
    if (activeLink) activeLink.classList.add('active');
}

function initPage() {
    initNavigation();
    initThemeToggle();
    initButtonEffect();
    initBackToTop();
    hideLoader();
    initLoginForm();
    initContactForm();
    initChatbot();
    initDashboard();
    activateCurrentLink();
    initPageScroll();
}

function initPageScroll() {
    initScrollReveal();
    window.addEventListener('scroll', () => {
        initScrollReveal();
        showTopButton();
    });
}

document.addEventListener('DOMContentLoaded', initPage);
