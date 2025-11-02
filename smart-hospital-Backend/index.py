# This file holds all the business logic (the 5 "functions")
import storage
from config import gemini_model, jwt_secret
import io
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from PIL import Image
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# --- Function 1: Photo Verification Logic ---
AI_PROMPT = """
Analyze the attached image of a hospital room and determine its cleanliness level.
Provide a 'status' (Clean, Partially Clean, Not Clean) and a one-sentence 'remark'.
Example Response:
Status: Clean
Remark: The floor is mopped, and all surfaces are clear of debris.
"""

def analyze_room_image(image_bytes: bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        response = gemini_model.generate_content([AI_PROMPT, image])
        
        status = "Needs Manual Review"
        remarks = "Could not parse AI response."
        
        for line in response.text.strip().split('\n'):
            if line.lower().startswith('status:'):
                status = line.split(':', 1)[1].strip()
            elif line.lower().startswith('remark:'):
                remarks = line.split(':', 1)[1].strip()
        
        if status not in ['Clean', 'Partially Clean', 'Not Clean']:
             remarks = response.text.strip()
             status = "Needs Manual Review"
             
        return {"success": True, "status": status, "remarks": remarks}
    except Exception as e:
        # This print statement is for debugging
        print("--- BEGIN GEMINI API ERROR ---")
        print(f"An exception occurred during Gemini API call: {e}")
        print("--- END GEMINI API ERROR ---")
        return {"success": False, "error": "Failed to analyze image."}

# --- Function 2: Dashboard Logic ---
def get_dashboard_data():
    """Gets all cleaning records that are pending approval."""
    return storage.get_pending_records()

def process_manager_approval(record_id, decision):
    """Processes a manager's approval or rework decision."""
    return storage.update_record_status(record_id, decision)

# --- Function 3: Report Generation Logic ---
def generate_pdf_report(records_data: list):
    """Takes a list of records and generates a PDF file in memory."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Weekly Hospital Cleaning Report", styles['h1']), Spacer(1, 12)]
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Report generated on: {date_str}", styles['Normal']))
    story.append(Spacer(1, 24))

    if not records_data:
        story.append(Paragraph("No approved cleaning records found for the past week.", styles['Normal']))
    else:
        table_data = [["Room ID", "Cleaner ID", "Status", "Cleaned On", "AI Remarks"]]
        for record in records_data:
            cleaned_date = datetime.fromisoformat(record['created_at']).strftime('%Y-%m-%d')
            table_data.append([
                record.get('room_id', 'N/A'), str(record.get('cleaner_id', 'N/A'))[:8], # Shorten UUID for display
                record.get('cleanliness_status', 'N/A'), cleaned_date,
                record.get('ai_remarks', 'N/A')
            ])
        
        report_table = Table(table_data)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        report_table.setStyle(style)
        story.append(report_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- Function 4: User Auth Logic ---
def register_new_user(email, password, role, full_name):
    """Hashes a password and creates a new user in the database."""
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    result = storage.create_user(
        email=email,
        password_hash=hashed_password.decode('utf-8'),
        role=role,
        full_name=full_name
    )
    return result

def login_user(email, password):
    """Verifies a user's password and issues a JWT token."""
    print("\n--- NEW LOGIN ATTEMPT ---")
    print(f"Attempting login for email: {email}")

    user_result = storage.get_user_by_email(email)

    # --- THIS IS THE CRITICAL NEW LOGGING ---
    # First, check if the database query itself was successful.
    if not user_result.get("success"):
        print(f"LOGIN FAILED: A database error occurred.")
        print(f"Supabase Error Details: {user_result.get('error')}")
        return {"success": False, "message": "A server error occurred during login."}

    # If the query succeeded, now check if a user was actually found.
    if not user_result.get("data"):
        print("LOGIN FAILED: Email not found in database.")
        return {"success": False, "message": "Invalid email or password."}

    user_data = user_result["data"]
    print(f"SUCCESS: Found user ID: {user_data['id']}")

    # Compare the provided password with the stored hash
    is_valid = bcrypt.checkpw(password.encode('utf-8'), user_data["password_hash"].encode('utf-8'))

    if not is_valid:
        print("LOGIN FAILED: Password check failed.")
        return {"success": False, "message": "Invalid email or password."}

    print("SUCCESS: Password is valid. Generating token.")
    payload = {
        "user_id": user_data["id"],
        "role": user_data["role"],
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    return {"success": True, "token": token}

# --- Function 5: Task Assignment Logic ---
def assign_new_task(room_id, cleaner_id, assigned_by_id, assignment_date, notes):
    """Assigns a new cleaning task to a worker."""
    return storage.create_task_assignment(
        room_id, cleaner_id, assigned_by_id, assignment_date, notes
    )

def get_cleaner_tasks(cleaner_id):
    """Gets all tasks for a specific cleaner."""
    return storage.get_tasks_for_cleaner(cleaner_id)
