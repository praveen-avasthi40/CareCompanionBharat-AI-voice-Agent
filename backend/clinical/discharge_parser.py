import re
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta

class DischargeParser:
    """
    Parse Indian hospital discharge summaries
    Handles Hindi/English mix, Indian medicine names, dates in DD/MM/YYYY
    """

    def __init__(self):
        # Common Indian medicine brands with generic names
        self.medicine_db = {
            # Pain relievers
            'crocin': {'generic': 'Paracetamol', 'category': 'analgesic', 'typical_dosage': '500mg', 'frequency': 'BD'},
            'dolo': {'generic': 'Paracetamol', 'category': 'analgesic', 'typical_dosage': '650mg', 'frequency': 'BD'},
            'calpol': {'generic': 'Paracetamol', 'category': 'analgesic', 'typical_dosage': '500mg', 'frequency': 'BD'},
            'combiflam': {'generic': 'Ibuprofen + Paracetamol', 'category': 'analgesic', 'typical_dosage': '400mg', 'frequency': 'BD'},

            # Antibiotics
            'mox': {'generic': 'Amoxicillin', 'category': 'antibiotic', 'typical_dosage': '500mg', 'frequency': 'TDS'},
            'novamox': {'generic': 'Amoxicillin', 'category': 'antibiotic', 'typical_dosage': '500mg', 'frequency': 'TDS'},
            'azithral': {'generic': 'Azithromycin', 'category': 'antibiotic', 'typical_dosage': '500mg', 'frequency': 'OD'},

            # Heart/BP
            'aten': {'generic': 'Atenolol', 'category': 'beta_blocker', 'typical_dosage': '25mg', 'frequency': 'OD'},
            'ecosprin': {'generic': 'Aspirin', 'category': 'antiplatelet', 'typical_dosage': '75mg', 'frequency': 'OD'},
            'storvas': {'generic': 'Atorvastatin', 'category': 'statin', 'typical_dosage': '10mg', 'frequency': 'HS'},

            # Diabetes
            'glyciphage': {'generic': 'Metformin', 'category': 'antidiabetic', 'typical_dosage': '500mg', 'frequency': 'BD'},
            'metfor': {'generic': 'Metformin', 'category': 'antidiabetic', 'typical_dosage': '850mg', 'frequency': 'BD'},
            'glimestar': {'generic': 'Glimepiride', 'category': 'antidiabetic', 'typical_dosage': '2mg', 'frequency': 'OD'},
        }

        # Common Indian conditions (Hindi + English)
        self.condition_keywords = {
            'heart_attack': {
                'keywords': ['हार्ट अटैक', 'दिल का दौरा', 'myocardial infarction', 'mi', 'heart attack'],
                'severity': 'high',
                'emergency_signs': ['chest pain', 'shortness of breath', 'sweating', 'nausea']
            },
            'diabetes': {
                'keywords': ['डायबिटीज', 'मधुमेह', 'sugar', 'diabetes mellitus', 'diabetes'],
                'severity': 'medium',
                'emergency_signs': ['very high sugar', 'fainting', 'excessive thirst', 'weakness']
            },
            'hypertension': {
                'keywords': ['बीपी', 'high bp', 'हाई बीपी', 'hypertension', 'blood pressure'],
                'severity': 'medium',
                'emergency_signs': ['severe headache', 'blurred vision', 'chest pain', 'nose bleeding']
            },
            'stroke': {
                'keywords': ['स्ट्रोक', 'लकवा', 'paralysis', 'brain attack', 'stroke'],
                'severity': 'critical',
                'emergency_signs': ['facial droop', 'arm weakness', 'speech difficulty', 'confusion']
            },
            'pneumonia': {
                'keywords': ['निमोनिया', 'pneumonia', 'chest infection', 'lung infection'],
                'severity': 'high',
                'emergency_signs': ['high fever', 'difficulty breathing', 'chest pain', 'cough with blood']
            },
            'fracture': {
                'keywords': ['फ्रैक्चर', 'हड्डी टूटी', 'fracture', 'broken bone'],
                'severity': 'medium',
                'emergency_signs': ['severe pain', 'swelling', 'numbness', 'cannot move']
            },
            'surgery': {
                'keywords': ['surgery', 'operation', 'सर्जरी', 'ऑपरेशन'],
                'severity': 'high',
                'emergency_signs': ['bleeding', 'infection', 'fever', 'severe pain']
            }
        }

        # Frequency mapping for reminders
        self.frequency_map = {
            'OD': ['08:00'],
            'BD': ['08:00', '20:00'],
            'TDS': ['08:00', '14:00', '20:00'],
            'QID': ['08:00', '12:00', '16:00', '20:00'],
            'HS': ['22:00']
        }

    def parse(self, text: str) -> Dict:
        """
        Main parse function - extract all information
        """
        text = text.strip()
        text_lower = text.lower()

        result = {
            'patient_name': self._extract_name(text),
            'age': self._extract_age(text),
            'gender': self._extract_gender(text),
            'admission_date': self._extract_date(text, 'admission'),
            'discharge_date': self._extract_date(text, 'discharge'),
            'diagnosis': self._extract_diagnosis(text_lower),
            'medications': self._extract_medications(text),
            'follow_up': self._extract_followup(text),
            'doctor_notes': self._extract_notes(text),
            'hospital': self._extract_hospital(text),
            'risk_level': self._calculate_risk(text_lower)
        }

        # Generate follow-up plan
        result['follow_up_plan'] = self._generate_plan(result)

        # Add emergency rules
        result['emergency_rules'] = self._get_emergency_rules(result['diagnosis'])

        return result

    def _extract_name(self, text: str) -> str:
        """Extract patient name - supports Hindi and English"""
        patterns = [
            r'(?:Name|Patient Name|नाम|मरीज का नाम)\s*[:\-]?\s*([A-Za-z\s]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*(?:Age|उम्र|M/F)',
            r'(?:Mr\.|Mrs\.|Ms\.|श्री|श्रीमती)\s*([A-Za-z\s]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 1:
                    return name
        return "Unknown Patient"

    def _extract_age(self, text: str) -> int:
        """Extract age"""
        patterns = [
            r'(?:Age|उम्र|Years?|साल)\s*[:\-]?\s*(\d+)',
            r'(\d+)\s*(?:years?|yrs?|साल)',
            r'(\d+)\s*years?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 0

    def _extract_gender(self, text: str) -> str:
        """Extract gender"""
        if re.search(r'\b[Mm](?:ale)?\b|\bपुरुष\b|\b[Mm]r\.\b', text):
            return 'Male'
        elif re.search(r'\b[Ff](?:emale)?\b|\bमहिला\b|\b[Mm]rs\.\b|\b[Mm]s\.\b', text):
            return 'Female'
        return 'Unknown'

    def _extract_date(self, text: str, date_type: str) -> Optional[str]:
        """Extract dates in DD/MM/YYYY format"""
        # Indian date patterns
        patterns = {
            'admission': [
                r'(?:Admission|Admitted|आने की तारीख|IPD)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})\s*(?:to|to|से)',
                r'Admission Date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
            ],
            'discharge': [
                r'(?:Discharge|Discharged|जाने की तारीख)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'(?:to|to|से)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'Discharge Date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
            ]
        }

        for pattern in patterns.get(date_type, []):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).replace('-', '/')
                # Validate date format
                try:
                    datetime.strptime(date_str, '%d/%m/%Y')
                    return date_str
                except:
                    continue
        return None

    def _extract_diagnosis(self, text: str) -> List[Dict]:
        """Extract diagnosis/conditions with details"""
        found = []

        for condition, details in self.condition_keywords.items():
            for keyword in details['keywords']:
                if keyword in text:
                    found.append({
                        'name': condition.replace('_', ' ').title(),
                        'severity': details['severity'],
                        'emergency_signs': details['emergency_signs']
                    })
                    break

        return found

    def _extract_medications(self, text: str) -> List[Dict]:
        """Extract medicines with dosage and frequency"""
        medications = []

        # Enhanced patterns for Indian prescriptions
        patterns = [
            # Tab. Crocin 500 mg BD x 5 days
            r'(?:Tab\.?|T\.?|Inj\.?|Syp\.?)\s*([A-Za-z]+)\s+(\d+)\s*(mg|mcg|g|ml)\s*(?:([A-Z]+))?\s*(?:x\s*(\d+)\s*days?)?',
            # Crocin 500 mg BD
            r'([A-Za-z]+)\s+(\d+)\s*(mg|mcg)\s+([A-Z]+)',
            # Tab Crocin 500mg BD
            r'(?:Tab\.?|T\.?)\s*([A-Za-z]+)\s+(\d+)(?:mg|mcg)\s*([A-Z]+)',
        ]

        lines = text.split('\n')
        in_medicine_section = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect medicine section
            if re.search(r'(Medications?|दवाइयाँ|Prescriptions?|T\.A\.?)', line, re.IGNORECASE):
                in_medicine_section = True
                continue

            if in_medicine_section:
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        med_name = match.group(1).lower()

                        # Get dosage
                        if len(match.groups()) >= 3:
                            dosage = f"{match.group(2)} {match.group(3)}" if match.group(3) else f"{match.group(2)} mg"
                        else:
                            dosage = "As directed"

                        # Get frequency
                        if len(match.groups()) >= 4 and match.group(4):
                            frequency = match.group(4).upper()
                        else:
                            frequency = 'OD'  # Default

                        # Check if it's an Indian brand
                        brand_info = self.medicine_db.get(med_name, {})

                        med = {
                            'name': match.group(1).title(),
                            'dosage': dosage,
                            'frequency': frequency,
                            'frequency_times': self.frequency_map.get(frequency, ['08:00']),
                            'duration': match.group(5) if len(match.groups()) >= 5 and match.group(5) else None,
                            'generic_name': brand_info.get('generic', med_name.title()),
                            'category': brand_info.get('category', 'unknown')
                        }
                        medications.append(med)
                        break

        return medications

    def _extract_followup(self, text: str) -> Dict:
        """Extract follow-up information"""
        followup = {
            'date': None,
            'days': None,
            'department': None,
            'doctor': None,
            'instructions': []
        }

        # Follow-up patterns
        patterns = [
            r'(?:Follow up|Review|Next visit|अगली बार)\s*(?:on|after|को)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Follow up|Review|Next visit)\s*(?:in|after|में)\s*(\d+)\s*(days?|weeks?|months?)',
            r'(?:OPD|Clinic)\s*(?:after|in)\s*(\d+)\s*(days?|weeks?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if '/' in match.group(1) or '-' in match.group(1):
                    followup['date'] = match.group(1).replace('-', '/')
                else:
                    days = int(match.group(1))
                    if 'week' in match.group(2).lower():
                        days *= 7
                    elif 'month' in match.group(2).lower():
                        days *= 30
                    followup['days'] = days
                    followup['date'] = (datetime.now() + timedelta(days=days)).strftime('%d/%m/%Y')
                break

        # Department
        dept_match = re.search(r'(Cardiology|Ortho|Medicine|Surgery|Gynae|Pediatrics|Neurology|हृदय|हड्डी)', text, re.IGNORECASE)
        if dept_match:
            followup['department'] = dept_match.group(1)

        # Doctor
        doctor_match = re.search(r'(?:Doctor|Dr\.|डॉ\.)\s*([A-Za-z\s]+)', text, re.IGNORECASE)
        if doctor_match:
            followup['doctor'] = doctor_match.group(1).strip()

        return followup

    def _extract_notes(self, text: str) -> List[str]:
        """Extract doctor's notes and instructions"""
        notes = []
        in_notes = False
        note_section_keywords = ['Instructions', 'सलाह', 'Advice', 'Notes', 'Discharge Instructions']

        for line in text.split('\n'):
            line = line.strip()

            # Check for note section start
            for keyword in note_section_keywords:
                if re.search(keyword, line, re.IGNORECASE):
                    in_notes = True
                    continue

            if in_notes and line and len(line) > 5:
                if not re.match(r'^(Medications|Diagnosis|Follow)', line, re.IGNORECASE):
                    notes.append(line)

            # Stop if we hit another section
            if in_notes and re.match(r'^(Medications|Diagnosis|Follow)', line, re.IGNORECASE):
                break

        return notes[:8]  # Max 8 notes

    def _extract_hospital(self, text: str) -> str:
        """Extract hospital name"""
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:Hospital|अस्पताल)',
            r'(?:Hospital|अस्पताल)\s*[:\-]?\s*([A-Za-z\s]+)',
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hospital = match.group(1).strip()
                if len(hospital) > 3:
                    return hospital

        return "Unknown Hospital"

    def _calculate_risk(self, text: str) -> str:
        """Calculate overall risk level based on conditions"""
        risk_levels = []

        for condition, details in self.condition_keywords.items():
            for keyword in details['keywords']:
                if keyword in text:
                    risk_levels.append(details['severity'])
                    break

        if 'critical' in risk_levels:
            return 'critical'
        elif 'high' in risk_levels:
            return 'high'
        elif 'medium' in risk_levels:
            return 'medium'
        return 'low'

    def _get_emergency_rules(self, diagnoses: List[Dict]) -> List[Dict]:
        """Get emergency rules based on diagnosis"""
        rules = []

        for diag in diagnoses:
            for sign in diag.get('emergency_signs', []):
                rules.append({
                    'condition': diag['name'],
                    'symptom': sign,
                    'action': 'IMMEDIATE DOCTOR NOTIFICATION',
                    'severity': diag['severity']
                })

        return rules

    def _generate_plan(self, data: Dict) -> Dict:
        """Generate follow-up plan based on diagnosis"""
        plan = {
            'call_schedule': [],
            'warning_signs': [],
            'medication_reminders': [],
            'next_appointment': None
        }

        # Default schedule
        base_schedule = [1, 3, 7, 14]

        # Adjust based on risk
        if data['risk_level'] == 'critical':
            base_schedule = [1, 2, 3, 4, 5, 6, 7, 14]
        elif data['risk_level'] == 'high':
            base_schedule = [1, 2, 3, 5, 7, 14]

        for day in base_schedule:
            plan['call_schedule'].append({
                'day': day,
                'date': (datetime.now() + timedelta(days=day)).strftime('%d/%m/%Y'),
                'type': 'followup' if day > 7 else 'checkup',
                'time': '10:00'
            })

        # Add warning signs from all diagnoses
        for diag in data['diagnosis']:
            plan['warning_signs'].extend(diag.get('emergency_signs', []))

        # Remove duplicates
        plan['warning_signs'] = list(set(plan['warning_signs']))

        # Medication reminders
        for med in data['medications']:
            reminder = {
                'medicine': med['name'],
                'generic': med['generic_name'],
                'dosage': med['dosage'],
                'frequency': med['frequency'],
                'times': med['frequency_times']
            }
            plan['medication_reminders'].append(reminder)

        # Next appointment from follow-up
        if data.get('follow_up', {}).get('date'):
            plan['next_appointment'] = data['follow_up']['date']

        return plan


# Test function
if __name__ == "__main__":
    parser = DischargeParser()

    # Sample Indian discharge summary
    sample_summary = """
    AIIMS New Delhi
    Discharge Summary
    
    Patient Name: Rajesh Kumar
    Age: 55 years
    Gender: Male
    
    Admission Date: 15/03/2025
    Discharge Date: 18/03/2025
    
    Diagnosis:
    - Acute Myocardial Infarction (हार्ट अटैक)
    - Hypertension (हाई बीपी)
    
    Medications:
    Tab. Crocin 500 mg BD x 5 days
    Tab. Aten 25 mg OD
    Tab. Ecosprin 75 mg OD
    Tab. Storvas 10 mg HS
    
    Follow up: After 1 week in Cardiology OPD
    
    Instructions:
    - Complete bed rest for 1 week
    - Low salt diet
    - Report if chest pain occurs
    - Take medicines on time
    """

    print("🔍 Parsing discharge summary...")
    result = parser.parse(sample_summary)

    print("\n📋 Extracted Information:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n📅 Follow-up Plan:")
    print(json.dumps(result['follow_up_plan'], indent=2, ensure_ascii=False))