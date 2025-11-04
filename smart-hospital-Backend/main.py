from flask import Flask, request, jsonify, Response
from flask_cors import CORS  # Import CORS
from datetime import datetime
import index  # Imports all functions from index.py
import storage # Imports all functions from storage.py
import jwt
from config import jwt_secret

app = Flask(__name__)
CORS(app)  # Initialize CORS to allow all origins

# --- Auth Routes ---

# --- Util Route ---
@app.route("/hospitals", methods=["GET"])
def get_hospitals_route():
    result = storage.get_hospitals()
    return jsonify(result), (200 if result["success"] else 500)

@app.route("/cleaners", methods=["GET"])
def get_cleaners_route():
    # --- NEW: Get the manager's hospital_id from their login token ---
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        user_hospital_id = payload.get('hospital_id')

        if not user_hospital_id:
            return jsonify({"error": "User is not associated with a hospital."}), 400

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
        return jsonify({"error": "Invalid or expired token"}), 401
    # --- END NEW LOGIC ---

    # Pass the manager's hospital_id to the function
    result = index.get_cleaner_list(user_hospital_id)
    return jsonify(result), (200 if result["success"] else 500)

@app.route("/register", methods=["POST"])
def register_route():
    data = request.get_json()
    if not data or not all(k in data for k in ["email", "password", "role", "full_name"]):
        return jsonify({"success": False, "message": "Missing required fields."}), 400
    
    hospital_id = data.get("hospital_id")
    
    result = index.register_new_user(data["email"], data["password"], data["role"], data["full_name"], hospital_id)
    if result["success"]:
        return jsonify(result), 201
    else:
        return jsonify(result), 409

@app.route("/login", methods=["POST"])
def login_route():
    data = request.get_json()
    if not data or not all(k in data for k in ["email", "password"]):
        return jsonify({"success": False, "message": "Missing email or password."}), 400
    
    result = index.login_user(data["email"], data["password"])
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 401 # 401 Unauthorized



# --- Task Routes ---
@app.route("/assign_task", methods=["POST"])
def assign_task_route():
    data = request.get_json()
    if not data or not all(k in data for k in ["room_id", "cleaner_id", "assignment_date", "assigned_by_id"]):
        return jsonify({"success": False, "message": "Missing required fields."}), 400
    
    result = index.assign_new_task(
        data["room_id"], data["cleaner_id"], data["assigned_by_id"],
        data["assignment_date"], data.get("notes", "")
    )
    return jsonify(result), (201 if result["success"] else 500)

@app.route("/tasks/<string:cleaner_id>", methods=["GET"])
def get_tasks_route(cleaner_id):
    result = index.get_cleaner_tasks(cleaner_id)
    return jsonify(result), (200 if result["success"] else 500)

# --- Manager Task Routes ---
@app.route("/assign_manager_task", methods=["POST"])
def assign_manager_task_route():
    data = request.get_json()
    if not data or not all(k in data for k in ["assigned_by_id", "assigned_to_id", "description", "due_date"]):
        return jsonify({"success": False, "message": "Missing required fields."}), 400
    
    result = index.assign_manager_task(
        data["assigned_by_id"], data["assigned_to_id"],
        data["description"], data["due_date"]
    )
    return jsonify(result), (201 if result["success"] else 500)

@app.route("/manager_tasks/<string:manager_id>", methods=["GET"])
def get_manager_tasks_route(manager_id):
    result = index.get_manager_tasks(manager_id)
    return jsonify(result), (200 if result["success"] else 500)

