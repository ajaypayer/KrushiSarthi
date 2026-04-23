import json
import os
import glob
import re

DATASET = None
FuzzAvailable = False
STOP_WORDS = {
    'what', 'is', 'the', 'a', 'an', 'about', 'give', 'me', 'info', 'information',
    'tell', 'please', 'of', 'and', 'to', 'how', 'why', 'are', 'can', 'i', 'my',
    'in', 'for', 'do', 'does', 'should', 'could', 'would', 'on', 'with', 'from'
}

try:
    from rapidfuzz import fuzz
    FuzzAvailable = True
except ImportError:
    fuzz = None


def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]+', ' ', text)
    return ' '.join(text.split())


def load_local_qa_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            if path.endswith('.json'):
                return json.load(f)
            if path.endswith('.jsonl'):
                return [json.loads(line) for line in f if line.strip()]
            if path.endswith('.csv'):
                import csv
                reader = csv.DictReader(f)
                return [row for row in reader]
    except Exception as exc:
        print(f"Warning: failed to load local QA file {path}: {exc}")
    return []


def load_local_qa():
    app_dir = os.path.dirname(__file__)
    data_dir = os.path.join(app_dir, 'data')
    dataset = []

    for path in [
        os.path.join(data_dir, 'local_agri_qa.json'),
        os.path.join(data_dir, 'agriculture_qa.csv'),
    ]:
        if os.path.exists(path):
            dataset.extend(load_local_qa_file(path) or [])

    return dataset


def find_uploaded_datasets():
    app_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(app_dir)
    search_dirs = [os.path.join(app_dir, 'data'), project_root]
    patterns = ['*.json', '*.jsonl', '*.csv']
    files = []

    for search_dir in search_dirs:
        for pattern in patterns:
            files.extend(glob.glob(os.path.join(search_dir, pattern)))

    excluded = {'local_agri_qa.json', 'agriculture_qa.csv'}
    files = [f for f in files if os.path.basename(f) not in excluded]
    return sorted(files)


def load_chat_data():
    global DATASET
    if DATASET is not None:
        return DATASET

    DATASET = load_local_qa()

    uploaded_files = find_uploaded_datasets()
    for uploaded_file in uploaded_files:
        loaded = load_local_qa_file(uploaded_file)
        if loaded:
            DATASET.extend(loaded)
            print(f"Using uploaded local dataset: {os.path.basename(uploaded_file)}")

    if not DATASET:
        try:
            from datasets import load_dataset
            dataset = load_dataset("KisanVaani/agriculture-qa-english-only")
            DATASET = list(dataset['train'])
        except Exception as exc:
            print(f"Warning: failed to load chatbot dataset: {exc}")

    if not DATASET:
        DATASET = load_local_qa()

    return DATASET


def normalize_answer(answer):
    if isinstance(answer, list):
        return answer[0] if answer else ""
    if answer is None:
        return ""
    return str(answer)


def get_answer(user_input):
    normalized_input = normalize_text(user_input)
    if not normalized_input:
        return "Sorry, I didn't understand your question."

    best_score = 0
    best_answer = None

    for item in load_chat_data():
        question = item.get('question', '')
        if not question:
            continue

        normalized_question = normalize_text(question)
        if not normalized_question:
            continue

        if normalized_input == normalized_question:
            return normalize_answer(item.get('answers'))

        input_words = set(normalized_input.split())
        question_words = set(normalized_question.split())
        shared_words = input_words & question_words

        if normalized_input in normalized_question or normalized_question in normalized_input:
            score = 90
        elif FuzzAvailable:
            score = fuzz.token_sort_ratio(normalized_input, normalized_question)
        else:
            score = 100 if len(shared_words) >= 2 else 0

        if len(shared_words) >= 2:
            score = max(score, 60)

        question_keywords = question_words - STOP_WORDS
        input_keywords = input_words - STOP_WORDS
        if question_keywords and question_keywords.issubset(input_keywords):
            score = max(score, 80)

        if score > best_score:
            best_score = score
            best_answer = normalize_answer(item.get('answers'))

    print("DEBUG SCORE:", best_score)

    if best_score >= 60 and best_answer:
        return best_answer
    return "Sorry, I didn't understand your question."

