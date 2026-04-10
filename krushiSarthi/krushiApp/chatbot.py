import json
import os
import glob

DATASET = None
FuzzAvailable = False

try:
    from rapidfuzz import fuzz
    FuzzAvailable = True
except ImportError:
    fuzz = None


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
    local_file = os.path.join(os.path.dirname(__file__), 'data', 'local_agri_qa.json')
    return load_local_qa_file(local_file)


def find_uploaded_dataset():
    app_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(app_dir)
    search_dirs = [os.path.join(app_dir, 'data'), project_root]
    patterns = ['*.json', '*.jsonl', '*.csv']
    files = []
    for search_dir in search_dirs:
        for pattern in patterns:
            files.extend(glob.glob(os.path.join(search_dir, pattern)))
    files = [f for f in files if os.path.basename(f) != 'local_agri_qa.json']
    return sorted(files)[0] if files else None


def load_chat_data():
    global DATASET
    if DATASET is not None:
        return DATASET

    DATASET = []
    uploaded_file = find_uploaded_dataset()
    if uploaded_file:
        DATASET = load_local_qa_file(uploaded_file)
        if DATASET:
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
    user_input = user_input.lower().strip()

    best_score = 0
    best_answer = None

    for item in load_chat_data():
        question = item.get('question', '')
        if not question:
            continue

        question_lower = question.lower()

        if FuzzAvailable:
            score = fuzz.token_sort_ratio(user_input, question_lower)
        else:
            score = 100 if user_input in question_lower else 0

        if score > best_score:
            best_score = score
            best_answer = normalize_answer(item.get('answers'))

    print("DEBUG SCORE:", best_score)  # 👈 IMPORTANT

    if best_score > 40:   # 👈 lower threshold
        return best_answer
    else:
        return "Sorry, I didn't understand your question."

