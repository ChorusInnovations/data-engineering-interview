import psycopg2
from prettytable import PrettyTable

# --- Database Configuration ---
DB_CONFIG = {
    "dbname": "postgres",
    "user": "user",            
    "password": "password",    
    "host": "localhost",
    "port": "5432"
}

# --- SQL Queries ---
QUERIES = {
    "active_patients": """
        SELECT * FROM "Patient" WHERE active = true LIMIT 10;
    """,
    "encounters_by_patient": """
        SELECT 
            e.id, 
            e.status, 
            e.reason,
            pr.name AS practitioner,
            p.name AS patient
        FROM "Encounter" e
        JOIN "Patient" p ON e.patient_id = p.id
        JOIN "Practitioner" pr ON e.practitioner_id = pr.id
        WHERE p.id = '9d18a0c6-8682-43fe-b465-938ce66133d1'
        ORDER BY e.encounter_date DESC;
    """,
    "observations_by_patient": """
        SELECT 
            o.id, 
            o.patient_id, 
            o.encounter_id,
            o.type, 
            o.value, 
            o.unit, 
            o.recorded_at,
            p.name AS patient
        FROM "Observation" o
        JOIN "Patient" p ON o.patient_id = p.id
        WHERE p.id = '3ed52e91-9a01-4a38-b8b6-55f0fe3662e6'
        ORDER BY o.recorded_at DESC;
    """,
    "last_encounter_per_patient": """
        SELECT DISTINCT ON (e.patient_id)
            e.encounter_date, 
            e.status, 
            p.name 
        FROM "Encounter" e 
        JOIN "Patient" p ON e.patient_id = p.id 
        ORDER BY e.patient_id, e.encounter_date DESC;
    """,
    "multi_practitioner_patients": """
        WITH multi_practitioner_patients AS (
            SELECT patient_id
            FROM "Encounter"
            GROUP BY patient_id
            HAVING COUNT(DISTINCT practitioner_id) > 1
        )
        SELECT 
            p.id AS patient_id,
            p.name AS patient_name,
            STRING_AGG(DISTINCT pr.name, ', ') AS practitioner_names
        FROM "Patient" p
        JOIN "Encounter" e ON p.id = e.patient_id
        JOIN "Practitioner" pr ON e.practitioner_id = pr.id
        WHERE p.id IN (SELECT patient_id FROM multi_practitioner_patients)
        GROUP BY p.id, p.name;
    """,
    "top_medications": """
        SELECT 
            id, medication_name, COUNT(*) AS prescription_count
        FROM "MedicationRequest"
        GROUP BY id, medication_name
        ORDER BY prescription_count DESC
        LIMIT 3;
    """,
    "inactive_prescribers": """
        SELECT 
            p.*
        FROM "Practitioner" p
        LEFT JOIN "MedicationRequest" mr ON p.id = mr.practitioner_id
        WHERE mr.practitioner_id IS NULL;
    """,
    "average_encounters": """
        SELECT ROUND(AVG(encounter_count), 2) AS avg_encounters_per_patient
        FROM (
            SELECT patient_id, COUNT(*) AS encounter_count
            FROM "Encounter"
            GROUP BY patient_id
        ) AS patient_encounters;
    """,
    "patients_with_meds_no_encounter": """
        SELECT DISTINCT
            p.*
        FROM "Patient" p
        JOIN "MedicationRequest" mr ON p.id = mr.patient_id
        LEFT JOIN "Encounter" e ON p.id = e.patient_id
        WHERE e.patient_id IS NULL;
    """,
    "retention_by_cohort": """
        WITH first_encounters AS (
            SELECT patient_id, DATE_TRUNC('month', MIN(encounter_date)) AS first_encounter_month
            FROM "Encounter"
            GROUP BY patient_id
        ),
        follow_up_encounters AS (
            SELECT fe.patient_id, fe.first_encounter_month,
                   MAX(CASE WHEN e.encounter_date BETWEEN fe.first_encounter_month AND 
                            (fe.first_encounter_month + INTERVAL '6 months') THEN 1 ELSE 0 END) AS retained
            FROM first_encounters fe
            JOIN "Encounter" e ON fe.patient_id = e.patient_id
            GROUP BY fe.patient_id, fe.first_encounter_month
        )
        SELECT 
            TO_CHAR(first_encounter_month, 'YYYY-MM') AS cohort_month,
            COUNT(*) AS total_patients,
            SUM(retained) AS retained_patients,
            ROUND(100.0 * SUM(retained) / COUNT(*), 2) AS retention_rate
        FROM follow_up_encounters
        GROUP BY first_encounter_month
        ORDER BY first_encounter_month;
    """
}

# --- Utility Function ---
def run_query(cursor, query: str, title: str):
    print(f"\n{'-' * 20} {title} {'-' * 20}")
    cursor.execute(query)
    rows = cursor.fetchall()
    table = PrettyTable()
    table.field_names = [desc[0] for desc in cursor.description]
    for row in rows:
        table.add_row(row)
    print(table)

# --- Main Execution ---
def main():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                run_query(cursor, QUERIES["active_patients"], "List of Active Patients")
                run_query(cursor, QUERIES["encounters_by_patient"], "Encounters for a Specific Patient")
                run_query(cursor, QUERIES["observations_by_patient"], "Observations for a Specific Patient")
                run_query(cursor, QUERIES["last_encounter_per_patient"], "Last Encounter per Patient")
                run_query(cursor, QUERIES["multi_practitioner_patients"], "Patients Seen by Multiple Practitioners")
                run_query(cursor, QUERIES["top_medications"], "Top 3 Prescribed Medications")
                run_query(cursor, QUERIES["inactive_prescribers"], "Practitioners Who Never Prescribed")
                run_query(cursor, QUERIES["average_encounters"], "Average Encounter per Patient")
                run_query(cursor, QUERIES["patients_with_meds_no_encounter"], "Patients with Medications but No Encounter")
                run_query(cursor, QUERIES["retention_by_cohort"], "Patient Retention by Cohort")

    except psycopg2.Error as e:
        print(f"Database error: {e}")

# --- Entry Point ---
if __name__ == "__main__":
    main()
