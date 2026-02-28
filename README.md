# Biblioteka — Library Management System

A comprehensive web-based library management system built with FastAPI, SQLAlchemy, and vanilla JavaScript. Manage books, members, loans, reservations, and memberships with an intuitive interface supporting Serbian and English languages.

## Features

- **Book Management**: Add, edit, and manage book inventory with details (title, author, publisher, genre, language, ISBN)
- **Member Management**: Track members, their membership status, and contact information
- **Loan System**: Issue books, track due dates, manage overdue items
- **Reservations**: Members can reserve books, automatic queue management
- **Membership System**: Manage annual memberships with flexible pricing per member type
- **Reports**: Generate reports on overdue items, membership income, popular books, expired memberships
- **Staff Management**: Multi-user system with role-based access
- **Import/Export**: Import/export data from legacy systems (Excel templates)
- **Database Backup**: Automatic daily backups with manual backup option
- **Multi-language Support**: Serbian and English with persistent language preference
- **Session Management**: Automatic logout after 30 minutes of inactivity with warning
- **Dynamic Currency**: Support for 9 currencies with settings configuration
- **Email Notifications**: Automatic notifications for loans, overdue items, reservations, memberships

## System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Windows, macOS, or Linux
- **RAM**: Minimum 512 MB (1 GB recommended)
- **Disk Space**: Minimum 500 MB for installation and database

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/Biblioteka.git
cd Biblioteka
```

### 2. Create Python Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.envexample` to `.env`:

```bash
# Windows
copy .envexample config\.env

# macOS / Linux
cp .envexample config/.env
```

Edit `config/.env` with your settings:

```env
# Database Configuration
DATABASE_URL=sqlite:///./biblioteka.db

# JWT Security - Change this to a secure random string
SECRET_KEY=your-very-secure-secret-key-here-change-in-production

# Server Settings
DEBUG=False
HOST=0.0.0.0
PORT=8000
```

### 5. Initialize Database

The database will be created automatically on first run. On first startup, a default admin user will be created:

- **Username**: `admin`
- **Password**: `admin`
- **⚠️ Change this password immediately after first login**

## Running the Application

### Development Mode

```bash
# Windows
python launcher.py

# macOS / Linux
python3 launcher.py
```

The application will be available at: **http://localhost:8000**

### Production Mode

For production deployment, modify `config/.env`:

```env
DEBUG=False
SECRET_KEY=your-production-secret-key
HOST=0.0.0.0
PORT=8000
```

Then run with a production ASGI server:

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

## Configuration

### Database

- **Default**: SQLite (`biblioteka.db`) - suitable for small to medium libraries
- **PostgreSQL**: For larger deployments, modify `DATABASE_URL` in `.env`:
  ```
  DATABASE_URL=postgresql://user:password@localhost/biblioteka
  ```

### Email Notifications

The system supports email notifications for:
- Loan reminders (before due date)
- Overdue notifications
- Reservation availability alerts
- Membership expiration warnings

Configure email settings in the **Settings** page (General tab).

### Membership Pricing

Set annual membership prices per member type in **Settings** → **Pricing** tab:
- Adults
- Students
- Children
- Pensioners
- Institutions

### Currency

Change the library's currency in **Settings** → **General** tab. Supported currencies:
- EUR, GBP, USD, RSD, BAM, PLN, HUF, CZK, HRK

### Language

Switch between Serbian (sr) and English (en) in **Settings** → **General** tab. Language preference is saved and persists across sessions.

## Default Credentials

After first installation:

| Field | Value |
|-------|-------|
| **Username** | admin |
| **Password** | admin |

⚠️ **Security**: Change password immediately after first login.

## Project Structure

```
Biblioteka/
├── app/
│   ├── models/              # SQLAlchemy database models
│   ├── routes/              # FastAPI route handlers
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic (backup, excel, notifications)
│   ├── utils/               # Utilities (auth, logging, scheduler)
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI app initialization
├── frontend/
│   ├── static/
│   │   ├── app.js           # Frontend JavaScript
│   │   ├── style.css        # Styling
│   │   └── translations.json # Multi-language translations
│   └── templates/           # Jinja2 HTML templates
├── config/
│   └── .env                 # Environment configuration (create from .envexample)
├── backups/                 # Automatic database backups
├── exports/                 # Exported reports (Excel, PDF)
├── requirements.txt         # Python dependencies
├── launcher.py              # Application entry point
├── Biblioteka.spec          # PyInstaller specification
└── README.md                # This file
```

## Key Technologies

- **Backend**: FastAPI, SQLAlchemy, Uvicorn
- **Frontend**: Vanilla JavaScript, Jinja2 templates
- **Database**: SQLite (default) or PostgreSQL
- **Authentication**: JWT (JSON Web Tokens)
- **Task Scheduling**: APScheduler
- **Reports**: OpenPyXL (Excel), ReportLab (PDF)
- **Email**: Python-Jose with SMTP

## Usage Guide

### Adding Books

1. Go to **Books** tab
2. Click **+ Nova knjiga** button
3. Fill in book details (title, author, publisher, etc.)
4. Click **Sačuvaj**

### Managing Members

1. Go to **Members** tab
2. Click **+ Novi član** button
3. Enter member information
4. Click **Registruj**

### Issuing Books

1. Go to **Books** tab
2. Find book and click to open
3. Click **+ Novi primerak** to add a copy (if needed)
4. Click action button on book copy
5. Search for member and confirm loan

### Generating Reports

1. Go to **Reports** tab
2. Select report type:
   - **Kašnjenja** (Overdue items)
   - **Članarine** (Membership payments by year)
   - **Najpopularnije** (Most borrowed books)
   - **Istekle članarine** (Expired memberships)

### Backing Up Database

1. Go to **Settings** → **Backup** tab
2. Click **Backup sada** to create immediate backup
3. Or use **Export komplet baze (ZIP)** to download complete database

## Troubleshooting

### Application Won't Start

1. Verify Python version: `python --version` (must be 3.9+)
2. Check virtual environment is activated
3. Verify all dependencies installed: `pip install -r requirements.txt`
4. Check `.env` file exists in `config/` directory
5. Check port 8000 is not in use: `netstat -an | find ":8000"` (Windows)

### Database Issues

1. Delete `biblioteka.db` to reset database
2. Restart application (database will be recreated)
3. Default admin user will be created again

### Port Already in Use

Change `PORT` in `.env`:

```env
PORT=8001
```

Then access at `http://localhost:8001`

### Language Not Changing

1. Clear browser cache (Ctrl+Shift+Delete)
2. Verify Settings page loads correctly
3. Check browser console (F12) for errors

## Security Notes

- **Never commit `.env` file** to version control
- Change `SECRET_KEY` before production deployment
- Use HTTPS in production
- Keep Python packages updated: `pip install --upgrade -r requirements.txt`
- Regularly backup database: `config/backups/` directory
- Change default admin password immediately after installation

## Performance Tips

- For 10,000+ books: Consider PostgreSQL instead of SQLite
- Enable database query caching for reports
- Regular database backups recommended
- Clean old backups periodically to save disk space

## Support & Contribution

For issues, feature requests, or contributions, please visit the GitHub repository.

## License

This project is licensed under the MIT License.

---

**Version**: 1.0.0  
**Last Updated**: February 2026
