<<<<<<< HEAD
# KrushiSarthi

Welcome to KrushiSarthi — a smart and user-friendly Django platform designed to support farmers with access to vital agricultural information, government schemes, MSP rates, loan guidance, and communication tools.

Whether you are a farmer looking for practical information or an admin managing content and outreach, KrushiSarthi brings everything together in one place.Support multilingual content for English, Hindi, and Marathi.

## Why This Project Matters

KrushiSarthi helps users quickly find:

- Government schemes and subsidy information
- MSP rates for crops by season and year
- Agricultural loan options from different banks
- Basic agricultural assistance through a chatbot
- Registration and communication features for farmers

## Key Features

- Browse government schemes with descriptions, benefits, eligibility, and application links
- View MSP rates for crops by season and year
- Explore agriculture loan opportunities and related details
- Register farmers through a simple form-based workflow
- Use an integrated chatbot for basic agricultural guidance
- Manage schemes, MSP data, and loans through a custom admin experience
- Send SMS notifications to registered farmers when configured
- Support multilingual content for English, Hindi, and Marathi

## Technologies Used

- Python 3.10+
- Django
- SQLite (default database)
- HTML, CSS, and JavaScript
- Django Templates
- Requests
- Localization support for Hindi and Marathi
=======
# KrushiSarthi 🌾

KrushiSarthi is a smart, localized Django-based agricultural helper platform built to empower farmers with quick and easy access to crucial resources. It supports multilingual content in **English, Hindi, and Marathi**.

The platform provides a comprehensive suite of tools, including a chatbot that dynamically translates queries, builds SQLite database lookups, and responds back in the farmer's native language.

---

## Key Features

- **Government Schemes**: Browse, filter, and learn about agricultural schemes, benefits, eligibility, and applications.
- **MSP Rates Tracker**: Keep track of the Minimum Support Prices (MSP) of crops by season, crop type, and marketing year.
- **Agriculture Loans**: Discover and compare farm loans, interest rates, repayment periods, and documents required.
- **Farmer Registration & SMS Broadcast**: Simple registration workflow with built-in capability to broadcast SMS alerts (via Fast2SMS) to registered farmers when new schemes are introduced.
- **Advanced AI Chatbot**:
  - **Online Flow**: Powered by Gemini API, the chatbot converts natural language queries to safe SQL, queries the SQLite database, and replies with precise details translated into the user's language.
  - **Offline Fallback Flow**: In case of rate limits or connectivity issues, it uses a fast-fail offline search mechanism with a Devanagari translation mapper, querying SQLite database tables directly and returning translated answers in under 100 milliseconds.

---
>>>>>>> f400828 (Integrate Gemini API chatbot, SQLite database migration, offline-first fallback, and configure gitignore to ignore sensitive files)

## Project Structure

```text
KrushiSarthi/
├── README.md
<<<<<<< HEAD
├── krushiSarthi/
│   ├── manage.py
│   ├── krushiApp/
=======
├── db.sqlite3                       # Main database (holds Django models & CSV converted tables)
├── krushiSarthi/                    # Project root
│   ├── manage.py
│   ├── import_csv_to_sqlite.py       # Migrates CSV files under krushiApp/data to SQLite
│   ├── test_chatbot.py              # Test suite for validating the chatbot queries & translation
│   ├── test_sms.py                  # Test suite for validating SMS notifications
│   ├── krushiApp/                   # Application directory
│   │   ├── data/                    # Holds raw government, loan, MSP, and QA CSV files
>>>>>>> f400828 (Integrate Gemini API chatbot, SQLite database migration, offline-first fallback, and configure gitignore to ignore sensitive files)
│   │   ├── templates/
│   │   ├── static/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
<<<<<<< HEAD
│   │   ├── utils.py
│   │   └── chatbot.py
│   └── krushiSarthi/
│       └── settings.py
└── db.sqlite3
```

## Prerequisites

Before getting started, make sure you have:

- Python 3.10 or newer
- pip
- A virtual environment tool such as venv

## Quick Start

Follow these simple steps to get the project running locally:

1. Clone the repository
2. Navigate to the project folder
3. Create and activate a virtual environment

```bash
cd KrushiSarthi/krushiSarthi
python -m venv .venv
.venv\Scripts\activate
```

4. Install the required dependencies

=======
│   │   ├── utils.py                 # Core utility functions (like SMS sending)
│   │   └── chatbot.py               # Two-stage Gemini SQL and offline-fallback chatbot logic
│   └── krushiSarthi/                # Settings and configurations
│       └── settings.py
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.10 or newer
- `pip`
- A virtual environment tool (such as `venv`)

### 2. Navigate and Create Virtual Environment
Open your shell (e.g., PowerShell on Windows or Bash on Linux/macOS):
```bash
cd KrushiSarthi
python -m venv .venv
```
Activate it:
- **Windows (PowerShell)**: `.venv\Scripts\Activate.ps1`
- **Linux/macOS**: `source .venv/bin/activate`

### 3. Install Dependencies
>>>>>>> f400828 (Integrate Gemini API chatbot, SQLite database migration, offline-first fallback, and configure gitignore to ignore sensitive files)
```bash
pip install django requests
```

<<<<<<< HEAD
5. Apply database migrations

```bash
python manage.py migrate
```

6. Start the development server

```bash
python manage.py runserver
```

7. Open the app in your browser at http://127.0.0.1:8000/

## Admin Setup

Create a superuser if you want to access the administrative area:

```bash
python manage.py createsuperuser
```

## Running the Application

Start the development server:

```bash
python manage.py runserver
```

Open the application in your browser at:

- http://127.0.0.1:8000/

## Main Pages

- Home: /
- Government Schemes: /schemes/
- MSP Rates: /msp/
- Agricultural Loans: /agriloans/
- Chatbot: /chatbot/
- Farmer Registration: /register/
- Admin Login: /admin-panel/login/

## SMS Configuration

SMS notifications are supported through a Fast2SMS-style API integration. To enable this feature, set the following environment variables:

```bash
set SMS_API_URL=https://www.fast2sms.com/dev/bulkV2
set SMS_API_KEY=your_api_key
```
=======
### 4. Configure Environment Variables (`.env`)
Create a `.env` file in the `krushiSarthi/` directory (where `manage.py` is located) and define your keys:
```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Fast2SMS Configuration
SMS_API_URL=https://www.fast2sms.com/dev/bulkV2
SMS_API_KEY=your_fast2sms_api_key_here
```

### 5. Convert CSV Datasets into SQLite Tables
Run the database import script to convert all agricultural CSV files into indexed SQLite tables (creating an FTS5 full-text index for the QA dataset):
```bash
python import_csv_to_sqlite.py
```

### 6. Apply Django Migrations & Start Server
```bash
python manage.py migrate
python manage.py runserver
```
Visit http://127.0.0.1:8000/ to view the application.

---



