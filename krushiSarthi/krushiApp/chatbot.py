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
    'who', 'you', 'your', 'he', 'she', 'it', 'they', 'them', 'we', 'our', 'us',
    'when', 'where', 'which', 'whose', 'know', 'ready', 'get', 'got', 'make', 'take',
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


def search_local_database(user_input):
    """
    Search the SQLite database for the top 3 most relevant records matching the user's input
    across Government Schemes, MSP Rates, Agriculture Loans, and Q&A tables.
    """
    normalized = normalize_text(user_input)
    words = normalized.split()
    
    # Filter keywords (excluding stop words)
    keywords = [w for w in words if len(w) >= 3 and w not in STOP_WORDS]
    if not keywords:
        return []

    # Map words using TRANSLATION_DICT to English terms
    english_keywords = []
    for w in keywords:
        if w in TRANSLATION_DICT:
            english_keywords.append(TRANSLATION_DICT[w])
        else:
            english_keywords.append(w)
            
    english_keywords = list(dict.fromkeys(english_keywords))
    
    db_path = get_db_path()
    conn = None
    results = []
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Search MSP Rates
        for kw in english_keywords:
            cursor.execute("""
                SELECT crop, variety, season, marketing_year, msp_rupees_per_quintal, unit 
                FROM csv_msp_rates 
                WHERE crop LIKE ? OR variety LIKE ?
                LIMIT 3
            """, (f'%{kw}%', f'%{kw}%'))
            rows = cursor.fetchall()
            for r in rows:
                results.append({
                    'type': 'MSP Rate',
                    'content': f"Crop: {r['crop']} ({r['variety']}), Season: {r['season']}, Marketing Year: {r['marketing_year']}, MSP Rate: Rs. {r['msp_rupees_per_quintal']} per {r['unit']}"
                })
                
        # 2. Search Government Schemes
        for kw in english_keywords:
            cursor.execute("""
                SELECT scheme_name, category, eligibility, benefits, official_website 
                FROM csv_government_schemes 
                WHERE scheme_name LIKE ? OR category LIKE ? OR benefits LIKE ? OR eligibility LIKE ?
                LIMIT 3
            """, (f'%{kw}%', f'%{kw}%', f'%{kw}%', f'%{kw}%'))
            rows = cursor.fetchall()
            for r in rows:
                results.append({
                    'type': 'Government Scheme',
                    'content': f"Scheme Name: {r['scheme_name']} ({r['category']}), Eligibility: {r['eligibility']}, Benefits: {r['benefits']}, Website: {r['official_website']}"
                })
                
        # 3. Search Agriculture Loans
        for kw in english_keywords:
            cursor.execute("""
                SELECT loan_name, category, eligibility, purpose, documents_required, repayment_period, official_source 
                FROM csv_agriculture_loans 
                WHERE loan_name LIKE ? OR category LIKE ? OR purpose LIKE ? OR eligibility LIKE ?
                LIMIT 3
            """, (f'%{kw}%', f'%{kw}%', f'%{kw}%', f'%{kw}%'))
            rows = cursor.fetchall()
            for r in rows:
                results.append({
                    'type': 'Agriculture Loan',
                    'content': f"Loan Name: {r['loan_name']} ({r['category']}), Eligibility: {r['eligibility']}, Purpose: {r['purpose']}, Documents Required: {r['documents_required']}, Repayment: {r['repayment_period']}, Source: {r['official_source']}"
                })
                
        # 4. Search Agriculture Q&A FTS5 (ordered by relevance rank)
        fts_query = " OR ".join(english_keywords)
        try:
            cursor.execute("""
                SELECT question, answers 
                FROM csv_agriculture_qa 
                WHERE csv_agriculture_qa MATCH ? 
                ORDER BY rank
                LIMIT 3
            """, (fts_query,))
            rows = cursor.fetchall()
            for r in rows:
                results.append({
                    'type': 'General Q&A',
                    'content': f"Question: {r['question']} -> Answer: {r['answers']}"
                })
        except sqlite3.OperationalError:
            # Fallback if FTS5 is not supported
            for kw in english_keywords:
                cursor.execute("""
                    SELECT question, answers 
                    FROM csv_agriculture_qa 
                    WHERE question LIKE ? 
                    LIMIT 3
                """, (f'%{kw}%',))
                rows = cursor.fetchall()
                for r in rows:
                    results.append({
                        'type': 'General Q&A',
                        'content': f"Question: {r['question']} -> Answer: {r['answers']}"
                    })
                    
    except Exception as e:
        print(f"[DATABASE SEARCH] Error: {e}")
    finally:
        if conn:
            conn.close()
            
    # Deduplicate results based on content
    seen = set()
    unique_results = []
    for r in results:
        if r['content'] not in seen:
            seen.add(r['content'])
            unique_results.append(r)
            
    # Return top 3 matches
    return unique_results[:3]


