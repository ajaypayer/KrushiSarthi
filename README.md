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

## Project Structure

```text
KrushiSarthi/
├── README.md
├── krushiSarthi/
│   ├── manage.py
│   ├── krushiApp/
│   │   ├── templates/
│   │   ├── static/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
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

```bash
pip install django requests
```

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



