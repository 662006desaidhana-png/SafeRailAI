import os
import sqlite3

from flask import (
    Flask,
    render_template,
    Response,
    request,
    redirect,
    url_for,
    send_from_directory,
    session
)

from werkzeug.security import generate_password_hash, check_password_hash

from stream import generate_frames


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "saferailai-development-secret-change-before-deployment"
)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "database.db"
)


# =========================
# DATABASE
# =========================

def init_users_table():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Existing users table ko preserve karega
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Existing database mein naye columns add karna
    columns = [
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(users)"
        ).fetchall()
    ]

    if "parent1_phone" not in columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN parent1_phone TEXT"
        )

    if "parent2_phone" not in columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN parent2_phone TEXT"
        )

    conn.commit()
    conn.close()


init_users_table()


# =========================
# PHONE VALIDATION
# =========================

def clean_phone(phone):

    phone = phone.strip()

    # Spaces, -, brackets etc. remove
    if phone.startswith("+"):
        cleaned = "+" + "".join(
            character for character in phone[1:]
            if character.isdigit()
        )
    else:
        cleaned = "".join(
            character for character in phone
            if character.isdigit()
        )

    return cleaned


def valid_phone(phone):

    digits = "".join(
        character for character in phone
        if character.isdigit()
    )

    return 10 <= len(digits) <= 15


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        parent1_phone = clean_phone(
            request.form.get(
                "parent1_phone",
                ""
            )
        )

        parent2_phone = clean_phone(
            request.form.get(
                "parent2_phone",
                ""
            )
        )

        # Basic validation
        if not username or not password:
            return render_template(
                "register.html",
                error="Username and password are required."
            )

        if len(username) < 3:
            return render_template(
                "register.html",
                error="Username must be at least 3 characters."
            )

        if len(password) < 4:
            return render_template(
                "register.html",
                error="Password must be at least 4 characters."
            )

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match."
            )

        if not valid_phone(parent1_phone):
            return render_template(
                "register.html",
                error="Please enter a valid Parent 1 phone number."
            )

        if not valid_phone(parent2_phone):
            return render_template(
                "register.html",
                error="Please enter a valid Parent 2 phone number."
            )

        password_hash = generate_password_hash(password)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    password,
                    parent1_phone,
                    parent2_phone
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    parent1_phone,
                    parent2_phone
                )
            )

            conn.commit()
            conn.close()

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                error="Username already exists. Please choose another."
            )

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, username, password
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(
            user[2],
            password
        ):

            session["user_id"] = user[0]
            session["username"] = user[1]

            print(
                "Login successful:",
                username
            )

            return redirect(
                url_for("dashboard")
            )

        print(
            "Login failed:",
            username
        )

        return render_template(
            "login.html",
            error="Wrong username or password."
        )

    return render_template("login.html")


# =========================
# LOGIN PROTECTION
# =========================

def is_logged_in():
    return "user_id" in session


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if not is_logged_in():
        return redirect(
            url_for("login")
        )

    return render_template(
        "dashboard.html",
        username=session.get("username")
    )


# =========================
# CAMERA
# =========================

@app.route("/camera")
def camera():

    if not is_logged_in():
        return redirect(
            url_for("login")
        )

    return render_template(
        "camera.html"
    )


# =========================
# LIVE VIDEO
# =========================

@app.route("/video_feed")
def video_feed():

    if not is_logged_in():
        return redirect(
            url_for("login")
        )

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# =========================
# INCIDENT REPORT
# =========================

@app.route("/report")
def report():

    if not is_logged_in():
        return redirect(
            url_for("login")
        )

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, time, object_name, image
        FROM incidents
        ORDER BY id DESC
    """)

    incidents = cursor.fetchall()

    conn.close()

    return render_template(
        "report.html",
        incidents=incidents
    )


# =========================
# INCIDENT IMAGE
# =========================

@app.route("/incidents/<filename>")
def incident_image(filename):

    if not is_logged_in():
        return redirect(
            url_for("login")
        )

    return send_from_directory(
        "incidents",
        filename)
# =========================
# ALERT CENTER
# =========================

@app.route("/alert")
def alert():

    if not is_logged_in():
        return redirect(
            url_for("login")
        )

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Logged-in user ke parent contacts
    cursor.execute(
        """
        SELECT
            username,
            parent1_phone,
            parent2_phone
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    # Latest AI incident
    cursor.execute(
        """
        SELECT
            date,
            time,
            object_name,
            image
        FROM incidents
        ORDER BY id DESC
        LIMIT 1
        """
    )

    latest_incident = cursor.fetchone()

    conn.close()

    parent1_phone = user[1] if user else ""
    parent2_phone = user[2] if user else ""

    if latest_incident:

        latest_date = latest_incident[0]
        latest_time = latest_incident[1]
        latest_object = latest_incident[2]
        latest_image = latest_incident[3]

    else:

        latest_date = None
        latest_time = None
        latest_object = None
        latest_image = None

    return render_template(
        "alert.html",
        username=session.get("username"),
        parent1_phone=parent1_phone,
        parent2_phone=parent2_phone,
        latest_date=latest_date,
        latest_time=latest_time,
        latest_object=latest_object,
        latest_image=latest_image
    )



   
# =========================
# SETTINGS
# =========================

@app.route("/settings")
def settings():

    if not is_logged_in():
        return redirect(
            url_for("login")
        )

    return render_template(
        "settings.html"
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )