from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import mysql.connector
from datetime import datetime, timedelta
import sys

# --- 1. CONFIGURATION ---
# CRITICAL: Replace with your actual MySQL credentials
DB_CONFIG = {
    'host': 'localhost',      
    'user': 'root',           
    'password': 'Riyu22@@', 
    'database': 'blood_bank_db'
}

app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication (necessary when running HTML locally)

# --- 2. DB CONNECTION AND UTILITIES ---

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"[DB ERROR] Failed to connect: {err}")
        return None

def get_default_phlebotomist_id():
    """Retrieves the default PHL001 staff_id for FKs."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT staff_id FROM staff WHERE employee_number = 'PHL001'")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception:
        if conn and conn.is_connected(): conn.close()
        return None

def db_execute_transaction(sql_commands):
    """Executes a list of SQL commands in a single transaction."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    
    cursor = conn.cursor()
    try:
        for sql, values in sql_commands:
            cursor.execute(sql, values)
        conn.commit()
        return True, "Transaction completed."
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"[DB TRANSACTION ERROR] {err}")
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def db_search_donor_by_last_name(last_name):
    """Searches for donors by last name."""
    conn = get_db_connection()
    if not conn: return []
    sql = "SELECT donor_id, first_name, last_name, blood_group FROM donor WHERE last_name = %s"
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (last_name,))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception:
        if conn and conn.is_connected(): conn.close()
        return []

def db_search_screening_by_donor_id(donor_id):
    """Searches for the latest ELIGIBLE screening record."""
    conn = get_db_connection()
    if not conn: return None
    sql = """
    SELECT screening_id, eligible, screening_datetime
    FROM donor_screening 
    WHERE donor_id = %s AND eligible = 'Eligible'
    ORDER BY screening_datetime DESC LIMIT 1
    """
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (donor_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception:
        if conn and conn.is_connected(): conn.close()
        return None

# --- 3. API ENDPOINTS ---

@app.route('/api/donor/register', methods=['POST'])
def api_register_donor():
    data = request.get_json()
    donor_id = str(uuid.uuid4())
    
    sql = """
    INSERT INTO donor (donor_id, first_name, last_name, date_of_birth, gender, blood_group) 
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (donor_id, data['firstName'], data['lastName'], data['dob'], data['gender'], data['bloodGroup'])
    
    success, message = db_execute_transaction([(sql, values)])
    
    if success:
        return jsonify({"status": "success", "message": f"Donor registered. ID: {donor_id[:8]}..."}), 201
    else:
        return jsonify({"status": "error", "message": f"Registration failed: {message}"}), 500

@app.route('/api/donor/search', methods=['POST'])
def api_search_donor():
    data = request.get_json()
    last_name = data.get('lastName', '')
    
    if not last_name:
        return jsonify({"status": "error", "message": "Last name is required."}), 400
        
    results = db_search_donor_by_last_name(last_name)
    
    if not results:
        return jsonify({"status": "not_found", "message": f"No donors found for '{last_name}'."}), 404
    
    # Format the results for easy JavaScript consumption
    formatted_results = [{
        "donorId": r['donor_id'],
        "name": f"{r['first_name']} {r['last_name']}",
        "bloodGroup": r['blood_group']
    } for r in results]
    
    return jsonify({"status": "success", "donors": formatted_results}), 200

@app.route('/api/screening/save', methods=['POST'])
def api_save_screening():
    data = request.get_json()
    donor_id = data.get('donorId')
    
    phlebotomist_id = get_default_phlebotomist_id()
    if not phlebotomist_id:
        return jsonify({"status": "error", "message": "Staff ID (PHL001) not found."}), 500

    screening_id = str(uuid.uuid4())
    screening_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sql = """
    INSERT INTO donor_screening (screening_id, donor_id, screening_datetime, hemoglobin_g_dl, bp_systolic, bp_diastolic, eligible, notes, staff_id) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (screening_id, donor_id, screening_datetime, data['hgb'], 
              data['bpSystolic'], data['bpDiastolic'], data['eligible'], data['notes'], phlebotomist_id)
    
    success, message = db_execute_transaction([(sql, values)])
    
    if success:
        return jsonify({"status": "success", "message": "Screening record saved.", "screeningId": screening_id}), 201
    else:
        return jsonify({"status": "error", "message": f"Screening failed: {message}"}), 500

@app.route('/api/collection/finalize', methods=['POST'])
def api_finalize_collection():
    data = request.get_json()
    donor_id = data.get('donorId')
    blood_group = data.get('bloodGroup')
    
    # 1. Check eligibility screening exists
    screening_result = db_search_screening_by_donor_id(donor_id)
    if not screening_result:
        return jsonify({"status": "error", "message": "Donor not eligible or no recent screening record found."}), 403
    
    screening_id = screening_result['screening_id']
    phlebotomist_id = get_default_phlebotomist_id()
    if not phlebotomist_id:
        return jsonify({"status": "error", "message": "Staff ID (PHL001) not found."}), 500
    
    # --- Transaction Commands ---
    commands = []
    
    # 1. Create Donation Record
    donation_id = str(uuid.uuid4())
    collection_date = datetime.now().strftime("%Y-%m-%d")
    sql_rec = """
    INSERT INTO donation_record (donation_id, donor_id, screening_id, collection_datetime, phlebotomist_id, status)
    VALUES (%s, %s, %s, %s, %s, 'Collected')
    """
    commands.append((sql_rec, (donation_id, donor_id, screening_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), phlebotomist_id)))
    
    # 2. Create Blood Unit
    unit_id = str(uuid.uuid4())
    expiry_date = (datetime.now() + timedelta(days=42)).strftime("%Y-%m-%d")
    sql_unit = """
    INSERT INTO blood_unit (unit_id, donation_id, collection_date, expiry_date, blood_group, status) 
    VALUES (%s, %s, %s, %s, %s, 'Available')
    """
    commands.append((sql_unit, (unit_id, donation_id, collection_date, expiry_date, blood_group)))
    
    # Execute the two-part transaction
    success, message = db_execute_transaction(commands)
    
    if success:
        return jsonify({
            "status": "success", 
            "message": "Collection and Unit created successfully.", 
            "unitId": unit_id[:8], 
            "donationId": donation_id[:8]
        }), 201
    else:
        return jsonify({"status": "error", "message": f"Transaction failed: {message}"}), 500

# --- 4. SERVER STARTUP ---

if __name__ == '__main__':
    # Running in debug mode, accessible from any device on the network (host='0.0.0.0')
    app.run(debug=True, host='127.0.0.1', port=5000)
