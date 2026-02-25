# Air Travel System — GitHub-ready Repository


- Flask REST backend (MySQL)
- React frontend (converted from Gradio design) calling the Flask API
- Optional Gradio demo (kept for quick testing)
- OpenAI/Gemini integration for natural-language booking queries
- MySQL schema, Dockerfile, Render/Railway deployment instructions, and deploy scripts

---

## Repo layout

```
air-travel-system/
├─ README.md
├─ .gitignore
├─ db_schema.sql
├─ docker-compose.yml
├─ .env.example
├─ backend/
│  ├─ app.py
│  ├─ requirements.txt
│  ├─ Dockerfile
│  ├─ Procfile
│  ├─ render.yaml
│  └─ templates/
│     └─ index.html
├─ frontend/
│  ├─ README.md
│  ├─ package.json
│  ├─ public/
│  │  └─ index.html
│  └─ src/
│     ├─ index.js
│     ├─ App.js
│     ├─ api.js
│     ├─ components/
│     │  ├─ FlightList.js
│     │  ├─ BookingForm.js
│     │  └─ NLQuery.js
│     └─ styles.css
├─ gradio_demo/
│  ├─ gradio_app.py
│  └─ requirements.txt
└─ deploy/
   ├─ render_deploy.md
   └─ railway_deploy.md
```

---

## Important: Environment variables

Fill a `.env` on your machine or set environment variables in Render/Railway with the following names (examples in `.env.example` below):

- `DB_HOST` (e.g., `localhost` or cloud DB host)
- `DB_PORT` (defaults 3306)
- `DB_USER`
- `DB_PASS`
- `DB_NAME` (air_travel_system)
- `FLASK_ENV` (development/production)
- `OPENAI_API_KEY` (for OpenAI)
- `GENIE_API_KEY` (placeholder if using Google Gemini — see notes)
- `PORT`

---

## db_schema.sql

```sql
-- db_schema.sql
CREATE DATABASE IF NOT EXISTS air_travel_system;
USE air_travel_system;

CREATE TABLE IF NOT EXISTS airlines (
  airline_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150),
  code VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS flights (
  flight_id INT AUTO_INCREMENT PRIMARY KEY,
  airline_id INT,
  flight_number VARCHAR(50),
  departure_airport VARCHAR(100),
  arrival_airport VARCHAR(100),
  departure_datetime DATETIME,
  arrival_datetime DATETIME,
  seats_total INT DEFAULT 0,
  seats_available INT DEFAULT 0,
  FOREIGN KEY (airline_id) REFERENCES airlines(airline_id)
);

CREATE TABLE IF NOT EXISTS passengers (
  passenger_id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(150),
  age INT,
  gender VARCHAR(20),
  email VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS reservations (
  reservation_id INT AUTO_INCREMENT PRIMARY KEY,
  flight_id INT,
  passenger_id INT,
  seat_number VARCHAR(20),
  travel_class VARCHAR(20),
  price DECIMAL(10,2),
  booked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
  FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id)
);

-- Sample Data
INSERT INTO airlines (name, code) VALUES ('Indigo','6E'), ('Air India','AI'), ('Vistara','UK');

INSERT INTO flights (airline_id, flight_number, departure_airport, arrival_airport, departure_datetime, arrival_datetime, seats_total, seats_available)
VALUES
(1,'6E-123','DEL','BLR','2025-11-20 08:00:00','2025-11-20 10:30:00',180,180),
(2,'AI-456','DEL','BOM','2025-11-20 09:00:00','2025-11-20 11:30:00',200,200);
```

---

## .env.example

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASS=yourpassword
DB_NAME=air_travel_system
FLASK_ENV=development
PORT=5000
OPENAI_API_KEY=sk-REPLACE_WITH_YOUR_KEY
GENIE_API_KEY=REPLACE_IF_USING_GEMINI
```

---

## backend/app.py

> Flask REST API + OpenAI / Gemini natural language integration

```python
# backend/app.py
import os
from flask import Flask, request, jsonify, render_template
import mysql.connector
from datetime import datetime
import requests

# --- config from env ---
DB_HOST = os.getenv('DB_HOST','localhost')
DB_PORT = int(os.getenv('DB_PORT','3306'))
DB_USER = os.getenv('DB_USER','root')
DB_PASS = os.getenv('DB_PASS','yourpassword')
DB_NAME = os.getenv('DB_NAME','air_travel_system')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GENIE_API_KEY = os.getenv('GENIE_API_KEY')  # if using Gemini via Google Cloud

app = Flask(__name__, static_folder='../frontend/build', template_folder='templates')

def get_db():
    return mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)

