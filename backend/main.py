import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conversation.engine import SimpleConversation
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
import uvicorn
from dotenv import load_dotenv
from datetime import datetime, timedelta
# Load environment
load_dotenv()

# ===== APSCHEDULER IMPORTS =====
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.date import DateTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    print("⚠️ APScheduler not installed. Auto-calls disabled. Run: pip install apscheduler")

# ===== TWILIO IMPORTS =====
try:
    from twilio.rest import Client
    from twilio.twiml.voice_response import VoiceResponse, Gather
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️ Twilio not installed. Real calls disabled.")

# ===== CORE CLASSES =====

class SimpleSTT:
    LANGUAGE_CODES = {
        'hindi': 'hi', 'tamil': 'ta', 'telugu': 'te',
        'bengali': 'bn', 'english': 'en', 'marathi': 'mr',
        'gujarati': 'gu', 'punjabi': 'pa', 'urdu': 'ur'
    }
    def __init__(self, model_size="tiny"):
        print(f"✅ STT Ready (Supports {len(self.LANGUAGE_CODES)} languages)")
    def transcribe(self, audio_path, language=None):
        return {'text': 'नमस्ते, कैसे हैं आप?', 'language': language or 'hindi'}

class SimpleTTS:
    def __init__(self):
        print("✅ TTS Ready (Indian languages supported)")
    def text_to_speech(self, text, language='hindi'):
        return b'demo_audio_bytes'

