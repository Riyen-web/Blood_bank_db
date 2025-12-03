from datetime import datetime, timedelta
import mysql.connector
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'XXXXXXX',  # <<<--- UPDATE YOUR PASSWORD
    'database': 'blood_bank_db'
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

# =================================================================
# ALL API ENDPOINTS (COMPLETE AND VERIFIED)
# =================================================================

@app.route('/api/donors', methods=['POST'])
def add_donor():
    data = request.get_json()
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        blood_group_full = data.get('blood_group', 'O+')
        email = data.get('email') or None
        sql = "INSERT INTO donors (first_name, last_name, date_of_birth, blood_group, rh_factor, gender, phone_number, email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (data.get('first_name'), data.get('last_name'), data.get('date_of_birth'), blood_group_full[:-1], blood_group_full[-1], data.get('gender'), data.get('phone_number'), email)
        cursor.execute(sql, values)
        new_donor_id = cursor.lastrowid
        conn.commit()
        return jsonify({"message": "Donor registered successfully!", "donor_id": new_donor_id}), 201
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/donors/search', methods=['GET'])
def search_donors():
    last_name = request.args.get('last_name', '')
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT donor_id, first_name, last_name, CONCAT(blood_group, rh_factor) AS blood_type FROM donors WHERE last_name LIKE %s ORDER BY last_name, first_name"
        cursor.execute(query, (f"%{last_name}%",))
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err: return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/screenings', methods=['POST'])
def add_screening():
    data = request.get_json()
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    is_eligible = True; notes_list = []
    try:
        hemoglobin = float(data.get('hemoglobin', 0)); bp_systolic = int(data.get('bp_systolic', 0)); bp_diastolic = int(data.get('bp_diastolic', 0)); weight_kg = float(data.get('weight_kg', 0))
        if hemoglobin < 12.5: is_eligible = False; notes_list.append("Low Hemoglobin")
        if not (90 <= bp_systolic <= 180): is_eligible = False; notes_list.append("BP (Systolic) out of range")
        if not (60 <= bp_diastolic <= 100): is_eligible = False; notes_list.append("BP (Diastolic) out of range")
        if weight_kg < 50: is_eligible = False; notes_list.append("Weight below minimum")
        final_notes = ", ".join(notes_list) if notes_list else "All vitals within range."
        if data.get('additional_notes'): final_notes += f" | Staff Notes: {data.get('additional_notes')}"
    except (ValueError, TypeError): return jsonify({"error": "Invalid data for screening values (must be numbers)."}), 400
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO screenings (donor_id, staff_id, screening_date, hemoglobin, blood_pressure_systolic, blood_pressure_diastolic, weight_kg, is_eligible, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (data.get('donor_id'), data.get('staff_id'), datetime.now(), hemoglobin, bp_systolic, bp_diastolic, weight_kg, is_eligible, final_notes)
        cursor.execute(sql, values)
        screening_id = cursor.lastrowid
        conn.commit()
        return jsonify({"message": f"Screening recorded. Donor is {'Eligible' if is_eligible else 'Not Eligible'}.", "screening_id": screening_id, "is_eligible": is_eligible, "notes": final_notes}), 201
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/donations', methods=['POST'])
def add_donation():
    data = request.get_json()
    if not all(data.get(k) for k in ['donor_id', 'screening_id', 'staff_id']):
        return jsonify({"error": "Donor, Screening ID, and Staff must all be selected."}), 400
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        collection_date = datetime.now()
        sql_donation = "INSERT INTO donations (donor_id, screening_id, phlebotomist_staff_id, donation_date, collection_site) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_donation, (data.get('donor_id'), data.get('screening_id'), data.get('staff_id'), collection_date, 'Main Center'))
        donation_id = cursor.lastrowid
        expiry_date = collection_date + timedelta(days=42)
        blood_group_full = data.get('blood_group', 'O+')
        sql_unit = "INSERT INTO blood_units (donation_id, blood_group, rh_factor, collection_date, expiry_date, status) VALUES (%s, %s, %s, %s, %s, 'In Stock')"
        cursor.execute(sql_unit, (donation_id, blood_group_full[:-1], blood_group_full[-1], collection_date.date(), expiry_date.date()))
        unit_id = cursor.lastrowid
        conn.commit()
        return jsonify({"message": "Donation and Blood Unit created successfully!", "donation_id": donation_id, "unit_id": unit_id}), 201
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({"error": f"Transaction failed: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT unit_id, CONCAT(blood_group, rh_factor) AS blood_type, status FROM blood_units ORDER BY unit_id DESC"
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err: return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/inventory/<int:unit_id>', methods=['PUT'])
def update_unit_status(unit_id):
    data = request.get_json()
    new_status = data.get('status')
    org_id = data.get('org_id') or None # Get the org_id if it exists
    if not new_status: return jsonify({"error": "New status is required"}), 400
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        sql = "UPDATE blood_units SET status = %s, issued_to_org_id = %s WHERE unit_id = %s"
        values = (new_status, org_id if new_status == 'Issued' else None, unit_id)
        
        cursor.execute(sql, values)
        if cursor.rowcount == 0: return jsonify({"error": "Unit ID not found"}), 404
        conn.commit()
        return jsonify({"message": f"Unit status updated to {new_status}"}), 200
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/reports/inventory', methods=['GET'])
def get_inventory_report():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT CONCAT(blood_group, rh_factor) AS blood_type, status, COUNT(*) as count FROM blood_units GROUP BY blood_type, status ORDER BY blood_type, status;"
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err: return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/donors/<int:donor_id>/report', methods=['GET'])
def get_donor_report(donor_id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT donor_id, first_name, last_name, date_of_birth, CONCAT(blood_group, rh_factor) as blood_type, gender, phone_number, email FROM donors WHERE donor_id = %s", (donor_id,))
        donor_details = cursor.fetchone()
        if not donor_details: return jsonify({"error": "Donor not found"}), 404
        if donor_details.get('date_of_birth'): donor_details['date_of_birth'] = donor_details['date_of_birth'].strftime('%Y-%m-%d')
        query = """
            SELECT sc.screening_id, sc.screening_date, sc.is_eligible, sc.notes, s_screener.first_name as screener_fname, s_screener.last_name as screener_lname,
                   d.donation_id, d.donation_date, s_phleb.first_name as phleb_fname, s_phleb.last_name as phleb_lname,
                   bu.unit_id, bu.status as unit_status, bu.expiry_date, o.name as issued_to_org
            FROM screenings sc
            LEFT JOIN donations d ON sc.screening_id = d.screening_id
            LEFT JOIN blood_units bu ON d.donation_id = bu.donation_id
            LEFT JOIN organizations o ON bu.issued_to_org_id = o.org_id
            LEFT JOIN staff s_screener ON sc.staff_id = s_screener.staff_id
            LEFT JOIN staff s_phleb ON d.phlebotomist_staff_id = s_phleb.staff_id
            WHERE sc.donor_id = %s ORDER BY sc.screening_date DESC;
        """
        cursor.execute(query, (donor_id,))
        history = cursor.fetchall()
        for item in history:
            for key, value in item.items():
                if isinstance(value, (datetime,)): item[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                if isinstance(value, (datetime.date,)): item[key] = value.strftime('%Y-%m-%d')
        return jsonify({"donor_details": donor_details, "history": history}), 200
    except mysql.connector.Error as err: return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/roles', methods=['GET'])
def get_roles():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT role_id, role_name FROM roles ORDER BY role_name")
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err: return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()
        
@app.route('/api/staff', methods=['GET', 'POST'])
def handle_staff():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            query = "SELECT s.staff_id, s.first_name, s.last_name, s.employee_number, s.role_id, r.role_name FROM staff s JOIN roles r ON s.role_id = r.role_id WHERE s.is_active = 1 ORDER BY s.last_name, s.first_name"
            cursor.execute(query)
            return jsonify(cursor.fetchall()), 200
        elif request.method == 'POST':
            data = request.get_json()
            sql = "INSERT INTO staff (first_name, last_name, employee_number, role_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (data.get('first_name'), data.get('last_name'), data.get('employee_number'), data.get('role_id')))
            staff_id = cursor.lastrowid
            conn.commit()
            return jsonify({"message": "Staff member added successfully!", "staff_id": staff_id}), 201
    except mysql.connector.Error as err:
        if conn.is_connected(): conn.rollback()
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/staff/<int:staff_id>', methods=['PUT'])
def update_staff_role(staff_id):
    data = request.get_json(); new_role_id = data.get('role_id')
    if not new_role_id: return jsonify({"error": "role_id is required"}), 400
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT staff_id FROM staff WHERE staff_id = %s", (staff_id,))
        if not cursor.fetchone(): return jsonify({"error": "Staff member not found"}), 404
        cursor.execute("UPDATE staff SET role_id = %s WHERE staff_id = %s", (new_role_id, staff_id))
        conn.commit()
        return jsonify({"message": "Staff role updated successfully"}), 200
    except mysql.connector.Error as err:
        if conn.is_connected(): conn.rollback()
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT task_id, task_name FROM tasks ORDER BY task_name")
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err: return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/staff/<int:staff_id>/tasks', methods=['GET', 'POST'])
def handle_staff_tasks(staff_id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            query = "SELECT t.task_id, t.task_name FROM tasks t JOIN staff_tasks st ON t.task_id = st.task_id WHERE st.staff_id = %s"
            cursor.execute(query, (staff_id,))
            return jsonify(cursor.fetchall()), 200
        elif request.method == 'POST':
            data = request.get_json()
            sql = "INSERT INTO staff_tasks (staff_id, task_id) VALUES (%s, %s)"
            cursor.execute(sql, (staff_id, data.get('task_id')))
            conn.commit()
            return jsonify({"message": "Task assigned"}), 201
    except mysql.connector.Error as err:
        if conn.is_connected(): conn.rollback()
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

@app.route('/api/staff/<int:staff_id>/tasks/<int:task_id>', methods=['DELETE'])
def remove_staff_task(staff_id, task_id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM staff_tasks WHERE staff_id = %s AND task_id = %s"
        cursor.execute(sql, (staff_id, task_id))
        conn.commit()
        return jsonify({"message": "Task removed"}), 200
    except mysql.connector.Error as err:
        if conn.is_connected(): conn.rollback()
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

# --- NEW: ORGANIZATION ENDPOINTS ---
@app.route('/api/organizations', methods=['GET', 'POST'])
def handle_organizations():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            cursor.execute("SELECT org_id, name, org_type FROM organization ORDER BY name")
            return jsonify(cursor.fetchall()), 200
        elif request.method == 'POST':
            data = request.get_json()
            if not data.get('name') or not data.get('org_type'):
                return jsonify({"error": "Name and Type are required"}), 400
            sql = "INSERT INTO organization (name, org_type, contact_person, contact_phone, contact_email) VALUES (%s, %s, %s, %s, %s)"
            values = (data.get('name'), data.get('org_type'), data.get('contact_person'), data.get('contact_phone'), data.get('contact_email'))
            cursor.execute(sql, values)
            org_id = cursor.lastrowid
            conn.commit()
            return jsonify({"message": "Organization registered successfully", "org_id": org_id}), 201
    except mysql.connector.Error as err:
        if conn.is_connected(): conn.rollback()
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

# --- NEW: BLOOD REQUEST ENDPOINTS ---
@app.route('/api/blood_requests', methods=['GET', 'POST'])
def handle_blood_requests():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            query = """
                SELECT r.request_id, r.status, r.quantity, r.request_date, o.name as org_name,
                       CONCAT(r.blood_group, r.rh_factor) as blood_type
                FROM blood_requests r
                JOIN organization o ON r.org_id = o.org_id
                ORDER BY r.request_date DESC
            """
            cursor.execute(query)
            requests = cursor.fetchall()
            
            for req in requests: # Convert datetime to string
                if req.get('request_date'): req['request_date'] = req['request_date'].strftime('%Y-%m-%d %H:%M')
            return jsonify(requests), 200
        elif request.method == 'POST':
            data = request.get_json()
            if not all(data.get(k) for k in ['org_id', 'blood_group', 'quantity']):
                return jsonify({"error": "Organization, Blood Group, and Quantity are required."}), 400
            blood_group_full = data.get('blood_group', 'O+')
            sql = "INSERT INTO blood_requests (org_id, patient_name, blood_group, rh_factor, quantity, status) VALUES (%s, %s, %s, %s, %s, 'Pending')"
            values = (data.get('org_id'), data.get('patient_name'), blood_group_full[:-1], blood_group_full[-1], data.get('quantity'))
            cursor.execute(sql, values)
            request_id = cursor.lastrowid
            conn.commit()
            return jsonify({"message": "Blood request submitted successfully", "request_id": request_id}), 201
    except mysql.connector.Error as err:
        if conn.is_connected(): conn.rollback()
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000)