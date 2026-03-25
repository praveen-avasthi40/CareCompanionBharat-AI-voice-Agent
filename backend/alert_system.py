import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText

class AlertSystem:
    """
    Automatic alert system for emergencies
    """

    def __init__(self):
        self.emergency_keywords = {
            'critical': [
                'heart attack', 'हार्ट अटैक', 'bleeding', 'खून',
                'unconscious', 'बेहोश', 'can\'t breathe', 'सांस नहीं'
            ],
            'high': [
                'severe pain', 'बहुत दर्द', 'high fever', 'तेज बुखार',
                'fall', 'गिर गया', 'chest pain', 'सीने में दर्द'
            ],
            'medium': [
                'medicine', 'दवा', 'missed', 'छूट गया',
                'anxious', 'घबराहट', 'dizzy', 'चक्कर'
            ]
        }

    def detect_emergency(self, message, patient_name, patient_phone):
        """Check if message contains emergency keywords"""
        message_lower = message.lower()

        for level, keywords in self.emergency_keywords.items():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    return {
                        "level": level,
                        "keyword": keyword,
                        "patient": patient_name,
                        "phone": patient_phone,
                        "message": message,
                        "time": datetime.now()
                    }
        return None

    def send_alert(self, emergency, doctor_email="doctor@hospital.com"):
        """Send alert to doctor"""
        if emergency['level'] == 'critical':
            subject = f"🚨 CRITICAL EMERGENCY - {emergency['patient']}"
            body = f"""
            EMERGENCY ALERT
            
            Patient: {emergency['patient']}
            Phone: {emergency['phone']}
            Time: {emergency['time']}
            
            Detected Keyword: {emergency['keyword']}
            Message: {emergency['message']}
            
            ACTION REQUIRED IMMEDIATELY!
            """
            # Here you would send email/SMS
            print(f"📧 CRITICAL ALERT SENT: {subject}")

        elif emergency['level'] == 'high':
            print(f"⚠️ HIGH ALERT: {emergency['patient']} - {emergency['keyword']}")
        else:
            print(f"ℹ️ MEDIUM ALERT: {emergency['patient']} - {emergency['keyword']}")

        return {"sent": True, "level": emergency['level']}

    def log_emergency(self, emergency):
        """Log emergency to database"""
        # Here you would save to database
        print(f"📝 Emergency logged: {emergency['patient']} at {emergency['time']}")


# Auto-monitor conversation
class EmergencyMonitor:
    def __init__(self):
        self.alert_system = AlertSystem()
        self.monitored_conversations = []

    def start_monitoring(self, patient_id, patient_name, patient_phone):
        """Start monitoring patient conversations"""
        self.monitored_conversations.append({
            "patient_id": patient_id,
            "name": patient_name,
            "phone": patient_phone,
            "messages": []
        })

    def check_message(self, patient_id, message):
        """Check each message for emergencies"""
        # Find patient
        patient = None
        for p in self.monitored_conversations:
            if p['patient_id'] == patient_id:
                patient = p
                break

        if patient:
            # Add to history
            patient['messages'].append(message)

            # Check for emergency
            emergency = self.alert_system.detect_emergency(
                message, patient['name'], patient['phone']
            )

            if emergency:
                self.alert_system.send_alert(emergency)
                self.alert_system.log_emergency(emergency)
                return emergency

        return None