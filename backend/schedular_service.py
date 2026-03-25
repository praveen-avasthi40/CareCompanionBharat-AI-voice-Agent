"""
Auto Call Scheduler Service
Background thread jo scheduled time pe automatically call trigger karega
"""

import threading
import time
from datetime import datetime, timedelta
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os

class AutoCallScheduler:
    """
    Automatic call scheduler that runs in background
    """

    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.scheduler = BackgroundScheduler()
        self.scheduled_jobs = {}
        self.running = False

    def start(self):
        """Start the background scheduler"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            print("✅ Auto-Call Scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            print("⏹️ Auto-Call Scheduler stopped")

    def schedule_patient_call(self, patient_id, patient_name, phone, call_time, call_type="followup"):
        """
        Schedule a call for a specific patient at specific time

        Args:
            patient_id: Patient ID
            patient_name: Patient name
            phone: Phone number
            call_time: datetime object when to call
            call_type: welcome, medication, followup, checkup
        """
        job_id = f"{patient_id}_{call_type}_{call_time.timestamp()}"

        # Remove existing job if any
        if job_id in self.scheduled_jobs:
            self.scheduler.remove_job(job_id)

        # Schedule the job
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

        print(f"📅 Scheduled {call_type} call for {patient_name} at {call_time}")
        return job_id

    def schedule_recurring_calls(self, patient_id, patient_name, phone, schedule_config):
        """
        Schedule recurring calls based on risk level

        Args:
            patient_id: Patient ID
            patient_name: Patient name
            phone: Phone number
            schedule_config: dict with days and times
                Example: {"days": [1,3,7], "time": "10:00"}
        """
        scheduled = []
        for day in schedule_config.get("days", []):
            call_time = datetime.now().replace(hour=int(schedule_config["time"].split(":")[0]),
                                               minute=int(schedule_config["time"].split(":")[1]),
                                               second=0, microsecond=0)
            call_time = call_time + timedelta(days=day)

            job_id = self.schedule_patient_call(
                patient_id, patient_name, phone, call_time, "followup"
            )
            scheduled.append(job_id)

        return scheduled

    def _make_call(self, patient_id, patient_name, phone, call_type):
        """Internal function to make the actual call"""
        print(f"📞 AUTO-CALL TRIGGERED: Calling {patient_name} ({phone}) for {call_type}")

        try:
            # Call the backend /call/initiate endpoint
            response = requests.post(
                f"{self.api_url}/call/initiate",
                params={
                    "patient_id": patient_id,
                    "language": "hindi",  # Auto-detect from patient data
                    "auto": True  # Flag to indicate auto call
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Auto-call initiated for {patient_name}: {data.get('call_sid', 'N/A')}")
                return {"success": True, "call_sid": data.get('call_sid')}
            else:
                print(f"❌ Auto-call failed for {patient_name}: {response.status_code}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"❌ Auto-call error for {patient_name}: {e}")
            return {"success": False, "error": str(e)}

    def get_scheduled_calls(self):
        """Get all scheduled calls"""
        return list(self.scheduled_jobs.values())

    def cancel_scheduled_call(self, job_id):
        """Cancel a scheduled call"""
        if job_id in self.scheduled_jobs:
            self.scheduler.remove_job(job_id)
            del self.scheduled_jobs[job_id]
            return True
        return False

    def cancel_all_patient_calls(self, patient_id):
        """Cancel all scheduled calls for a patient"""
        cancelled = []
        for job_id, job in list(self.scheduled_jobs.items()):
            if job['patient_id'] == patient_id:
                self.scheduler.remove_job(job_id)
                del self.scheduled_jobs[job_id]
                cancelled.append(job_id)
        return cancelled


# Global scheduler instance
_scheduler = None

def get_scheduler():
    """Get or create global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AutoCallScheduler()
    return _scheduler