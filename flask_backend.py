# flask_backend/app.py
from flask import Flask, request, jsonify, render_template
import mysql.connector
import os
from datetime import datetime

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST","localhost")
DB_USER = os.getenv("DB_USER","root")
DB_PASS = os.getenv("DB_PASS","yourpassword")
DB_NAME = os.getenv("DB_NAME","air_travel_system")

def get_db():
    return mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/flights", methods=["GET"])
def list_flights():
    cnx = get_db()
    cur = cnx.cursor(dictionary=True)
    cur.execute("SELECT f.*, a.name AS airline_name, a.code AS airline_code FROM flights f LEFT JOIN airlines a ON f.airline_id = a.airline_id")
    rows = cur.fetchall()
    cnx.close()
    return jsonify(rows)

@app.route("/api/flights/search", methods=["GET"])
def search_flights():
    frm = request.args.get("from")
    to = request.args.get("to")
    date = request.args.get("date")  # YYYY-MM-DD
    cnx = get_db()
    cur = cnx.cursor(dictionary=True)
    query = "SELECT f.*, a.name AS airline_name FROM flights f LEFT JOIN airlines a ON f.airline_id = a.airline_id WHERE 1=1"
    params=[]
    if frm:
        query += " AND departure_airport = %s"; params.append(frm)
    if to:
        query += " AND arrival_airport = %s"; params.append(to)
    if date:
        query += " AND DATE(departure_datetime) = %s"; params.append(date)
    cur.execute(query, params)
    rows = cur.fetchall()
    cnx.close()
    return jsonify(rows)

@app.route("/api/book", methods=["POST"])
def book():
    payload = request.json
    # expected payload keys: passenger {full_name,age,gender,email}, flight_id, seat_number, travel_class, price
    p = payload.get("passenger", {})
    flight_id = payload.get("flight_id")
    seat_number = payload.get("seat_number")
    travel_class = payload.get("travel_class", "Economy")
    price = float(payload.get("price", 0.0))
    if not p.get("full_name") or not flight_id:
        return jsonify({"error":"missing passenger name or flight_id"}), 400

    cnx = get_db(); cur = cnx.cursor()
    try:
        cur.execute("INSERT INTO passengers (full_name, age, gender, email) VALUES (%s,%s,%s,%s)",
                    (p.get("full_name"), p.get("age"), p.get("gender"), p.get("email")))
        passenger_id = cur.lastrowid

        cur.execute("SELECT seats_available FROM flights WHERE flight_id = %s FOR UPDATE", (flight_id,))
        res = cur.fetchone()
        if not res:
            cnx.rollback(); cnx.close()
            return jsonify({"error":"flight not found"}), 404
        if res[0] <= 0:
            cnx.rollback(); cnx.close()
            return jsonify({"error":"no seats available"}), 400

        cur.execute("INSERT INTO reservations (flight_id, passenger_id, seat_number, travel_class, price) VALUES (%s,%s,%s,%s,%s)",
                    (flight_id, passenger_id, seat_number, travel_class, price))
        cur.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE flight_id = %s", (flight_id,))
        cnx.commit()
        cnx.close()
        return jsonify({"status":"booked"})
    except Exception as e:
        cnx.rollback(); cnx.close()
        return jsonify({"error":str(e)}), 500

@app.route("/api/reservations", methods=["GET"])
def reservations():
    cnx = get_db(); cur = cnx.cursor(dictionary=True)
    cur.execute("""SELECT r.*, p.full_name AS passenger_name, f.flight_number
                   FROM reservations r
                   JOIN passengers p ON r.passenger_id = p.passenger_id
                   JOIN flights f ON r.flight_id = f.flight_id""")
    rows = cur.fetchall()
    cnx.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)), debug=True)
