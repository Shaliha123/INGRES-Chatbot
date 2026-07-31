// Global Localization & Multilingual Management for INGRES Official Portal
const translations = {
    en: {
        dashboard: "Dashboard",
        chat: "Chat Assistant",
        knowledge: "Knowledge Base",
        documents: "Documents",
        history: "History",
        analytics: "Analytics",
        settings: "Settings",
        profile: "Profile",
        logout: "Logout",
        welcome: "Welcome back",
        status: "Status",
        search: "Search hydro reports...",
        total_docs: "Total Documents",
        total_users: "Registered Users",
        conversations: "Conversations",
        kb_articles: "Knowledge Articles"
    },
    ta: {
        dashboard: "டாஷ்போர்டு",
        chat: "அரட்டை உதவி",
        knowledge: "அறிவு தளம்",
        documents: "ஆவணங்கள்",
        history: "வரலாறு",
        analytics: "பகுப்பாய்வு",
        settings: "அமைப்புகள்",
        profile: "சுயவிவரம்",
        logout: "வெளியேறு",
        welcome: "நல்வரவு",
        status: "நிலை",
        search: "நீர் தகவல்களைத் தேடுக...",
        total_docs: "மொத்த ஆவணங்கள்",
        total_users: "பதிவுசெய்த பயனர்கள்",
        conversations: "உரையாடல்கள்",
        kb_articles: "அறிவு கட்டுரைகள்"
    },
    hi: {
        dashboard: "डैशबोर्ड",
        chat: "सहायक चैट",
        knowledge: "ज्ञान केंद्र",
        documents: "दस्तावेज़",
        history: "इतिहास",
        analytics: "विश्लेषण",
        settings: "सेटिंग्स",
        profile: "प्रोफ़ाइल",
        logout: "लॉगआउट",
        welcome: "स्वागत है",
        status: "स्थिति",
        search: "जल रिपोर्ट खोजें...",
        total_docs: "कुल दस्तावेज़",
        total_users: "पंजीकृत उपयोगकर्ता",
        conversations: "बातचीत",
        kb_articles: "ज्ञान लेख"
    },
    te: {
        dashboard: "డాష్‌బోర్డ్",
        chat: "చాట్ అసిస్టెంట్",
        knowledge: "జ్ఞాన కేంద్రం",
        documents: "పత్రాలు",
        history: "చరిత్ర",
        analytics: "విశ్లేషణ",
        settings: "సెట్టింగ్‌లు",
        profile: "ప్రొఫైల్",
        logout: "లాగౌట్",
        welcome: "స్వాగతం",
        status: "స్థితి",
        search: "నీటి నివేదికలను శోధించండి...",
        total_docs: "మొత్తం పత్రాలు",
        total_users: "నమోదిత వినియోగదారులు",
        conversations: "సంభాషణలు",
        kb_articles: "జ్ఞాన వ్యాసాలు"
    }
};

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
    initLanguage();
}

// Auto-run language application on page load
if (typeof window !== 'undefined') {
    initLanguage();
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initLanguage();
        });
    }
}