# ===== CONVERSATION WITH 14 QUESTIONS (FROM HACKATHON DATA) =====
class SimpleConversation:
    def __init__(self, patient_language='hindi'):
        self.patient_language = patient_language
        self.conversation_history = []
        self.patient_context = {}
        self.emergency_detected = False
        self.conversation_count = 0
        self.current_question_index = 0
        self.answers = {}
        self.checkin_complete = False
        self.greeting_done = False

        # 14 Health Questions from Hackathon transcripts
        self.health_questions = [
            {"id": "q1", "question_hindi": "आपका वर्तमान वजन कितना है? (किलो में)",
             "question_english": "What's your current weight in pounds?"},
            {"id": "q2", "question_hindi": "पिछले हफ्ते आपका वजन कितना बदला?",
             "question_english": "How much weight have you lost this past month in pounds?"},
            {"id": "q3", "question_hindi": "क्या आपको कोई साइड इफेक्ट महसूस हो रहा है?",
             "question_english": "Any side effects from your medication this month?"},
            {"id": "q4", "question_hindi": "क्या आपको कोई एलर्जी है?",
             "question_english": "Any new allergies?"},
            {"id": "q5", "question_hindi": "आप कौन सी दवाइयाँ ले रहे हैं?",
             "question_english": "Have you started any new medications or supplements since last month?"},
            {"id": "q6", "question_hindi": "क्या आपने कोई दवा छोड़ दी है?",
             "question_english": "Any requests about your dosage?"},
            {"id": "q7", "question_hindi": "आपका ब्लड प्रेशर कितना है?",
             "question_english": "Do you have any new medical conditions since your last check-in?"},
            {"id": "q8", "question_hindi": "आपका शुगर लेवल कितना है?",
             "question_english": "How have you been feeling overall?"},
            {"id": "q9", "question_hindi": "क्या आपको सीने में दर्द होता है?",
             "question_english": "Any chest pain?"},
            {"id": "q10", "question_hindi": "क्या आपको सांस लेने में तकलीफ है?",
             "question_english": "Any difficulty breathing?"},
            {"id": "q11", "question_hindi": "क्या आपको चक्कर आते हैं?",
             "question_english": "Any dizziness?"},
            {"id": "q12", "question_hindi": "क्या आपको बुखार है?",
             "question_english": "Any fever?"},
            {"id": "q13", "question_hindi": "क्या आपको उल्टी या मिचली हो रही है?",
             "question_english": "Any nausea or vomiting?"},
            {"id": "q14", "question_hindi": "क्या आपको कोई और समस्या है?",
             "question_english": "Any questions for your doctor?"}
        ]

    def set_patient_context(self, data):
        self.patient_context = data

    def get_greeting(self):
        """First greeting with first question"""
        name = self.patient_context.get('name', 'Patient')
        first_q = self.health_questions[0]['question_hindi'] if self.patient_language == 'hindi' else self.health_questions[0]['question_english']
        return f"नमस्ते {name} जी, मैं स्वस्थ्य साथी AI बोल रही हू। आपकी दवा रिफिल के लिए हेल्थ चेक-इन करना है। कृपया मेरे सवालों का जवाब दें। {first_q}"

    def get_next_question(self):
        if self.current_question_index < len(self.health_questions):
            q = self.health_questions[self.current_question_index]
            if self.patient_language == 'hindi':
                return q['question_hindi']
            return q['question_english']
        return None

    def record_answer(self, answer):
        if self.current_question_index < len(self.health_questions):
            qid = self.health_questions[self.current_question_index]['id']
            self.answers[qid] = answer
            self.current_question_index += 1
            return True
        return False

    def is_checkin_complete(self):
        return self.current_question_index >= len(self.health_questions)

    def process_message(self, message):
        self.conversation_count += 1
        message_lower = message.lower()

        # CRITICAL EMERGENCY KEYWORDS (only these escalate)
        critical_emergency = [
            'हार्ट अटैक', 'heart attack', 'सांस नहीं', "can't breathe",
            'बेहोश', 'unconscious', 'ब्लीडिंग', 'bleeding'
        ]

        if any(k in message_lower for k in critical_emergency):
            response = "🚨 यह गंभीर है! मैं तुरंत डॉक्टर को सूचित कर रहा हूँ।"
            return {'text': response, 'emergency': True, 'escalate': True, 'checkin_complete': False}

        # First message after greeting
        if not self.greeting_done:
            self.greeting_done = True
            self.record_answer(message)
            next_q = self.get_next_question()
            response = next_q if next_q else self._get_checkin_complete_response()
        # Continue with questions
        elif not self.is_checkin_complete():
            self.record_answer(message)
            next_q = self.get_next_question()
            if next_q:
                response = next_q
            else:
                response = self._get_checkin_complete_response()
        else:
            response = self._get_normal_response()

        self.conversation_history.append({'role': 'user', 'text': message})
        self.conversation_history.append({'role': 'assistant', 'text': response})

        return {
            'text': response,
            'emergency': False,
            'escalate': False,
            'checkin_complete': self.is_checkin_complete()
        }

    def _get_checkin_complete_response(self):
        return "धन्यवाद! आपकी सभी जानकारी नोट कर ली गई है। आपकी दवा रिफिल की प्रक्रिया शुरू कर दी गई है।"

    def _get_normal_response(self):
        return "ठीक है। दवा समय पर लें और आराम करें।"


# ===== AUTOMATION CLASS WITH ESCALATION =====

