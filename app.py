import os
import json
from flask import Flask, request, jsonify, render_template, session
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict

# Initialize Flask app
app = Flask(__name__, template_folder="templates")

# ===============================
# ✅ Environment Configuration
# ===============================

# Load environment variables
SERVICE_ACCOUNT_KEY = os.getenv('GOOGLE_CREDENTIALS')
if not SERVICE_ACCOUNT_KEY:
    raise ValueError("Missing GOOGLE_CREDENTIALS environment variable")

# Load Google service account credentials
service_account_info = json.loads(SERVICE_ACCOUNT_KEY)
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(creds)

# Open Google Sheets
USER_SHEET_NAME = os.getenv('USER_SHEET_NAME', 'BookverseUsers')  # For user data
METADATA_SHEET_NAME = os.getenv('METADATA_SHEET_NAME', 'Metadata')  # For book data

# Open sheets
user_sheet = client.open(USER_SHEET_NAME).sheet1
metadata_sheet = client.open(METADATA_SHEET_NAME).sheet1

# Set Flask secret key for session management
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

# Admin credentials (from environment variables)
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# ===============================
# ✅ Routes
# ===============================

# 👉 Home Page
@app.route('/')
def home():
    return render_template("book_search_intro.html")

# 👉 Admin Login Page
@app.route('/admin_login_page')
def admin_login_page():
    return render_template("admin_login.html")

# 👉 Logout (Clear Session)
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

# 👉 Admin Login
@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        session['admin'] = True
        return jsonify({"message": "Admin login successful!"}), 200
    else:
        return jsonify({"error": "Invalid admin email or password"}), 401

# 👉 Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized access"}), 401
    return render_template("admin_dashboard.html")

# 👉 Login Page
@app.route('/login_page')
def login_page():
    return render_template("login.html")

# 👉 Register Page
@app.route('/register_page')
def register_page():
    return render_template("register.html")

# 👉 Search Page
@app.route('/search_page')
def search_page():
    return render_template("search.html")

# ===============================
# ✅ User Management
# ===============================

# 👉 Get All Users
@app.route('/get_users')
def get_users():
    try:
        records = user_sheet.get_all_records()
        users = [{"fullname": record["Full Name"], "email": record["Email"]} for record in records]
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 👉 Register New User
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    fullname = data.get("fullname")
    email = data.get("email")
    password = data.get("password")
    
    if not fullname or not email or not password:
        return jsonify({"message": "All fields are required!"}), 400
    
    user_sheet.append_row([fullname, email, password])
    return jsonify({"message": "Registration successful!"})

# 👉 User Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    #print(f"📌 Debug - Received login attempt: Email: {email}, Password: {password}")  

    # Fetch all records from Google Sheets
    records = sheet.get_all_records()
    #print("📌 Debug - Google Sheets Records:", records)  # Debugging output

    if not records:
        return jsonify({"error": "No records found in database"}), 500

    # Check user credentials
    for record in records:
        #print(f"📌 Debug - Checking record: {record}")  # Debugging output
        if str(record.get("Email")).strip() == str(email).strip() and str(record.get("Password")).strip() == str(password).strip():
            return jsonify({"message": "Login successful!"}), 200

    return jsonify({"error": "Invalid email or password"}), 401


# ===============================
# ✅ Book Management
# ===============================

# 👉 Get Book Statistics
@app.route('/get_book_statistics')
def get_book_statistics():
    try:
        records = metadata_sheet.get_all_records()
        book_counts = defaultdict(int)

        for record in records:
            subject = record.get("Subject", "Unknown")
            book_counts[subject] += 1

        return jsonify({"book_counts": book_counts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 👉 Get Books
@app.route('/get_books')
def get_books():
    try:
        records = metadata_sheet.get_all_records()
        total_books = len(records)
        records = records[:50]  # Limit response to 50 records

        books = [
            {
                "AccNum": record.get("AccNum", "N/A"),
                "CardAuthor": record.get("CardAuthor", "N/A"),
                "Authors": record.get("Authors", "N/A"),
                "CardTitle": record.get("CardTitle", "N/A"),
                "subTitle": record.get("subTitle", "N/A"),
                "AuthorMark": record.get("AuthorMark", "N/A"),
                "Subject": record.get("Subject", "N/A"),
                "Department": record.get("Department", "N/A"),
                "Publisher": record.get("Publisher", "N/A"),
                "PublYear": record.get("PublYear", "N/A"),
                "Gener": record.get("Gener", "N/A"),
                "Link": record.get("Link", "#")
            }
            for record in records
        ]

        return jsonify({"total_books": total_books, "books": books})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 👉 Search Books
@app.route("/search", methods=["POST"])
def search():
    query_data = request.form.to_dict()
    records = metadata_sheet.get_all_records()

    filtered_results = [
        record for record in records
        if all(value.lower() in str(record.get(key, "")).lower() for key, value in query_data.items() if value)
    ]

    return jsonify(filtered_results)

# ===============================
# ✅ Start Flask App
# ===============================

if __name__ == '__main__':
    app.run(debug=True)
