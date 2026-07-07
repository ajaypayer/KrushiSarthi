import json
import os
import glob
import re
import requests
import sqlite3
import time
import urllib.parse

DATASET = None
FuzzAvailable = False
STOP_WORDS = {
    'what', 'is', 'the', 'a', 'an', 'about', 'give', 'me', 'info', 'information',
    'tell', 'please', 'of', 'and', 'to', 'how', 'why', 'are', 'can', 'i', 'my',
    'in', 'for', 'do', 'does', 'should', 'could', 'would', 'on', 'with', 'from',
    'what is', 'tell me', 'how to', 'give me', 'want to', 'details of'
}

# Generic agricultural words that should not trigger structured keyword matching (MSP, Schemes, Loans)
# but are fine for general FTS5 QA queries. This prevents false positive matches on common terms.
STRUCTURED_STOP_WORDS = {
    'crop', 'crops', 'farming', 'farm', 'farmer', 'farmers', 'agriculture', 'agricultural',
    'details', 'info', 'information', 'question', 'answer', 'ask', 'need', 'want', 'give',
    'pik', 'pika', 'pikasathi', 'sheti', 'shetkari'
}

# Extensive mapping for localized farming queries to English database terms (including inflections)
TRANSLATION_DICT = {
    # Hindi/Marathi Crops -> English Crops
    'धान': 'paddy', 'भात': 'paddy', 'तांदूळ': 'paddy', 'धान्य': 'paddy',
    'गेहूं': 'wheat', 'गहू': 'wheat', 'गव्हाचे': 'wheat', 'गव्हासाठी': 'wheat',
    'मक्का': 'maize', 'मका': 'maize', 'मक्याचे': 'maize',
    'कपास': 'cotton', 'कापूस': 'cotton', 'कापसाचे': 'cotton',
    'बाजरा': 'bajra', 'बाजरी': 'bajra',
    'ज्वार': 'jowar', 'ज्वारी': 'jowar',
    'चना': 'gram', 'हरभरा': 'gram', 'हरभऱ्याचे': 'gram',
    'सोयाबीन': 'soyabean', 'सोयाबीनचा': 'soyabean', 'सोयाबीनचे': 'soyabean',
    'तूर': 'tur', 'अरहर': 'tur',
    'मूंग': 'moong', 'मूग': 'moong',
    'उड़द': 'urad', 'उडीद': 'urad',
    'रागी': 'ragi',
    'मूंगफली': 'groundnut', 'भुईमूग': 'groundnut',
    'सूरजमुखी': 'sunflower', 'सूर्यफूल': 'sunflower',
    'गन्ना': 'sugarcane', 'ऊस': 'sugarcane',
    'प्याज': 'onion', 'कांदा': 'onion',
    'आलू': 'potato', 'बटाटा': 'potato',
    'टमाटर': 'tomato', 'टोमॅटो': 'tomato',
    
    # Hindi/Marathi general terms -> English terms
    'एमएसपी': 'msp', 'हमीभाव': 'msp', 'दर': 'rate', 'भाव': 'rate',
    'योजना': 'scheme', 'स्कीम': 'scheme', 'योजनेची': 'scheme', 'योजनांची': 'scheme',
    'कर्ज': 'loan', 'ऋण': 'loan', 'लोन': 'loan', 'कर्जा': 'loan', 'कर्जासाठी': 'loan', 'कर्जाचे': 'loan', 'कर्जाला': 'loan',
    'कागदपत्रे': 'document', 'कागदपत्र': 'document', 'कागदपत्रांची': 'document', 'दस्तावेज': 'document', 'कागजात': 'document',
    'पात्रता': 'eligibility', 'पात्र': 'eligibility',
    'लागतील': 'need', 'हवी': 'need', 'पाहिजे': 'need', 'चाहिए': 'need',
    'माहिती': 'info', 'जानकारी': 'info',
    'पीक': 'crop', 'पिका': 'crop', 'पिकासाठी': 'crop', 'पिकाचे': 'crop'
}

try:
    from rapidfuzz import fuzz
    FuzzAvailable = True
except ImportError:
    fuzz = None


