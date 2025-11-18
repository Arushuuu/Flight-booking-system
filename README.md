air-travel-project/
├─ gradio_app.py               # Quick Gradio UI + OpenSky live flights + booking to MySQL
├─ flask_backend/
│  ├─ app.py                   # Flask REST API (flights, book, view bookings)
│  ├─ requirements.txt
│  ├─ Dockerfile
│  ├─ Procfile                 # (Render / Heroku style)
│  └─ templates/
│     └─ index.html            # Simple frontend to call the REST API
├─ db_schema.sql               # MySQL schema for flights/passengers/reservations
├─ README.md                   # Instructions (short)
└─ deploy.md                   # Hosting/deployment steps (Hugging Face, Render, Railway)
# Flight-booking-system
Flask REST backend
