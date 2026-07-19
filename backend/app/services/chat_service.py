"""
Citizen Health Advisory Chat Service.
Multi-language AI-powered chatbot providing personalized air quality
advisories in English, Hindi, Tamil, Kannada, and Telugu.

Supports optional Gemini LLM integration for natural conversation.
Falls back to intelligent rule-based responses with full AQI context.
"""

import os
import re
import ssl
import json as _json
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "kn": "Kannada",
    "te": "Telugu",
}

HEALTH_ADVISORIES = {
    "en": {
        "good": {
            "general": "Air quality is good. It's a great day for outdoor activities!",
            "exercise": "You can exercise outdoors freely.",
            "mask": "No mask needed.",
            "children": "Children can play outdoors without any concerns.",
            "elderly": "Safe for elderly to go on walks and outdoor activities.",
        },
        "satisfactory": {
            "general": "Air quality is satisfactory. Most people can continue normal activities.",
            "exercise": "Outdoor exercise is fine for most people.",
            "mask": "No mask needed for most people.",
            "children": "Children can play outdoors. Watch for any unusual coughing.",
            "elderly": "Elderly can go outdoors with normal precautions.",
        },
        "moderate": {
            "general": "Air quality is moderate. Sensitive groups should limit prolonged outdoor exertion.",
            "exercise": "Consider reducing intense outdoor exercise during peak traffic hours (8-10 AM, 5-8 PM).",
            "mask": "Surgical mask recommended for those with respiratory conditions.",
            "children": "Limit outdoor playtime for children with asthma. Keep rescue inhaler accessible.",
            "elderly": "Elderly with heart or lung conditions should reduce outdoor time.",
        },
        "poor": {
            "general": "Air quality is poor. Everyone should reduce prolonged outdoor exertion.",
            "exercise": "Shift exercise indoors. If outdoors, use an N95 mask.",
            "mask": "N95 mask recommended for everyone going outdoors.",
            "children": "Keep children indoors during peak pollution hours. No outdoor sports.",
            "elderly": "Elderly should stay indoors. Ensure proper ventilation with air purifiers.",
        },
        "very_poor": {
            "general": "Air quality is very poor! Avoid all outdoor activities if possible.",
            "exercise": "No outdoor exercise. Use indoor gym or home workouts only.",
            "mask": "N95 mask mandatory for any outdoor exposure.",
            "children": "Children must stay indoors. Schools should cancel outdoor activities.",
            "elderly": "Elderly must stay indoors. Seek medical help if breathing difficulty occurs.",
        },
        "severe": {
            "general": "HEALTH EMERGENCY! Severe air pollution. Stay indoors with windows closed.",
            "exercise": "Absolutely no outdoor physical activity.",
            "mask": "N95 mask essential even for brief outdoor exposure.",
            "children": "Keep children strictly indoors. Consider school closures.",
            "elderly": "Medical alert for elderly. Monitor for chest pain, breathlessness, coughing.",
        },
    },
    "hi": {
        "good": {
            "general": "हवा की गुणवत्ता अच्छी है। बाहरी गतिविधियों के लिए शानदार दिन!",
            "exercise": "आप बेझिझक बाहर व्यायाम कर सकते हैं।",
            "mask": "मास्क की जरूरत नहीं।",
            "children": "बच्चे बिना किसी चिंता के बाहर खेल सकते हैं।",
            "elderly": "बुजुर्गों के लिए बाहर टहलना सुरक्षित है।",
        },
        "satisfactory": {
            "general": "हवा की गुणवत्ता संतोषजनक है। अधिकांश लोग सामान्य गतिविधियां जारी रख सकते हैं।",
            "exercise": "बाहर व्यायाम करना ठीक है।",
            "mask": "अधिकांश लोगों के लिए मास्क जरूरी नहीं।",
            "children": "बच्चे बाहर खेल सकते हैं।",
            "elderly": "बुजुर्ग सामान्य सावधानियों के साथ बाहर जा सकते हैं।",
        },
        "moderate": {
            "general": "हवा की गुणवत्ता मध्यम है। संवेदनशील लोगों को बाहरी गतिविधि सीमित करनी चाहिए।",
            "exercise": "पीक ट्रैफिक घंटों (सुबह 8-10, शाम 5-8) में बाहर व्यायाम कम करें।",
            "mask": "सांस की बीमारी वालों के लिए सर्जिकल मास्क अनुशंसित।",
            "children": "अस्थमा वाले बच्चों का बाहरी खेल सीमित करें। इनहेलर पास रखें।",
            "elderly": "हृदय या फेफड़ों की बीमारी वाले बुजुर्ग बाहरी समय कम करें।",
        },
        "poor": {
            "general": "हवा की गुणवत्ता खराब है। सभी को लंबे समय तक बाहर रहने से बचना चाहिए।",
            "exercise": "व्यायाम घर के अंदर करें। बाहर जाएं तो N95 मास्क पहनें।",
            "mask": "बाहर जाने वाले सभी लोगों के लिए N95 मास्क अनुशंसित।",
            "children": "प्रदूषण के चरम घंटों में बच्चों को घर के अंदर रखें।",
            "elderly": "बुजुर्ग घर के अंदर रहें। एयर प्यूरीफायर का उपयोग करें।",
        },
        "very_poor": {
            "general": "हवा की गुणवत्ता बहुत खराब है! सभी बाहरी गतिविधियां बंद करें।",
            "exercise": "बाहर व्यायाम बिल्कुल न करें।",
            "mask": "बाहर किसी भी समय N95 मास्क अनिवार्य।",
            "children": "बच्चों को सख्ती से घर के अंदर रखें।",
            "elderly": "बुजुर्ग अवश्य घर के अंदर रहें। सांस लेने में कठिनाई हो तो डॉक्टर से मिलें।",
        },
        "severe": {
            "general": "स्वास्थ्य आपातकाल! गंभीर वायु प्रदूषण। खिड़कियां बंद करके घर में रहें।",
            "exercise": "बाहर किसी भी शारीरिक गतिविधि की अनुमति नहीं।",
            "mask": "बाहर संक्षिप्त समय के लिए भी N95 मास्क अनिवार्य।",
            "children": "बच्चों को सख्ती से घर में रखें। स्कूल बंद करने पर विचार करें।",
            "elderly": "बुजुर्गों के लिए मेडिकल अलर्ट। सीने में दर्द, सांस फूलना की निगरानी करें।",
        },
    },
    "ta": {
        "good": {
            "general": "காற்றின் தரம் நல்லது. வெளிப்புற செயல்பாடுகளுக்கு சிறந்த நாள்!",
            "exercise": "வெளியில் சுதந்திரமாக உடற்பயிற்சி செய்யலாம்.",
            "mask": "முகமூடி தேவையில்லை.",
            "children": "குழந்தைகள் வெளியில் விளையாடலாம்.",
            "elderly": "முதியவர்கள் வெளியில் நடக்கலாம்.",
        },
        "moderate": {
            "general": "காற்றின் தரம் மிதமானது. உணர்திறன் உள்ளவர்கள் வெளிப்புற செயல்பாடுகளை குறைக்கவும்.",
            "exercise": "பீக் ட்ராஃபிக் நேரத்தில் வெளிப்புற உடற்பயிற்சியை குறைக்கவும்.",
            "mask": "சுவாச நோயாளிகளுக்கு சர்ஜிகல் முகமூடி பரிந்துரைக்கப்படுகிறது.",
            "children": "ஆஸ்துமா உள்ள குழந்தைகளின் வெளிப்புற விளையாட்டை கட்டுப்படுத்தவும்.",
            "elderly": "இதய அல்லது நுரையீரல் நோயுள்ள முதியவர்கள் வெளிப்புற நேரத்தை குறைக்கவும்.",
        },
        "poor": {
            "general": "காற்றின் தரம் மோசமாக உள்ளது. அனைவரும் வெளிப்புற செயல்பாடுகளை குறைக்கவும்.",
            "exercise": "உடற்பயிற்சியை வீட்டிற்குள் மாற்றவும்.",
            "mask": "வெளியில் செல்வோருக்கு N95 முகமூடி பரிந்துரைக்கப்படுகிறது.",
            "children": "குழந்தைகளை வீட்டிற்குள் வைக்கவும்.",
            "elderly": "முதியவர்கள் வீட்டிற்குள் இருக்கவும்.",
        },
        "severe": {
            "general": "சுகாதார அவசரநிலை! கடுமையான காற்று மாசு. ஜன்னல்களை மூடி வீட்டிற்குள் இருங்கள்.",
            "exercise": "வெளிப்புற உடற்பயிற்சி முற்றிலும் தடை.",
            "mask": "வெளியில் சிறிது நேரம் கூட N95 முகமூடி கட்டாயம்.",
            "children": "குழந்தைகளை கண்டிப்பாக வீட்டிற்குள் வைக்கவும்.",
            "elderly": "முதியவர்களுக்கு மருத்துவ எச்சரிக்கை.",
        },
    },
    "kn": {
        "good": {
            "general": "ಗಾಳಿಯ ಗುಣಮಟ್ಟ ಚೆನ್ನಾಗಿದೆ. ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಗಳಿಗೆ ಉತ್ತಮ ದಿನ!",
            "exercise": "ನೀವು ಹೊರಗೆ ಮುಕ್ತವಾಗಿ ವ್ಯಾಯಾಮ ಮಾಡಬಹುದು.",
            "mask": "ಮಾಸ್ಕ್ ಅಗತ್ಯವಿಲ್ಲ.",
            "children": "ಮಕ್ಕಳು ಹೊರಗೆ ಆಡಬಹುದು.",
            "elderly": "ಹಿರಿಯರು ಹೊರಗೆ ನಡೆಯಬಹುದು.",
        },
        "moderate": {
            "general": "ಗಾಳಿಯ ಗುಣಮಟ್ಟ ಮಧ್ಯಮವಾಗಿದೆ. ಸೂಕ್ಷ್ಮ ಗುಂಪುಗಳು ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಯನ್ನು ಮಿತಿಗೊಳಿಸಬೇಕು.",
            "exercise": "ಪೀಕ್ ಟ್ರಾಫಿಕ್ ಸಮಯದಲ್ಲಿ ಹೊರಾಂಗಣ ವ್ಯಾಯಾಮವನ್ನು ಕಡಿಮೆ ಮಾಡಿ.",
            "mask": "ಉಸಿರಾಟ ಸಮಸ್ಯೆ ಇರುವವರಿಗೆ ಸರ್ಜಿಕಲ್ ಮಾಸ್ಕ್ ಶಿಫಾರಸು.",
            "children": "ಆಸ್ತಮಾ ಇರುವ ಮಕ್ಕಳ ಹೊರಾಂಗಣ ಆಟವನ್ನು ಮಿತಿಗೊಳಿಸಿ.",
            "elderly": "ಹೃದಯ ಅಥವಾ ಶ್ವಾಸಕೋಶ ರೋಗ ಇರುವ ಹಿರಿಯರು ಹೊರಾಂಗಣ ಸಮಯ ಕಡಿಮೆ ಮಾಡಿ.",
        },
        "severe": {
            "general": "ಆರೋಗ್ಯ ತುರ್ತುಸ್ಥಿತಿ! ತೀವ್ರ ವಾಯು ಮಾಲಿನ್ಯ. ಕಿಟಕಿ ಮುಚ್ಚಿ ಮನೆಯೊಳಗೆ ಇರಿ.",
            "exercise": "ಹೊರಾಂಗಣ ವ್ಯಾಯಾಮ ಸಂಪೂರ್ಣ ನಿಷೇಧ.",
            "mask": "ಹೊರಗೆ ಸ್ವಲ್ಪ ಸಮಯವೂ N95 ಮಾಸ್ಕ್ ಕಡ್ಡಾಯ.",
            "children": "ಮಕ್ಕಳನ್ನು ಖಂಡಿತವಾಗಿ ಮನೆಯೊಳಗೆ ಇಡಿ.",
            "elderly": "ಹಿರಿಯರಿಗೆ ವೈದ್ಯಕೀಯ ಎಚ್ಚರಿಕೆ.",
        },
    },
    "te": {
        "good": {
            "general": "గాలి నాణ్యత మంచిగా ఉంది. బయట కార్యకలాపాలకు మంచి రోజు!",
            "exercise": "మీరు బయట స్వేచ్ఛగా వ్యాయామం చేయవచ్చు.",
            "mask": "మాస్క్ అవసరం లేదు.",
            "children": "పిల్లలు బయట ఆడుకోవచ్చు.",
            "elderly": "పెద్దవారు బయట నడవచ్చు.",
        },
        "moderate": {
            "general": "గాలి నాణ్యత మోస్తరుగా ఉంది. సున్నితమైన వ్యక్తులు బయటి కార్యకలాపాలను తగ్గించాలి.",
            "exercise": "పీక్ ట్రాఫిక్ సమయంలో బయట వ్యాయామాన్ని తగ్గించండి.",
            "mask": "శ్వాస సమస్యలు ఉన్నవారికి సర్జికల్ మాస్క్ సిఫారసు.",
            "children": "ఆస్తమా ఉన్న పిల్లల బయటి ఆటలను పరిమితం చేయండి.",
            "elderly": "గుండె లేదా ఊపిరితిత్తుల వ్యాధి ఉన్న పెద్దవారు బయటి సమయాన్ని తగ్గించాలి.",
        },
        "severe": {
            "general": "ఆరోగ్య అత్యవసర పరిస్థితి! తీవ్ర వాయు కాలుష్యం. కిటికీలు మూసి ఇంట్లో ఉండండి.",
            "exercise": "బయట వ్యాయామం పూర్తిగా నిషేధం.",
            "mask": "బయట కొద్ది సమయానికి కూడా N95 మాస్క్ తప్పనిసరి.",
            "children": "పిల్లలను ఖచ్చితంగా ఇంట్లో ఉంచండి.",
            "elderly": "పెద్దవారికి వైద్య హెచ్చరిక.",
        },
    },
}

