import json
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

def load_transcript_samples():
    """Load 35 sample transcripts to understand conversation flow"""
    with open(os.path.join(DATA_DIR, 'transcript_samples.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def load_training_data():
    """Load training data with call transcripts and outcomes"""
    train_df = pd.read_csv(os.path.join(DATA_DIR, 'hackathon_train.csv'))
    return train_df

def get_call_transcript(call_id):
    """Get transcript for a specific call"""
    train_df = load_training_data()
    row = train_df[train_df['call_id'] == call_id]
    if not row.empty:
        return row.iloc[0]['transcript_text']
    return None

def get_question_patterns():
    """Extract 14 health questions from training data"""
    samples = load_transcript_samples()
    questions = []

    for sample in samples:
        transcript = sample.get('transcript', '')
        # Extract question patterns
        import re
        patterns = re.findall(r'\[AGENT\]:\s*(.*?)\?', transcript)
        for p in patterns:
            if len(p) > 10 and p not in questions:
                questions.append(p)

    return questions[:14]  # First 14 unique questions