class CallAutomation:
    def __init__(self):
        self.patients = {}
        self.call_log = []
        self.running = False

    def register_patient(self, patient_data):
        patient_id = patient_data.get('id')
        risk = patient_data.get('risk', 'medium')
        gender = patient_data.get('gender', 'Not specified')
        language = patient_data.get('language', 'Hindi')

        schedule = self._get_schedule_for_risk(risk)

        self.patients[patient_id] = {
            "data": patient_data,
            "schedule": schedule,
            "calls_completed": [],
            "missed_calls": 0,
            "risk": risk,
            "gender": gender,
            "language": language
        }

        return schedule

    def _get_schedule_for_risk(self, risk):
        """Return schedule based on risk level"""
        if risk == 'critical':
            schedule = []
            for day in range(1, 8):
                schedule.append({"day": day, "type": "morning_check", "time": "09:00"})
                schedule.append({"day": day, "type": "evening_check", "time": "18:00"})
            return schedule
        elif risk == 'high':
            return [{"day": day, "type": "daily_check", "time": "10:00"} for day in range(1, 8)]
        elif risk == 'medium':
            return [
                {"day": 1, "type": "welcome", "time": "10:00"},
                {"day": 3, "type": "medication_check", "time": "09:00"},
                {"day": 7, "type": "followup", "time": "10:00"}
            ]
        else:  # low
            return [
                {"day": 1, "type": "welcome", "time": "10:00"},
                {"day": 7, "type": "followup", "time": "10:00"}
            ]

    def get_patient(self, patient_id):
        return self.patients.get(patient_id)

    def get_today_calls(self):
        today_calls = []
        for pid, p in self.patients.items():
            for call in p['schedule']:
                today_calls.append({
                    "patient_id": pid,
                    "patient_name": p['data']['name'],
                    "phone": p['data']['phone'],
                    "time": call['time'],
                    "type": call['type']
                })
        return today_calls[:10]

    def get_status(self):
        return {
            "total_patients": len(self.patients),
            "today_calls": len(self.get_today_calls()),
            "high_risk": sum(1 for p in self.patients.values() if p['risk'] in ['high', 'critical'])
        }

    def mark_call_missed(self, patient_id):
        """Mark a call as missed and auto-escalate if needed"""
        if patient_id in self.patients:
            self.patients[patient_id]['missed_calls'] += 1
            missed = self.patients[patient_id]['missed_calls']
            current_risk = self.patients[patient_id]['risk']

            if missed >= 3:
                risk_order = {'low': 'medium', 'medium': 'high', 'high': 'critical'}
                if current_risk in risk_order:
                    new_risk = risk_order[current_risk]
                    self.patients[patient_id]['risk'] = new_risk
                    print(f"🚨 AUTO-ESCALATED: Patient {patient_id} from {current_risk} to {new_risk}")

                    self.patients[patient_id]['schedule'] = self._get_schedule_for_risk(new_risk)

                    if APSCHEDULER_AVAILABLE and hasattr(app, 'call_scheduler'):
                        app.call_scheduler.cancel_all_patient_calls(patient_id)
                        self._schedule_patient_calls(patient_id, app.call_scheduler)

                    return True
        return False

    def _schedule_patient_calls(self, patient_id, scheduler):
        patient = self.get_patient(patient_id)
        if not patient:
            return

        schedule = patient['schedule']
        now = datetime.now()

        for call in schedule:
            call_time = now.replace(hour=int(call['time'].split(':')[0]),
                                    minute=int(call['time'].split(':')[1]),
                                    second=0, microsecond=0) + timedelta(days=call['day'])

            if call_time > now:
                scheduler.schedule_patient_call(
                    patient_id=patient_id,
                    patient_name=patient['data']['name'],
                    phone=patient['data']['phone'],
                    call_time=call_time,
                    call_type=call['type']
                )


# ===== AUTO CALL SCHEDULER SERVICE =====