GREETING = {
    "en": "Hello! I'm VayuDrishti, your AI air quality advisor. I can help you with:\n- Current AQI and health advisories for any city\n- Safety tips for outdoor activities\n- Advice for children, elderly, and vulnerable groups\n- Mask and precaution recommendations\n\nWhich city would you like to know about?",
    "hi": "नमस्ते! मैं वायुबुद्धि हूं, आपका AI वायु गुणवत्ता सलाहकार। मैं आपकी मदद कर सकता हूं:\n- किसी भी शहर का वर्तमान AQI और स्वास्थ्य सलाह\n- बाहरी गतिविधियों के लिए सुरक्षा सुझाव\n- बच्चों, बुजुर्गों और संवेदनशील समूहों के लिए सलाह\n- मास्क और सावधानी की सिफारिशें\n\nआप किस शहर के बारे में जानना चाहेंगे?",
    "ta": "வணக்கம்! நான் வாயுபுத்தி, உங்கள் AI காற்று தர ஆலோசகர். நான் உதவ முடியும்:\n- எந்த நகரத்தின் தற்போதைய AQI மற்றும் சுகாதார ஆலோசனை\n- வெளிப்புற செயல்பாடுகளுக்கான பாதுகாப்பு குறிப்புகள்\n- குழந்தைகள் மற்றும் முதியவர்களுக்கான ஆலோசனை\n\nஎந்த நகரத்தைப் பற்றி தெரிந்துகொள்ள விரும்புகிறீர்கள்?",
    "kn": "ನಮಸ್ಕಾರ! ನಾನು ವಾಯುಬುದ್ಧಿ, ನಿಮ್ಮ AI ಗಾಳಿ ಗುಣಮಟ್ಟ ಸಲಹೆಗಾರ. ನಾನು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ:\n- ಯಾವುದೇ ನಗರದ ಪ್ರಸ್ತುತ AQI ಮತ್ತು ಆರೋಗ್ಯ ಸಲಹೆ\n- ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಗಳಿಗೆ ಸುರಕ್ಷತೆ ಸಲಹೆಗಳು\n\nಯಾವ ನಗರದ ಬಗ್ಗೆ ತಿಳಿಯಲು ಬಯಸುತ್ತೀರಿ?",
    "te": "నమస్కారం! నేను వాయుబుద్ధి, మీ AI గాలి నాణ్యత సలహాదారు. నేను సహాయం చేయగలను:\n- ఏ నగరం యొక్క ప్రస్తుత AQI మరియు ఆరోగ్య సలహా\n- బయటి కార్యకలాపాలకు భద్రతా చిట్కాలు\n\nమీరు ఏ నగరం గురించి తెలుసుకోవాలనుకుంటున్నారు?",
}


