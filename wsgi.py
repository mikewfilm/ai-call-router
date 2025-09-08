import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from app import app  # <-- your production routes
    logger.info("✅ Loaded app from app.py")
except Exception as e:
    logger.warning("⚠️ Failed loading app from app.py (%s); falling back to main.py", e)
    from main import app
    logger.info("✅ Loaded app from main.py (fallback)")