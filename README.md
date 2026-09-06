# Smart Digital Visitor Pass Generator

A web-based visitor management system for a college major project. Visitors register before arrival, receive a unique Pass ID with a QR code and a printable digital pass, and security staff verify, check in, and check out visitors from an admin dashboard.

This is a local demonstration project. It is **not** production software.

## Features

- Visitor pre-registration with photo upload
- Unique Pass IDs such as `VIS-2026-00001`
- QR codes that open a public verification page (no personal data inside the QR)
- Professional digital visitor pass (HTML + PDF download)
- Pass verification by typing a Pass ID or scanning the QR code
- Check-in and check-out with status rules
- Admin dashboard with search, filters, and pagination
- Visitor history and basic reports (CSV and PDF export)
- Optional email notifications over SMTP
- RPA-style automation module for the registration pipeline
- Optional visitor-purpose classification (keyword-based; AI API only if you add a key)

## Technology stack

| Layer | Tools |
| --- | --- |
| Backend | Python, Flask |
| Database | SQLite + SQLAlchemy |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| QR / PDF | `qrcode`, ReportLab, Pillow |
| Email | SMTP (optional) |
| Automation | Python bot + optional Playwright |

## Architecture

```
Visitor (browser)
    → Flask routes
        → Validation
        → SQLite (Visitor / Admin)
        → QR generator
        → PDF pass generator
        → Optional email bot
Admin (browser)
    → Session login
    → Dashboard / reports / check-in / check-out
Security phone camera
    → QR URL  /verify/VIS-2026-00001
```

The RPA module (`automation/visitor_bot.py`) runs the same steps a clerk would repeat: validate → create record → Pass ID → QR → PDF → notify → keep status `EXPECTED`.

## Installation

### macOS / Linux

```bash
cd digital-visitor-pass
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows

```bat
cd digital-visitor-pass
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Playwright is only needed for the optional browser demo:

```bash
playwright install chromium
```

You can skip that command. The website and the Python visitor bot work without it.

## Database setup

The SQLite database is created automatically on first run:

`instance/visitor.db`

A demo admin account is also created automatically.

## How to run

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

Optional sample records (about 10 fake visitors):

```bash
python app.py --demo-data
```

Then start the server with `python app.py`.

## Demo login

These credentials are for classroom demonstration only. Change them before any real deployment.

- Username: `admin`
- Password: `admin123`

Passwords are stored as hashes, not as plain text.

## Environment variables

Copy `.env.example` to `.env` if you want to override defaults.

Email is **disabled** when `SMTP_HOST` or `MAIL_FROM` is empty. The rest of the project still works.

```
SECRET_KEY=change-this-to-a-random-string
ORGANIZATION_NAME=Apex Institute of Technology
BASE_URL=http://127.0.0.1:5000
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
MAIL_FROM=
OPENAI_API_KEY=
```

Never put real passwords in source files.

## How QR verification works

1. Each pass gets a QR code whose only content is a URL, for example `http://127.0.0.1:5000/verify/VIS-2026-00001`.
2. A phone camera can open that URL.
3. Security can also type the Pass ID on `/verify`.
4. Valid passes show name, host, purpose, date, time, and status.
5. Unknown IDs show **INVALID VISITOR PASS** without extra personal data.
6. Old unused passes show **EXPIRED VISITOR PASS**.

## How RPA works

`VisitorBot.process()` automates the clerk workflow in Python:

1. Validate visitor information
2. Create the database record
3. Generate a Pass ID
4. Generate a QR code
5. Generate the PDF pass
6. Send email if SMTP is configured
7. Leave the visitor in `EXPECTED` status until check-in

Optional Playwright helper `run_browser_registration()` fills the public web form the way a desktop RPA bot would.

## Project workflow

1. Open the website
2. Register a visitor and upload a photo
3. System creates a Pass ID, QR code, and PDF
4. Download or view the digital pass
5. Verify the pass by ID or QR
6. Admin signs in
7. Dashboard shows the visitor
8. Check in, then later check out
9. Export a CSV or PDF report

## Folder structure

```
digital-visitor-pass/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── database/
│   ├── __init__.py
│   └── models.py
├── routes/
│   ├── visitor_routes.py
│   ├── admin_routes.py
│   └── verification_routes.py
├── automation/
│   ├── visitor_bot.py
│   └── email_bot.py
├── utils/
│   ├── qr_generator.py
│   ├── pass_generator.py
│   ├── email_sender.py
│   └── ...
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   ├── uploads/
│   ├── qr/
│   └── passes/
└── instance/
    └── visitor.db
```

## Status values

- `EXPECTED` — registered, not yet at the gate
- `CHECKED_IN` — currently inside
- `CHECKED_OUT` — visit finished
- `EXPIRED` — visit date passed without check-in
- `CANCELLED` — pass cannot be used

Check-in is allowed only on the visit date, and only from `EXPECTED`. Check-out is allowed only from `CHECKED_IN`.

## Future enhancements

- Host email field and per-host notifications
- SMS alerts
- Live camera QR scanner in the admin page
- Role-based staff accounts
- Appointment slots and visitor capacity limits

## License

Prepared as an academic demonstration project.