def _get_category(aqi: int) -> str:
    if aqi <= 50: return "good"
    if aqi <= 100: return "satisfactory"
    if aqi <= 200: return "moderate"
    if aqi <= 300: return "poor"
    if aqi <= 400: return "very_poor"
    return "severe"


def _detect_city(message: str) -> str | None:
    msg = message.lower()
    cities = {
        "delhi": "Delhi", "dilli": "Delhi", "दिल्ली": "Delhi",
        "mumbai": "Mumbai", "bombay": "Mumbai", "मुंबई": "Mumbai",
        "kolkata": "Kolkata", "calcutta": "Kolkata", "कोलकाता": "Kolkata",
        "bengaluru": "Bengaluru", "bangalore": "Bengaluru", "बेंगलुरु": "Bengaluru",
        "chennai": "Chennai", "madras": "Chennai", "चेन्नई": "Chennai",
        "lucknow": "Lucknow", "लखनऊ": "Lucknow",
        "patna": "Patna", "पटना": "Patna",
        "hyderabad": "Hyderabad", "हैदराबाद": "Hyderabad",
    }
    for key, city in cities.items():
        if key in msg:
            return city
    return None


def _detect_topic(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["exercise", "run", "jog", "walk", "gym", "yoga", "व्यायाम", "दौड़"]):
        return "exercise"
    if any(w in msg for w in ["mask", "n95", "protection", "मास्क"]):
        return "mask"
    if any(w in msg for w in ["child", "kid", "school", "student", "बच्च", "स्कूल"]):
        return "children"
    if any(w in msg for w in ["elder", "old", "senior", "बुजुर्ग", "बूढ़"]):
        return "elderly"
    if any(w in msg for w in ["predict", "forecast", "tomorrow", "future", "कल", "भविष्य"]):
        return "forecast"
    return "general"


