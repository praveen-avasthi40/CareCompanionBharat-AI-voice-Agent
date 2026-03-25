# 🏥 CareCompanion Bharat

AI-powered voice agent for post-discharge patient follow-up in 14 Indian languages.

## Features
- 🎤 14 Indian languages (Hindi, Tamil, Telugu, Bengali, etc.)
- 📞 Real phone calls via Twilio
- 💬 14 health check-in questions
- 🚨 Emergency detection and escalation
- 📊 Hospital dashboard with analytics
- 🤖 GPT-4 powered conversation

## Tech Stack
- Backend: FastAPI, Python
- Frontend: Streamlit
- Voice: Twilio, gTTS
- AI: OpenAI GPT-4
- Database: JSON / SQLite

## Setup

1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your API keys
6. Run backend: `python backend/main.py`
7. Run dashboard: `streamlit run frontend/dashboard.py`

## Environment Variables
- `OPENAI_API_KEY` - OpenAI API key
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `TWILIO_PHONE_NUMBER` - Twilio phone number

## Team
- [Your Name] - Developer

## License
MIT