class AutoCallScheduler:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = "http://localhost:8000"
        self.scheduled_jobs = {}
        self.running = False
        print(f"🔧 Scheduler API URL: {self.api_url}")

        if APSCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()
            print("✅ Auto-Call Scheduler initialized")
        else:
            print("⚠️ APScheduler not available")

    def start(self):
        if self.scheduler and not self.running:
            self.scheduler.start()
            self.running = True
            print("✅ Auto-Call Scheduler started")

    def stop(self):
        if self.scheduler and self.running:
            self.scheduler.shutdown()
            self.running = False
            print("⏹️ Auto-Call Scheduler stopped")

    def schedule_patient_call(self, patient_id, patient_name, phone, call_time, call_type="followup"):
        if not self.scheduler:
            print("⚠️ Scheduler not available")
            return None

        job_id = f"{patient_id}_{call_type}_{int(call_time.timestamp())}"

        if job_id in self.scheduled_jobs:
            try:
                self.scheduler.remove_job(job_id)
            except:
                pass

        job = self.scheduler.add_job(
            func=self._make_call,
            trigger='date',
            run_date=call_time,
            args=[patient_id, patient_name, phone, call_type],
            id=job_id,
            replace_existing=True
        )

        self.scheduled_jobs[job_id] = {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "call_time": call_time,
            "call_type": call_type,
            "job_id": job_id
        }

        print(f"📅 Scheduled {call_type} call for {patient_name} at {call_time.strftime('%Y-%m-%d %H:%M')}")
        return job_id

    def _make_call(self, patient_id, patient_name, phone, call_type):
        print(f"📞 AUTO-CALL TRIGGERED: Calling {patient_name} ({phone}) for {call_type}")

        try:
            import httpx
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "http://localhost:8000/call/initiate",
                    params={
                        "patient_id": patient_id,
                        "language": "hindi",
                        "auto": "true"
                    }
                )

                print(f"🔧 Response status: {response.status_code}")
                print(f"🔧 Response: {response.text[:200]}")

                if response.status_code == 200:
                    print(f"✅ Auto-call initiated for {patient_name}")
                    return {"success": True}
                else:
                    print(f"❌ Auto-call failed: {response.status_code}")
                    automation.mark_call_missed(patient_id)
                    return {"success": False}

        except Exception as e:
            print(f"❌ Exception: {e}")
            automation.mark_call_missed(patient_id)
            return {"success": False}

    def get_scheduled_calls(self):
        return list(self.scheduled_jobs.values())

    def cancel_scheduled_call(self, job_id):
        if job_id in self.scheduled_jobs:
            try:
                self.scheduler.remove_job(job_id)
                del self.scheduled_jobs[job_id]
                return True
            except:
                pass
        return False

    def cancel_all_patient_calls(self, patient_id):
        cancelled = []
        for job_id, job in list(self.scheduled_jobs.items()):
            if job['patient_id'] == patient_id:
                try:
                    self.scheduler.remove_job(job_id)
                    del self.scheduled_jobs[job_id]
                    cancelled.append(job_id)
                except:
                    pass
        return cancelled


# ===== TWILIO CONFIG =====
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client = None
if TWILIO_AVAILABLE and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio client initialized")
    except Exception as e:
        print(f"⚠️ Twilio init failed: {e}")
else:
    print("⚠️ Twilio not configured. Real calls disabled.")

# ===== INITIALIZE =====

stt_engine = SimpleSTT()
tts_engine = SimpleTTS()
conversation_engines = {}
automation = CallAutomation()

# ===== AUTO REGISTER PATIENTS =====
def get_schedule_for_risk(risk):
    if risk == 'critical':
        schedule = []
        for day in range(1, 8):
            schedule.append({"days": day, "time": "09:00", "type": "morning_check"})
            schedule.append({"days": day, "time": "18:00", "type": "evening_check"})
        return schedule
    elif risk == 'high':
        return [{"days": day, "time": "10:00", "type": "daily_check"} for day in range(1, 8)]
    elif risk == 'medium':
        return [
            {"days": 1, "time": "10:00", "type": "welcome"},
            {"days": 3, "time": "09:00", "type": "medication_check"},
            {"days": 7, "time": "10:00", "type": "followup"}
        ]
    else:
        return [
            {"days": 1, "time": "10:00", "type": "welcome"},
            {"days": 7, "time": "10:00", "type": "followup"}
        ]

