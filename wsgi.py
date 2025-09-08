import logging, traceback
logging.basicConfig(level=logging.INFO)

try:
    from main import app  # import the real Flask app from main.py
except Exception:
    logging.exception("❌ App failed to import at startup")
    # Fallback minimal app to ensure Gunicorn binds the port and logs the traceback
    from flask import Flask, Response
    app = Flask(__name__)

    @app.get("/")
    def import_failed():
        return Response(
            "Import failed. Check logs for traceback (look for 'App failed to import at startup').",
            status=500,
        )
