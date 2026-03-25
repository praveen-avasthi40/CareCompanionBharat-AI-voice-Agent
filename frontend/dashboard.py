import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import plotly.express as px


# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="CareCompanion Bharat",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Poppins', sans-serif; }
    .gradient-header {
        background: linear-gradient(135deg, #FF9933 0%, #FFCC00 50%, #138808 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        animation: fadeInDown 0.8s ease;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
        background: rgba(255, 255, 255, 0.35);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .patient-card {
        background: black;
        border-radius: 20px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 5px solid #FF9933;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .patient-card:hover {
        transform: translateX(5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-left-width: 8px;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 20px 20px 5px 20px;
        margin: 0.5rem 0;
        max-width: 80%;
        float: right;
        clear: both;
        animation: slideInRight 0.3s ease;
    }
    .ai-message {
        background: #f0f2f6;
        color: #1e293b;
        padding: 0.8rem 1.2rem;
        border-radius: 20px 20px 20px 5px;
        margin: 0.5rem 0;
        max-width: 80%;
        float: left;
        clear: both;
        animation: slideInLeft 0.3s ease;
        border-left: 3px solid #FF9933;
    }
    .emergency-message {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 20px;
        margin: 0.5rem 0;
        animation: pulse 1s infinite;
        border: 2px solid #ff0000;
    }
    .stButton button {
        background: linear-gradient(135deg, #FF9933 0%, #FFCC00 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(255, 153, 51, 0.4);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255,153,51,0.3);
        transform: translateY(-2px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF9933 0%, #FFCC00 100%);
        color: white;
    }
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .status-completed { background: #10b981; color: white; }
    .status-pending { background: #f59e0b; color: white; }
    .status-escalated { background: #ef4444; color: white; animation: pulse 1s infinite; }
    .status-progress { background: #3b82f6; color: white; }
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(50px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-50px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    @media (max-width: 768px) {
        .gradient-header { padding: 1rem; }
        .metric-card { padding: 0.8rem; margin-bottom: 0.5rem; }
        .user-message, .ai-message { max-width: 95%; }
    }
</style>
""", unsafe_allow_html=True)

# ===== SAMPLE PATIENTS =====
def get_patients():
    return {
        "P001": {"name": "राम कुमार", "age": 55, "language": "Hindi", "gender": "Male", "condition": "Heart Attack", "medicines": ["Crocin 500mg", "Aten 25mg", "Ecosprin 75mg"], "phone": "+919617043074", "status": "pending", "risk": "high", "last_call": "2 hours ago"},
        "P002": {"name": "सीता देवी", "age": 62, "language": "Hindi", "gender": "Female", "condition": "Diabetes", "medicines": ["Glyciphage 500mg", "Metfor 850mg"], "phone": "+919171013806", "status": "completed", "risk": "medium", "last_call": "1 day ago"},
        "P003": {"name": "M. Rajan", "age": 48, "language": "Tamil", "gender": "Male", "condition": "Stroke", "medicines": ["Storvas 10mg", "Ecosprin 75mg"], "phone": "+919171013806", "status": "in_progress", "risk": "high", "last_call": "30 min ago"},
        "P004": {"name": "रहीम खान", "age": 45, "language": "Urdu", "gender": "Male", "condition": "Hypertension", "medicines": ["Amlodipine 5mg", "Losartan 50mg"], "phone": "+919171013806", "status": "escalated", "risk": "critical", "last_call": "15 min ago"},
        "P005": {"name": "लक्ष्मी बाई", "age": 58, "language": "Marathi", "gender": "Female", "condition": "Surgery", "medicines": ["Paracetamol 650mg", "Augmentin 625mg"], "phone": "+919171013806", "status": "pending", "risk": "medium", "last_call": "5 hours ago"},
        "P006": {"name": "Priya Singh", "age": 35, "language": "English", "gender": "Female", "condition": "Pneumonia", "medicines": ["Azithromycin 500mg", "Dolo 650mg"], "phone": "+919171013806", "status": "completed", "risk": "low", "last_call": "2 days ago"},
        "P007": {"name": "अब्दुल्ला खान", "age": 52, "language": "Urdu", "gender": "Male", "condition": "Heart Attack", "medicines": ["Ecosprin 75mg", "Storvas 10mg"], "phone": "+919171013806", "status": "pending", "risk": "high", "last_call": "1 hour ago"},
        "P008": {"name": "K. Rajeshwari", "age": 41, "language": "Tamil", "gender": "Female", "condition": "Diabetes", "medicines": ["Metfor 850mg", "Glimestar 2mg"], "phone": "+919171013806", "status": "in_progress", "risk": "medium", "last_call": "45 min ago"}
    }

# ===== SESSION STATE =====
if 'patients' not in st.session_state:
    st.session_state.patients = get_patients()
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'emergencies' not in st.session_state:
    st.session_state.emergencies = []
if 'call_history' not in st.session_state:
    st.session_state.call_history = []
if 'scheduled_calls' not in st.session_state:
    st.session_state.scheduled_calls = []
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

# ===== API CONNECTION =====
API_URL = "http://localhost:8000"
api_connected = False
try:
    response = requests.get(f"{API_URL}/health", timeout=2)
    if response.status_code == 200:
        api_connected = True
except:
    pass

# ===== HEADER =====
st.markdown("""
<div class='gradient-header'>
    <h1 style='color: white; text-align: center; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>
        🏥 केयरकंपेनियन भारत
    </h1>
    <h3 style='color: white; text-align: center; margin-top: 0.5rem; opacity: 0.95;'>
        AI-Powered Post-Discharge Follow-up System
    </h3>
</div>
""", unsafe_allow_html=True)

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <h2 style='color: #FF9933;'>🏥 केयरकंपेनियन</h2>
        <h4 style='color: #138808;'>भारत</h4>
        <hr style='border-color: #FF9933;'>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 🏥 Hospital")
    hospital = st.selectbox("Select Hospital", ["AIIMS Delhi", "CMC Vellore", "KEM Mumbai", "PGI Chandigarh", "Apollo Hyderabad"])
    st.markdown("### 👨‍⚕️ Doctor")
    doctor = st.selectbox("Select Doctor", ["Dr. Sharma (Cardiology)", "Dr. Patel (Medicine)", "Dr. Rao (Surgery)"])
    if api_connected:
        st.success("✅ API Connected")
    else:
        st.warning("⚠️ Demo Mode")
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    all_languages = ["Hindi", "Tamil", "Telugu", "Bengali", "English", "Marathi", "Urdu"]
    selected_langs = st.multiselect("Languages", all_languages, default=all_languages)
    all_risks = ["low", "medium", "high", "critical"]
    selected_risks = st.multiselect("Risk Level", all_risks, default=all_risks)
    all_status = ["pending", "in_progress", "completed", "escalated"]
    selected_status = st.multiselect("Status", all_status, default=all_status)
    st.markdown("---")
    st.session_state.auto_refresh = st.toggle("🔄 Auto-refresh (5s)", value=False)
    st.markdown(f"**📅 {datetime.now().strftime('%d %B %Y')}**")
    st.markdown(f"**🕐 {datetime.now().strftime('%I:%M %p')}**")

# ===== MAIN CONTENT =====
st.markdown(f"""
<div style='animation: fadeInUp 0.6s ease;'>
    <h2>👋 Welcome back, {doctor}</h2>
    <p><strong>🏥 {hospital}</strong> | 📅 {datetime.now().strftime('%d %B %Y')}</p>
</div>
""", unsafe_allow_html=True)

# ===== KEY METRICS =====
col1, col2, col3, col4, col5 = st.columns(5)
total = len(st.session_state.patients)
completed = sum(1 for p in st.session_state.patients.values() if p['status'] == 'completed')
escalated = sum(1 for p in st.session_state.patients.values() if p['status'] == 'escalated')
pending = sum(1 for p in st.session_state.patients.values() if p['status'] in ['pending', 'in_progress'])
critical = sum(1 for p in st.session_state.patients.values() if p.get('risk') == 'critical')
with col1:
    st.markdown(f"<div class='metric-card'><h3>📞 Total Patients</h3><h2 style='font-size: 2rem;'>{total}</h2><small>+2 today</small></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #10b981 0%, #059669 100%);'><h3>✅ Completed</h3><h2 style='font-size: 2rem;'>{completed}</h2><small>{int(completed/total*100)}%</small></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);'><h3>⏳ Pending</h3><h2 style='font-size: 2rem;'>{pending}</h2><small>active</small></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);'><h3>🚨 Escalated</h3><h2 style='font-size: 2rem;'>{escalated}</h2><small>{'urgent' if escalated > 0 else 'none'}</small></div>", unsafe_allow_html=True)
with col5:
    st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);'><h3>⚠️ Critical</h3><h2 style='font-size: 2rem;'>{critical}</h2><small>{'🚨' if critical > 0 else 'safe'}</small></div>", unsafe_allow_html=True)
st.markdown("---")

# ===== TABS =====
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Patient List", "💬 AI Conversation", "🚨 Emergency Alerts", "📊 Analytics", "⚙️ Management"])

# ========== TAB 1: PATIENT LIST ==========
with tab1:
    search = st.text_input("🔍 Search patient", placeholder="Name or phone number...")
    filtered = []
    for pid, p in st.session_state.patients.items():
        if p['language'] not in selected_langs: continue
        if p.get('risk', 'medium') not in selected_risks: continue
        if p['status'] not in selected_status: continue
        if search and search.lower() not in p['name'].lower() and search not in p['phone']: continue
        filtered.append((pid, p))
    st.caption(f"Showing {len(filtered)} of {total} patients")
    if not filtered:
        st.warning("⚠️ No patients match selected filters.")
    else:
        for pid, p in filtered:
            risk_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(p.get('risk', 'medium'), "⚪")
            status_class = {"pending": "status-pending", "in_progress": "status-progress", "completed": "status-completed", "escalated": "status-escalated"}.get(p['status'], "status-pending")
            st.markdown(f"<div class='patient-card'><div style='display: flex; justify-content: space-between; align-items: center;'><div><h4 style='margin: 0;'>{p['name']} ({p['age']} yrs)</h4><small>📞 {p['phone']} | 💊 {', '.join(p['medicines'][:2])}</small></div><div style='text-align: right;'><span class='status-badge {status_class}'>{p['status'].replace('_', ' ').title()}</span><br><small>Risk: {risk_icon} {p.get('risk', 'medium').upper()}</small></div></div></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📞 Simulate Call", key=f"sim_{pid}", use_container_width=True):
                    st.session_state.selected_patient = p['name']
                    st.success(f"Simulating call to {p['name']}...")
            with col2:
                if st.button(f"📱 Real Call", key=f"real_{pid}", use_container_width=True):
                    with st.spinner(f"Calling {p['name']} at {p['phone']}..."):
                        try:
                            response = requests.post(f"{API_URL}/call/initiate", params={"patient_id": pid, "language": p['language'].lower()}, timeout=10)
                            if response.status_code == 200:
                                data = response.json()
                                st.success(f"✅ Call initiated to {p['name']}!")
                                st.info(f"Call SID: {data['call_sid']}")
                            else:
                                st.error("Failed to call")
                        except Exception as e:
                            st.error(f"Error: {e}")
            with col3:
                if st.button(f"✏️ Edit", key=f"edit_{pid}", use_container_width=True):
                    st.session_state.edit_patient = pid
                    st.rerun()
            st.markdown("---")

# ========== TAB 2: AI CONVERSATION ==========
with tab2:
    col1, col2 = st.columns([1, 2])
    with col1:
        patient_names = [p['name'] for p in st.session_state.patients.values()]
        selected_patient_name = st.selectbox("Select Patient", patient_names, key="conv_patient")
        selected_patient = None
        for p in st.session_state.patients.values():
            if p['name'] == selected_patient_name:
                selected_patient = p
                break
        if selected_patient:
            st.markdown(f"<div class='glass-card'><h4>{selected_patient['name']}</h4><p>Age: {selected_patient['age']} | Language: {selected_patient['language']}</p><p>Condition: {selected_patient['condition']}</p><p>Risk: <strong style='color:{"red" if selected_patient.get('risk')=='critical' else "orange"}'>{selected_patient.get('risk', 'medium').upper()}</strong></p></div>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💊 Medicines", use_container_width=True):
                    st.info(f"💊 {', '.join(selected_patient['medicines'])}")
            with col_b:
                if st.button("📞 Call Now", use_container_width=True):
                    st.success(f"Calling {selected_patient['phone']}...")
    with col2:
        st.markdown("#### 💬 Conversation")
        placeholders = {"Hindi": "मुझे सीने में दर्द है", "Tamil": "எனக்கு மார்பு வலி", "Telugu": "నాకు ఛాతీ నొప్పి", "English": "I have chest pain"}
        placeholder = placeholders.get(selected_patient['language'] if selected_patient else "Hindi", "Type your message...")
        user_msg = st.text_area("Patient Message", placeholder, height=100, key="msg_input")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📤 Send Message", type="primary", use_container_width=True):
                if user_msg and selected_patient:
                    st.session_state.conversation.append({"role": "user", "text": user_msg, "time": datetime.now().strftime("%H:%M:%S")})
                    msg_lower = user_msg.lower()
                    if 'दर्द' in msg_lower or 'pain' in msg_lower:
                        ai_response = "मैं समझ सकता हूँ कि दर्द बहुत है। कृपया 1 से 10 के पैमाने पर बताइए कितना दर्द है? इससे हमें आपकी बेहतर मदद करने में सुविधा होगी।"
                        emergency = False
                    elif 'दवा' in msg_lower or 'medicine' in msg_lower:
                        ai_response = f"आपकी दवा {selected_patient['medicines'][0]} का समय हो गया है। कृपया इसे समय पर लें। दवा नियमित रूप से लेने से आप जल्दी ठीक होंगे। क्या आपने ले ली?"
                        emergency = False
                    elif 'बहुत' in msg_lower or 'severe' in msg_lower:
                        ai_response = "🚨 यह गंभीर लग रहा है! मैं तुरंत डॉक्टर को सूचित कर रहा हूँ। कृपया शांत रहें और अपना स्थान बताएं। मदद आ रही है।"
                        emergency = True
                    else:
                        ai_response = "ठीक है, मैं समझ गया। कृपया अपनी दवा समय पर लें और आराम करें। अगर कोई और समस्या हो तो बताइए। मैं आपकी मदद के लिए यहाँ हूँ।"
                        emergency = False
                    st.session_state.conversation.append({"role": "assistant", "text": ai_response, "time": datetime.now().strftime("%H:%M:%S"), "emergency": emergency})
                    st.session_state.call_history.append({"patient": selected_patient['name'], "message": user_msg, "response": ai_response, "time": datetime.now(), "emergency": emergency})
                    if emergency:
                        st.session_state.emergencies.append({"patient": selected_patient['name'], "message": user_msg, "time": datetime.now()})
                        st.error("🚨 EMERGENCY DETECTED! Doctor notified.")
                    st.rerun()
        with col_btn2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.conversation = []
                st.rerun()
        st.markdown("---")
        if not st.session_state.conversation:
            st.info("👆 Send a message to start the conversation")
        else:
            for msg in st.session_state.conversation[-10:]:
                if msg['role'] == 'user':
                    st.markdown(f"<div class='user-message'><b>You:</b> {msg['text']}<br><small>{msg['time']}</small></div>", unsafe_allow_html=True)
                else:
                    if msg.get('emergency'):
                        st.markdown(f"<div class='emergency-message'><b>🚨 AI (Emergency):</b> {msg['text']}<br><small>{msg['time']}</small></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='ai-message'><b>🤖 AI:</b> {msg['text']}<br><small>{msg['time']}</small></div>", unsafe_allow_html=True)


# ===== PATIENT HEALTH SUMMARY SECTION =====
st.markdown("---")
st.markdown("### 📋 Patient Health Summary")

if selected_patient and api_connected:
    try:
        # Get patient ID
        patient_id = None
        for pid, p in st.session_state.patients.items():
            if p['name'] == selected_patient_name:
                patient_id = pid
                break

        if patient_id:
            # Fetch answers from backend
            response = requests.get(f"{API_URL}/conversation/answers/{patient_id}", timeout=5)

            if response.status_code == 200:
                data = response.json()['data']

                # Display check-in status
                if data.get('complete'):
                    st.success("✅ Check-in Complete!")
                else:
                    st.info(f"📝 Check-in in progress ({len(data.get('responses', {}))}/14 questions answered)")

                # Display all answers
                if data.get('responses'):
                    with st.expander("📋 View All Answers", expanded=True):
                        for qid, ans in data['responses'].items():
                            if ans.get('answer'):
                                st.markdown(f"""
                                <div style='border-left: 3px solid #FF9933; padding: 0.5rem; margin: 0.3rem 0; background: #f9f9f9;'>
                                    <b>{ans.get('question', 'Question')}</b><br>
                                    <span style='color: #2c3e50;'>📝 {ans.get('answer', 'No answer')}</span>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style='border-left: 3px solid #ccc; padding: 0.5rem; margin: 0.3rem 0; background: #f9f9f9; opacity: 0.6;'>
                                    <b>{ans.get('question', 'Question')}</b><br>
                                    <span style='color: #999;'>⏳ Pending</span>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.info("No answers recorded yet. Start a conversation to collect health information.")

                # Show conversation history
                if data.get('conversation_history'):
                    with st.expander("💬 Conversation History"):
                        for msg in data['conversation_history'][-10:]:
                            if msg['role'] == 'user':
                                st.markdown(f"👤 **You:** {msg['text']}")
                            else:
                                st.markdown(f"🤖 **AI:** {msg['text']}")

            elif response.status_code == 404:
                st.info("No active conversation. Start a conversation to collect health information.")
            else:
                st.warning("Could not fetch health summary")
        else:
            st.info("Select a patient to view health summary")
    except Exception as e:
        st.info("Start a conversation to collect health information")
else:
    st.info("Select a patient to view health summary")



# ========== TAB 3: EMERGENCY ALERTS ==========
with tab3:
    st.markdown("### 🚨 Emergency Response Center")
    if st.session_state.auto_refresh:
        time.sleep(5)
        st.rerun()
    active_emergencies = [e for e in st.session_state.emergencies if not e.get('resolved')]
    if active_emergencies:
        st.error(f"⚠️ {len(active_emergencies)} ACTIVE EMERGENCIES")
        for e in active_emergencies[-5:]:
            st.markdown(f"<div style='background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%); padding: 1rem; border-radius: 15px; margin: 0.5rem 0; animation: pulse 1s infinite;'><h4>🚨 {e['patient']}</h4><p><strong>Message:</strong> {e['message'][:100]}</p><p><strong>Time:</strong> {e['time'].strftime('%H:%M:%S') if hasattr(e['time'], 'strftime') else e['time']}</p></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📞 Call {e['patient']}", key=f"call_emerg_{e['patient']}"):
                    st.success(f"Calling {e['patient']}...")
            with col2:
                if st.button(f"👨‍⚕️ Notify Doctor", key=f"doc_emerg_{e['patient']}"):
                    st.success("Doctor notified")
            with col3:
                if st.button(f"✅ Resolve", key=f"res_emerg_{e['patient']}"):
                    e['resolved'] = True
                    st.rerun()
    else:
        st.success("✅ No active emergencies")

# ========== TAB 4: ANALYTICS ==========
with tab4:
    st.markdown("### 📊 Analytics Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🌐 Languages Distribution")
        lang_counts = {}
        for p in st.session_state.patients.values():
            lang_counts[p['language']] = lang_counts.get(p['language'], 0) + 1
        if lang_counts:
            lang_df = pd.DataFrame({'Language': list(lang_counts.keys()), 'Patients': list(lang_counts.values())})
            fig = px.bar(lang_df, x='Language', y='Patients', title='Patients by Language', color='Patients')
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### 🚨 Risk Distribution")
        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for p in st.session_state.patients.values():
            risk_counts[p.get('risk', 'medium')] += 1
        risk_df = pd.DataFrame({'Risk': list(risk_counts.keys()), 'Count': list(risk_counts.values())})
        fig = px.pie(risk_df, values='Count', names='Risk', title='Risk Distribution')
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### 📈 Weekly Call Trends")
    trend_data = pd.DataFrame({
        'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'Calls': [45, 52, 48, 61, 55, 42, 38],
        'Completed': [38, 44, 40, 52, 47, 36, 32]
    })
    fig = px.line(trend_data, x='Day', y=['Calls', 'Completed'], title='Weekly Trends', color_discrete_sequence=['#FF9933', '#138808'])
    st.plotly_chart(fig, use_container_width=True)

# ========== TAB 5: MANAGEMENT ==========
with tab5:
    st.markdown("### 👤 Add New Patient")

    # ===== PHONE NUMBER FORMATTING FUNCTION =====
    def format_phone(phone):
        """Format phone number to +91XXXXXXXXXX format"""
        phone = phone.strip().replace(" ", "").replace("-", "")

        # Remove any existing +91 prefix if present
        if phone.startswith('+'):
            phone = phone[1:]

        # If starts with 91, remove it
        if phone.startswith('91'):
            phone = phone[0:]

        # If starts with 0, remove it
        if phone.startswith('0'):
            phone = phone[1:]

        # Check if we have exactly 10 digits after cleaning
        if len(phone) != 10:
            return None, f"Invalid phone number. Please enter 10 digits (got {len(phone)} digits)"

        # Check if all digits
        if not phone.isdigit():
            return None, "Phone number must contain only digits"

        # Return formatted number
        return '+91' + phone, None

    # ===== DUPLICATE CHECK FUNCTION (Only Name + Age, No Phone Check) =====
    def is_duplicate_patient(name, age, existing_patients):
        """
        Check for duplicates:
        - Same name AND same age: NOT allowed (likely same person)
        - Same name but different age: ALLOWED
        - Phone number can be same (removed restriction)
        """
        for pid, p in existing_patients.items():
            # Same name AND same age - not allowed (likely same person)
            if p['name'].lower() == name.lower() and p['age'] == age:
                return True, f"Patient with name '{name}' and age {age} already exists"

        return False, ""

    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Full Name *", placeholder="e.g., राम कुमार", key="new_name")
        new_age = st.number_input("Age *", min_value=1, max_value=120, value=35, key="new_age")
        new_gender = st.selectbox("Gender", ["Male", "Female", "Other", "Not Specified"], key="new_gender")
        new_language = st.selectbox("Language", ["Hindi", "Tamil", "Telugu", "English", "Marathi", "Urdu", "Bengali", "Gujarati", "Punjabi", "Malayalam", "Kannada"], key="new_lang")
    with col2:
        new_phone = st.text_input("Mobile Number *", placeholder="+91  phone number", key="new_phone")
        new_risk = st.selectbox("Risk Level", ["low", "medium", "high", "critical"], key="new_risk")
        new_condition = st.text_input("Medical Condition", placeholder="e.g., Heart Attack, Diabetes", key="new_cond")
        new_medicines = st.text_input("Medicines", placeholder="Crocin 500mg, Aten 25mg (comma separated)", key="new_meds")
        new_status = st.selectbox("Status", ["pending", "in_progress", "completed", "escalated"], key="new_status")

    # st.caption("📌 **Rules:** Phone number must be exactly 10 digits (auto adds +91) | Same name + same age cannot be registered twice")

    # Show formatted phone preview
    if new_phone:
        formatted, error = format_phone(new_phone)
        if error:
            st.error(f"❌ {error}")
        else:
            st.success(f"✅ Phone will be saved as: **{formatted}**")

    if st.button("➕ Add Patient", type="primary", key="add_patient_btn"):
        # Validate name
        if not new_name or not new_name.strip():
            st.error("❌ Please enter patient name")
        # Validate age
        elif new_age < 1 or new_age > 120:
            st.error("❌ Age must be between 1 and 120")
        # Validate phone
        elif not new_phone:
            st.error("❌ Please enter phone number")
        else:
            formatted_phone, phone_error = format_phone(new_phone)
            if phone_error:
                st.error(f"❌ {phone_error}")
            else:
                # Check duplicate (name + age only, no phone check)
                is_dup, dup_msg = is_duplicate_patient(new_name, new_age, st.session_state.patients)
                if is_dup:
                    st.error(f"❌ {dup_msg}")
                else:
                    new_id = f"P{len(st.session_state.patients)+1:03d}"

                    # Prepare patient data
                    new_patient = {
                        "name": new_name.strip(),
                        "age": new_age,
                        "gender": new_gender,
                        "language": new_language,
                        "condition": new_condition if new_condition else "General",
                        "medicines": [m.strip() for m in new_medicines.split(",")] if new_medicines else [],
                        "phone": formatted_phone,
                        "status": new_status,
                        "risk": new_risk,
                        "last_call": "Just added"
                    }

                    # Add to frontend
                    st.session_state.patients[new_id] = new_patient

                    # Add to backend if connected
                    if api_connected:
                        try:
                            backend_data = {
                                "id": new_id,
                                "name": new_name.strip(),
                                "phone": formatted_phone,
                                "condition": new_condition,
                                "risk": new_risk,
                                "gender": new_gender,
                                "language": new_language,
                                "age": new_age
                            }
                            requests.post(f"{API_URL}/register-patient", json=backend_data, timeout=5)
                        except:
                            pass

                    st.success(f"✅ Patient {new_name} added successfully!")
                    st.balloons()
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Patient Directory")
    st.caption(f"Total Patients: {len(st.session_state.patients)}")

    search_manage = st.text_input("🔍 Search", placeholder="Search by name or phone...", key="search_manage")

    # Display patients with unique keys
    import time
    for idx, (pid, p) in enumerate(st.session_state.patients.items()):
        if search_manage:
            if search_manage.lower() not in p['name'].lower() and search_manage not in p['phone']:
                continue

        unique_suffix = f"{idx}_{int(time.time()*1000)}_{pid}"

        risk_color = {
            "critical": "🔴 CRITICAL",
            "high": "🟠 HIGH",
            "medium": "🟡 MEDIUM",
            "low": "🟢 LOW"
        }.get(p.get('risk', 'medium'), "⚪ MEDIUM")

        with st.expander(f"🩺 {p['name']} ({p['age']} yrs) - {p['condition']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**ID:** `{pid}`")
                st.markdown(f"**Name:** {p['name']}")
                st.markdown(f"**Age:** {p['age']}")
                st.markdown(f"**Gender:** {p.get('gender', 'Not specified')}")
                st.markdown(f"**Language:** {p['language']}")
            with col2:
                st.markdown(f"**Phone:** {p['phone']}")
                st.markdown(f"**Risk:** {risk_color}")
                st.markdown(f"**Status:** {p['status'].replace('_', ' ').title()}")
                st.markdown(f"**Medicines:** {', '.join(p['medicines'][:3]) if p['medicines'] else 'None'}")

            col_del1, col_del2 = st.columns(2)
            with col_del1:
                if st.button(f"✏️ Edit", key=f"edit_{pid}_{unique_suffix}"):
                    st.info("✏️ Edit feature - Coming soon")
            with col_del2:
                if st.button(f"🗑️ Delete", key=f"del_{pid}_{unique_suffix}"):
                    del st.session_state.patients[pid]
                    st.success(f"✅ Patient {p['name']} deleted!")
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📞 Scheduled Auto-Calls")

    # Fetch scheduled calls from backend
    if api_connected:
        try:
            response = requests.get(f"{API_URL}/scheduled-calls", timeout=5)
            if response.status_code == 200:
                scheduled_data = response.json()
                if scheduled_data:
                    st.success(f"📅 {len(scheduled_data)} calls scheduled")

                    # Group by date
                    calls_by_date = {}
                    for call in scheduled_data:
                        call_time = call.get('call_time', '')
                        date_str = call_time.split('T')[0] if 'T' in call_time else call_time[:10]
                        if date_str not in calls_by_date:
                            calls_by_date[date_str] = []
                        calls_by_date[date_str].append(call)

                    # Display by date
                    for date_str, calls in sorted(calls_by_date.items()):
                        with st.expander(f"📅 {date_str} ({len(calls)} calls)"):
                            for call in calls:
                                time_str = call.get('call_time', '').split('T')[1][:5] if 'T' in call.get('call_time', '') else call.get('call_time', '')
                                st.markdown(f"""
                                <div style='border-left: 3px solid #FF9933; padding: 0.5rem; margin: 0.3rem 0;'>
                                    <b>🕐 {time_str}</b> - {call.get('patient_name', 'Unknown')}<br>
                                    <small>Type: {call.get('call_type', 'followup')}</small>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.info("No scheduled calls. Add patients or manually schedule.")
            else:
                st.warning("Could not fetch scheduled calls")
        except Exception as e:
            st.warning(f"Backend not reachable: {e}")
    else:
        st.info("Connect to backend to see scheduled calls")

    # ===== MANUAL SCHEDULE SECTION =====
    st.markdown("### ✏️ Manual Schedule a Call")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.session_state.patients:
            manual_patient = st.selectbox(
                "Select Patient",
                [p['name'] for p in st.session_state.patients.values()],
                key="manual_patient"
            )
        else:
            st.warning("No patients available")
            manual_patient = None

    with col2:
        manual_date = st.date_input("Call Date", key="manual_date")

    with col3:
        manual_time = st.time_input("Call Time", key="manual_time")

    with col4:
        manual_type = st.selectbox(
            "Call Type",
            ["welcome", "medication", "followup", "checkup", "emergency"],
            key="manual_type"
        )

    if st.button("📅 Schedule Call", key="manual_schedule_btn"):
        if manual_patient and api_connected:
            # Find patient ID
            patient_id = None
            for pid, p in st.session_state.patients.items():
                if p['name'] == manual_patient:
                    patient_id = pid
                    break

            if patient_id:
                call_datetime = datetime.combine(manual_date, manual_time)

                with st.spinner("Scheduling call..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/schedule-manual-call",
                            json={
                                "patient_id": patient_id,
                                "patient_name": manual_patient,
                                "phone": st.session_state.patients[patient_id]['phone'],
                                "call_time": call_datetime.isoformat(),
                                "call_type": manual_type
                            },
                            timeout=5
                        )
                        if response.status_code == 200:
                            st.success(f"✅ Call scheduled for {manual_patient} on {manual_date} at {manual_time}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Failed to schedule call")
                    except Exception as e:
                        st.error(f"Error: {e}")
        elif not api_connected:
            st.error("Backend not connected. Start backend first.")
        else:
            st.error("Please select a patient")


# ===== AUTO-REFRESH =====
if st.session_state.auto_refresh:
    time.sleep(5)
    st.rerun()

# ===== FOOTER =====
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🇮🇳 केयरकंपेनियन भारत - AI-Powered Post-Discharge Care | VoiceHack2026</p>
    <p>🏥 Connected to: AIIMS Delhi | CMC Vellore | KEM Mumbai | PGI Chandigarh</p>
    <p style='font-size: 0.7rem;'>© 2026 CareCompanion Bharat - Prototype v2.0</p>
</div>
""", unsafe_allow_html=True)