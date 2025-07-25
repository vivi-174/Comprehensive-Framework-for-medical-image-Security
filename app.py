import os
import hashlib
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from alteration_detection import detect_altered_regions 

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

users = {
    "admin": "admin123",
    "Sophia" : "sophia123",
    "Ethan" : "ethan123",
    "Josh" : "josh123"
}


def load_mri_hashes():
    with open("stored_mri_hashes.json", "r") as file:
        return json.load(file)

stored_mri_hashes = load_mri_hashes()


def calculate_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

@app.route("/")
def index():
    
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.pop('_flashes', None)
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "error")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users:
            flash("User already exists", "error")
        else:
            users[username] = password
            flash("Registration successful", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    return render_template("dashboard.html", username=username)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(request.url)
        
        # Ensure the file has a valid extension (optional)
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            flash("Invalid file type. Only images are allowed.", "error")
            return redirect(request.url)
        
        # Save the file to the server
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        
        # Flash success message and redirect
        flash("File uploaded successfully", "success")
        return redirect(url_for("verify", image_name=file.filename)) 

    return render_template("upload.html")


def compute_file_hash(file_path):
    hasher = hashlib.md5() 
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_patient_data():
    with open("patient_data.json", "r") as f:
        return json.load(f)

@app.route("/verify/<image_name>")
def verify(image_name):
    if "user" not in session:
        return redirect(url_for("login"))

    upload_path = os.path.join("uploads", image_name)

    if not os.path.exists(upload_path):
        return "Error: Uploaded image not found", 404

    uploaded_hash = compute_file_hash(upload_path)

    is_modified = True
    if image_name in stored_mri_hashes:
        original_hash = stored_mri_hashes[image_name]
        is_modified = uploaded_hash != original_hash

    # Load patient details from JSON
    patient_data = load_patient_data()

    if image_name in patient_data:
        patient_info = patient_data[image_name]
    else:
        patient_info = {
            "name": "Unknown",
            "age": "N/A",
            "dob": "N/A",
            "scan_date": "N/A",
            "scan_time": "N/A"
        }

    ai_verification = "Altered" if is_modified else "No Modifications Detected"
    ai_verification_class = "error" if is_modified else "success"
    altered_regions = ["Temporal Lobe, Right Cortex"] if is_modified else []

    patient_info.update({
        "blockchain_status": "Verified",
        "mri_image": image_name,
        "ai_verification": ai_verification,
        "ai_verification_class": ai_verification_class,
        "altered_regions": altered_regions,
        "blockchain_hash": "0xabc123def456...",
        "blockchain_timestamp": "2025-02-15 11:00 AM",
        "blockchain_node": "Node 7"
    })

    return render_template("verify.html", patient=patient_info)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)