import json
import os
from datetime import datetime

class SimpleConversation:
    def __init__(self, patient_language='hindi'):
        self.patient_language = patient_language
        self.conversation_history = []
        self.patient_context = {}
        self.emergency_detected = False
        self.current_question_index = 0
        self.answers = {}
        self.checkin_complete = False
        self.greeting_done = False
        self.patient_condition_summary = {}
        self.first_question_asked = False  # NEW: Track if first question already asked

        # ===== MULTI-LINGUAL GREETINGS =====
        self.greetings = {
            'hindi': {
                'greeting': "नमस्ते {name} जी, मैं केयरकंपेनियन बोल रहा हूँ। आपकी दवा रिफिल के लिए हेल्थ चेक-इन करना है।",
                'question_prefix': "कृपया मेरे सवालों का जवाब दें।",
                'farewell': "धन्यवाद! आपकी सभी जानकारी नोट कर ली गई है। आपकी दवा रिफिल की प्रक्रिया शुरू कर दी गई है।"
            },
            'tamil': {
                'greeting': "வணக்கம் {name} ஜி, நான் கேர்கம்பேனியன் பேசுகிறேன். உங்கள் மருந்து ரீஃபில் செய்ய உடல்நலம் சரிபார்க்க வேண்டும்.",
                'question_prefix': "தயவுசெய்து என் கேள்விகளுக்கு பதிலளிக்கவும்.",
                'farewell': "நன்றி! உங்கள் தகவல்கள் பதிவு செய்யப்பட்டுள்ளன. உங்கள் மருந்து ரீஃபில் செயல்முறை தொடங்கப்பட்டுள்ளது."
            },
            'telugu': {
                'greeting': "నమస్కారం {name} గారు, నేను కేర్‌కంపానియన్ మాట్లాడుతున్నాను. మీ మందు రీఫిల్ కోసం హెల్త్ చెక్-ఇన్ చేయాలి.",
                'question_prefix': "దయచేసి నా ప్రశ్నలకు సమాధానం ఇవ్వండి.",
                'farewell': "ధన్యవాదాలు! మీ సమాచారం నమోదు చేయబడింది. మీ మందు రీఫిల్ ప్రక్రియ ప్రారంభించబడింది."
            },
            'bengali': {
                'greeting': "নমস্কার {name} জি, আমি কেয়ারকম্প্যানিয়ন বলছি। আপনার ওষুধ রিফিলের জন্য হেলথ চেক-ইন করতে হবে।",
                'question_prefix': "দয়া করে আমার প্রশ্নের উত্তর দিন।",
                'farewell': "ধন্যবাদ! আপনার সমস্ত তথ্য নোট করা হয়েছে। আপনার ওষুধ রিফিলের প্রক্রিয়া শুরু হয়েছে।"
            },
            'marathi': {
                'greeting': "नमस्कार {name} जी, मी केअरकंपॅनियन बोलतोय. तुमच्या औषध रिफिलसाठी हेल्थ चेक-इन करायचे आहे.",
                'question_prefix': "कृपया माझ्या प्रश्नांची उत्तरे द्या.",
                'farewell': "धन्यवाद! तुमची सर्व माहिती नोंदवली गेली आहे. तुमच्या औषध रिफिलची प्रक्रिया सुरू केली आहे."
            },
            'gujarati': {
                'greeting': "નમસ્તે {name} જી, હું કેયરકંપેનિયન બોલું છું. તમારી દવા રિફિલ માટે હેલ્થ ચેક-ઇન કરવાનું છે.",
                'question_prefix': "કૃપા કરીને મારા પ્રશ્નોના જવાબ આપો.",
                'farewell': "આભાર! તમારી બધી માહિતી નોંધી લેવામાં આવી છે. તમારી દવા રિફિલની પ્રક્રિયા શરૂ કરી દેવામાં આવી છે."
            },
            'punjabi': {
                'greeting': "ਨਮਸਤੇ {name} ਜੀ, ਮੈਂ ਕੇਅਰਕੰਪੇਨੀਅਨ ਬੋਲ ਰਿਹਾ ਹਾਂ। ਤੁਹਾਡੀ ਦਵਾਈ ਰੀਫਿਲ ਲਈ ਹੈਲਥ ਚੈਕ-ਇਨ ਕਰਨਾ ਹੈ।",
                'question_prefix': "ਕਿਰਪਾ ਕਰਕੇ ਮੇਰੇ ਸਵਾਲਾਂ ਦੇ ਜਵਾਬ ਦਿਓ।",
                'farewell': "ਧੰਨਵਾਦ! ਤੁਹਾਡੀ ਸਾਰੀ ਜਾਣਕਾਰੀ ਨੋਟ ਕਰ ਲਈ ਗਈ ਹੈ। ਤੁਹਾਡੀ ਦਵਾਈ ਰੀਫਿਲ ਦੀ ਪ੍ਰਕਿਰਿਆ ਸ਼ੁਰੂ ਕਰ ਦਿੱਤੀ ਗਈ ਹੈ।"
            },
            'urdu': {
                'greeting': "نمستے {name} جی، میں کیئرکمپینیئن بول رہا ہوں۔ آپ کی دوائی ریفل کے لیے ہیلتھ چیک ان کرنا ہے۔",
                'question_prefix': "براہ کرم میرے سوالوں کے جواب دیں۔",
                'farewell': "شکریہ! آپ کی تمام معلومات نوٹ کر لی گئی ہیں۔ آپ کی دوائی ریفل کا عمل شروع کر دیا گیا ہے۔"
            },
            'english': {
                'greeting': "Hello {name}, this is CareCompanion. I'm here for your medication refill health check-in.",
                'question_prefix': "Please answer my questions.",
                'farewell': "Thank you! All your information has been recorded. Your medication refill process has been initiated."
            }
        }

        # 14 Health Questions
        self.health_questions = [
            {"id": "q1", "question_hindi": "आपका वर्तमान वजन कितना है? (किलो में)", "question_english": "What's your current weight in pounds?"},
            {"id": "q2", "question_hindi": "पिछले हफ्ते आपका वजन कितना बदला?", "question_english": "How much weight have you lost this past month in pounds?"},
            {"id": "q3", "question_hindi": "क्या आपको कोई साइड इफेक्ट महसूस हो रहा है?", "question_english": "Any side effects from your medication this month?"},
            {"id": "q4", "question_hindi": "क्या आपको कोई एलर्जी है?", "question_english": "Any new allergies?"},
            {"id": "q5", "question_hindi": "आप कौन सी दवाइयाँ ले रहे हैं?", "question_english": "What medications are you taking?"},
            {"id": "q6", "question_hindi": "क्या आपने कोई दवा छोड़ दी है?", "question_english": "Any requests about your dosage?"},
            {"id": "q7", "question_hindi": "आपका ब्लड प्रेशर कितना है?", "question_english": "Do you have any new medical conditions?"},
            {"id": "q8", "question_hindi": "आपका शुगर लेवल कितना है?", "question_english": "How have you been feeling overall?"},
            {"id": "q9", "question_hindi": "क्या आपको सीने में दर्द होता है?", "question_english": "Any chest pain?"},
            {"id": "q10", "question_hindi": "क्या आपको सांस लेने में तकलीफ है?", "question_english": "Any difficulty breathing?"},
            {"id": "q11", "question_hindi": "क्या आपको चक्कर आते हैं?", "question_english": "Any dizziness?"},
            {"id": "q12", "question_hindi": "क्या आपको बुखार है?", "question_english": "Any fever?"},
            {"id": "q13", "question_hindi": "क्या आपको उल्टी या मिचली हो रही है?", "question_english": "Any nausea or vomiting?"},
            {"id": "q14", "question_hindi": "क्या आपको कोई और समस्या है?", "question_english": "Any questions for your doctor?"}
        ]

    def set_patient_context(self, data):
        self.patient_context = data

    def get_greeting(self):
        """Get greeting WITH first question included"""
        name = self.patient_context.get('name', 'Patient')
        lang_data = self.greetings.get(self.patient_language, self.greetings['hindi'])
        first_q = self.health_questions[0]['question_hindi'] if self.patient_language == 'hindi' else self.health_questions[0]['question_english']
        # Important: Include first question in greeting
        return f"{lang_data['greeting']} {lang_data['question_prefix']} {first_q}"

    def get_first_question_only(self):
        """Get just the first question (for follow-up if needed)"""
        return self.health_questions[0]['question_hindi'] if self.patient_language == 'hindi' else self.health_questions[0]['question_english']

    def get_farewell(self):
        lang_data = self.greetings.get(self.patient_language, self.greetings['hindi'])
        return lang_data['farewell']

    def get_next_question(self):
        """Get next question based on current index"""
        if self.current_question_index < len(self.health_questions):
            q = self.health_questions[self.current_question_index]
            if self.patient_language == 'hindi':
                return q['question_hindi']
            return q['question_english']
        return None

    def record_answer(self, answer):
        if self.current_question_index < len(self.health_questions):
            qid = self.health_questions[self.current_question_index]['id']
            question_text = self.health_questions[self.current_question_index]['question_hindi'] if self.patient_language == 'hindi' else self.health_questions[self.current_question_index]['question_english']
            self.answers[qid] = {
                'question': question_text,
                'answer': answer,
                'timestamp': datetime.now().isoformat()
            }
            self.current_question_index += 1
            return True
        return False

    def is_checkin_complete(self):
        return self.current_question_index >= len(self.health_questions)

    def analyze_patient_condition(self):
        condition = {
            'status': 'stable',
            'warning_signs': [],
            'medication_adherence': 'unknown',
            'symptoms': []
        }

        for qid, data in self.answers.items():
            answer = data['answer'].lower() if data['answer'] else ''

            if qid in ['q9', 'q10', 'q11']:
                if 'है' in answer or 'yes' in answer or 'होता' in answer:
                    condition['warning_signs'].append(self.health_questions[int(qid[1:])-1]['question_hindi'])
                    condition['status'] = 'needs_attention'

            if qid == 'q6':
                if 'हाँ' in answer or 'yes' in answer:
                    condition['medication_adherence'] = 'missed'
                    condition['warning_signs'].append('Medication missed')

            if qid in ['q9', 'q10', 'q11', 'q12', 'q13']:
                if answer and answer not in ['नहीं', 'no', 'नही', 'nope', 'no.', 'not really']:
                    condition['symptoms'].append({
                        'question': self.health_questions[int(qid[1:])-1]['question_hindi'],
                        'answer': data['answer']
                    })

        if len(condition['warning_signs']) >= 2:
            condition['status'] = 'urgent'
        elif len(condition['warning_signs']) >= 1:
            condition['status'] = 'needs_attention'
        else:
            condition['status'] = 'stable'

        self.patient_condition_summary = condition
        return condition

    def get_structured_answers(self):
        self.analyze_patient_condition()
        return {
            "patient_name": self.patient_context.get('name'),
            "patient_language": self.patient_language,
            "checkin_date": datetime.now().isoformat(),
            "responses": self.answers,
            "complete": self.is_checkin_complete(),
            "condition_summary": self.patient_condition_summary,
            "conversation_history": self.conversation_history[-10:]
        }

    def process_message(self, message):
        """Main method to process user messages"""
        message_lower = message.lower()

        # CRITICAL EMERGENCY ONLY
        critical_emergency = ['हार्ट अटैक', 'heart attack', 'सांस नहीं', "can't breathe", 'बेहोश', 'unconscious']

        if any(k in message_lower for k in critical_emergency):
            response = "🚨 यह गंभीर है! मैं तुरंत डॉक्टर को सूचित कर रहा हूँ।"
            return {'text': response, 'emergency': True, 'escalate': True, 'checkin_complete': self.is_checkin_complete()}

        # IMPORTANT FIX: Process first message correctly
        if not self.greeting_done:
            # This is the first message after greeting
            self.greeting_done = True

            # Record the answer to first question
            self.record_answer(message)

            # Move to next question index
            next_q = self.get_next_question()

            if next_q:
                response = next_q
            else:
                response = self.get_farewell()

        elif not self.is_checkin_complete():
            # Normal flow: record answer, then ask next question
            self.record_answer(message)
            next_q = self.get_next_question()
            if next_q:
                response = next_q
            else:
                response = self.get_farewell()
        else:
            response = self.get_farewell()

        # Store conversation history
        self.conversation_history.append({'role': 'user', 'text': message})
        self.conversation_history.append({'role': 'assistant', 'text': response})

        return {
            'text': response,
            'emergency': False,
            'escalate': False,
            'checkin_complete': self.is_checkin_complete()
        }


# Test function
if __name__ == "__main__":
    print("=" * 50)
    print("Testing Conversation Engine with 14 Questions")
    print("=" * 50)

    conv = SimpleConversation('hindi')
    conv.set_patient_context({'name': 'राम कुमार'})

    # Get greeting (includes first question)
    greeting = conv.get_greeting()
    print(f"AI: {greeting}")

    # Simulate patient answers
    test_answers = [
        "75 kg",
        "2 kg",
        "कोई नहीं",
        "कोई नहीं",
        "क्रोसिन, एटेन",
        "नहीं",
        "120/80",
        "100",
        "नहीं",
        "नहीं",
        "नहीं",
        "नहीं",
        "नहीं",
        "नहीं"
    ]

    for i, ans in enumerate(test_answers):
        print(f"\n👤 Patient: {ans}")
        result = conv.process_message(ans)
        print(f"🤖 AI: {result['text']}")
        if result['checkin_complete']:
            print("\n✅ Check-in complete!")
            break

    print("\n📊 Final Summary:")
    print(json.dumps(conv.get_structured_answers(), indent=2, ensure_ascii=False)[:500])