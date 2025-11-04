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
def get_dashboard_data(hospital_id):
    """Gets all cleaning records pending approval for a specific hospital."""
    return storage.get_pending_records(hospital_id)

def process_manager_approval(record_id, decision, hospital_id):
    """Processes a manager's approval or rework decision for their hospital."""
    # Now it correctly passes all three arguments to the next function
    return storage.update_record_status(record_id, decision, hospital_id)

# --- Function 3: Report Generation Logic ---
# Replace the entire function in index.py with this one

def generate_pdf_report(records_data: list, user_role: str, hospital_name: str = None):
    """Takes a list of records and generates a role-specific PDF file with text wrapping."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Weekly Hospital Cleaning Report", styles['h1']), Spacer(1, 12)]

    if user_role == 'dean' and hospital_name:
        story.append(Paragraph(f"For: {hospital_name}", styles['h2']))
        story.append(Spacer(1, 12))
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Report generated on: {date_str}", styles['Normal']))
    story.append(Spacer(1, 24))

    if not records_data:
        story.append(Paragraph("No approved cleaning records found for the past week.", styles['Normal']))
    else:
        if user_role == 'bmc_commissioner':
            table_data = [["Hospital", "Room ID", "Cleaner ID", "Status", "Cleaned On", "AI Remarks"]]
            for record in records_data:
                cleaned_date = datetime.fromisoformat(record['created_at']).strftime('%Y-%m-%d')
                hosp_name = record.get('hospitals', {}).get('name', 'N/A') if record.get('hospitals') else 'N/A'
                
                # --- THIS IS THE FIX ---
                # Wrap the long text in a Paragraph object to enable text wrapping.
                ai_remarks_paragraph = Paragraph(record.get('ai_remarks', 'N/A'), styles['Normal'])
                
                table_data.append([
                    hosp_name,
                    record.get('room_id', 'N/A'),
                    str(record.get('cleaner_id', 'N/A'))[:8],
                    record.get('cleanliness_status', 'N/A'),
                    cleaned_date,
                    ai_remarks_paragraph # Use the paragraph object here
                ])
        else:
            table_data = [["Room ID", "Cleaner ID", "Status", "Cleaned On", "AI Remarks"]]
            for record in records_data:
                cleaned_date = datetime.fromisoformat(record['created_at']).strftime('%Y-%m-%d')

                # --- THIS IS THE SAME FIX, APPLIED FOR THE DEAN'S REPORT ---
                ai_remarks_paragraph = Paragraph(record.get('ai_remarks', 'N/A'), styles['Normal'])
                
                table_data.append([
                    record.get('room_id', 'N/A'),
                    str(record.get('cleaner_id', 'N/A'))[:8],
                    record.get('cleanliness_status', 'N/A'),
                    cleaned_date,
                    ai_remarks_paragraph # Use the paragraph object here
                ])
        
        report_table = Table(table_data)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), # Good for vertical alignment
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        report_table.setStyle(style)
        story.append(report_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- Function 4: User Auth Logic ---
# Add hospital_id to the function signature
def register_new_user(email, password, role, full_name, hospital_id=None):
    """Hashes a password and creates a new user in the database."""
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    result = storage.create_user(
        email=email,
        password_hash=hashed_password.decode('utf-8'),
        role=role,
        full_name=full_name,
        hospital_id=hospital_id # Pass it to the storage function
    )
    return result

def login_user(email, password):
    """Verifies a user's password and issues a JWT token."""
    user_result = storage.get_user_by_email(email)
    
    if not user_result.get("data"):
        return {"success": False, "message": "Invalid email or password."}
    
    user_data = user_result["data"]
    is_valid = bcrypt.checkpw(password.encode('utf-8'), user_data["password_hash"].encode('utf-8'))

    if not is_valid:
        return {"success": False, "message": "Invalid email or password."}

    payload = {
        "user_id": user_data["id"],
        "role": user_data["role"],
        "hospital_id": user_data.get("hospital_id"), # <-- ADD THIS LINE
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

# --- Function 6: Manager Task Logic ---
def assign_manager_task(assigned_by_id, assigned_to_id, description, due_date):
    """Assigns a new high-level task to a manager."""
    return storage.create_manager_task(
        assigned_by_id, assigned_to_id, description, due_date
    )

def get_manager_tasks(manager_id):
    """Gets all high-level tasks for a specific manager."""
    return storage.get_tasks_for_manager(manager_id)

def get_cleaner_list(hospital_id):
    """Gets a list of all cleaners for a specific hospital."""
    return storage.get_all_cleaners(hospital_id)
