from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html ") 

@app.route("/report")
def report():
    return"<h1> Incident Report "


if __name__ == "__main__":
    app.run(debug=True)