# ---------- Utility: parse NL query via OpenAI (or Gemini) ----------
def parse_nl_query_to_search_params(nl_text):
    """
    Send the natural-language text to OpenAI (or Gemini) to extract structured parameters:
    expected output JSON: {"from": "DEL", "to":"BOM", "date":"2025-11-20", "class":"Economy"}
    """
    # Prefer OpenAI if key provided
    if OPENAI_API_KEY:
        # simple OpenAI call using Chat Completions (gpt-4o or gpt-4o-mini) style
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        system = "You are a helpful assistant that extracts flight search parameters from a user's query. Respond with JSON only. Keys: from, to, date (YYYY-MM-DD), travel_class. Use empty string for missing values."
        prompt = f"{system}\nUser: {nl_text}\nRespond only with JSON."
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role":"user","content":prompt}],
            "temperature": 0
        }
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        j = r.json()
        # try to extract text
        text = j['choices'][0]['message']['content']
        # Attempt to parse JSON from text
        import json
        try:
            parsed = json.loads(text)
            return parsed
        except Exception:
            # fallback: try to find JSON substring
            import re
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
            return {"from":"","to":"","date":"","travel_class":""}
    elif GENIE_API_KEY:
        # Placeholder: if using Gemini via Google Cloud, call its REST endpoint with appropriate auth
        # For students: use Google Cloud client libraries and set up credentials.
        return {"from":"","to":"","date":"","travel_class":""}
    else:
        return {"from":"","to":"","date":"","travel_class":""}

# ---------- Routes ----------
@app.route('/')
def serve_frontend():
    # frontend build will be served if exists
    return app.send_static_file('index.html')

@app.route('/api/flights', methods=['GET'])
def list_flights():
    cnx = get_db(); cur = cnx.cursor(dictionary=True)
    cur.execute("SELECT f.*, a.name AS airline_name, a.code AS airline_code FROM flights f LEFT JOIN airlines a ON f.airline_id = a.airline_id")
    rows = cur.fetchall(); cnx.close()
    return jsonify(rows)

@app.route('/api/flights/search', methods=['GET','POST'])
def search_flights():
    # Accept query params or JSON
    if request.method == 'POST' and request.is_json:
        payload = request.json
        frm = payload.get('from')
        to = payload.get('to')
        date = payload.get('date')
    else:
        frm = request.args.get('from')
        to = request.args.get('to')
        date = request.args.get('date')

    cnx = get_db(); cur = cnx.cursor(dictionary=True)
    query = "SELECT f.*, a.name AS airline_name FROM flights f LEFT JOIN airlines a ON f.airline_id = a.airline_id WHERE 1=1"
    params = []
    if frm:
        query += " AND departure_airport = %s"; params.append(frm)
    if to:
        query += " AND arrival_airport = %s"; params.append(to)
    if date:
        query += " AND DATE(departure_datetime) = %s"; params.append(date)
    cur.execute(query, params)
    rows = cur.fetchall(); cnx.close()
    return jsonify(rows)

@app.route('/api/book', methods=['POST'])
def book():
    data = request.json
    passenger = data.get('passenger', {})
    flight_id = data.get('flight_id')
    seat_number = data.get('seat_number')
    travel_class = data.get('travel_class','Economy')
    price = float(data.get('price',0))
    if not passenger.get('full_name') or not flight_id:
        return jsonify({'error':'missing fields'}), 400
    cnx = get_db(); cur = cnx.cursor()
    try:
        cur.execute("INSERT INTO passengers (full_name, age, gender, email) VALUES (%s,%s,%s,%s)",
                    (passenger.get('full_name'), passenger.get('age'), passenger.get('gender'), passenger.get('email')))
        passenger_id = cur.lastrowid
        cur.execute("SELECT seats_available FROM flights WHERE flight_id = %s FOR UPDATE", (flight_id,))
        res = cur.fetchone()
        if not res:
            cnx.rollback(); cnx.close(); return jsonify({'error':'flight not found'}), 404
        if res[0] <= 0:
            cnx.rollback(); cnx.close(); return jsonify({'error':'no seats'}), 400
        cur.execute("INSERT INTO reservations (flight_id, passenger_id, seat_number, travel_class, price) VALUES (%s,%s,%s,%s,%s)",
                    (flight_id, passenger_id, seat_number, travel_class, price))
        cur.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE flight_id = %s", (flight_id,))
        cnx.commit(); cnx.close()
        return jsonify({'status':'booked'})
    except Exception as e:
        cnx.rollback(); cnx.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/nlsearch', methods=['POST'])