def load_env():
    if 'GEMINI_API_KEY' in os.environ:
        return
    current = os.path.abspath(os.path.dirname(__file__))
    for _ in range(5):
        env_path = os.path.join(current, '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ.setdefault(k, v)
            break
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent


# Load environment variables on import
load_env()


def get_db_path():
    try:
        from django.conf import settings
        return str(settings.DATABASES['default']['NAME'])
    except:
        pass
    app_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(app_dir)
    return os.path.join(project_root, 'db.sqlite3')


def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\u0900-\u097F\s]+', ' ', text)  # Keep Devanagari characters
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


# --- Gemini API & Database Querying Integration ---

def call_gemini(prompt, retries=1, initial_delay=1):
    api_key = os.environ.get('GEMINI_API_KEY')
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')

    if not api_key:
        print("[GEMINI] Error: GEMINI_API_KEY not found in environment variables.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    delay = initial_delay
    for attempt in range(retries):
        try:
            # Short timeout to keep response snappy
            response = requests.post(url, json=payload, headers=headers, timeout=8)
            
            # Fast fail for rate limits and service issues without waiting/sleeping
            if response.status_code == 429:
                print(f"[GEMINI] 429 Rate Limit. Fast-failing immediately to local database fallback.")
                return None
            elif response.status_code == 503:
                print(f"[GEMINI] 503 Service Unavailable. Fast-failing immediately to local database fallback.")
                return None
            
            response.raise_for_status()
            res_json = response.json()
            text = res_json['candidates'][0]['content']['parts'][0]['text']
            return text.strip()
        except Exception as e:
            print(f"[GEMINI] Connection attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                break
    return None


def clean_sql(sql_str):
    if not sql_str:
        return ""
    sql_str = sql_str.strip()
    sql_str = re.sub(r'^```sql\s*', '', sql_str, flags=re.IGNORECASE)
    sql_str = re.sub(r'^```\s*', '', sql_str)
    sql_str = re.sub(r'\s*```$', '', sql_str)
    return sql_str.strip()


def is_safe_sql(sql_str):
    cleaned = sql_str.strip().upper()
    if not cleaned.startswith("SELECT"):
        return False
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "REPLACE", "CREATE", "PRAGMA", "ATTACH", "DETACH"]
    for word in forbidden:
        if re.search(r'\b' + word + r'\b', cleaned):
            return False
    return True


def execute_sql(sql_query):
    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        return results
    except Exception as exc:
        print(f"[DATABASE] SQL Execution Error: {exc} for query: {sql_query}")
        return None
    finally:
        if conn:
            conn.close()


def format_db_results(results):
    if not results:
        return "No records found."
    lines = []
    for idx, row in enumerate(results, 1):
        row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
        lines.append(f"Record {idx}: {row_str}")
    return "\n".join(lines)


# --- Helper Translation & Language Detection for Fallbacks ---

def detect_language(text):
    if re.search(r'[\u0900-\u097f]', text):
        marathi_indicators = ['आहे', 'कागदपत्रे', 'साठी', 'काय', 'मला', 'हमीभाव', 'कापूस', 'तांदूळ', 'गहू', 'नका', 'करा', 'पाहिजे', 'हवी', 'लागतील', 'कर्जासाठी']
        for mw in marathi_indicators:
            if mw in text:
                return 'mr'
        return 'hi'
    return 'en'


def translate_to_lang(text, dest_lang):
    if dest_lang == 'en' or not text:
        return text
    try:
        quoted_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={dest_lang}&dt=t&q={quoted_text}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            res_json = res.json()
            translated_segments = []
            for segment in res_json[0]:
                if segment[0]:
                    translated_segments.append(segment[0])
            return "".join(translated_segments)
    except Exception as e:
        print(f"[TRANSLATION FALLBACK] Translation to {dest_lang} failed: {e}")
    return text


# --- Offline/Local SQLite Database Fallback Search ---

def get_local_db_answer(user_input):
    normalized = normalize_text(user_input)
    words = normalized.split()
    
    # 1. Extract and translate keywords for structured matching (excluding generic stop words)
    structured_keywords = []
    general_keywords = []
    
    for word in words:
        translated_val = None
        if word in TRANSLATION_DICT:
            translated_val = TRANSLATION_DICT[word]
            general_keywords.append(translated_val)
        else:
            general_keywords.append(word)

        target_word = translated_val if translated_val else word
        
        # Add to structured keywords if not a generic stop word
        if len(target_word) >= 3 and target_word not in STOP_WORDS and target_word not in STRUCTURED_STOP_WORDS:
            structured_keywords.append(target_word)

    structured_keywords = list(dict.fromkeys(structured_keywords))
    general_keywords = list(dict.fromkeys(general_keywords))
    
    print(f"[OFFLINE FALLBACK] Structured keywords: {structured_keywords}")
    print(f"[OFFLINE FALLBACK] General keywords: {general_keywords}")

    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check for specific compound search terms:
        # A. Crop Loan specific search (prioritize Kisan Credit Card over listing 20 unrelated loans)
        if 'crop' in general_keywords and 'loan' in general_keywords:
            cursor.execute("""
                SELECT loan_name, category, eligibility, purpose, documents_required, repayment_period, official_source 
                FROM csv_agriculture_loans 
                WHERE category LIKE '%Crop%' OR loan_name LIKE '%Crop%' OR purpose LIKE '%Crop%'
            """)
            rows = cursor.fetchall()
            if rows:
                lines = []
                for r in rows:
                    lines.append(f"Loan Name: {r['loan_name']} ({r['category']})")
                    lines.append(f"• Eligibility: {r['eligibility']}")
                    lines.append(f"• Purpose: {r['purpose']}")
                    lines.append(f"• Required Documents: {r['documents_required']}")
                    lines.append(f"• Repayment Period: {r['repayment_period']}")
                    if r['official_source']:
                        lines.append(f"• Official Source: {r['official_source']}")
                return "\n".join(lines)

        # Try to query structured tables ONLY if we have specific structured keywords
        if structured_keywords:
            # B. Search MSP Rates Table
            for keyword in structured_keywords:
                cursor.execute("""
                    SELECT crop, variety, season, marketing_year, msp_rupees_per_quintal, unit 
                    FROM csv_msp_rates 
                    WHERE crop LIKE ? OR variety LIKE ?
                """, (f'%{keyword}%', f'%{keyword}%'))
                rows = cursor.fetchall()
                if rows:
                    lines = ["MSP rates found in our database:"]
                    for r in rows:
                        lines.append(f"• {r['crop']} ({r['variety']}) - {r['season']} ({r['marketing_year']}): Rs. {r['msp_rupees_per_quintal']} per {r['unit']}")
                    return "\n".join(lines)

            # C. Search Agriculture Loans Table (matches category/name/purpose/eligibility)
            for keyword in structured_keywords:
                cursor.execute("""
                    SELECT loan_name, category, eligibility, purpose, documents_required, repayment_period, official_source 
                    FROM csv_agriculture_loans 
                    WHERE loan_name LIKE ? OR category LIKE ? OR purpose LIKE ? OR documents_required LIKE ?
                """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
                rows = cursor.fetchall()
                if rows:
                    lines = []
                    for r in rows:
                        lines.append(f"Loan Name: {r['loan_name']} ({r['category']})")
                        lines.append(f"• Eligibility: {r['eligibility']}")
                        lines.append(f"• Purpose: {r['purpose']}")
                        lines.append(f"• Required Documents: {r['documents_required']}")
                        lines.append(f"• Repayment Period: {r['repayment_period']}")
                        if r['official_source']:
                            lines.append(f"• Official Source: {r['official_source']}")
                    return "\n".join(lines)

            # D. Search Government Schemes Table (matches name/category/benefits/eligibility)
            for keyword in structured_keywords:
                cursor.execute("""
                    SELECT scheme_name, category, eligibility, benefits, official_website 
                    FROM csv_government_schemes 
                    WHERE scheme_name LIKE ? OR category LIKE ? OR benefits LIKE ? OR eligibility LIKE ?
                """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
                rows = cursor.fetchall()
                if rows:
                    lines = []
                    for r in rows:
                        lines.append(f"Scheme Name: {r['scheme_name']} ({r['category']})")
                        lines.append(f"• Eligibility: {r['eligibility']}")
                        lines.append(f"• Benefits: {r['benefits']}")
                        if r['official_website']:
                            lines.append(f"• Official Website: {r['official_website']}")
                    return "\n".join(lines)

        # E. Search Agriculture Q&A Table using FTS5 (matching all general keywords)
        if general_keywords:
            valid_words = [w for w in general_keywords if len(w) >= 3 and w not in STOP_WORDS]
            if valid_words:
                fts_query = " OR ".join(valid_words)
                try:
                    cursor.execute("""
                        SELECT question, answers 
                        FROM csv_agriculture_qa 
                        WHERE csv_agriculture_qa MATCH ? 
                        LIMIT 1
                    """, (fts_query,))
                    row = cursor.fetchone()
                    if row:
                        return row['answers']
                except sqlite3.OperationalError:
                    # Standard LIKE fallback if FTS5 fails
                    for keyword in valid_words:
                        cursor.execute("""
                            SELECT answers 
                            FROM csv_agriculture_qa 
                            WHERE question LIKE ? 
                            LIMIT 1
                        """, (f'%{keyword}%',))
                        row = cursor.fetchone()
                        if row:
                            return row['answers']

    except Exception as exc:
        print(f"[OFFLINE FALLBACK] Database error: {exc}")
    finally:
        if conn:
            conn.close()

    return None


def get_answer_fallback(user_input):
    normalized_input = normalize_text(user_input)
    if not normalized_input:
        return "Sorry, I didn't understand your question."

    input_words = set(normalized_input.split())
    input_keywords = input_words - STOP_WORDS
    
    if not input_keywords:
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

        question_words = set(normalized_question.split())
        question_keywords = question_words - STOP_WORDS

        shared_keywords = input_keywords & question_keywords
        if not shared_keywords:
            continue

        if normalized_input == normalized_question:
            return normalize_answer(item.get('answers'))

        if normalized_input in normalized_question or normalized_question in normalized_input:
            score = 90
        elif FuzzAvailable:
            score = fuzz.token_sort_ratio(normalized_input, normalized_question)
        else:
            score = 100 if len(shared_keywords) >= 2 else 0

        if len(shared_keywords) >= 2:
            score = max(score, 60)

        if question_keywords and question_keywords.issubset(input_keywords):
            score = max(score, 80)

        if score > best_score:
            best_score = score
            best_answer = normalize_answer(item.get('answers'))

    if best_score >= 60 and best_answer:
        return best_answer
    return "Sorry, I didn't understand your question."


def get_answer(user_input):
    load_env()
    user_lang = detect_language(user_input)
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("[CHATBOT] Gemini API key not found. Using offline local search fallback.")
        local_res = get_local_db_answer(user_input)
        if local_res:
            return translate_to_lang(local_res, user_lang)
        return get_answer_fallback(user_input)

    # Stage 1: Generate SQL query to answer the question
    sql_prompt = f"""You are a database querying assistant for an agricultural platform. Given a user's question, write a single SQLite SELECT query to retrieve relevant info to answer it.
If the question does not require querying the database (e.g. standard greetings, general non-agricultural questions), reply ONLY with the word "NONE".

Our SQLite database has these tables and columns:

1. Table: `csv_government_schemes` (Government schemes for farmers)
   Columns:
   - id (INTEGER PRIMARY KEY)
   - scheme_name (TEXT)
   - category (TEXT)
   - eligibility (TEXT)
   - benefits (TEXT)
   - documents_required (TEXT)
   - official_website (TEXT)

2. Table: `csv_msp_rates` (Minimum Support Price rates for crops)
   Columns:
   - id (INTEGER PRIMARY KEY)
   - crop (TEXT) (e.g., Paddy, Wheat, Bajra, Maize, Cotton)
   - variety (TEXT) (e.g., Common, Grade A, Hybrid, Maldandi)
   - season (TEXT) (e.g., Kharif, Rabi)
   - marketing_year (TEXT) (e.g., 2025-26)
   - msp_rupees_per_quintal (REAL) (The price rate)
   - unit (TEXT) (e.g., Quintal)

3. Table: `csv_agriculture_loans` (Loans available for farming and agriculture)
   Columns:
   - id (INTEGER PRIMARY KEY)
   - loan_name (TEXT) (e.g., Kisan Credit Card (KCC), Tractor Loan, Farm Pond Loan)
   - category (TEXT) (e.g., Crop Loan, Animal Husbandry, Farm Machinery, Irrigation, Infrastructure)
   - eligibility (TEXT)
   - purpose (TEXT)
   - documents_required (TEXT)
   - repayment_period (TEXT)
   - official_source (TEXT)

4. Table: `csv_agriculture_qa` (General agricultural Q&A dataset containing 29,000+ QA pairs. Use this table if the user asks a general agriculture/farming question that is not covered by schemes, loans, or MSPs)
   Columns:
   - question (TEXT)
   - answers (TEXT)
   Note: This table is an FTS5 full-text search table. To query it, use SQLite MATCH or LIKE. For example:
   SELECT answers FROM csv_agriculture_qa WHERE csv_agriculture_qa MATCH 'tomato crop' LIMIT 2;
   Or:
   SELECT answers FROM csv_agriculture_qa WHERE question LIKE '%soil erosion%' LIMIT 2;

Rules:
- The database columns and data (like crop names, scheme names) are stored in English.
- The user might ask the question in English, Hindi, or Marathi. You MUST translate user terms to English in the SQL query (e.g., if the user asks about "धान" or "भात", search for "Paddy" in the crop column; if they ask about "कर्ज" or "ऋण", search for loan tables).
- Always select all relevant/descriptive columns so that the query results are self-explanatory and contain rich context (e.g., select `crop, variety, season, marketing_year, msp_rupees_per_quintal, unit` instead of just `msp_rupees_per_quintal`).
- Use case-insensitive LIKE pattern matching (e.g. `WHERE crop LIKE '%paddy%'`) for flexible text matching to prevent spelling mismatches.
- Limit query results (using LIMIT 3 or LIMIT 5) to avoid returning too much data.
- Return ONLY the raw SQL query. Do not wrap it in markdown code blocks like ```sql ... ```. Do not add comments. Do not explain. If no query is needed, reply ONLY with "NONE".

User's Question: "{user_input}"
SQL Query:"""

    print(f"[CHATBOT] User input: {user_input} (Detected Language: {user_lang})")
    gemini_sql = call_gemini(sql_prompt)
    
    if gemini_sql:
        gemini_sql = clean_sql(gemini_sql)
        print(f"[CHATBOT] Gemini generated SQL: {gemini_sql}")
    else:
        print("[CHATBOT] Stage 1 SQL generation failed. Using local search fallback.")
        local_res = get_local_db_answer(user_input)
        if local_res:
            return translate_to_lang(local_res, user_lang)
        return get_answer_fallback(user_input)

    # Check if SQL generated is a valid query
    db_results = None
    if gemini_sql and gemini_sql.upper() != "NONE" and is_safe_sql(gemini_sql):
        db_results = execute_sql(gemini_sql)
        print(f"[CHATBOT] Database results: {db_results}")
    elif gemini_sql and gemini_sql.upper() == "NONE":
        response_prompt = f"""You are a helpful agricultural assistant chatbot called KrushiSarthi.
Respond to the user's message politely and in the same language. If they greet you, greet them back and offer help with agricultural schemes, MSP rates, loans, and general farming.

User's Message: "{user_input}"
Your Response:"""
        final_response = call_gemini(response_prompt)
        if final_response:
            return final_response
        else:
            return translate_to_lang("Hello! I am KrushiSarthi. How can I help you today?", user_lang)
    else:
        print("[CHATBOT] SQL unsafe or failed. Using local search fallback.")
        local_res = get_local_db_answer(user_input)
        if local_res:
            return translate_to_lang(local_res, user_lang)
        return get_answer_fallback(user_input)

    # Stage 2: Generate response using Gemini in the user's language
    if db_results is not None:
        formatted_data = format_db_results(db_results)
        response_prompt = f"""You are a helpful agricultural assistant chatbot called KrushiSarthi.
The user asked a question, and we retrieved some information from our database to help answer it.

User's Question: "{user_input}"
Database Results:
{formatted_data}

Guidelines:
1. Answer the user's question clearly, politely, and accurately based on the database results.
2. YOU MUST ANSWER IN THE SAME LANGUAGE AS THE USER'S QUESTION (e.g., Hindi for Hindi, Marathi for Marathi, English for English).
3. If the database results are empty or do not contain relevant information to answer the question, politely tell the user in their language that you couldn't find the exact details, and provide general agricultural advice if possible.
4. Keep the response concise, informative, and formatted with clean paragraphs or bullet points if necessary.

Your Response:"""
        final_response = call_gemini(response_prompt)
        if final_response:
            return final_response
        else:
            print("[CHATBOT] Stage 2 response generation failed. Using local search fallback.")
            local_res = get_local_db_answer(user_input)
            if local_res:
                return translate_to_lang(local_res, user_lang)
            return get_answer_fallback(user_input)
    else:
        local_res = get_local_db_answer(user_input)
        if local_res:
            return translate_to_lang(local_res, user_lang)
        return get_answer_fallback(user_input)
