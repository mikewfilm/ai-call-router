# wsgi.py
import logging
logger = logging.getLogger("wsgi")

# Try to import the Flask app object named `app` from app.py.
# If that fails, log and try main.py as a last resort.
try:
    from app import app as app  # must export a module-level name `app`
    logger.info("✅ Loaded app from app.py")
except Exception as e_app:
    logger.warning("⚠️ Failed loading app from app.py (%s); trying main.py", e_app)
    try:
        from main import app as app  # also module-level `app`
        logger.info("✅ Loaded app from main.py (fallback)")
    except Exception as e_main:
        logger.exception("❌ Could not load Flask app from app.py or main.py")
        raise

# Gunicorn will look for `app` in this module (wsgi:app)