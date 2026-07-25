// Global Theme & Language Management
const translations = {
    en: {
        dashboard: "Dashboard",
        chat: "Chat",
        knowledge: "Knowledge Base",
        documents: "Documents",
        history: "History",
        analytics: "Analytics",
        settings: "Settings",
        profile: "Profile",
        logout: "Logout",
        welcome: "Welcome back",
        status: "Status",
        compare: "Compare"
    },
    hi: {
        dashboard: "डैशबोर्ड",
        chat: "चैट",
        knowledge: "ज्ञान केंद्र",
        documents: "दस्तावेज़",
        history: "इतिहास",
        analytics: "विश्लेषण",
        settings: "सेटिंग्स",
        profile: "प्रोफ़ाइल",
        logout: "लॉगआउट",
        welcome: "स्वागत है",
        status: "स्थिति",
        compare: "तुलना"
    },
    ta: {
        dashboard: "டாஷ்போர்டு",
        chat: "அரட்டை",
        knowledge: "அறிவு தளம்",
        documents: "ஆவணங்கள்",
        history: "வரலாறு",
        analytics: "பகுப்பாய்வு",
        settings: "அமைப்புகள்",
        profile: "சுயவிவரம்",
        logout: "வெளியேறு",
        welcome: "நல்வரவு",
        status: "நிலை",
        compare: "ஒப்பிடு"
    }
};

export function initTheme() {
    const savedTheme = localStorage.getItem('ingres-theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
}

export function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('ingres-theme', isDark ? 'dark' : 'light');
    return isDark;
}

export function initLanguage() {
    const savedLang = localStorage.getItem('ingres-lang') || 'en';
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[savedLang] && translations[savedLang][key]) {
            el.textContent = translations[savedLang][key];
        }
    });
}

export function setLanguage(lang) {
    localStorage.setItem('ingres-lang', lang);
    location.reload();
}
