import os
import sys

# Configure stdout/stderr to use UTF-8 to prevent unicode print crashes on Windows terminal
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from krushiApp.chatbot import get_answer, get_db_path, is_safe_sql, clean_sql

def run_tests():
    print("--- Chatbot Implementation Test ---")
    print(f"Database Path: {get_db_path()}")
    
    # Verify .env loading
    api_key = os.environ.get('GEMINI_API_KEY')
    model = os.environ.get('GEMINI_MODEL')
    print(f"GEMINI_API_KEY found: {'Yes (Length: ' + str(len(api_key)) + ')' if api_key else 'No'}")
    print(f"GEMINI_MODEL: {model}")

    if not api_key:
        print("ERROR: Please make sure GEMINI_API_KEY is configured in your .env file.")
        return

    # SQL safety checks
    print("\n--- Testing SQL Safety Helper ---")
    test_queries = [
        ("SELECT * FROM csv_msp_rates", True),
        ("INSERT INTO csv_msp_rates VALUES (1, 'Test')", False),
        ("SELECT * FROM csv_msp_rates; DROP TABLE csv_msp_rates;", False),
        ("select crop, season from csv_msp_rates where crop = 'Paddy'", True)
    ]
    for q, expected in test_queries:
        safe = is_safe_sql(q)
        print(f"Query: {q} | Safe: {safe} | Expected: {expected}")
        assert safe == expected, f"Failed safety check for query: {q}"

    # Chatbot Q&A testing
    test_questions = [
        "Hello! Who are you?",
        "What is the MSP of Paddy for 2025-26?",
        "धान का एमएसपी क्या है?",
        "मला पीक कर्जासाठी कोणती कागदपत्रे लागतील?",
        "Why is crop rotation important in farming?"
    ]

    import time
    print("\n--- Testing Chatbot Responses ---")
    for q in test_questions:
        print(f"\nUser Question: {q}")
        reply = get_answer(q)
        print(f"Bot Reply: {reply}")
        print("-" * 50)
        time.sleep(7)

if __name__ == '__main__':
    run_tests()
