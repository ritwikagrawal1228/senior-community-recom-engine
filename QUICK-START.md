# 🚀 Quick Start Guide

## How to Start the Senior Living Recommendation System

### Prerequisites

1. **Python 3.8+** installed
2. **pip** (Python package manager)
3. **Environment variables** configured (see below)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Required: Gemini API Key for AI processing
GEMINI_API_KEY=your_gemini_api_key_here

# Required: Flask secret key for sessions
SECRET_KEY=your_secret_key_here

# Optional: Google Sheets credentials (if using CRM integration)
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
```

**To generate a SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

### Step 3: Start the Application

#### Option A: Direct Python (Recommended for Development)

```bash
python app.py
```

#### Option B: Flask CLI

```bash
flask run --host=0.0.0.0 --port=5050
```

### Step 4: Access the Application

Once started, open your browser and navigate to:

- **Main Application:** http://localhost:5050
- **Login Page:** http://localhost:5050/login
- **Health Check:** http://localhost:5050/api/health

### Default Login Credentials

Check your `app.py` file for the default username/password setup, or look for authentication configuration.

---

## 🐳 Alternative: Docker Deployment

If you prefer using Docker:

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

See `DOCKER_DEPLOYMENT.md` for detailed Docker instructions.

---

## 🛠️ Troubleshooting

### Port Already in Use
If port 5050 is already in use, you can change it in `app.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5050)  # Change 5050 to another port
```

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Environment Variables Not Loading
Make sure:
- `.env` file exists in the root directory
- `python-dotenv` is installed (`pip install python-dotenv`)
- Variables are correctly formatted (no spaces around `=`)

### Module Not Found Errors
```bash
# Make sure you're in the project root directory
cd /path/to/Capstone-final

# Verify Python can find the modules
python -c "import app; print('OK')"
```

---

## 📝 Notes

- The app runs on **port 5050** by default
- Debug mode is **disabled** by default (change `debug=False` to `debug=True` in `app.py` for development)
- Make sure all required data files (like `DataFile_students_OPTIMIZED.xlsx`) are in the project directory
- The UI reskin features are automatically included - no additional setup needed!

---

**Happy coding! 🎉**

