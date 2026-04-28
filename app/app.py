from flask import Flask, request, jsonify, send_file
import sqlite3
import hashlib
import os

app = Flask(__name__)

# Vulnerability 1: Hardcoded secret
app.config["SECRET_KEY"] = "super-secret-key-12345"
API_KEY = "sk_live_1234567890abcdef"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def get_db():
    return sqlite3.connect("database.db")


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS invoices")

    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE invoices (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount INTEGER,
            description TEXT
        )
    """)

    # Vulnerability 2: Weak hashing using MD5
    admin_password = hashlib.md5("admin123".encode()).hexdigest()
    user_password = hashlib.md5("user123".encode()).hexdigest()

    cur.execute("INSERT INTO users VALUES (1, 'admin', ?)", (admin_password,))
    cur.execute("INSERT INTO users VALUES (2, 'pratik', ?)", (user_password,))

    cur.execute("INSERT INTO invoices VALUES (1, 1, 5000, 'Admin laptop purchase')")
    cur.execute("INSERT INTO invoices VALUES (2, 2, 1200, 'Pratik training reimbursement')")

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return "Vulnerable Flask App for DevSecOps Demo"


@app.route("/init-db")
def setup():
    init_db()
    return "Database initialized"


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    password_hash = hashlib.md5(password.encode()).hexdigest()

    conn = get_db()
    cur = conn.cursor()

    # Vulnerability 3: SQL Injection
    query = (
        "SELECT * FROM users WHERE username = '"
        + username
        + "' AND password = '"
        + password_hash
        + "'"
    )

    cur.execute(query)
    user = cur.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful", "user_id": user[0]})
    return jsonify({"message": "Invalid credentials"}), 401


@app.route("/invoice/<int:invoice_id>")
def get_invoice(invoice_id):
    conn = get_db()
    cur = conn.cursor()

    # Vulnerability 4: IDOR
    # No check that current user owns this invoice
    cur.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    invoice = cur.fetchone()
    conn.close()

    if invoice:
        return jsonify({
            "invoice_id": invoice[0],
            "user_id": invoice[1],
            "amount": invoice[2],
            "description": invoice[3]
        })

    return jsonify({"message": "Invoice not found"}), 404


@app.route("/ping")
def ping():
    host = request.args.get("host")

    # Vulnerability 5: Command Injection
    result = os.popen("ping -n 1 " + host).read()

    return "<pre>" + result + "</pre>"


@app.route("/download")
def download_file():
    filename = request.args.get("file")

    # Vulnerability 6: Path Traversal
    file_path = os.path.join("files", filename)

    return send_file(file_path)


if __name__ == "__main__":
    app.run(debug=True)