def nlsearch():
    # Accept a natural language query, parse it to structured params, and run flight search
    data = request.json
    q = data.get('query','')
    if not q:
        return jsonify({'error':'no query provided'}), 400
    params = parse_nl_query_to_search_params(q)
    # call search_flights via internal request
    # normalize keys
    frm = params.get('from') or params.get('origin') or ''
    to = params.get('to') or params.get('destination') or ''
    date = params.get('date','')
    # forward to search_flights logic
    cnx = get_db(); cur = cnx.cursor(dictionary=True)
    query = "SELECT f.*, a.name AS airline_name FROM flights f LEFT JOIN airlines a ON f.airline_id = a.airline_id WHERE 1=1"
    ps=[]
    if frm:
        query += " AND departure_airport = %s"; ps.append(frm)
    if to:
        query += " AND arrival_airport = %s"; ps.append(to)
    if date:
        query += " AND DATE(departure_datetime) = %s"; ps.append(date)
    cur.execute(query, ps)
    rows = cur.fetchall(); cnx.close()
    return jsonify({'params':params, 'results': rows})

@app.route('/api/reservations', methods=['GET'])
def reservations():
    cnx = get_db(); cur = cnx.cursor(dictionary=True)
    cur.execute("SELECT r.*, p.full_name AS passenger_name, f.flight_number FROM reservations r JOIN passengers p ON r.passenger_id = p.passenger_id JOIN flights f ON r.flight_id = f.flight_id")
    rows = cur.fetchall(); cnx.close(); return jsonify(rows)

if __name__ == '__main__':
    port = int(os.getenv('PORT',5000))
    app.run(host='0.0.0.0', port=port, debug=(os.getenv('FLASK_ENV')=='development'))
```

---

## backend/requirements.txt

```
Flask==2.3.3
mysql-connector-python==8.0.33
requests==2.31.0
gunicorn==20.1.0
```

---

## backend/Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PORT=5000
CMD ["gunicorn","-b","0.0.0.0:5000","app:app","--workers=1"]
```

---

## frontend (React) — key files

### frontend/package.json

```json
{
  "name": "air-travel-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
```

### frontend/public/index.html

```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Air Travel Booking</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
```

### frontend/src/index.js

```javascript
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

createRoot(document.getElementById('root')).render(<App />);
```

### frontend/src/api.js

```javascript
const API_BASE = process.env.REACT_APP_API_BASE || '';

export async function fetchFlights(){
  const res = await fetch(`${API_BASE}/api/flights`);
  return res.json();
}

export async function searchFlights(params){
  const res = await fetch(`${API_BASE}/api/flights/search`, {
    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(params)
  });
  return res.json();
}

export async function bookFlight(payload){
  const res = await fetch(`${API_BASE}/api/book`, {
    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)
  });
  return res.json();
}

export async function nlSearch(query){
  const res = await fetch(`${API_BASE}/api/nlsearch`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query})});
  return res.json();
}
```

### frontend/src/App.js

```javascript
import React, {useState, useEffect} from 'react';
import {fetchFlights, searchFlights, bookFlight, nlSearch} from './api';
import FlightList from './components/FlightList';
import BookingForm from './components/BookingForm';
import NLQuery from './components/NLQuery';

export default function App(){
  const [flights, setFlights] = useState([]);
  useEffect(()=>{ fetchFlights().then(setFlights); },[]);

  return (
    <div className="container">
      <h1>Air Travel Booking</h1>
      <NLQuery onResults={(r)=>setFlights(r)} />
      <FlightList flights={flights} />
      <BookingForm />
    </div>
  )
}
```

### frontend/src/components/FlightList.js

```javascript
import React from 'react';
export default function FlightList({flights}){
  return (
    <div>
      <h2>Available Flights</h2>
      <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(flights, null, 2)}</pre>
    </div>
  )
}
```

### frontend/src/components/BookingForm.js

```javascript
import React, {useState} from 'react';
import {bookFlight} from '../api';
export default function BookingForm(){
  const [flightId, setFlightId] = useState('');
  const [name, setName] = useState('');
  const [seat, setSeat] = useState('');
  const [resp, setResp] = useState(null);
  async function submit(e){
    e.preventDefault();
    const payload = { passenger: { full_name: name }, flight_id: Number(flightId), seat_number: seat, travel_class:'Economy', price:1000 };
    const r = await bookFlight(payload);
    setResp(r);
  }
  return (
    <div>
      <h2>Book a Flight</h2>
      <form onSubmit={submit}>
        <label>Flight ID <input value={flightId} onChange={e=>setFlightId(e.target.value)} /></label><br />
        <label>Name <input value={name} onChange={e=>setName(e.target.value)} /></label><br />
        <label>Seat <input value={seat} onChange={e=>setSeat(e.target.value)} /></label><br />
        <button>Book</button>
      </form>
      <pre>{JSON.stringify(resp,null,2)}</pre>
    </div>
  )
}
```

