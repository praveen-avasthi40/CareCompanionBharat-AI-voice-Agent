import schedule
import time
import threading
from datetime import datetime, timedelta
import requests

class CallScheduler:
    """
    Automatic call scheduler for patients
    """

    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.scheduled_calls = []
        self.running = False

    def schedule_daily_check(self, patient_id, phone, time_str="10:00"):
        """Schedule daily follow-up call"""
        schedule.every().day.at(time_str).do(
            self.trigger_call, patient_id, phone, "daily_check"
        )
        return f"Scheduled daily check for patient {patient_id} at {time_str}"

    def schedule_medication_reminder(self, patient_id, phone, medicine, time_str="09:00"):
        """Schedule medicine reminder"""
        schedule.every().day.at(time_str).do(
            self.trigger_call, patient_id, phone, "medication_reminder", medicine
        )
        return f"Scheduled medicine reminder for {medicine} at {time_str}"

    def schedule_followup(self, patient_id, phone, days_from_now=7):
        """Schedule follow-up call after X days"""
        followup_date = datetime.now() + timedelta(days=days_from_now)
        # Store in database
        self.scheduled_calls.append({
            "patient_id": patient_id,
            "phone": phone,
            "date": followup_date,
            "type": "followup"
        })
        return f"Scheduled follow-up for {patient_id} on {followup_date.strftime('%d/%m/%Y')}"

    def trigger_call(self, patient_id, phone, call_type, medicine=None):
        """Trigger actual call"""
        print(f"📞 Calling {phone} for {call_type}")
        # Here you would integrate with Twilio or other call service
        return {"status": "call_initiated", "patient_id": patient_id}

    def start(self):
        """Start scheduler in background"""
        self.running = True
        thread = threading.Thread(target=self._run)
        thread.daemon = True
        thread.start()

    def _run(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        self.running = False


# ===== POST-DISCHARGE AUTO CALL PLAN =====
def auto_schedule_patient_calls(patient_data):
    """
    Automatically schedule calls based on discharge plan
    """
    scheduler = CallScheduler()

    patient_id = patient_data.get('id')
    phone = patient_data.get('phone')
    condition = patient_data.get('condition', '').lower()

    # Call schedule based on condition
    schedule_plan = []

    if 'heart' in condition or 'cardiac' in condition:
        # Heart patients - more frequent calls
        schedule_plan = [
            {"days": 1, "type": "welcome", "time": "10:00"},
            {"days": 2, "type": "symptom_check", "time": "10:00"},
            {"days": 3, "type": "medication", "time": "09:00"},
            {"days": 5, "type": "medication", "time": "09:00"},
            {"days": 7, "type": "followup", "time": "10:00"},
            {"days": 14, "type": "final", "time": "10:00"}
        ]
    elif 'diabetes' in condition:
        schedule_plan = [
            {"days": 1, "type": "welcome", "time": "10:00"},
            {"days": 3, "type": "sugar_check", "time": "09:00"},
            {"days": 7, "type": "medication", "time": "09:00"},
            {"days": 14, "type": "followup", "time": "10:00"}
        ]
    else:
        # Default schedule
        schedule_plan = [
            {"days": 1, "type": "welcome", "time": "10:00"},
            {"days": 3, "type": "medication", "time": "09:00"},
            {"days": 7, "type": "followup", "time": "10:00"}
        ]

    # Schedule all calls
    results = []
    for item in schedule_plan:
        call_date = datetime.now() + timedelta(days=item['days'])
        results.append({
            "date": call_date.strftime("%d/%m/%Y"),
            "time": item['time'],
            "type": item['type']
        })

    return results


# Test
if __name__ == "__main__":
    scheduler = CallScheduler()
    scheduler.start()

    # Schedule a test call
    scheduler.schedule_daily_check("P001", "+919876543210", "10:00")

    print("Scheduler running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()