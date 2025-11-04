from config import supabase
from datetime import datetime, timedelta, timezone

def get_hospitals():
    """Fetches a list of all hospitals."""
    try:
        response = supabase.table("hospitals").select("id, name").execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- User and Auth Functions ---
# Find the create_user function and add hospital_id
def create_user(email, password_hash, role, full_name, hospital_id=None): # Add hospital_id
    try:
        user_data = {
            "email": email, "password_hash": password_hash,
            "role": role, "full_name": full_name
        }
        if hospital_id: # Add hospital_id if provided
            user_data["hospital_id"] = hospital_id
            
        response = supabase.table("users").insert(user_data).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_by_email(email):
    try:
        response = supabase.table("users").select("*").eq("email", email).limit(1).execute()
        return {"success": True, "data": response.data[0] if response.data else None}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Task Assignment Functions ---
def create_task_assignment(room_id, cleaner_id, assigned_by_id, assignment_date, notes):
    try:
        task_data = {
            "room_id": room_id, "cleaner_id": cleaner_id, "assigned_by_id": assigned_by_id,
            "assignment_date": assignment_date, "notes": notes, "status": "Pending"
        }
        response = supabase.table("task_assignments").insert(task_data).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_tasks_for_cleaner(cleaner_id):
    try:
        response = supabase.table("task_assignments").select("*").eq("cleaner_id", cleaner_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Cleaning Records Functions ---
# Find this function and add hospital_id
def save_cleaning_record(room_id, cleaner_id, before_photo_url, after_photo_url, cleanliness_status, ai_remarks, hospital_id): # Add hospital_id
    try:
        record = {
            "room_id": room_id, "cleaner_id": cleaner_id,
            "before_photo_url": before_photo_url, "after_photo_url": after_photo_url,
            "cleanliness_status": cleanliness_status, "ai_remarks": ai_remarks,
            "manager_approval_status": "Pending",
            "hospital_id": hospital_id # Add hospital_id to the record
        }
        response = supabase.table('cleaning_records').insert(record).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_pending_records(hospital_id):
    """Gets pending records ONLY for a specific hospital."""
    try:
        response = supabase.table('cleaning_records') \
            .select('*') \
            .eq('manager_approval_status', 'Pending') \
            .eq('hospital_id', hospital_id) \
            .execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Replace the entire function in storage.py with this one

def update_record_status(record_id, new_status, hospital_id):
    """
    Securely updates a record's status, ensuring it matches the manager's hospital.
    """
    try:
        # This query will only match if both the record ID and hospital ID are correct.
        response = supabase.table('cleaning_records') \
            .update({'manager_approval_status': new_status}) \
            .eq('id', record_id) \
            .eq('hospital_id', hospital_id) \
            .execute()
            
        # --- THIS IS THE CRITICAL FIX ---
        # If the query updated zero rows (because of a mismatch), response.data will be empty.
        # This check now prevents the code from crashing.
        if not response.data:
             return {"success": False, "message": "Record not found in your hospital, or permission denied."}
        # --- END OF FIX ---
             
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Find this function and modify it to accept an optional hospital_id
def get_weekly_approved_records(hospital_id=None):
    """Fetches weekly records, including the hospital name for each record."""
    try:
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        # The select query now joins the hospitals table to get the name
        query = supabase.table('cleaning_records') \
            .select('*, hospitals(name)') \
            .eq('manager_approval_status', 'Approved') \
            .gte('created_at', seven_days_ago.isoformat())
        
        if hospital_id:
            query = query.eq('hospital_id', hospital_id)
            
        response = query.execute()
        print(f"Successfully fetched {len(response.data)} records for the weekly report.")
        return {"success": True, "data": response.data, "error": None}
    except Exception as e:
        print(f"Database error fetching weekly report data: {e}")
        return {"success": False, "data": [], "error": str(e)}
    
# --- Manager Task Functions ---
def create_manager_task(assigned_by_id, assigned_to_id, description, due_date):
    """Saves a new high-level task for a manager."""
    try:
        task_data = {
            "assigned_by_id": assigned_by_id,
            "assigned_to_id": assigned_to_id,
            "task_description": description,
            "due_date": due_date
        }
        response = supabase.table("manager_tasks").insert(task_data).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_tasks_for_manager(manager_id):
    """Gets all high-level tasks assigned to a specific manager."""
    try:
        # We also want to fetch the full name of the person who assigned the task
        response = supabase.table("manager_tasks").select("*, assigned_by:users!manager_tasks_assigned_by_id_fkey(full_name)").eq("assigned_to_id", manager_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def get_user_by_id(user_id):
    try:
        response = supabase.table("users").select("*").eq("id", user_id).limit(1).execute()
        return {"success": True, "data": response.data[0] if response.data else None}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def get_all_cleaners(hospital_id):
    """Fetches all users with the 'cleaner' role for a specific hospital."""
    try:
        # Add the .eq() filter to only get cleaners from the specified hospital
        response = supabase.table("users") \
            .select("id, full_name") \
            .eq("role", "cleaner") \
            .eq("hospital_id", hospital_id) \
            .execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def get_hospital_name_by_id(hospital_id):
    """Fetches the name of a single hospital by its ID."""
    try:
        response = supabase.table("hospitals").select("name").eq("id", hospital_id).limit(1).execute()
        return response.data[0]['name'] if response.data else None
    except Exception:
        return None