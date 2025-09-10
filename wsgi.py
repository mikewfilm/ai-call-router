import logging
import os
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FALLBACK_TO_MAIN = int(os.getenv("FALLBACK_TO_MAIN", "0"))
try:
    from app import app as application
    logger.info("✅ Loaded app from app.py")
except Exception as e:
    logger.error("Failed to import app.py: %s", e)
    import traceback
    logger.error("Traceback: %s", traceback.format_exc())
    if FALLBACK_TO_MAIN:
        logger.warning("FALLBACK_TO_MAIN=1, falling back to main.py")
        from main import app as application
        logger.info("✅ Loaded app from main.py (fallback)")
    else:
        logger.error("FALLBACK_TO_MAIN=0, raising exception")
        raise