async def _try_gemini_response(message: str, context: str, lang: str) -> str | None:
    if not GEMINI_API_KEY:
        return None

    lang_name = LANGUAGES.get(lang, "English")
    prompt = f"""You are VayuDrishti, an AI air quality health advisor for Indian cities.
Respond in {lang_name}. Be concise (2-3 sentences max). Use the following real-time data:

{context}

User question: {message}

Provide a helpful, health-focused response based on the AQI data. Include specific advice."""

    def _call_gemini():
        _ssl_ctx = ssl.create_default_context()
        _ssl_ctx.check_hostname = False
        _ssl_ctx.verify_mode = ssl.CERT_NONE

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        body = _json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 300, "temperature": 0.7},
        }).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "User-Agent": "VayuDrishti/1.0",
        })
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx) as resp:
            data = _json.loads(resp.read().decode())
            return data["candidates"][0]["content"]["parts"][0]["text"]

    try:
        import asyncio
        return await asyncio.to_thread(_call_gemini)
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


async def process_chat_message(
    message: str,
    language: str = "en",
    city_data: dict | None = None,
    session_context: dict | None = None,
) -> dict:
    """Process a citizen chat message and return advisory response."""

    lang = language if language in LANGUAGES else "en"

    if not message.strip() or message.strip().lower() in ["hi", "hello", "hey", "namaste", "नमस्ते", "vanakkam"]:
        return {
            "response": GREETING.get(lang, GREETING["en"]),
            "type": "greeting",
            "language": lang,
            "suggestions": _get_suggestions(lang),
        }

    detected_city = _detect_city(message)
    topic = _detect_topic(message)

    ctx = session_context or {}
    current_city = detected_city or ctx.get("city")

    if not current_city:
        no_city = {
            "en": "I'd be happy to help! Which city would you like air quality information for? I monitor: Delhi, Mumbai, Kolkata, Bengaluru, Chennai, Lucknow, Patna, and Hyderabad.",
            "hi": "मैं मदद करने के लिए तैयार हूं! किस शहर की वायु गुणवत्ता जानकारी चाहिए? मैं निगरानी करता हूं: दिल्ली, मुंबई, कोलकाता, बेंगलुरु, चेन्नई, लखनऊ, पटना, और हैदराबाद।",
            "ta": "உதவ தயாராக இருக்கிறேன்! எந்த நகரத்தின் காற்று தர தகவல் வேண்டும்?",
            "kn": "ಸಹಾಯ ಮಾಡಲು ಸಿದ್ಧ! ಯಾವ ನಗರದ ಗಾಳಿ ಗುಣಮಟ್ಟ ಮಾಹಿತಿ ಬೇಕು?",
            "te": "సహాయం చేయడానికి సిద్ధంగా ఉన్నాను! ఏ నగరం గాలి నాణ్యత సమాచారం కావాలి?",
        }
        return {
            "response": no_city.get(lang, no_city["en"]),
            "type": "clarification",
            "language": lang,
            "suggestions": _get_suggestions(lang),
        }

    aqi = 0
    pm25 = 0
    pm10 = 0
    station_count = 0
    if city_data and current_city in city_data:
        cd = city_data[current_city]
        aqi = cd.get("avg_aqi", 0)
        pm25 = cd.get("pm25_avg", 0)
        pm10 = cd.get("pm10_avg", 0)
        station_count = cd.get("station_count", 0)

    category = _get_category(aqi)

    context_str = f"City: {current_city}, AQI: {aqi}, Category: {category}, PM2.5: {pm25} µg/m³, PM10: {pm10} µg/m³, Stations: {station_count}"

    gemini_response = await _try_gemini_response(message, context_str, lang)
    if gemini_response:
        return {
            "response": gemini_response,
            "type": "ai_advisory",
            "language": lang,
            "city": current_city,
            "aqi": aqi,
            "category": category,
            "data_context": {"pm25": pm25, "pm10": pm10, "stations": station_count},
            "powered_by": "gemini",
            "suggestions": _get_city_suggestions(lang, current_city),
        }

    lang_advisories = HEALTH_ADVISORIES.get(lang, HEALTH_ADVISORIES["en"])
    advisory = lang_advisories.get(category, lang_advisories.get("moderate", {}))

    response_text = advisory.get(topic, advisory.get("general", ""))

    aqi_prefix = {
        "en": f"📊 {current_city} AQI: {aqi} ({category.replace('_', ' ').title()})\n\n",
        "hi": f"📊 {current_city} AQI: {aqi} ({category.replace('_', ' ').title()})\n\n",
        "ta": f"📊 {current_city} AQI: {aqi} ({category.replace('_', ' ').title()})\n\n",
        "kn": f"📊 {current_city} AQI: {aqi} ({category.replace('_', ' ').title()})\n\n",
        "te": f"📊 {current_city} AQI: {aqi} ({category.replace('_', ' ').title()})\n\n",
    }

    full_response = aqi_prefix.get(lang, aqi_prefix["en"]) + response_text

    return {
        "response": full_response,
        "type": "health_advisory",
        "language": lang,
        "city": current_city,
        "aqi": aqi,
        "category": category,
        "topic": topic,
        "data_context": {"pm25": pm25, "pm10": pm10, "stations": station_count},
        "powered_by": "rule_based",
        "suggestions": _get_city_suggestions(lang, current_city),
    }