# --- Offline/Local SQLite Database Fallback Search ---

def get_local_db_answer(user_input):
    normalized = normalize_text(user_input)
    words = normalized.split()
    
    # Fast intercept for simple greetings and thank-yous
    GREETINGS = {
        'hello', 'hi', 'hey', 'hola', 'good morning', 'thanks', 'thank you',
        'namaste', 'namaskar', 'dhanyawad',
        'नमस्ते', 'नमस्कार', 'धन्यवाद', 'आभारी', 'थँक्स', 'जय महाराष्ट्र', 'राम राम'
    }
    if set(words).issubset(GREETINGS) and words:
        return "Hello! I am KrushiSarthi, your smart agricultural assistant. How can I help you today with crop rates, government schemes, or farm loans?"
    
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

    # Indicators configuration to ensure precise query routing
    MSP_INDICATORS = {
        'msp', 'rate', 'price', 'rates', 'prices', 'quintal', 'cost', 'costs',
        'एमएसपी', 'किंमत', 'भाव', 'दर', 'क्विंटल', 'उत्पादन खर्च'
    }
    LOAN_INDICATORS = {
        'loan', 'loans', 'interest', 'repayment', 'documents', 'eligibility', 'eligible', 'bank', 'banks',
        'credit', 'kcc', 'limit', 'limits',
        'कर्ज', 'कर्जासाठी', 'कागदपत्रे', 'व्याज', 'बँक', 'बँका', 'पात्रता', 'मुदत', 'अटी'
    }
    SCHEME_INDICATORS = {
        'scheme', 'schemes', 'subsidy', 'subsidies', 'benefit', 'benefits', 'yojana', 'yojna',
        'yojanas', 'websites', 'website', 'apply', 'applying',
        'योजना', 'अनुदान', 'फायदा', 'लाभ', 'संकेतस्थळ'
    }

    has_msp_indicator = any(word in general_keywords for word in MSP_INDICATORS)
    has_loan_indicator = any(word in general_keywords for word in LOAN_INDICATORS)
    has_scheme_indicator = any(word in general_keywords for word in SCHEME_INDICATORS)

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

        # Try to query structured tables ONLY if we have specific structured keywords and category indicators match
        if structured_keywords:
            # B. Search MSP Rates Table
            if has_msp_indicator:
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
            if has_loan_indicator:
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
            if has_scheme_indicator:
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
                        ORDER BY rank
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

    # If nothing was matched in the database, check for general greeting words to reply warmly
    GREETING_WORDS = {'hello', 'hi', 'hey', 'namaste', 'namaskar', 'dhanyawad', 'thanks', 'thank you', 'नमस्ते', 'नमस्कार', 'धन्यवाद', 'थँक्स', 'राम राम'}
    if any(word in GREETING_WORDS for word in words):
        return "Hello! I am KrushiSarthi, your smart agricultural assistant. How can I help you today with crop rates, government schemes, or farm loans?"

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


