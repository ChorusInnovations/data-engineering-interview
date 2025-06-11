import psycopg2
from prettytable import PrettyTable
from queriesDef import QUERIES

# --- Database Configuration ---
DB_CONFIG = {
    "dbname": "postgres",
    "user": "user",            
    "password": "password",    
    "host": "localhost",
    "port": "5432"
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