def _get_suggestions(lang: str) -> list[str]:
    suggestions = {
        "en": ["How is Delhi's air today?", "Is it safe to exercise in Mumbai?", "Should my child wear a mask in Bengaluru?"],
        "hi": ["दिल्ली की हवा कैसी है?", "क्या मुंबई में व्यायाम सुरक्षित है?", "क्या मेरे बच्चे को मास्क पहनना चाहिए?"],
        "ta": ["டெல்லியின் காற்று எப்படி?", "சென்னையில் உடற்பயிற்சி பாதுகாப்பானதா?", "முகமூடி அணிய வேண்டுமா?"],
        "kn": ["ದೆಹಲಿಯ ಗಾಳಿ ಹೇಗಿದೆ?", "ಬೆಂಗಳೂರಿನಲ್ಲಿ ವ್ಯಾಯಾಮ ಸುರಕ್ಷಿತವೇ?", "ಮಾಸ್ಕ್ ಧರಿಸಬೇಕೇ?"],
        "te": ["ఢిల్లీ గాలి ఎలా ఉంది?", "హైదరాబాద్‌లో వ్యాయామం సురక్షితమా?", "మాస్క్ ధరించాలా?"],
    }
    return suggestions.get(lang, suggestions["en"])


def _get_city_suggestions(lang: str, city: str) -> list[str]:
    suggestions = {
        "en": [f"Is it safe to go outside in {city}?", f"Should I wear a mask in {city}?", f"Can my child play outdoors?", f"What's the forecast for {city}?"],
        "hi": [f"क्या {city} में बाहर जाना सुरक्षित है?", f"क्या मास्क पहनना चाहिए?", f"क्या बच्चे बाहर खेल सकते हैं?"],
        "ta": [f"{city}ல் வெளியே செல்வது பாதுகாப்பானதா?", "முகமூடி அணிய வேண்டுமா?", "குழந்தைகள் வெளியில் விளையாடலாமா?"],
        "kn": [f"{city}ನಲ್ಲಿ ಹೊರಗೆ ಹೋಗುವುದು ಸುರಕ್ಷಿತವೇ?", "ಮಾಸ್ಕ್ ಧರಿಸಬೇಕೇ?", "ಮಕ್ಕಳು ಹೊರಗೆ ಆಡಬಹುದೇ?"],
        "te": [f"{city}లో బయటకు వెళ్లడం సురక్షితమా?", "మాస్క్ ధరించాలా?", "పిల్లలు బయట ఆడవచ్చా?"],
    }
    return suggestions.get(lang, suggestions["en"])
