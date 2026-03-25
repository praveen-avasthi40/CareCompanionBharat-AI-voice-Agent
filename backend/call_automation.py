"""
Call Automation System for Post-Discharge Follow-up
"""

import json
import os
from datetime import datetime, timedelta

class CallAutomation:
    """
    Call automation for post-discharge follow-up
    """

    def __init__(self, data_file="schedule_data.json"):
        self.data_file = data_file
        self.patients = {}
        self.call_log = []
        self._load()

    def register_patient(self, patient_data: dict) -> dict:
        """
        Register new patient and generate call schedule

        Args:
            patient_data: dict with id, name, phone, condition, risk, discharge_date

        Returns:
            dict with patient_id and schedule
        """
        patient_id = patient_data.get('id', f"P{len(self.patients)+1:03d}")
        risk = patient_data.get('risk', 'medium')
        condition = patient_data.get('condition', '').lower()

        # Generate schedule based on risk and condition
        schedule = self._generate_schedule(patient_data)

        self.patients[patient_id] = {
            "data": patient_data,
            "schedule": schedule,
            "calls_completed": [],
            "missed_calls": 0,
            "risk": risk,
            "registered_date": datetime.now().isoformat()
        }

        self._save()
        return {"patient_id": patient_id, "schedule": schedule}

    def _generate_schedule(self, patient_data: dict) -> list:
        """Generate personalized call schedule"""
        risk = patient_data.get('risk', 'medium')
        discharge_date = patient_data.get('discharge_date')

        if discharge_date and isinstance(discharge_date, str):
            try:
                discharge_date = datetime.strptime(discharge_date, '%d/%m/%Y')
            except:
                discharge_date = datetime.now()
        else:
            discharge_date = datetime.now()

        schedule = []

        # Base schedule for all patients
        schedule.append({
            "day": 1,
            "date": (discharge_date + timedelta(days=1)).strftime('%d/%m/%Y'),
            "time": "10:00",
            "type": "welcome",
            "priority": "normal"
        })

        schedule.append({
            "day": 3,
            "date": (discharge_date + timedelta(days=3)).strftime('%d/%m/%Y'),
            "time": "09:00",
            "type": "medication_check",
            "priority": "normal"
        })

        schedule.append({
            "day": 7,
            "date": (discharge_date + timedelta(days=7)).strftime('%d/%m/%Y'),
            "time": "10:00",
            "type": "followup",
            "priority": "normal"
        })

        # Additional calls for high risk
        if risk == 'high':
            schedule.append({
                "day": 2,
                "date": (discharge_date + timedelta(days=2)).strftime('%d/%m/%Y'),
                "time": "10:00",
                "type": "checkup",
                "priority": "high"
            })
            schedule.append({
                "day": 5,
                "date": (discharge_date + timedelta(days=5)).strftime('%d/%m/%Y'),
                "time": "10:00",
                "type": "checkup",
                "priority": "high"
            })

        # Additional calls for critical risk
        if risk == 'critical':
            schedule.append({
                "day": 2,
                "date": (discharge_date + timedelta(days=2)).strftime('%d/%m/%Y'),
                "time": "09:00",
                "type": "morning_check",
                "priority": "critical"
            })
            schedule.append({
                "day": 2,
                "date": (discharge_date + timedelta(days=2)).strftime('%d/%m/%Y'),
                "time": "18:00",
                "type": "evening_check",
                "priority": "critical"
            })
            schedule.append({
                "day": 4,
                "date": (discharge_date + timedelta(days=4)).strftime('%d/%m/%Y'),
                "time": "09:00",
                "type": "morning_check",
                "priority": "critical"
            })
            schedule.append({
                "day": 4,
                "date": (discharge_date + timedelta(days=4)).strftime('%d/%m/%Y'),
                "time": "18:00",
                "type": "evening_check",
                "priority": "critical"
            })

        return schedule

    def get_today_calls(self) -> list:
        """Get calls scheduled for today"""
        today = datetime.now().strftime('%d/%m/%Y')
        today_calls = []

        for patient_id, status in self.patients.items():
            for call in status['schedule']:
                if call['date'] == today:
                    today_calls.append({
                        "patient_id": patient_id,
                        "patient_name": status['data']['name'],
                        "phone": status['data']['phone'],
                        "time": call['time'],
                        "type": call['type'],
                        "priority": call['priority']
                    })

        return sorted(today_calls, key=lambda x: x['time'])

    def get_pending_calls(self) -> list:
        """Get pending/overdue calls"""
        now = datetime.now()
        current_time = now.strftime('%H:%M')

        pending = []
        for call in self.get_today_calls():
            if call['time'] < current_time:
                pending.append(call)

        return pending

    def mark_call_completed(self, patient_id: str, call_type: str = None, success: bool = True, notes: str = ""):
        """Mark a call as completed"""
        if patient_id in self.patients:
            self.patients[patient_id]['calls_completed'].append({
                "type": call_type or "call",
                "date": datetime.now().strftime('%d/%m/%Y'),
                "time": datetime.now().strftime('%H:%M'),
                "success": success,
                "notes": notes
            })

            if not success:
                self.patients[patient_id]['missed_calls'] += 1

                # Escalate if 3 missed calls
                if self.patients[patient_id]['missed_calls'] >= 3:
                    self._escalate_patient(patient_id)

            self._save()

    def _escalate_patient(self, patient_id: str):
        """Escalate patient risk level due to missed calls"""
        if patient_id in self.patients:
            old_risk = self.patients[patient_id]['risk']
            risk_order = {'low': 'medium', 'medium': 'high', 'high': 'critical'}
            new_risk = risk_order.get(old_risk, 'critical')

            self.patients[patient_id]['risk'] = new_risk
            print(f"🚨 Patient {patient_id} escalated from {old_risk} to {new_risk}")

    def get_status(self) -> dict:
        """Get automation status"""
        return {
            "total_patients": len(self.patients),
            "today_calls": len(self.get_today_calls()),
            "pending_calls": len(self.get_pending_calls()),
            "high_risk": sum(1 for p in self.patients.values() if p['risk'] in ['high', 'critical']),
            "missed_calls_total": sum(p['missed_calls'] for p in self.patients.values())
        }

    def get_patient(self, patient_id: str) -> dict:
        """Get patient data by ID"""
        return self.patients.get(patient_id, None)

    def get_all_patients(self) -> dict:
        """Get all registered patients"""
        return self.patients

    def _save(self):
        """Save data to file"""
        try:
            data = {
                "patients": self.patients,
                "call_log": self.call_log
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Save error: {e}")

    def _load(self):
        """Load data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.patients = data.get("patients", {})
                    self.call_log = data.get("call_log", [])
            except Exception as e:
                print(f"Load error: {e}")


# ===== TEST =====
if __name__ == "__main__":
    print("🔍 Testing CallAutomation...")

    auto = CallAutomation()

    # Test patient
    test_patient = {
        "id": "TEST001",
        "name": "राम कुमार",
        "phone": "+919876543210",
        "condition": "Heart Attack",
        "risk": "high",
        "discharge_date": datetime.now().strftime('%d/%m/%Y')
    }

    result = auto.register_patient(test_patient)
    print(f"✅ Patient registered: {result['patient_id']}")
    print(f"📅 Schedule: {len(result['schedule'])} calls")

    print(f"\n📊 Today's calls: {len(auto.get_today_calls())}")
    print(f"📈 Status: {auto.get_status()}")

    print("\n✅ CallAutomation ready!")