### frontend/src/components/NLQuery.js

```javascript
import React, {useState} from 'react';
import {nlSearch} from '../api';

export default function NLQuery({onResults}){
  const [q, setQ] = useState('');
  const [resp, setResp] = useState(null);
  async function submit(e){
    e.preventDefault();
    const r = await nlSearch(q);
    setResp(r);
    if(r && r.results) onResults(r.results);
  }
  return (
    <div>
      <h2>Natural Language Search</h2>
      <form onSubmit={submit}>
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder="e.g., flights from DEL to BOM on 2025-11-20" style={{width:'60%'}} />
        <button>Search</button>
      </form>
      <pre>{JSON.stringify(resp,null,2)}</pre>
    </div>
  )
}
```

### frontend/src/styles.css

```css
.container{ max-width:900px; margin:20px auto; font-family: Arial, sans-serif }
pre{ background:#f7f7f7; padding:10px }
```

---

## gradio_demo/gradio_app.py

```python
# lightweight demo that shows live flights (OpenSky) and allows quick booking to DB
import gradio as gr
import requests, pandas as pd, os
import mysql.connector
from datetime import datetime

OPENSKY_URL = 'https://opensky-network.org/api/states/all'
DB_HOST=os.getenv('DB_HOST','localhost')
DB_USER=os.getenv('DB_USER','root')
DB_PASS=os.getenv('DB_PASS','yourpassword')
DB_NAME=os.getenv('DB_NAME','air_travel_system')

def fetch_live(limit=50):
    r = requests.get(OPENSKY_URL, timeout=10); r.raise_for_status(); data=r.json(); states=data.get('states',[]) or []
    rows=[]
    for s in states[:limit]: rows.append({'callsign':(s[1] or '').strip(),'origin_country':s[2]})
    return pd.DataFrame(rows)

def book_demo(full_name, flight_id):
    cnx = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
    cur = cnx.cursor()
    cur.execute("INSERT INTO passengers (full_name) VALUES (%s)", (full_name,))
    pid = cur.lastrowid
    cur.execute("INSERT INTO reservations (flight_id, passenger_id, seat_number, travel_class, price) VALUES (%s,%s,%s,%s,%s)", (flight_id, pid, 'A1', 'Economy', 1000))
    cnx.commit(); cnx.close()
    return f'Booked {full_name} on flight {flight_id}'

with gr.Blocks() as demo:
    gr.Markdown('# Live Flight Demo (OpenSky)')
    df = gr.Dataframe()
    btn = gr.Button('Fetch Live')
    btn.click(fetch_live, inputs=[], outputs=df)
    name = gr.Textbox(label='Full name')
    fid = gr.Number(label='Flight ID', precision=0)
    bbtn = gr.Button('Book (demo)')
    out = gr.Textbox()
    bbtn.click(book_demo, inputs=[name, fid], outputs=out)

if __name__=='__main__':
    demo.launch(share=False)
```

`gradio_demo/requirements.txt`:
```
gradio
pandas
requests
mysql-connector-python
```

---

## deploy/render_deploy.md

Contains step-by-step Render deploy. See the full file in the repo.

---

## deploy/railway_deploy.md

Contains Railway step-by-step including linking the MySQL plugin and setting ENV.

---

## How to push this to GitHub quickly

1. Create a new GitHub repo `air-travel-system`.
2. On your laptop, create the folder and files exactly as in this document.
3. Run:
```bash
git init
git add .
git commit -m "Initial commit: Air Travel System starter"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/air-travel-system.git
git push -u origin main
```

---

## Render deploy quick script (example)

1. From the Render dashboard, create a new Web Service.
2. Connect to the GitHub repo.
3. Use these settings:
   - Build Command: `pip install -r backend/requirements.txt && cd frontend && npm ci && npm run build && cd ..`
   - Start Command: `gunicorn -b 0.0.0.0:5000 backend.app:app`
4. Add environment variables as in `.env.example`.

---

## Railway deploy quick steps (example)

1. Create a Railway project and link your GitHub repo.
2. Add a MySQL plugin (provisioned DB) and copy the DB credentials into env vars.
3. Set service to run `backend/app.py` with `gunicorn backend.app:app` and build to install both backend and frontend.

---

## Notes & Next actions

- Replace placeholders for OpenAI/Gemini keys. For Google Gemini, follow Google Cloud instructions and use their client library; code includes placeholder.
- Security: do not push real keys. Use repository secrets for CI or Render/Railway env vars.
- I can also produce a downloadable ZIP of this repo or push it to your GitHub if you give me a repo URL (or I can provide copy-paste ready files).

---

*End of repository document.*

