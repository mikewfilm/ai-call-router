# wsgi.py
import logging
logger = logging.getLogger("wsgi")

try:
    from app import app as app
    logger.info("✅ Loaded app from app.py")
except Exception as e_app:
    logger.warning("⚠️ Failed loading app from app.py (%s); trying main.py", e_app)
    from main import app as app
    logger.info("✅ Loaded app from main.py (fallback)")