def auto_register_patients():
    print("🔍 Auto-registering patients...")

    sample_patients = [
        {"id": "P001", "name": "राम कुमार", "phone": "+919617043074", "condition": "Heart Attack", "risk": "high", "language": "hindi", "gender": "Male"},
        {"id": "P002", "name": "सीता देवी", "phone": "+919171013806", "condition": "Diabetes", "risk": "medium", "language": "hindi", "gender": "Female"},
        {"id": "P003", "name": "M. Rajan", "phone": "+919171013806", "condition": "Stroke", "risk": "high", "language": "tamil", "gender": "Male"},
        {"id": "P004", "name": "रहीम खान", "phone": "+919171013806", "condition": "Hypertension", "risk": "critical", "language": "urdu", "gender": "Male"},
        {"id": "P005", "name": "लक्ष्मी बाई", "phone": "+919171013806", "condition": "Surgery", "risk": "medium", "language": "marathi", "gender": "Female"},
        {"id": "P006", "name": "Priya Singh", "phone": "+919171013806", "condition": "Pneumonia", "risk": "low", "language": "english", "gender": "Female"},
    ]

    registered_count = 0
    for patient in sample_patients:
        if patient['id'] not in automation.patients:
            automation.register_patient(patient)
            print(f"✅ Registered: {patient['name']} ({patient['id']}) - Risk: {patient['risk']}")
            registered_count += 1

    print(f"📊 Summary: {registered_count} new patients registered")


# ===== FASTAPI APP =====

