import os
from flask import Flask, request, jsonify,render_template,session
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__,template_folder="templates")

# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive","https://www.googleapis.com/auth/spreadsheets.readonly"]

# Authenticate using service account credentials
creds = ServiceAccountCredentials.from_json_keyfile_name("bookverse-453507-4a59e72b7895.json", scope)
client = gspread.authorize(creds)

# Open the Google Sheet by name
sheet = client.open("BookverseUsers").sheet1  # Replace with your Google Sheet name
sheets = client.open("Metadata").sheet1
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
@app.route('/')
def home():
    return render_template("book_search_intro.html")

@app.route('/admin_login_page')
def admin_login_page():
    return render_template("admin_login.html")

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clears session data
    return '', 204

@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # Replace with your actual admin credentials
    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PASSWORD = "admin123"

    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        return jsonify({"message": "Admin login successful!"}), 200
    else:
        return jsonify({"error": "Invalid admin email or password"}), 401

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route('/login_page')
def login_page():
    return render_template("login.html")

@app.route('/register_page')
def register_page():
    return render_template("register.html")


@app.route('/get_users')
def get_users():
    try:
        records = sheet.get_all_records()
        users = [{"fullname": record["Full Name"], "email": record["Email"]} for record in records]
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import json
import math
from collections import defaultdict
@app.route('/get_book_statistics')
def get_book_statistics():
    try:
        records = sheets.get_all_records()
        book_counts = defaultdict(int)  # Dictionary to store book count by subject

        for record in records:
            subject = record.get("Subject", "Unknown")  # Get subject column
            book_counts[subject] += 1  # Count books for each subject

        return jsonify({"book_counts": book_counts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_books')
def get_books():
    try:
        records = sheets.get_all_records()
        total_books = len(records)  # Get total book count
        print(f"📌 Debug - Total Books Count: {total_books}")  # Debugging output

        if not records:
            return jsonify({"error": "No books found"}), 404

        # Limit response to 50 records
        records = records[:50]

        books = []
        for record in records:
            book = {
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
                "Link": record.get("Link", "#")  # Default to "#" if no link
            }
            books.append(book)

        return jsonify({"total_books": total_books, "books": books})  # Send count + books
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/search_page')
def search_page():
    return render_template("search.html")

def get_metadata():
    try:
        values = sheets.get_all_values()
        headers = values[0]  # First row as headers
        records = values[1:]  # Remaining rows as data

        metadata = []
        for row in records:
            item = {headers[i]: row[i] for i in range(len(headers))}
            item["pdf_url"] = item.get("Link", "")  # Fetch the existing link from the 'Link' column
            metadata.append(item)

        return metadata
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return []

@app.route("/search", methods=["POST"])
def search():
    query_data = request.form.to_dict()
    metadata = get_metadata()
    filtered_results = []

    for item in metadata:
        match = all(value.lower() in str(item.get(key, "")).lower() for key, value in query_data.items() if value)
        if match:
            filtered_results.append(item)

    return jsonify(filtered_results)

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


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    fullname = data.get("fullname")
    email = data.get("email")
    password = data.get("password")
    
    if not fullname or not email or not password:
        return jsonify({"message": "All fields are required!"}), 400
    
    sheet.append_row([fullname, email, password])
    return jsonify({"message": "Registration successful!"})

if __name__ == '__main__':
    app.run(debug=True)
