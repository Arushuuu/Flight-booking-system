# gradio_app.py
import gradio as gr
import requests
import pandas as pd
from datetime import datetime
import mysql.connector
import os

# Read DB config from env
DB_HOST = os.getenv("DB_HOST","localhost")
DB_USER = os.getenv("DB_USER","root")
DB_PASS = os.getenv("DB_PASS","yourpassword")
DB_NAME = os.getenv("DB_NAME","air_travel_system")

OPENSKY_URL = "https://opensky-network.org/api/states/all"

def fetch_live_flights(country_filter="", callsign_contains="", limit=50):
    try:
        r = requests.get(OPENSKY_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        states = data.get("states",[]) or []
        rows = []
        for s in states:
            rows.append({
                "callsign": (s[1] or "").strip(),
                "origin_country": s[2],
                "time_position": datetime.utcfromtimestamp(s[3]).isoformat() if s[3] else None,
                "longitude": s[5],
                "latitude": s[6],
                "baro_alt_m": s[7],
                "on_ground": s[8],
            })
        df = pd.DataFrame(rows)
        if country_filter:
            df = df[df["origin_country"].str.contains(country_filter, case=False, na=False)]
        if callsign_contains:
            df = df[df["callsign"].str.contains(callsign_contains, case=False, na=False)]
        if not df.empty:
            df = df.head(int(limit))
            status = f"Snapshot rows: {len(df)}"
            return status, df
        return "No flights matched filters.", pd.DataFrame()
    except Exception as e:
        return f"Error: {e}", pd.DataFrame()

def book_ticket(passenger_name, age, gender, email,
                flight_id, seat_number, travel_class, price):
    try:
        # Insert passenger -> reservation
        cnx = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cur = cnx.cursor()
        cur.execute("INSERT INTO passengers (full_name, age, gender, email) VALUES (%s,%s,%s,%s)",
                    (passenger_name, int(age) if age else None, gender, email))
        passenger_id = cur.lastrowid

        # Check seats_available
        cur.execute("SELECT seats_available FROM flights WHERE flight_id = %s", (flight_id,))
        res = cur.fetchone()
        if not res:
            cnx.rollback(); cnx.close()
            return f"Flight id {flight_id} not found."
        seats_available = res[0]
        if seats_available <= 0:
            cnx.rollback(); cnx.close()
            return "No seats available."

        cur.execute("""INSERT INTO reservations (flight_id, passenger_id, seat_number, travel_class, price)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (flight_id, passenger_id, seat_number, travel_class, float(price) if price else 0.0))
        cur.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE flight_id = %s", (flight_id,))
        cnx.commit()
        cnx.close()
        return f"Booking successful! Reservation ID: {cur.lastrowid}"
    except Exception as e:
        return f"Error: {e}"

with gr.Blocks(title="Air Travel - Gradio Demo") as demo:
    gr.Markdown("## Live Flights (OpenSky) + Simple Booking (MySQL)")
    with gr.Tab("Live Flights"):
        country = gr.Textbox(label="Origin Country (optional)")
        callsign = gr.Textbox(label="Callsign contains (optional)")
        limit = gr.Slider(10, 200, value=50, label="Max rows")
        fetch = gr.Button("Fetch")
        status = gr.Markdown()
        table = gr.Dataframe(headers=["callsign","origin_country","time_position","longitude","latitude","baro_alt_m","on_ground"])
        fetch.click(fetch_live_flights, inputs=[country,callsign,limit], outputs=[status,table])

    with gr.Tab("Book Ticket"):
        name = gr.Textbox(label="Full name")
        age = gr.Number(label="Age", precision=0)
        gender = gr.Radio(["Male","Female","Other"], label="Gender")
        email = gr.Textbox(label="Email")
        flight_id = gr.Number(label="Flight ID (from DB)", precision=0)
        seat_no = gr.Textbox(label="Seat number")
        travel_class = gr.Dropdown(["Economy","Business","First"], label="Class")
        price = gr.Number(label="Price (INR)", precision=2)
        book_btn = gr.Button("Book")
        book_out = gr.Textbox()
        book_btn.click(book_ticket, inputs=[name,age,gender,email,flight_id,seat_no,travel_class,price], outputs=book_out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
demo.launch(share=True)