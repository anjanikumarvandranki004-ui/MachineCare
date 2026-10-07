import os
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "localhost"),
    "port": int(os.getenv("MYSQLPORT", "3306")),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", "YOUR_MYSQL_PASSWORD"),
    "database": os.getenv("MYSQLDATABASE", "machine_health_db")
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def seed_demo_data():
    """Add five realistic demo machines and sensor/prediction data once.
    Existing records are preserved, so refreshing the site does not duplicate data.
    """
    db = get_db()
    cur = db.cursor()

    # Ensure the departments and machine types needed by the demo data exist.
    departments = ["Production", "Machining", "Maintenance"]
    for name in departments:
        cur.execute("SELECT department_id FROM department WHERE department_name=%s LIMIT 1", (name,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO department (department_name) VALUES (%s)", (name,))

    types = ["CNC", "Lathe", "Milling", "Drilling", "Grinding"]
    for name in types:
        cur.execute("SELECT type_id FROM machine_type WHERE type_name=%s LIMIT 1", (name,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO machine_type (type_name) VALUES (%s)", (name,))

    cur.execute("SELECT department_id, department_name FROM department")
    dept = {row[1]: row[0] for row in cur.fetchall()}
    cur.execute("SELECT type_id, type_name FROM machine_type")
    mtype = {row[1]: row[0] for row in cur.fetchall()}

    demo = [
        ("CNC Machine 01", "CNC", "Production", "2022-05-10", 8500, 72, 2.1, 5.2, "Healthy", 8.00, "Continue operation; routine monitoring"),
        ("Lathe Machine 01", "Lathe", "Machining", "2021-08-15", 10200, 91, 6.8, 5.5, "Warning", 35.00, "Schedule inspection and lubrication"),
        ("Milling Machine 01", "Milling", "Production", "2020-03-22", 12400, 110, 9.2, 6.1, "Critical", 78.00, "Immediate inspection and maintenance"),
        ("Drilling Machine 01", "Drilling", "Production", "2023-01-18", 5200, 68, 2.5, 4.9, "Healthy", 6.00, "Continue operation; routine monitoring"),
        ("Grinding Machine 01", "Grinding", "Maintenance", "2021-11-05", 9100, 85, 5.1, 5.7, "Warning", 42.00, "Schedule inspection and check bearings"),
    ]

    for item in demo:
        name, type_name, dept_name, install_date, hours, temp, vibration, pressure, status, risk, action = item

        cur.execute("SELECT machine_id FROM machine WHERE machine_name=%s LIMIT 1", (name,))
        row = cur.fetchone()
        if row is None:
            cur.execute("""
                INSERT INTO machine
                (machine_name, type_id, department_id, installation_date, operating_hours)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, mtype[type_name], dept[dept_name], install_date, hours))
            machine_id = cur.lastrowid
        else:
            machine_id = row[0]

        # One sensor per machine for the dashboard demo.
        cur.execute("""
            SELECT sensor_id FROM sensor
            WHERE machine_id=%s AND sensor_type='Condition Sensor'
            LIMIT 1
        """, (machine_id,))
        sensor_row = cur.fetchone()
        if sensor_row is None:
            cur.execute("""
                INSERT INTO sensor (machine_id, sensor_type)
                VALUES (%s, 'Condition Sensor')
            """, (machine_id,))
            sensor_id = cur.lastrowid
        else:
            sensor_id = sensor_row[0]

        # Add a reading only if this sensor has no reading yet.
        cur.execute("SELECT reading_id FROM sensor_reading WHERE sensor_id=%s LIMIT 1", (sensor_id,))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO sensor_reading
                (sensor_id, temperature, vibration, pressure)
                VALUES (%s, %s, %s, %s)
            """, (sensor_id, temp, vibration, pressure))

        # Add one prediction if the machine has none.
        cur.execute("SELECT prediction_id FROM prediction WHERE machine_id=%s LIMIT 1", (machine_id,))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO prediction
                (machine_id, health_status, failure_probability, predicted_action)
                VALUES (%s, %s, %s, %s)
            """, (machine_id, status, risk, action))

    db.commit()
    cur.close()
    db.close()


@app.route("/")
def dashboard():
    # Populate the demo records automatically the first time the dashboard is opened.
    seed_demo_data()

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total FROM machine")
    total = cur.fetchone()["total"]

    cur.execute("""
        SELECT health_status, COUNT(*) AS count
        FROM prediction
        GROUP BY health_status
    """)
    health_rows = cur.fetchall()
    health = {r["health_status"]: r["count"] for r in health_rows}

    cur.execute("""
        SELECT m.machine_name, mt.type_name, d.department_name,
               m.operating_hours,
               COALESCE(p.health_status, 'Not Analysed') AS health_status,
               COALESCE(p.failure_probability, 0) AS failure_probability
        FROM machine m
        LEFT JOIN machine_type mt ON m.type_id = mt.type_id
        LEFT JOIN department d ON m.department_id = d.department_id
        LEFT JOIN prediction p ON p.prediction_id = (
            SELECT MAX(p2.prediction_id)
            FROM prediction p2
            WHERE p2.machine_id = m.machine_id
        )
        ORDER BY m.machine_id
        LIMIT 8
    """)
    machines = cur.fetchall()

    cur.execute("""
        SELECT m.machine_name, sr.temperature, sr.vibration, sr.pressure,
               sr.reading_time,
               COALESCE(p.health_status, 'Not Analysed') AS health_status
        FROM sensor_reading sr
        JOIN sensor s ON sr.sensor_id = s.sensor_id
        JOIN machine m ON s.machine_id = m.machine_id
        LEFT JOIN prediction p ON p.prediction_id = (
            SELECT MAX(p2.prediction_id)
            FROM prediction p2
            WHERE p2.machine_id = m.machine_id
        )
        ORDER BY sr.reading_time DESC
        LIMIT 5
    """)
    readings = cur.fetchall()

    cur.close()
    db.close()

    return render_template(
        "index.html",
        total=total,
        healthy=health.get("Healthy", 0),
        warning=health.get("Warning", 0),
        critical=health.get("Critical", 0),
        machines=machines,
        readings=readings
    )


@app.route("/machines")
def machines_page():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT m.*, mt.type_name, d.department_name
        FROM machine m
        LEFT JOIN machine_type mt ON m.type_id = mt.type_id
        LEFT JOIN department d ON m.department_id = d.department_id
        ORDER BY m.machine_id DESC
    """)
    machines = cur.fetchall()
    cur.execute("SELECT * FROM machine_type ORDER BY type_name")
    types = cur.fetchall()
    cur.execute("SELECT * FROM department ORDER BY department_name")
    departments = cur.fetchall()
    cur.close()
    db.close()
    return render_template("machines.html", machines=machines, types=types, departments=departments)


@app.route("/machines/add", methods=["POST"])
def add_machine():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO machine
        (machine_name, type_id, department_id, installation_date, operating_hours)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        request.form["machine_name"], request.form["type_id"],
        request.form["department_id"], request.form["installation_date"],
        request.form["operating_hours"]
    ))
    db.commit()
    cur.close()
    db.close()
    return redirect(url_for("machines_page"))


@app.route("/sensors")
def sensors_page():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT sr.reading_id, m.machine_name, s.sensor_type,
               sr.temperature, sr.vibration, sr.pressure, sr.reading_time
        FROM sensor_reading sr
        JOIN sensor s ON sr.sensor_id = s.sensor_id
        JOIN machine m ON s.machine_id = m.machine_id
        ORDER BY sr.reading_time DESC
        LIMIT 50
    """)
    readings = cur.fetchall()
    cur.close()
    db.close()
    return render_template("sensors.html", readings=readings)


@app.route("/maintenance")
def maintenance_page():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT ma.*, m.machine_name, t.technician_name
        FROM maintenance ma
        JOIN machine m ON ma.machine_id = m.machine_id
        LEFT JOIN technician t ON ma.technician_id = t.technician_id
        ORDER BY ma.maintenance_date DESC
    """)
    records = cur.fetchall()
    cur.close()
    db.close()
    return render_template("maintenance.html", records=records)


@app.route("/predictions")
def predictions_page():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, m.machine_name
        FROM prediction p
        JOIN machine m ON p.machine_id = m.machine_id
        ORDER BY p.prediction_date DESC
    """)
    predictions = cur.fetchall()
    cur.close()
    db.close()
    return render_template("predictions.html", predictions=predictions)


if __name__ == "__main__":
    app.run(debug=True)