def get_translated_note(dest_lang):
    """
    Get the general knowledge footnote translated to the target language.
    """
    if dest_lang == 'hi':
        return "नोट: यह प्रतिक्रिया एआई के सामान्य ज्ञान का उपयोग करके उत्पन्न की गई है और यह आधिकारिक सरकारी जानकारी का प्रतिनिधित्व नहीं कर सकती है।"
    if dest_lang == 'mr':
        return "टीप: हा प्रतिसाद AI च्या सामान्य ज्ञानाचा वापर करून तयार केला गेला आहे आणि तो अधिकृत सरकारी माहितीचे प्रतिनिधित्व करू शकत नाही."
    return "Note: This response is generated using AI's general knowledge and may not represent official government information."


def get_answer(user_input):
    load_env()
    user_lang = detect_language(user_input)
    
    # Translate language code to full language name for the prompt
    lang_names = {'hi': 'Hindi', 'mr': 'Marathi', 'en': 'English'}
    user_lang_name = lang_names.get(user_lang, 'English')
    
    # Step 2: Search local SQLite database for up to 3 relevant records
    db_records = search_local_database(user_input)
    
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if db_records:
        # Step 3 & 6: Combine matched database records into a single context
        context_parts = []
        for idx, rec in enumerate(db_records, 1):
            context_parts.append(f"Record {idx} ({rec['type']}):\n{rec['content']}")
        context = "\n\n".join(context_parts)
        
        print(f"[CHATBOT] DB context found. Querying Gemini with strict context rules.")
        
        prompt = f"""You are a helpful agricultural assistant chatbot named KrushiSarthi.
An user asked a question, and we retrieved the following relevant records from our database:

Database Context:
{context}

User's Question: "{user_input}"

Guidelines (CRITICAL):
1. Answer the user's question clearly, politely, and concisely.
2. YOU MUST ANSWER THE QUESTION ONLY USING THE PROVIDED DATABASE CONTEXT.
3. NEVER fabricate, invent, or hallucinate information. If the context does not contain the answer to the user's question, state that you couldn't find the exact details in the database.
4. Preserve important numbers, eligibility criteria, interest rates, dates, and official source links exactly as they are in the context.
5. YOU MUST RESPOND IN the detected user language ({user_lang_name}).

Your Response:"""
        
        if api_key:
            response = call_gemini(prompt)
            if response:
                return response
                
        # Offline fallback if API key is missing or call fails (429/503)
        print("[CHATBOT] Gemini API offline/rate-limited. Falling back to direct database results.")
        local_res = get_local_db_answer(user_input)
        if local_res:
            return translate_to_lang(local_res, user_lang)
        return get_answer_fallback(user_input)
        
    else:
        # Step 4: No context found in database. Answer using Gemini's general knowledge.
        print(f"[CHATBOT] No DB context found. Querying Gemini's general knowledge.")
        
        prompt = f"""You are a helpful agricultural assistant chatbot named KrushiSarthi.
Answer the user's question using your general knowledge about agriculture, farming, crops, and rural livelihoods.

User's Question: "{user_input}"

Guidelines:
1. Answer the user's question clearly, politely, and accurately.
2. Keep the response helpful and focused on agriculture.
3. YOU MUST RESPOND IN the detected user language ({user_lang_name}).

Your Response:"""
        
        if api_key:
            response = call_gemini(prompt)
            if response:
                # Step 5: Append the general knowledge warning footnote
                footnote = get_translated_note(user_lang)
                return f"{response}\n\n{footnote}"
                
        # Offline fallback if API key is missing or call fails (429/503)
        print("[CHATBOT] Gemini API offline/rate-limited. Querying offline backup search.")
        local_res = get_local_db_answer(user_input)
        if local_res:
            return translate_to_lang(local_res, user_lang)
        return get_answer_fallback(user_input)