app = FastAPI(title="CareCompanion Bharat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.call_scheduler = AutoCallScheduler(api_url="http://localhost:8000")

# ===== API ENDPOINTS =====

@app.get("/")
async def root():
    return {
        "message": "CareCompanion Bharat API",
        "status": "running",
        "languages": list(SimpleSTT.LANGUAGE_CODES.keys()),
        "twilio_available": twilio_client is not None
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/conversation/start")
async def start_conversation(data: dict):
    patient_id = data.get("patient_id", "unknown")
    language = data.get("language", "hindi")
    patient_data = data.get("patient_data", {})

    engine = SimpleConversation(patient_language=language)
    engine.set_patient_context(patient_data)
    conversation_engines[patient_id] = engine

    return {
        "success": True,
        "welcome_message": engine.get_greeting()
    }

@app.post("/conversation/message")
async def send_message(data: dict):
    patient_id = data.get("patient_id")
    message = data.get("message")

    if patient_id not in conversation_engines:
        raise HTTPException(404, "Conversation not found")

    engine = conversation_engines[patient_id]
    response = engine.process_message(message)

    return {
        "success": True,
        "response": response['text'],
        "emergency": response.get('emergency', False),
        "escalate": response.get('escalate', False),
        "checkin_complete": response.get('checkin_complete', False)
    }

@app.post("/register-patient")
async def register_patient(patient: dict):
    schedule = automation.register_patient(patient)
    return {
        "success": True,
        "patient_id": patient.get('id'),
        "schedule": schedule,
        "total_patients": len(automation.patients)
    }

@app.get("/automation-status")
async def automation_status():
    return automation.get_status()

@app.get("/today-calls")
async def today_calls():
    return automation.get_today_calls()

@app.get("/scheduled-calls")
async def get_scheduled_calls():
    return app.call_scheduler.get_scheduled_calls()

@app.get("/test-call")
async def test_call():
    from datetime import datetime, timedelta
    call_time = datetime.now() + timedelta(seconds=30)
    job_id = app.call_scheduler.schedule_patient_call(
        patient_id="P001",
        patient_name="राम कुमार",
        phone="+919171013806",
        call_time=call_time,
        call_type="test"
    )
    return {"success": True, "message": f"Call scheduled at {call_time.strftime('%H:%M:%S')}", "job_id": job_id}

# ===== TWILIO CALL ENDPOINTS =====

@app.post("/call/initiate")
async def initiate_call(patient_id: str, language: str = "hindi", auto: str = "false"):
    if not twilio_client:
        raise HTTPException(400, "Twilio not configured")

    patient = automation.get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    phone_number = patient['data']['phone']
    ngrok_url = os.getenv("NGROK_URL", "https://your-ngrok-url.ngrok.io")

    is_auto = auto.lower() == "true"

    try:
        call = twilio_client.calls.create(
            url=f"{ngrok_url}/voice/response?patient_id={patient_id}&language={language}",
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER
        )

        if is_auto:
            print(f"📞 AUTO-CALL: Initiated call to {patient['data']['name']} (SID: {call.sid})")

        return {
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "auto": is_auto
        }
    except Exception as e:
        if is_auto:
            automation.mark_call_missed(patient_id)
        raise HTTPException(400, str(e))

@app.post("/voice/response")
async def voice_response(request: Request, patient_id: str, language: str = "hindi"):
    from twilio.twiml.voice_response import VoiceResponse, Gather

    form_data = await request.form()
    speech_result = form_data.get('SpeechResult')

    patient = automation.get_patient(patient_id)
    if not patient:
        response = VoiceResponse()
        response.say("Patient not found. Goodbye.", voice="Polly.Aditi")
        return Response(content=str(response), media_type="application/xml")

    if patient_id not in conversation_engines:
        engine = SimpleConversation(patient_language=language)
        engine.set_patient_context(patient['data'])
        conversation_engines[patient_id] = engine
    else:
        engine = conversation_engines[patient_id]

    response = VoiceResponse()

    if speech_result:
        ai_response = engine.process_message(speech_result)
        message = ai_response['text']

        if ai_response.get('emergency'):
            response.say("Emergency detected! Transferring to doctor.", voice="Polly.Aditi")
            response.dial(patient['data'].get('emergency_contact', "+919876543210"))
            return Response(content=str(response), media_type="application/xml")
    else:
        if engine.conversation_history:
            message = engine.conversation_history[0]['text']
        else:
            message = engine.get_greeting()

    gather = Gather(
        input='speech dtmf',
        timeout=5,
        speech_timeout='auto',
        speech_model='phone_call',
        action=f"/voice/response?patient_id={patient_id}&language={language}",
        method='POST'
    )
    gather.say(message, voice="Polly.Aditi", language="hi-IN")
    response.append(gather)
    response.redirect(f"/voice/response?patient_id={patient_id}&language={language}", method='POST')

    return Response(content=str(response), media_type="application/xml")

@app.post("/voice/call-simulate")
async def simulate_voice_call(patient_id: str, message: str, language: str = "hindi"):
    patient = automation.get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    engine = SimpleConversation(patient_language=language)
    engine.set_patient_context(patient['data'])
    response = engine.process_message(message)

    return {
        "success": True,
        "response_text": response['text'],
        "emergency": response.get('emergency', False),
        "escalate": response.get('escalate', False)
    }

@app.post("/schedule-manual-call")
async def schedule_manual_call(data: dict):
    try:
        patient_id = data.get("patient_id")
        patient_name = data.get("patient_name")
        phone = data.get("phone")
        call_time_str = data.get("call_time")
        call_type = data.get("call_type", "followup")

        if not patient_id or not call_time_str:
            raise HTTPException(400, "Missing patient_id or call_time")

        call_time = datetime.fromisoformat(call_time_str)

        if hasattr(app, 'call_scheduler') and app.call_scheduler and app.call_scheduler.running:
            job_id = app.call_scheduler.schedule_patient_call(
                patient_id=patient_id,
                patient_name=patient_name,
                phone=phone,
                call_time=call_time,
                call_type=call_type
            )
            return {"success": True, "job_id": job_id, "message": f"Call scheduled for {patient_name} at {call_time}"}
        else:
            return {"success": True, "message": f"Call logged for {patient_name} at {call_time}"}
    except Exception as e:
        raise HTTPException(400, str(e))


# ===== MAIN =====

if __name__ == "__main__":
    app.call_scheduler = AutoCallScheduler(api_url="http://localhost:8000")
    app.call_scheduler.start()
    auto_register_patients()

    print("=" * 50)
    print("🚀 CareCompanion Bharat Server")
    print("📞 14 Health Check-in Questions Ready")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