# --- Verification Route ---
# Replace your entire /verify_room route with this
@app.route("/verify_room", methods=["POST"])
def verify_room_endpoint():
    # --- Step 1: Check for the uploaded photo ---
    if 'after_photo' not in request.files:
        return jsonify({"error": "No 'after_photo' file part in the request."}), 400
    
    after_photo = request.files['after_photo']
    
    # --- Step 2: Get the form data (THIS WAS THE MISSING PART) ---
    room_id = request.form.get('room_id')
    cleaner_id = request.form.get('cleaner_id')
    
    # --- Step 3: Validate the form data ---
    if not all([room_id, cleaner_id]):
        return jsonify({"error": "Missing required form data."}), 400

    # --- Step 4: Get the cleaner's hospital_id safely ---
    cleaner_data_result = storage.get_user_by_id(cleaner_id)
    if not cleaner_data_result.get("success") or not cleaner_data_result.get("data"):
        return jsonify({"error": "Could not verify cleaner's hospital."}), 500
    
    hospital_id = cleaner_data_result["data"].get("hospital_id")
    if not hospital_id:
        return jsonify({"error": "This cleaner is not assigned to a hospital and cannot submit work."}), 400

    # --- Step 5: Analyze the image with Gemini ---
    image_bytes = after_photo.read()
    ai_result = index.analyze_room_image(image_bytes)
    
    if not ai_result["success"]:
        return jsonify({"error": ai_result.get("error", "Failed to analyze image.")}), 500

    # --- Step 6: Save the record to the database ---
    after_photo_url = f"https://your-bucket-url.com/photos/{after_photo.filename}"
    before_photo_url = "http://example.com/before_placeholder.jpg" 

    save_result = storage.save_cleaning_record(
        room_id, cleaner_id, before_photo_url, after_photo_url,
        ai_result["status"], ai_result["remarks"], hospital_id
    )
    return jsonify(save_result), (201 if save_result["success"] else 500)

# --- Dashboard Routes ---
@app.route("/dashboard", methods=["GET"])
def get_dashboard_data():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        user_hospital_id = payload.get('hospital_id')

        if not user_hospital_id:
            return jsonify({"error": "Manager is not associated with a hospital."}), 400

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
        return jsonify({"error": "Invalid or expired token"}), 401
    # --- END NEW LOGIC ---

    # Pass the manager's hospital_id to get the filtered data
    result = index.get_dashboard_data(user_hospital_id)
    return jsonify(result), (200 if result["success"] else 500)

# --- Report Route ---
@app.route("/report/weekly", methods=["GET"])
@app.route("/report/weekly", methods=["GET"])
def generate_report_endpoint():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        user_role = payload.get('role')
        user_hospital_id = payload.get('hospital_id')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return jsonify({"error": "Invalid or expired token"}), 401

    # --- THIS IS THE NEW LOGIC ---
    hospital_to_filter = None
    report_hospital_name = None

    if user_role == 'dean':
        hospital_to_filter = user_hospital_id
        # Fetch the hospital name to display in the PDF title
        report_hospital_name = storage.get_hospital_name_by_id(user_hospital_id)

    # The commissioner's hospital_to_filter remains None to get all records
    
    result = storage.get_weekly_approved_records(hospital_id=hospital_to_filter)
    
    if not result["success"]:
        return jsonify({"error": f"Failed to fetch data: {result['error']}"}), 500

    try:
        # Pass the user's role and hospital name to the PDF generator
        pdf_content = index.generate_pdf_report(
            records_data=result["data"],
            user_role=user_role,
            hospital_name=report_hospital_name
        )
        # --- END OF NEW LOGIC ---

        filename = f"Weekly_Report_{datetime.now().strftime('%Y-%m-%d')}.pdf"
        
        return Response(
            pdf_content,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500
    
@app.route("/approve", methods=["POST", "OPTIONS"])
def approve_task_route():
    # This pre-flight check is needed for browsers
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # Get the manager's hospital_id from their login token
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        user_hospital_id = payload.get('hospital_id')

        if not user_hospital_id:
            return jsonify({"error": "Manager is not associated with a hospital."}), 400

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
        return jsonify({"error": "Invalid or expired token"}), 401

    # Get the data from the frontend
    data = request.get_json()
    if not data or not all(k in data for k in ["record_id", "new_status"]):
        return jsonify({"success": False, "message": "Missing 'record_id' or 'new_status'."}), 400
    
    new_status = data["new_status"]
    if new_status not in ["Approved", "Rework"]:
        return jsonify({"success": False, "message": "Invalid status. Must be 'Approved' or 'Rework'."}), 400

    # Call the approval function, passing the hospital_id for security
    result = index.process_manager_approval(data["record_id"], new_status, user_hospital_id)
    return jsonify(result), (200 if result["success"] else 500)


# --- Run the Single Server ---
if __name__ == "__main__":
    print("Starting single Smart Hospital server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
