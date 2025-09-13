import os
import io
import json
import uuid
import threading
import re
import hashlib
import hmac
import random
import time
import traceback
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, Response, url_for, has_request_context, render_template, jsonify, redirect, current_app, make_response, send_from_directory
import mimetypes
import requests
from collections import defaultdict
import base64
import queue
import subprocess
import tempfile
import shutil
from pathlib import Path
import urllib.parse
from urllib.parse import urljoin
import logging
import sys
import traceback
import asyncio
import aiohttp

# Global logger and BASE_URL configuration
logger = logging.getLogger("app")

PUBLIC_BASE = os.getenv("PUBLIC_BASE", "").rstrip("/")
if not PUBLIC_BASE:
    # Try Railway hint, then fail fast.
    RB = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if RB:
        if not RB.startswith("http"):
            RB = "https://" + RB
        PUBLIC_BASE = RB.rstrip("/")

logger.info("[BOOT] PUBLIC_BASE=%s", PUBLIC_BASE)

# Module-level flag for one-time warning
_BASE_WARNED = False

def _env_bool(name: str, default=False):
    v = os.getenv(name)
    if v is None: 
        return default
    return v.strip().lower() in ("1", "true", "t", "yes", "y", "on")

# ===== CONFIG ORDER + DEFAULTS =====
# All config flags and constants with safe defaults - defined before ANY route definitions
GATHER_TIMEOUT = int(os.getenv("GATHER_TIMEOUT", "5"))
GATHER_MAX_ATTEMPTS = int(os.getenv("GATHER_MAX_ATTEMPTS", "3"))
GATHER_MAX_SECONDS = int(os.getenv("GATHER_MAX_SECONDS", "45"))
GATHER_HINTS = os.getenv("GATHER_HINTS", "bananas, pharmacy, prescriptions, coupons, produce, deli, bakery, customer service")
REDIS_URL = os.getenv("REDIS_URL", "")
USE_LOCAL_WHISPER = int(os.getenv("USE_LOCAL_WHISPER", "0"))
GATHER_SPEECH_SECONDS = int(os.getenv("GATHER_SPEECH_SECONDS", "7"))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")
USE_FILLER = os.getenv("USE_FILLER", "1") == "1"
VOICE_SAFE_MODE = _env_bool("VOICE_SAFE_MODE", False)
DEBUG_RESULT_SAY = _env_bool("DEBUG_RESULT_SAY", False)   # when true, /result speaks its poll count
MAX_RESULT_POLLS = int(os.getenv("MAX_RESULT_POLLS", "8")) # hard cap on redirects
HOLDY_TINY_CDN = os.getenv("HOLDY_TINY_CDN", "https://call-router-audio-2526.twil.io/holdy_tiny.mp3")
HOLDY_MID_CDN  = os.getenv("HOLDY_MID_CDN",  "https://call-router-audio-2526.twil.io/holdy_mid.mp3")
HOLD_BG_CDN    = os.getenv("HOLD_BG_CDN",    "")
HOLDY_CLARIFY_CDN = os.getenv("HOLDY_CLARIFY_CDN", "https://call-router-audio-2526.twil.io/holdy_clarify.mp3")
CALL_TIMEOUT_SECONDS = int(os.getenv("CALL_TIMEOUT_SECONDS", "300"))
POLL_PAUSE = int(os.getenv("POLL_PAUSE", "2"))
HOLD_MIN_GAP_SEC = int(os.getenv("HOLD_MIN_GAP_SEC", "8"))
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "en")
CONF_TIMEOUT = int(os.getenv("CONF_TIMEOUT", "5"))
MAIN_MAXLEN = int(os.getenv("MAIN_MAXLEN", "30"))
MAIN_TIMEOUT = int(os.getenv("MAIN_TIMEOUT", "10"))
USE_GATHER_MAIN = os.getenv("USE_GATHER_MAIN", "1") == "1"

# --- BEGIN: hardened config defaults ---
DIAG_TWILIO         = int(os.getenv("DIAG_TWILIO", "0") or 0)
DIAG_LOG_BODY_LIMIT = int(os.getenv("DIAG_LOG_BODY_LIMIT", "4000") or 4000)

# -------- Twilio Webhook Diagnostics (safe to keep in prod, gated by DIAG_TWILIO) --------
DIAG_TWILIO = os.getenv("DIAG_TWILIO", "0") == "1"
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

def _b64_hmac_sha1(key: str, msg: bytes) -> str:
    return base64.b64encode(hmac.new(key.encode("utf-8"), msg, hashlib.sha1).digest()).decode("utf-8")

def _twilio_signature_status() -> str:
    """
    Recompute Twilio signature per spec:
    1) Start with the full request URL without query string (Twilio signs the URL it posts to; if behind a proxy ensure your PUBLIC_BASE is correct).
    2) Append each POST param as key+value in key-sorted order.
    3) Base64(HMAC-SHA1(auth_token, concatenated_string)).
    """
    try:
        sig_hdr = request.headers.get("X-Twilio-Signature", "") or ""
        if not TWILIO_AUTH_TOKEN:
            return f"VERIFY_ERROR(no TWILIO_AUTH_TOKEN)"
        url = request.url.split("?")[0]
        # Ensure all form params included in sorted key order; include each value for list-typed fields.
        pieces = [url] + [k + v for k in sorted(request.form.keys()) for v in request.form.getlist(k)]
        computed = _b64_hmac_sha1(TWILIO_AUTH_TOKEN, "".join(pieces).encode("utf-8"))
        ok = hmac.compare_digest(sig_hdr, computed)
        return f"{'OK' if ok else 'MISMATCH'} (hdr={sig_hdr} cmp={computed})"
    except Exception as e:
        return f"VERIFY_ERROR({e})"

def log_twilio_webhook(where: str) -> None:
    """
    Log exactly what Twilio posted. No-ops if DIAG_TWILIO != 1.
    Safe for production; emits at INFO level.
    """
    if not DIAG_TWILIO:
        return
    # Curate headers for noise reduction
    hdr_whitelist = {"user-agent","content-type","x-twilio-signature","x-forwarded-for","x-forwarded-proto","x-request-id"}
    hdrs = {k: v for k, v in request.headers.items() if k.lower() in hdr_whitelist}
    form_dict = {k: request.form.getlist(k) for k in request.form.keys()}
    try:
        raw = request.get_data(as_text=True)  # exact body
    except Exception:
        raw = "<unavailable>"

    try:
        sig_status = _twilio_signature_status()
    except Exception as e:
        sig_status = f"VERIFY_ERROR({e})"

    current_app.logger.info("[TWILIO %s] url=%s method=%s sig_check=%s", where, request.url, request.method, sig_status)
    current_app.logger.info("[TWILIO %s] headers=%s", where, json.dumps(hdrs))
    current_app.logger.info("[TWILIO %s] form=%s", where, json.dumps(form_dict))
    current_app.logger.info("[TWILIO %s] raw=%s", where, raw)
# -------- end diagnostics --------

# --- Build fingerprint (for deploy verification) ---
BUILD_ID = os.getenv("BUILD_ID", time.strftime("%Y%m%d-%H%M%S"))

# Public base used to build absolute URLs that Twilio can fetch.
# Example: https://ai-call-router-production.up.railway.app
PUBLIC_WS_BASE = os.getenv("PUBLIC_WS_BASE", "").rstrip("/")
PUBLIC_BASE = os.getenv("PUBLIC_BASE", "").strip().rstrip("/")
PREFERRED_URL_SCHEME = "https"

from urllib.parse import urljoin

def _effective_base() -> str:
    """
    Absolute https base that Twilio can reach.
    Priority:
      1) PUBLIC_BASE env (e.g. https://ai-call-router-production.up.railway.app)
      2) request.url_root (forced to https)
    """
    base = PUBLIC_BASE
    if not base:
        try:
            if has_request_context():
                base = request.url_root.strip().rstrip("/")
            else:
                base = ""
        except Exception:
            base = ""
    if base.startswith("http://"):
        base = "https://" + base[len("http://"):]
    return base

def public_url(path_or_url: str) -> str:
    """
    Build an absolute URL for Twilio. Works both in-request and in background threads.
    Never shadows the 'os' module; never raises if no request context.
    """
    if not path_or_url:
        return path_or_url

    # Already absolute?
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url

    # Make sure it starts with a leading slash
    if not path_or_url.startswith("/"):
        path_or_url = "/" + path_or_url

    # Prefer the live request when available
    try:
        if has_request_context() and request:
            return f"{request.url_root.rstrip('/')}{path_or_url}"
    except Exception:
        pass

    # Next: environment-provided base(s)
    base = (os.getenv("PUBLIC_BASE")
            or os.getenv("PUBLIC_HTTP_BASE")
            or os.getenv("PUBLIC_BASE_URL")
            or "").strip().rstrip("/")
    if base:
        return f"{base}{path_or_url}"

    # Railway/host fallbacks
    scheme = os.getenv("PREFERRED_URL_SCHEME", "https").strip() or "https"
    host = (os.getenv("RAILWAY_PUBLIC_DOMAIN")
            or os.getenv("RAILWAY_STATIC_URL")
            or os.getenv("RAILWAY_URL")
            or os.getenv("HOST")
            or "").strip()
    if host:
        if not host.startswith("http"):
            host = f"{scheme}://{host}"
        return f"{host.rstrip('/')}{path_or_url}"

    # Last resort: relative (Twilio may reject; but don't crash)
    return path_or_url

def sanitize_twiml_xml(xml: str) -> str:
    # make http -> https, and replace any localhost/127.* with PUBLIC_BASE
    if not isinstance(xml, str):
        return xml
    xml = xml.replace("http://", "https://")
    base = os.getenv("PUBLIC_BASE", "").rstrip("/")
    if base:
        xml = re.sub(r"https://(localhost|127\.0\.0\.1)(:\d+)?", base, xml)
    return xml

# --- END: hardened config defaults ---

# ===== FLASK APP CREATION =====
app = Flask(__name__, static_folder="static")

# Log the build ID at boot so we can confirm the running version via logs
app.logger.info("[BUILD] %s", BUILD_ID)

# Startup sanity log
logger.info("[BOOT] Ready. PUBLIC_BASE=%s, DIAG_TWILIO=%s", PUBLIC_BASE, os.getenv("DIAG_TWILIO", "0"))

# Configure ProxyFix for Railway deployment
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.setdefault("PREFERRED_URL_SCHEME", "https")

# Optional Whisper imports - only load if explicitly enabled
logger = logging.getLogger(__name__)
FasterWhisper = None
WhisperLegacy = None
if USE_LOCAL_WHISPER:
    try:
        from faster_whisper import WhisperModel as FasterWhisper  # preferred
    except Exception as e:
        logger.warning("faster-whisper unavailable: %s", e)
    try:
        import whisper as WhisperLegacy  # fallback legacy whisper
    except Exception as e:
        logger.warning("openai-whisper unavailable: %s", e)
else:
    logger.info("Local Whisper disabled (USE_LOCAL_WHISPER=0); prod will use Twilio Gather.")
from bs4 import BeautifulSoup
import wikipedia
from googlesearch import search
from typing import Optional, Dict, List, Tuple

from twilio.twiml.voice_response import VoiceResponse, Gather

# ========== TTS CACHING SYSTEM ==========

class TTSCacheManager:
    """Manages TTS audio file caching to reduce ElevenLabs API calls"""
    
    def __init__(self, cache_dir: str = "static/tts_cache"):
        self.cache_dir = cache_dir
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "tts_calls": 0,
            "total_chars_synthesized": 0,
            "total_cached_files": 0
        }
        self._ensure_cache_dir()
        self._load_stats()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _load_stats(self):
        """Load existing stats from cache directory"""
        try:
            stats_file = os.path.join(self.cache_dir, "cache_stats.json")
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    saved_stats = json.load(f)
                    self.stats.update(saved_stats)
        except Exception as e:
            print(f"[CACHE] Error loading stats: {e}")
    
    def _save_stats(self):
        """Save stats to cache directory"""
        try:
            stats_file = os.path.join(self.cache_dir, "cache_stats.json")
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"[CACHE] Error saving stats: {e}")
    
    def canonicalize_text(self, text: str) -> str:
        """Normalize text for consistent cache keys"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove emojis and special characters
        text = re.sub(r'[^\w\s\-.,!?]', '', text)
        
        # Standardize punctuation
        text = text.replace('!', '.').replace('?', '.')
        
        # Convert numbers to digits (e.g., "twelve" -> "12")
        number_words = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
            'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
            'eighteen': '18', 'nineteen': '19', 'twenty': '20'
        }
        
        words = text.lower().split()
        normalized_words = []
        for word in words:
            if word in number_words:
                normalized_words.append(number_words[word])
            else:
                normalized_words.append(word)
        
        return ' '.join(normalized_words)
    
    def get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        canonical = self.canonicalize_text(text)
        # Include voice settings in cache key
        voice_config = f"{ELEVENLABS_VOICE_ID}_{ELEVENLABS_MODEL}_{ELEVENLABS_STABILITY}_{ELEVENLABS_SIMILARITY_BOOST}"
        combined = f"{voice_config}:{canonical}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def get_cached_file(self, text: str) -> Optional[str]:
        """Get cached file path if exists"""
        cache_key = self.get_cache_key(text)
        file_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        
        if os.path.exists(file_path):
            self.stats["cache_hits"] += 1
            self._save_stats()
            print(f"[CACHE] HIT: {text[:50]}... -> {cache_key}.mp3")
            return file_path
        else:
            self.stats["cache_misses"] += 1
            self._save_stats()
            print(f"[CACHE] MISS: {text[:50]}... -> {cache_key}.mp3")
            return None
    
    def cache_file(self, text: str, file_path: str):
        """Cache a generated file"""
        cache_key = self.get_cache_key(text)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        
        try:
            if os.path.exists(file_path) and not os.path.exists(cache_path):
                shutil.copy2(file_path, cache_path)
                self.stats["total_cached_files"] += 1
                self._save_stats()
                print(f"[CACHE] STORED: {text[:50]}... -> {cache_key}.mp3")
        except Exception as e:
            print(f"[CACHE] Error caching file: {e}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate_percent": round(hit_rate, 1),
            "tts_calls": self.stats["tts_calls"],
            "total_chars_synthesized": self.stats["total_chars_synthesized"],
            "total_cached_files": self.stats["total_cached_files"],
            "cache_dir": self.cache_dir
        }

    def find_cached_path(self, text: str) -> Optional[str]:
        """Return absolute path to cached mp3 if present for text."""
        try:
            cache_key = self.get_cache_key(text)
            path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
            return path if os.path.exists(path) else None
        except Exception as e:
            print(f"[CACHE] find_cached_path error: {e}")
            return None

    def invalidate(self, text: str) -> bool:
        """Delete cached mp3 for text if exists."""
        try:
            p = self.find_cached_path(text)
            deleted_any = False
            if p and os.path.exists(p):
                os.remove(p)
                deleted_any = True
                print(f"[CACHE] INVALIDATED: {os.path.basename(p)} for '{text[:50]}...' ")

            # Also remove legacy md5-named file if present (older cache path)
            try:
                legacy_md5 = _tts_cache_filename_for(text)
                legacy_path = os.path.join(app.static_folder, CACHE_SUBDIR, legacy_md5)
                if os.path.exists(legacy_path):
                    os.remove(legacy_path)
                    deleted_any = True
                    print(f"[CACHE] INVALIDATED (legacy): {legacy_md5} for '{text[:50]}...' ")
            except Exception:
                pass

            return deleted_any
        except Exception as e:
            print(f"[CACHE] invalidate error: {e}")
            return False

    def regenerate(self, text: str, job_id: str | None = None, service: str = "TTS") -> Optional[str]:
        """Invalidate then re-synthesize and cache; return public URL."""
        try:
            self.invalidate(text)
            url = tts_line_url(text, None, get_base_url(), job_id, service)
            return url
        except Exception as e:
            print(f"[CACHE] regenerate error: {e}")
            return None
    
    def record_tts_call(self, chars_synthesized: int):
        """Record a TTS API call"""
        self.stats["tts_calls"] += 1
        self.stats["total_chars_synthesized"] += chars_synthesized
        self._save_stats()
    
    def prewarm_common_phrases(self):
        """Prewarm cache with common phrases"""
        common_phrases = [
            "Thanks for calling our store. How can I help you today?",
            "One moment while I check that for you.",
            "I'm sorry, I didn't catch that. Could you repeat it?",
            "I'll connect you to an associate who can help with that.",
            "Is there anything else I can help you with today?",
            "Thanks, I'll send those coupons now.",
            "I'm sorry, we're experiencing technical difficulties. Please call back in a moment.",
            "Our store hours are 7 AM to 10 PM, seven days a week.",
            "Yes, we have that in stock.",
            "I'm sorry, that item is currently out of stock."
        ]
        
        print(f"[CACHE] Prewarming {len(common_phrases)} common phrases...")
        for phrase in common_phrases:
            if not self.get_cached_file(phrase):
                # Generate and cache the phrase
                try:
                    result = elevenlabs_tts_to_file(phrase, f"prewarm_{self.get_cache_key(phrase)}.mp3")
                    if result and os.path.exists(result):
                        self.cache_file(phrase, result)
                except Exception as e:
                    print(f"[CACHE] Error prewarming '{phrase}': {e}")

# Initialize cache manager
CACHE_MANAGER = TTSCacheManager()

# ========== CREDIT TRACKING SYSTEM ==========

class CreditTracker:
    """Tracks estimated credit usage for various services"""
    
    def __init__(self):
        self.active_calls = {}
        self.daily_usage = defaultdict(int)
        self.service_breakdown = defaultdict(int)
        self.log_file = "call_credits.log"
    
    def start_call(self, call_id: str):
        """Start tracking a new call"""
        self.active_calls[call_id] = {
            "start_time": datetime.now(),
            "credits_used": 0,
            "services_used": defaultdict(int)
        }
        print(f"[CREDIT_TRACK] Call {call_id} STARTED")
    
    def log_tts_usage(self, call_id: str, text: str, service: str = "TTS"):
        """Log TTS usage for a call"""
        if call_id not in self.active_calls:
            return
        
        # Estimate credits based on character count
        chars = len(text)
        estimated_credits = max(1, chars // 100)  # Rough estimate
        
        self.active_calls[call_id]["credits_used"] += estimated_credits
        self.active_calls[call_id]["services_used"][service] += estimated_credits
        
        # Update daily totals
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_usage[today] += estimated_credits
        self.service_breakdown[service] += estimated_credits
        
        # Log to file
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} | {call_id} | {service} | {chars} chars | {estimated_credits} credits\n")
        
        print(f"[CREDIT_TRACK] {call_id} | {service} | {chars} chars | {estimated_credits} credits")
    
    def end_call(self, call_id: str):
        """End tracking for a call"""
        if call_id not in self.active_calls:
            return
        
        call_data = self.active_calls[call_id]
        total_credits = call_data["credits_used"]
        duration = datetime.now() - call_data["start_time"]
        
        print(f"[CREDIT_TRACK] Call {call_id} ENDED - Characters: {total_credits * 100}, Credits: {total_credits}")
        
        # Log final call summary
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} | {call_id} | CALL_END | {total_credits} total credits | {duration.total_seconds():.1f}s\n")
        
        del self.active_calls[call_id]
    
    def get_daily_summary(self) -> Dict:
        """Get daily credit usage summary"""
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "date": today,
            "total_credits": self.daily_usage[today],
            "active_calls": len(self.active_calls)
        }
    
    def get_call_summary(self, call_id: str) -> Dict:
        """Get summary for a specific call"""
        if call_id not in self.active_calls:
            return {"error": "Call not found"}
        
        call_data = self.active_calls[call_id]
        return {
            "call_id": call_id,
            "credits_used": call_data["credits_used"],
            "services_used": dict(call_data["services_used"]),
            "duration": str(datetime.now() - call_data["start_time"])
        }
    
    def get_service_breakdown(self) -> Dict:
        """Get breakdown by service"""
        return dict(self.service_breakdown)

# Initialize credit tracker
credit_tracker = CreditTracker()

def play_cached(text: str) -> Optional[str]:
    """Play cached audio if available, return file path or None"""
    cached_file = CACHE_MANAGER.get_cached_file(text)
    if cached_file:
        return static_file_url(cached_file.replace("static/", ""))
    return None

def tts_say(text: str, job_id: str = None) -> str:
    """Generate TTS audio and cache it, return file URL"""
    # Check cache first
    cached_url = play_cached(text)
    if cached_url:
        return cached_url
    
    # Generate new audio
    filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    result = elevenlabs_tts_to_file(text, filename, job_id, "TTS")
    
    if result:
        # Cache the generated file
        CACHE_MANAGER.cache_file(text, result)
        CACHE_MANAGER.record_tts_call(len(text))
        return static_file_url(filename)
    else:
        # Fallback to error message
        return static_file_url("tts_cache/err_global.mp3")

def sandwich_response(start_text: str, dynamic_text: str, end_text: str, job_id: str = None) -> List[str]:
    """Create a sandwich response: cached start + dynamic middle + cached end"""
    urls = []
    
    # Start with cached audio
    start_url = play_cached(start_text)
    if start_url:
        urls.append(start_url)
    else:
        # Generate and cache start
        start_url = tts_say(start_text, job_id)
        urls.append(start_url)
    
    # Dynamic middle (always generate)
    middle_url = tts_say(dynamic_text, job_id)
    urls.append(middle_url)
    
    # End with cached audio
    end_url = play_cached(end_text)
    if end_url:
        urls.append(end_url)
    else:
        # Generate and cache end
        end_url = tts_say(end_text, job_id)
        urls.append(end_url)
    
    return urls

# Import shared data manager
try:
    from shared_data_manager import shared_data
    SHARED_DATA_AVAILABLE = True
    print("[INFO] Shared data manager loaded successfully")
except ImportError:
    SHARED_DATA_AVAILABLE = False
    print("[WARNING] shared_data_manager.py not found - using default data")
from openai import OpenAI

# Import comprehensive grocery department routing
try:
    from grocery_departments import (
        GROCERY_DEPT_RULES,
        GROCERY_AMBIGUOUS_ITEMS,
        classify_grocery_department,
        get_grocery_department_candidates
    )
    GROCERY_ROUTING_AVAILABLE = True
except ImportError:
    GROCERY_ROUTING_AVAILABLE = False
    print("[WARNING] grocery_departments.py not found - using basic routing only")

# Import inventory system
try:
    from inventory_system import (
        search_inventory,
        get_item_by_sku,
        check_stock,
        get_price,
        get_department_summary,
        generate_simulated_inventory_response,
        InventoryItem,
        InventorySearchResult
    )
    INVENTORY_AVAILABLE = True
    print("[INFO] Inventory system loaded successfully")
except ImportError:
    INVENTORY_AVAILABLE = False
    print("[WARNING] inventory_system.py not found - inventory features disabled")
    def search_inventory(search_term: str):
        return None
    def get_item_by_sku(sku: str):
        return None
    def check_stock(sku: str):
        return False, 0
    def get_price(sku: str):
        return None
    def get_department_summary(department: str):
        return {}
    def generate_simulated_inventory_response(search_term: str):
        return ("Unknown Item", "Grocery", 0.0, 0)

# Import pharmacy system
try:
    from pharmacy_system import (
        handle_pharmacy_query,
        get_prescription_by_rx,
        get_prescriptions_by_phone,
        PharmacyQuery,
        Prescription
    )
    PHARMACY_AVAILABLE = True
    print("[INFO] Pharmacy system loaded successfully")
except ImportError:
    PHARMACY_AVAILABLE = False
    print("[WARNING] pharmacy_system.py not found - pharmacy features disabled")
    def handle_pharmacy_query(query: str):
        return None
    def get_prescription_by_rx(rx_number: str):
        return None
    def get_prescriptions_by_phone(phone: str):
        return []

# Import coupon system
try:
    from coupon_system import handle_coupon_query, CouponQuery, CouponManager
    COUPON_AVAILABLE = True
    print("[INFO] Coupon system loaded successfully")
except ImportError:
    COUPON_AVAILABLE = False
    print("[WARNING] coupon_system.py not found - coupon features disabled")
    def handle_coupon_query(query: str):
        return None

# Credit tracking system
CALL_CREDITS = {}  # Store credit usage per call

def get_elevenlabs_usage():
    """Get current ElevenLabs character count"""
    try:
        if not ELEVENLABS_API_KEY:
            return None
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("character_count", 0)
        else:
            print(f"[CREDIT_TRACK] API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[CREDIT_TRACK] Error getting usage: {e}")
        return None

def log_call_credits(call_id, phase="start"):
    """Log credit usage for a call"""
    try:
        usage = get_elevenlabs_usage()
        if usage is not None:
            if phase == "start":
                CALL_CREDITS[call_id] = {"start": usage, "end": None}
                print(f"[CREDIT_TRACK] Call {call_id} STARTED - Characters: {usage:,}")
            elif phase == "end":
                if call_id in CALL_CREDITS:
                    CALL_CREDITS[call_id]["end"] = usage
                    start_usage = CALL_CREDITS[call_id]["start"]
                    usage_diff = usage - start_usage
                    print(f"[CREDIT_TRACK] Call {call_id} ENDED - Characters: {usage:,} (used: {usage_diff:,})")
                    
                    # Log to file for persistent tracking
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "call_id": call_id,
                        "start_usage": start_usage,
                        "end_usage": usage,
                        "usage_diff": usage_diff
                    }
                    
                    with open("call_credits.log", "a") as f:
                        f.write(json.dumps(log_entry) + "\n")
                else:
                    print(f"[CREDIT_TRACK] Warning: No start record for call {call_id}")
    except Exception as e:
        print(f"[CREDIT_TRACK] Error logging credits: {e}")

def schedule_end_credit_tracking(call_id, delay_seconds=60):
    """Schedule credit tracking after call ends with delay"""
    def delayed_tracking():
        time.sleep(delay_seconds)
        log_call_credits(call_id, "end")
    
    threading.Thread(target=delayed_tracking, daemon=True).start()

def get_elevenlabs_usage():
    """Get current ElevenLabs character count"""
    try:
        if not ELEVENLABS_API_KEY:
            return None
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("character_count", 0)
        else:
            print(f"[CREDIT_TRACK] API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[CREDIT_TRACK] Error getting usage: {e}")
        return None

def log_call_credits(call_id, phase="start"):
    """Log credit usage for a call"""
    try:
        usage = get_elevenlabs_usage()
        if usage is not None:
            if phase == "start":
                CALL_CREDITS[call_id] = {"start": usage, "end": None}
                print(f"[CREDIT_TRACK] Call {call_id} STARTED - Characters: {usage:,}")
            elif phase == "end":
                if call_id in CALL_CREDITS:
                    CALL_CREDITS[call_id]["end"] = usage
                    start_usage = CALL_CREDITS[call_id]["start"]
                    usage_diff = usage - start_usage
                    print(f"[CREDIT_TRACK] Call {call_id} ENDED - Characters: {usage:,} (used: {usage_diff:,})")
                    
                    # Log to file for persistent tracking
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "call_id": call_id,
                        "start_usage": start_usage,
                        "end_usage": usage,
                        "usage_diff": usage_diff
                    }
                    
                    with open("call_credits.log", "a") as f:
                        f.write(json.dumps(log_entry) + "\n")
                else:
                    print(f"[CREDIT_TRACK] Warning: No start record for call {call_id}")
    except Exception as e:
        print(f"[CREDIT_TRACK] Error logging credits: {e}")

def schedule_end_credit_tracking(call_id, delay_seconds=60):
    """Schedule credit tracking after call ends with delay"""
    def delayed_tracking():
        time.sleep(delay_seconds)
        log_call_credits(call_id, "end")
    
    threading.Thread(target=delayed_tracking, daemon=True).start()

FILLER_FILES = [
    "filler1.mp3","filler2.mp3","filler3.mp3","filler4.mp3",
    "filler6.mp3","filler7.mp3","filler9.mp3","filler10.mp3",
    "filler11.mp3","filler14.mp3","filler15.mp3","filler17.mp3",
    "filler18.mp3","filler19.mp3","filler20.mp3",
]

load_dotenv()
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL    = os.getenv("ELEVENLABS_MODEL", "eleven_monolingual_v1")
ELEVENLABS_STABILITY = float(os.getenv("ELEVENLABS_STABILITY", "0.5"))
ELEVENLABS_SIMILARITY_BOOST = float(os.getenv("ELEVENLABS_SIMILARITY_BOOST", "0.75"))
TWILIO_SID          = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN        = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER  = os.getenv("TWILIO_FROM_NUMBER", "").strip()
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "").strip()

PUBLIC_BASE_URL     = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
USE_FILLER = os.getenv("USE_FILLER", "0") == "1"

HOLDY_TINY_CDN = os.getenv("HOLDY_TINY_CDN", "https://call-router-audio-2526.twil.io/holdy_tiny.mp3")
HOLDY_MID_CDN  = os.getenv("HOLDY_MID_CDN",  "https://call-router-audio-2526.twil.io/holdy_mid.mp3")
HOLD_BG_CDN    = os.getenv("HOLD_BG_CDN", "").strip()
# NEW: short chirp to play right after clarification prompts
HOLDY_CLARIFY_CDN = os.getenv("HOLDY_CLARIFY_CDN", HOLDY_TINY_CDN)

# NEW: operator routing config
OPERATOR_NUMBER = os.getenv("OPERATOR_NUMBER", "").strip()
try:
    DEPT_DIAL_MAP = json.loads(os.getenv("DEPT_DIAL_MAP_JSON","{}") or "{}")
except Exception:
    DEPT_DIAL_MAP = {}

DEFAULT_LANG = (os.getenv("DEFAULT_LANG","en") or "en").lower()  # greeting language only; detection still runs

client = OpenAI(api_key=OPENAI_API_KEY)

def _strip_env(name: str, default: str) -> str:
    val = os.getenv(name, default)
    return val.strip() if isinstance(val, str) else str(default)

def safe_int_env(name: str, default: int) -> int:
    raw = _strip_env(name, str(default))
    try: return int(float(raw))
    except (ValueError, TypeError):
        print(f"[WARN] Invalid value for {name}='{raw}', using default={default}")
        return default

def safe_float_env(name: str, default: float) -> float:
    raw = _strip_env(name, str(default))
    try: return float(raw)
    except (ValueError, TypeError):
        print(f"[WARN] Invalid value for {name}='{raw}', using default={default}")
        return default

def clamp_int(v: int, lo: int, hi: int, name: str) -> int:
    if v < lo:
        print(f"[WARN] {name} too small ({v}); clamping to {lo}")
        return lo
    if v > hi:
        print(f"[WARN] {name} too large ({v}); clamping to {hi}")
        return hi
    return v

def safe_bool_env(name: str, default: bool) -> bool:
    raw = _strip_env(name, "1" if default else "0")
    return str(raw).strip().lower() in {"1","true","t","yes","y","on"}

RECORD_BEEP      = safe_bool_env("RECORD_BEEP", False)
POLL_PAUSE       = clamp_int(safe_int_env("POLL_PAUSE", 1), 0, 5, "POLL_PAUSE")  # was 0, increased to reduce polling frequency

# === SNAPPY DEFAULTS (tuned for noisy environments) ===
USE_GATHER_MAIN  = safe_bool_env("USE_GATHER_MAIN", True)  # NEW: prefer Twilio ASR for first utterance
MAIN_TIMEOUT     = clamp_int(safe_int_env("REC_TIMEOUT", 1), 1, 60, "REC_TIMEOUT")   # was 3
MAIN_MAXLEN      = clamp_int(safe_int_env("REC_MAXLEN", 5), 1, 120, "REC_MAXLEN")    # was 8, reduced for faster response
CONF_TIMEOUT     = clamp_int(safe_int_env("CONFIRM_TIMEOUT", 5), 1, 10, "CONFIRM_TIMEOUT")
CONF_MAXLEN      = clamp_int(safe_int_env("CONFIRM_MAXLEN", 3), 1, 8, "CONFIRM_MAXLEN")

MIN_ASR_LOGPROB  = safe_float_env("MIN_ASR_LOGPROB", -0.35)
# Enforce a minimum gap so the tiny chirp can't stutter back-to-back.
# If you REALLY want zero, set HOLD_MIN_GAP_FORCE_ZERO=1 in .env.
HOLD_MIN_GAP_FORCE_ZERO = safe_bool_env("HOLD_MIN_GAP_FORCE_ZERO", False)
HOLD_MIN_GAP_SEC = 0.0 if HOLD_MIN_GAP_FORCE_ZERO else max(1.2, safe_float_env("HOLD_MIN_GAP_SEC", 1.2))
CORRECTION_HOPS_MAX = clamp_int(safe_int_env("CORRECTION_HOPS_MAX", 2), 1, 5, "CORRECTION_HOPS_MAX")

# --- ASR / Twilio Gather tuning (configurable via env) ---
GATHER_LANGUAGE = os.getenv("GATHER_LANGUAGE", "en-US")

def gather_kwargs(**overrides):
    base = dict(
        input="speech dtmf",
        language="en-US",
        speechModel="phone_call",
        speechTimeout=3,  # int seconds
        profanityFilter="false",
        bargeInOnSpeech="true",
        actionOnEmptyResult=True,
        method="POST"
    )
    base.update(overrides)
    return base

def log_effective_config():
    print("[CONFIG] PUBLIC_BASE_URL =", PUBLIC_BASE_URL or "(auto from request.url_root)")
    print("[CONFIG] USE_FILLER      =", USE_FILLER)
    print("[CONFIG] HOLDY_TINY_CDN  =", HOLDY_TINY_CDN)
    print("[CONFIG] HOLDY_MID_CDN   =", HOLDY_MID_CDN)
    print("[CONFIG] HOLDY_CLARIFY_CDN =", HOLDY_CLARIFY_CDN)
    print("[CONFIG] HOLD_BG_CDN     =", HOLD_BG_CDN or "(disabled)")
    print("[CONFIG] POLL_PAUSE      =", POLL_PAUSE)
    print("[CONFIG] MAIN_TIMEOUT    =", MAIN_TIMEOUT)
    print("[CONFIG] MAIN_MAXLEN     =", MAIN_MAXLEN)
    print("[CONFIG] CONF_TIMEOUT    =", CONF_TIMEOUT)
    print("[CONFIG] CONF_MAXLEN     =", CONF_MAXLEN)
    print("[CONFIG] RECORD_BEEP     =", RECORD_BEEP)
    print("[CONFIG] MIN_ASR_LOGPROB =", MIN_ASR_LOGPROB)
    print("[CONFIG] HOLD_MIN_GAP_SEC =", HOLD_MIN_GAP_SEC)
    print("[CONFIG] CORRECTION_HOPS_MAX =", CORRECTION_HOPS_MAX)
    print("[CONFIG] OPERATOR_NUMBER =", OPERATOR_NUMBER or "(unset)")
    print("[CONFIG] DEPT_DIAL_MAP   =", DEPT_DIAL_MAP or "(empty)")
    print("[CONFIG] USE_GATHER_MAIN =", USE_GATHER_MAIN)  # NEW

def get_store_config():
    """Get store configuration from shared data or fallback to default"""
    if SHARED_DATA_AVAILABLE:
        try:
            # Get departments from shared data
            departments = shared_data.get_departments()
            dept_dict = {}
            for dept in departments:
                if dept.get('is_active', True):
                    dept_dict[dept['name']] = dept.get('phone_extension', '')
            
            # Get store info
            store_info = shared_data.get_store_info()
            
            return {
                "departments": dept_dict,
                "store_info": store_info
            }
        except Exception as e:
            print(f"[WARNING] Error getting shared store config: {e}")
    
    # Fallback to default config
    return {
        "departments": {
            "Grocery": "",
            "Meat & Seafood": "",
            "Deli": "",
            "Bakery": "",
            "Electronics": "",
            "Home and Garden": "",
            "Health and Beauty": "",
            "Pet Supplies": "",
            "Customer Service": ""
        },
        "store_info": {
            "name": "Your Store",
            "address": "123 Main Street",
            "phone": "(555) 123-4567",
            "greeting_message": "Thank you for calling our store. How can I help you today?"
        }
    }

# Get initial store config
store_config = get_store_config()

# --- Deterministic dept classification (pre-LLM) ---
# Ensure we have a Clothing dept (add your preferred label if different)
store_config["departments"].setdefault("Clothing", "")
# Add Office and Stationery for office items routing
store_config["departments"].setdefault("Office and Stationery", "")

SHOE_TERMS    = r"shoe|sneaker|trainer|boot|cleat|sandal|heel|loafer|samba|air force|jordan|converse|adidas|nike|new balance"
APPAREL_TERMS = r"beanie|hat|cap|glove|scarf|hoodie|sweater|jeans|carhartt|levi'?s|501"
BIKE_TERMS    = r"bike|bicycle|biking|bmx|kids? bike"

DEPT_RULES = [
    (re.compile(rf"\b({SHOE_TERMS})s?\b", re.I), "Clothing"),
    (re.compile(rf"\b({APPAREL_TERMS})s?\b", re.I), "Clothing"),
    (re.compile(rf"\b({BIKE_TERMS})\b", re.I), "Home and Garden"),  # change to "Sporting Goods" if you add it
]

def classify_department_rule_based(text: str) -> str | None:
    t = (text or "").lower()
    
    print(f"[DEBUG] classify_department_rule_based called with: '{text}' -> '{t}'")
    print(f"[DEBUG] GROCERY_ROUTING_AVAILABLE = {GROCERY_ROUTING_AVAILABLE}")
    
    # Use comprehensive grocery routing if available
    if GROCERY_ROUTING_AVAILABLE:
        grocery_dept = classify_grocery_department(t)
        print(f"[DEBUG] classify_grocery_department returned: '{grocery_dept}'")
        if grocery_dept:
            print(f"[DEBUG] Using grocery department: {grocery_dept}")
            return grocery_dept
    
    # Fall back to original rules
    for rx, dept in DEPT_RULES:
        if rx.search(t):
            print(f"[DEBUG] Found match in DEPT_RULES: {dept}")
            return dept
    
    print(f"[DEBUG] No department found, returning None")
    return None

def classify_department_with_internet_fallback(text: str, job_id: str = None) -> tuple[str, bool]:
    """
    AI-powered department classification using GPT-4 as the primary method.
    Returns (department, used_internet_search)
    """
    classify_start_time = time.time()
    if not text or not text.strip():
        return "Customer Service", False
    
    # Use AI classification as the PRIMARY method for all products
    print(f"[AI CLASSIFY] Using GPT-4 to classify: '{text}'")
    ai_start_time = time.time()
    ai_dept = classify_product_with_ai(text)
    ai_time = time.time() - ai_start_time
    print(f"[TIMING] AI classification took {ai_time:.3f}s")
    
    if ai_dept and ai_dept != "Customer Service":
        classify_total_time = time.time() - classify_start_time
        print(f"[AI CLASSIFY] GPT-4 classified '{text}' as '{ai_dept}' (total classify time: {classify_total_time:.3f}s)")
        return ai_dept, False
    
    # Only use rule-based classification as a fallback for very common items
    # This is just for speed on items we're 100% confident about
    if is_very_common_product(text):
        print(f"[RULE-BASED] Using rule-based classification for very common product: '{text}'")
        local_dept = classify_department_rule_based(text)
        if local_dept and local_dept != "Customer Service":
            classify_total_time = time.time() - classify_start_time
            print(f"[RULE-BASED] Rule-based classification result: '{local_dept}' (total classify time: {classify_total_time:.3f}s)")
            return local_dept, False
    
    # Final fallback to internet search for unknown products
    if should_use_internet_search(text):
        print(f"[SEARCH] AI classification failed for '{text}', using internet search")
        search_result = search_product_online(text)
        classify_total_time = time.time() - classify_start_time
        print(f"[SEARCH] Internet search result: '{search_result['department']}' (total classify time: {classify_total_time:.3f}s)")
        return search_result['department'], True
    
    classify_total_time = time.time() - classify_start_time
    print(f"[TIMING] Classification fallback to Customer Service (total time: {classify_total_time:.3f}s)")
    return "Customer Service", False

def is_very_common_product(text: str) -> bool:
    """
    Check if this is a very common product that we can confidently classify with rules.
    Only the most basic, obvious items should be here.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Only the most basic, obvious items that we're 100% confident about
    very_common_products = [
        # Basic beverages
        "milk", "water", "soda", "pop", "coke", "pepsi",
        # Basic produce
        "banana", "apple", "orange", "lettuce", "tomato",
        # Basic bread
        "bread", "bagel", "muffin",
        # Basic snacks
        "chips", "crackers", "cookies",
        # Basic household
        "soap", "shampoo", "toothpaste"
    ]
    
    # Check if the text contains any very common product keywords
    for product in very_common_products:
        if product in text_lower:
            return True
    
    return False

def is_known_product(text: str) -> bool:
    """
    Check if a product is likely to be in our rule-based system.
    Returns True if it's a common product we have rules for.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Special case: if it contains "chicken" but is not a common meat product, use AI
    if "chicken" in text_lower and not any(common in text_lower for common in ["chicken breast", "chicken thigh", "chicken wing", "chicken leg", "chicken meat", "chicken filet", "chicken tender"]):
        return False
    
    # Common products we have rules for
    known_products = [
        # Beverages
        "mountain dew", "coke", "pepsi", "sprite", "dr pepper", "soda", "pop",
        # Dairy
        "milk", "cheese", "yogurt", "butter", "eggs",
        # Produce
        "banana", "apple", "orange", "lettuce", "tomato", "carrot",
        # Meat (but not chicken grit, chicken feed, etc.)
        "beef", "pork", "fish", "turkey",
        # Bread
        "bread", "bagel", "muffin", "donut",
        # Snacks
        "chips", "crackers", "cookies", "candy",
        # Household
        "soap", "shampoo", "toothpaste", "paper towels",
        # Hardware
        "hammer", "screwdriver", "paint", "tools"
    ]
    
    # Check if the text contains any known product keywords
    for product in known_products:
        if product in text_lower:
            return True
    
    # If it's a short phrase (1-3 words), it's more likely to be unknown
    if len(text.split()) <= 3:
        return False
    
    return False

# Cache for AI classifications to avoid repeated API calls
AI_CLASSIFICATION_CACHE = {}  # Cache cleared to force reclassification with new Pet Supplies rules

def classify_product_with_ai(product_name: str) -> str:
    """
    Use GPT-4 to intelligently classify any product into a grocery store department.
    This replaces the need for manual rule-based classification.
    """
    # Check cache first
    cache_key = product_name.lower().strip()
    if cache_key in AI_CLASSIFICATION_CACHE:
        print(f"[AI CLASSIFY] Cache hit for '{product_name}' -> {AI_CLASSIFICATION_CACHE[cache_key]}")
        return AI_CLASSIFICATION_CACHE[cache_key]
    
    try:
        # Create a comprehensive prompt for product classification
        prompt = f"""
You are an expert grocery store employee who knows exactly where every product belongs in this specific store.

Given the product: "{product_name}"

Classify it into ONE of these departments:
- Grocery (human food items, snacks, beverages, canned goods, condiments, household consumables like toilet paper, paper towels, dish soap)
- Meat & Seafood (fresh meat, fish, poultry, deli meats)
- Deli (prepared foods, sliced meats/cheeses, rotisserie chicken, hot meals)
- Bakery (fresh baked goods like bread, pastries, cakes, cookies)
- Electronics (phones, computers, chargers, TVs, gaming consoles, office electronics)
- Home and Garden (tools, hardware, plants, garden supplies, outdoor items, home improvement)
- Pet Supplies (pet food, pet treats, pet toys, pet care items, pet supplies, pet litter, pet grooming)
- Health and Beauty (personal care, cosmetics, vitamins, over-the-counter medicine)
- Customer Service (returns, complaints, general inquiries)
- Clothing (apparel, shoes, accessories)
- Office and Stationery (office supplies, paper, pens, notebooks)
- Toys & Games (toys, games, puzzles, board games, dice, playing cards, entertainment items)

CRITICAL RULES:
1. ALL pet-related items (pet food, pet treats, pet toys, pet supplies, pet care) go to "Pet Supplies"
2. Pet food brands like Purina, Fancy Feast, Iams, Science Diet, etc. go to "Pet Supplies"
3. Cat food, dog food, bird food, fish food, etc. go to "Pet Supplies"
4. Pet litter, pet toys, pet grooming items go to "Pet Supplies"
5. ALL gaming items (dice, board games, puzzles, toys, playing cards) go to "Toys & Games"
6. Gaming consoles and video games go to "Electronics"

Examples:
- "Purina cat food" -> Pet Supplies (pet food)
- "Fancy Feast" -> Pet Supplies (pet food)
- "Dog treats" -> Pet Supplies (pet supplies)
- "Cat litter" -> Pet Supplies (pet supplies)
- "Mountain Dew" -> Grocery (human beverage)
- "Shampoo" -> Health and Beauty (personal care)
- "Dice" -> Toys & Games (gaming)
- "Board games" -> Toys & Games (gaming)
- "Puzzles" -> Toys & Games (gaming)
- "Playing cards" -> Toys & Games (gaming)
- "Toys" -> Toys & Games (entertainment)

Respond with ONLY the department name, nothing else.
"""

        # Call GPT-4 for classification
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a grocery store expert. Respond with only the department name."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.1  # Low temperature for consistent classification
        )
        
        department = response.choices[0].message.content.strip()
        
        # Clean up the response
        department = re.sub(r'[^\w\s&]', '', department).strip()
        
        # Validate the department is in our list
        valid_departments = [
            "Grocery", "Meat & Seafood", "Deli", "Bakery", "Electronics", 
            "Home and Garden", "Health and Beauty", "Pet Supplies", "Customer Service", 
            "Clothing", "Office and Stationery", "Toys & Games"
        ]
        
        if department in valid_departments:
            # Cache the result
            AI_CLASSIFICATION_CACHE[cache_key] = department
            return department
        else:
            print(f"[AI CLASSIFY] Invalid department '{department}' for '{product_name}', defaulting to Customer Service")
            AI_CLASSIFICATION_CACHE[cache_key] = "Customer Service"
            return "Customer Service"
            
    except Exception as e:
        print(f"[AI CLASSIFY] Error classifying '{product_name}': {e}")
        AI_CLASSIFICATION_CACHE[cache_key] = "Customer Service"
        return "Customer Service"

def clean_item_label(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"^(i\s*am|i'?m)\s+looking\s+for\s+", "", s, flags=re.I)
    s = re.sub(r"^(looking\s+for|need|want)\s+", "", s, flags=re.I)
    s = re.sub(r"[.?!]+$", "", s)
    return " ".join(s.split())[:80]

# Use a multilingual model by default so language detection actually works.
# You can override via WHISPER_MODEL env (e.g., "medium" or "large-v3").
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "small")

def _get_whisper_impl():
    if not USE_LOCAL_WHISPER:
        return None
    if FasterWhisper is not None:
        def transcribe_faster(path):
            model = FasterWhisper(WHISPER_MODEL_NAME, device="cpu", compute_type="int8")
            segments, info = model.transcribe(path, beam_size=2, vad_filter=True, language=None)
            return " ".join(s.text for s in segments if getattr(s, "text", None)), getattr(info, "language", "en"), getattr(info, "language_probability", 0.0)
        return transcribe_faster
    if WhisperLegacy is not None:
        def transcribe_legacy(path):
            model = WhisperLegacy.load_model(WHISPER_MODEL_NAME)
            res = model.transcribe(path)
            return (res.get("text") or "").strip(), "en", 1.0
        return transcribe_legacy
    return None


# Global error handlers for Twilio webhooks (fix 12300)
@app.errorhandler(404)
def _e404(e):
    tw = VoiceResponse()
    tw.play(public_url("/static/tts_cache/holdy_tiny.mp3"))
    return xml_response(tw)

@app.errorhandler(500)
def _e500(e):
    tw = VoiceResponse()
    tw.play(public_url("/static/tts_cache/holdy_tiny.mp3"))
    return xml_response(tw)

@app.after_request
def _force_twiml_xml(resp):
    try:
        body = (resp.get_data(as_text=True) or "").lstrip()
        if body.startswith("<?xml") or body.startswith("<Response"):
            resp.mimetype = "text/xml"
    except Exception:
        pass
    return resp

def ensure_static_dir():
    os.makedirs(app.static_folder, exist_ok=True)

def get_base_url() -> str:
    if PUBLIC_BASE_URL:
        base = PUBLIC_BASE_URL
    else:
        try:
            root = (request.url_root or "").rstrip("/")
            base = "https://" + root[len("http://"):] if root.startswith("http://") else root
        except RuntimeError:
            # Called outside of request context (e.g., during startup)
            base = ""
    return base

# Helper for absolute HTTPS URLs
from urllib.parse import urljoin
PUBLIC_HTTP_BASE = os.getenv("PUBLIC_HTTP_BASE", "").rstrip("/")

def abs_url(path: str) -> str:
    """Always return https absolute URL"""
    if path.startswith("http://") or path.startswith("https://"):
        return path.replace("http://", "https://", 1)
    base = PUBLIC_HTTP_BASE or (request.url_root if request else "")
    return urljoin(base, path).replace("http://", "https://", 1)

def _log_twilio_request(where: str, req=None):
    try:
        if DIAG_TWILIO != 1:
            return
        
        from flask import request
        r = req or request
        
        # Get headers, args, form safely
        headers = dict(r.headers) if hasattr(r, 'headers') else {}
        args = r.args.to_dict(flat=True) if hasattr(r, 'args') and r.args else {}
        form = r.form.to_dict(flat=True) if hasattr(r, 'form') and r.form else {}
        
        # Get raw body safely
        try:
            raw = r.get_data(as_text=True) or ""
        except:
            raw = ""
        
        if not raw and form:
            from urllib.parse import urlencode
            raw = urlencode(form)
        
        raw_len = len(raw) if raw else 0
        
        app.logger.info("[TWILIO %s] headers=%s args=%s form=%s raw_len=%s", 
                       where, headers, args, form, raw_len)
        
    except Exception as e:
        app.logger.error("[TWILIO %s] log-failed: %s", where, e)

def external_base() -> str:
    if PUBLIC_WS_BASE:
        return PUBLIC_WS_BASE
    # request.url_root ends with slash; strip to normalize
    return request.url_root.rstrip("/")

def absolute(url_path: str) -> str:
    if not url_path:
        return external_base()
    if url_path.startswith("http://") or url_path.startswith("https://"):
        return url_path
    if not url_path.startswith("/"):
        url_path = "/" + url_path
    return f"{external_base()}{url_path}"

def build_confirmation_audio_url(filename_or_path: str) -> str:
    path = filename_or_path
    if not path.startswith("/static/"):
        path = f"/static/tts_cache/{path}"
    return public_url(path)

from urllib.parse import urljoin

# --- Redis-backed job state with in-proc fallback ---
from typing import Optional
_redis = None
_fallback_state = {}  # key -> (expires_ts, json_str)

def get_redis():
    global _redis
    if '_redis' in globals() and _redis is not None:
        return _redis
    url = REDIS_URL
    if not url:
        _redis = None
        return None
    from redis import Redis
    _redis = Redis.from_url(url, decode_responses=True, socket_timeout=2, socket_connect_timeout=2)
    return _redis

def _fb_set(key, value, ttl):
    _fallback_state[key] = (time.time() + ttl, json.dumps(value))

def _fb_get(key) -> Optional[dict]:
    item = _fallback_state.get(key)
    if not item:
        return None
    exp, js = item
    if exp < time.time():
        _fallback_state.pop(key, None)
        return None
    return json.loads(js)

def _fb_del(key):
    _fallback_state.pop(key, None)

def save_state(job_id: str, data: dict, ttl_sec: int = 900):
    key = f"job:{job_id}"
    try:
        r = get_redis()
        if r:
            r.setex(key, ttl_sec, json.dumps(data))
        else:
            _fb_set(key, data, ttl_sec)
        current_app.logger.info("[STATE] saved job=%s data=%s", job_id, data)
    except Exception as e:
        current_app.logger.exception("[STATE] ERROR saving job=%s", job_id)
        raise

def load_state(job_id: str) -> dict:
    key = f"job:{job_id}"
    try:
        r = get_redis()
        if r:
            js = r.get(key)
            return json.loads(js) if js else {}
        return _fb_get(key) or {}
    except Exception as e:
        current_app.logger.exception("[STATE] ERROR loading job=%s", job_id)
        return {}

def update_state(job_id: str, updates: dict, ttl_sec: int = 900) -> dict:
    cur = load_state(job_id) or {}
    cur.update(updates)
    save_state(job_id, cur, ttl_sec)
    return cur

def clear_state(job_id: str):
    key = f"job:{job_id}"
    r = get_redis()
    if r:
        r.delete(key)
    _fb_del(key)

def _state_debug(job_id, where):
    try:
        st = load_state(job_id)  # whatever you currently use to read state
    except Exception as e:
        current_app.logger.warning("[STATE] %s job=%s -> READ ERROR: %s", where, job_id, e)
        return
    current_app.logger.info("[STATE] %s job=%s -> %s", where, job_id, st)

# Simple Redis helpers for deterministic job lifecycle
def state_key(job_id: str) -> str:
    return f"job:{job_id}"

def state_get(job_id: str) -> dict:
    r = get_redis()
    if not r:
        return {}
    raw = r.get(state_key(job_id))
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}

def state_set(job_id: str, data: dict, ttl=900):
    r = get_redis()
    if not r:
        return
    r.setex(state_key(job_id), ttl, json.dumps(data))

def _abs_audio(url_or_path: str) -> str:
    # If already absolute https, return as-is; otherwise route through public_url
    if url_or_path.startswith("https://"):
        return url_or_path
    # common case: we stored just a filename like 'ccc7f39....mp3'
    if not url_or_path.startswith("/"):
        url_or_path = f"/static/tts_cache/{url_or_path}"
    return public_url(url_or_path)

def static_file_url(relpath: str) -> str:
    rel = (relpath or "").lstrip("/")
    if rel.startswith("static/"):
        rel = rel[len("static/"):]
    return public_url(f"/static/{rel}")

# --- Twilio XML helper (always text/xml) ---
from flask import make_response
from flask import Response
try:
    from twilio.twiml.voice_response import VoiceResponse
except Exception:
    VoiceResponse = None  # optional import

def xml_response(x):
    """Return TwiML with correct content-type. Accepts str or VoiceResponse."""
    if isinstance(x, VoiceResponse):
        body = str(x)
    else:
        body = str(x)
    body = sanitize_twiml_xml(body)
    from flask import make_response
    resp = make_response(body, 200)
    resp.headers["Content-Type"] = "text/xml; charset=utf-8"
    return resp

CACHE_SUBDIR = "tts_cache"

def _ensure_cache_dir():
    ensure_static_dir()
    cache_dir = os.path.join(app.static_folder, CACHE_SUBDIR)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def _tts_cache_filename_for(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest() + ".mp3"

def elevenlabs_tts_to_file(text: str, filename: str | None = None, job_id: str = None, service: str = "TTS"):
	cache_dir = _ensure_cache_dir()
	if filename is None:
		filename = _tts_cache_filename_for(text)
		out_path = os.path.join(cache_dir, filename)
	else:
		# Normalize to avoid duplicating tts_cache/ in the path
		if os.path.isabs(filename):
			out_path = filename
		elif filename.startswith(f"{CACHE_SUBDIR}/"):
			# Already under tts_cache -> resolve from static folder
			out_path = os.path.join(app.static_folder, filename)
		else:
			# Bare filename -> write inside cache dir
			out_path = os.path.join(cache_dir, filename)
	print(f"[TTS DEBUG] Checking for existing file: {out_path}")
	if os.path.exists(out_path):
		print(f"[TTS DEBUG] File exists, returning: {out_path}")
		return out_path
	
	# Check if we have valid API credentials
	if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY.strip() == "":
		print(f"[TTS ERROR] ElevenLabs API key is missing or empty")
		# Return a fallback URL to prevent infinite loops
		return None
	
	try:
		url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
		headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
		data = {"text": text, "voice_settings": {"stability": 0.4, "similarity_boost": 0.5}}
		r = requests.post(url, headers=headers, json=data, timeout=60)
		r.raise_for_status()
		with open(out_path, "wb") as f:
			f.write(r.content)
		
		# Track credit usage if job_id is provided
		if job_id:
			credit_tracker.log_tts_usage(job_id, text, service)
		
		return out_path
	except requests.exceptions.HTTPError as e:
		if e.response.status_code == 401:
			print(f"[TTS ERROR] ElevenLabs API key is invalid (401 Unauthorized)")
		else:
			print(f"[TTS ERROR] ElevenLabs API error: {e}")
		return None
	except Exception as e:
		print(f"[TTS ERROR] Failed to generate TTS: {e}")
		return None

def tts_line_url(text: str, filename: str | None = None, base_url: str | None = None, job_id: str = None, service: str = "TTS") -> str | None:
	tts_start_time = time.time()
	# Use caching system if available
	if CACHE_MANAGER:
		# Check cache first
		cache_check_start = time.time()
		cached_url = play_cached(text)
		cache_check_time = time.time() - cache_check_start
		if cached_url:
			tts_total_time = time.time() - tts_start_time
			print(f"[TTS CACHE] Using cached audio for: {text[:50]}... (cache check: {cache_check_time:.3f}s, total: {tts_total_time:.3f}s)")
			return cached_url
		
		# Generate new audio and cache it
		tts_gen_start = time.time()
		if filename:
			result = elevenlabs_tts_to_file(text, filename, job_id, service)
			if result is None:
				print(f"[TTS DEBUG] TTS generation failed for filename '{filename}', returning None")
				return None
			mp3_rel = filename
		else:
			mp3_rel = f"{CACHE_SUBDIR}/{_tts_cache_filename_for(text)}"
			result = elevenlabs_tts_to_file(text, mp3_rel, job_id, service)
			if result is None:
				print(f"[TTS DEBUG] TTS generation failed for text hash, returning None")
				return None
		tts_gen_time = time.time() - tts_gen_start
		print(f"[TIMING] TTS generation took {tts_gen_time:.3f}s")
		
		# Cache the generated file
		CACHE_MANAGER.cache_file(text, result)
		CACHE_MANAGER.record_tts_call(len(text))
		
		# If caller passed a path like "tts_cache/foo.mp3", keep it.
		# If it's a bare filename, put it under tts_cache/.
		if "/" not in mp3_rel:
			mp3_rel = f"{CACHE_SUBDIR}/{mp3_rel}"
		
		try:
			final_url = public_url(f"/static/{mp3_rel}")
			print(f"[TTS DEBUG] Returning URL: {final_url}")
			app.logger.info(f"[AUDIO] url={final_url}")
			return final_url
		except Exception as e:
			logger.exception("[AUDIO] Failed to build public URL for %r", f"/static/{mp3_rel}")
			# Provide a safe Twilio-hosted fallback tone so Twilio has something to fetch
			return "https://api.twilio.com/cowbell.mp3"  # harmless short tone
	else:
		# Fallback to original behavior if cache manager not available
		if filename:
			result = elevenlabs_tts_to_file(text, filename, job_id, service)
			if result is None:
				print(f"[TTS DEBUG] TTS generation failed for filename '{filename}', returning None")
				return None
			mp3_rel = filename
		else:
			mp3_rel = f"{CACHE_SUBDIR}/{_tts_cache_filename_for(text)}"
			result = elevenlabs_tts_to_file(text, mp3_rel, job_id, service)
			if result is None:
				print(f"[TTS DEBUG] TTS generation failed for text hash, returning None")
				return None
		
		# If caller passed a path like "tts_cache/foo.mp3", keep it.
		# If it's a bare filename, put it under tts_cache/.
		if "/" not in mp3_rel:
			mp3_rel = f"{CACHE_SUBDIR}/{mp3_rel}"
		
		try:
			final_url = public_url(f"/static/{mp3_rel}")
			print(f"[TTS DEBUG] Returning URL: {final_url}")
			app.logger.info(f"[AUDIO] url={final_url}")
			return final_url
		except Exception as e:
			logger.exception("[AUDIO] Failed to build public URL for %r", f"/static/{mp3_rel}")
			# Provide a safe Twilio-hosted fallback tone so Twilio has something to fetch
			return "https://api.twilio.com/cowbell.mp3"  # harmless short tone

# ========== TTS Regeneration API ==========
@app.route("/api/tts/regenerate", methods=["POST"])
def api_tts_regenerate():
    try:
        data = request.get_json(force=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"ok": False, "error": "text is required"}), 400

        # Optional: dry_run just invalidates without regenerating
        dry_run = bool(data.get("dry_run", False))

        invalidated = CACHE_MANAGER.invalidate(text)
        url = None
        if not dry_run:
            url = CACHE_MANAGER.regenerate(text)

        return jsonify({
            "ok": True,
            "invalidated": bool(invalidated),
            "url": url
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

def twiml_play_tts(vr: VoiceResponse, text: str, filename: str | None = None, job_id: str = None, service: str = "TTS"):
    # If ElevenLabs API key is missing, always use vr.say()
    masked_key = ELEVENLABS_API_KEY[:4] + "…" + ELEVENLABS_API_KEY[-4:] if ELEVENLABS_API_KEY else "None"
    print(f"[TTS DEBUG] ELEVENLABS_API_KEY: '{masked_key}'")
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY.strip() == "":
        print(f"[TTS FALLBACK] No API key, using vr.say() for: {text[:50]}...")
        vr.say(text)
        return
    
    # Try to generate TTS, but if it fails, use vr.say()
    try:
        url = tts_line_url(text, filename, None, job_id, service)
        if url and url != "None":
            vr.play(url)
        else:
            print(f"[TTS FALLBACK] URL is None, using vr.say() for: {text[:50]}...")
            vr.say(text)
    except Exception as e:
        print(f"[TTS FALLBACK] Exception in TTS generation, using vr.say(): {e}")
        vr.say(text)

# ======= Localized prompts =======
MESSAGES = {
    "en": {
        "greet": "Thanks for calling. What can I help you find today?",
        "confirm_prefix": "Got it—did you say:",
        "yes_no": "Sorry, was that a yes or a no?",
        "err_global": "Sorry, we hit a snag. Please call back in a moment.",
        "err_confirm": "Sorry, we had trouble processing that. Goodbye.",
        "no_record": "Sorry, we did not get your message. Goodbye.",
        "reask": "No problem—please tell me again what you're looking for.",
        "reask_cap": "No worries—tell me again what you need so I get it right.",
        "connecting_operator": "Connecting you to an operator now. Thanks for calling.",
    },
    "es": {
        "greet": "Gracias por llamar. ¿Qué puedo ayudarle a encontrar hoy?",
        "confirm_prefix": "Entendido—¿dijo:",
        "yes_no": "Perdón, ¿fue un sí o un no?",
        "err_global": "Lo sentimos, hubo un problema. Por favor, vuelva a llamar en un momento.",
        "err_confirm": "Lo sentimos, hubo un problema con su respuesta. Adiós.",
        "no_record": "Lo sentimos, no recibimos su mensaje. Adiós.",
        "reask": "No hay problema—dígame otra vez qué está buscando.",
        "reask_cap": "Sin problema—repítame lo que necesita para acertar.",
        "connecting_operator": "Le conecto con un operador ahora. Gracias por llamar.",
    }
}

def msg(key: str, lang: str) -> str:
    lang = (lang or "en")[:2]
    
    # Use shared data for greeting message if available
    if key == "greet" and SHARED_DATA_AVAILABLE:
        try:
            store_info = shared_data.get_store_info()
            greeting = store_info.get('greeting_message', MESSAGES.get(lang, MESSAGES["en"]).get(key, MESSAGES["en"][key]))
            return greeting
        except Exception as e:
            print(f"[WARNING] Error getting shared greeting message: {e}")
    
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, MESSAGES["en"][key])

def prewarm_tts_files():
    try:
        _ensure_cache_dir()
        # Prewarm EN only (ES will synthesize on the fly if needed)
        files_to_prewarm = [
            (MESSAGES["en"]["yes_no"], "tts_cache/yes_or_no.mp3"),
            (MESSAGES["en"]["err_global"], "tts_cache/err_global.mp3"),
            (MESSAGES["en"]["err_confirm"], "tts_cache/err_confirm.mp3"),
            (MESSAGES["en"]["no_record"], "tts_cache/no_recording.mp3"),
            (MESSAGES["en"]["reask"], "tts_cache/reask.mp3"),
            (MESSAGES["en"]["reask_cap"], "tts_cache/reask_cap.mp3"),
            (MESSAGES["en"]["err_global"], "tts_cache/err_result.mp3"),
            ("Is there anything else I can help you with today?", "tts_cache/anything_else.mp3")
        ]
        
        success_count = 0
        for text, filename in files_to_prewarm:
            if elevenlabs_tts_to_file(text, filename) is not None:
                success_count += 1
        
        # Use cache manager to prewarm common phrases
        if CACHE_MANAGER:
            CACHE_MANAGER.prewarm_common_phrases()
        
        if success_count == len(files_to_prewarm):
            print("[BOOT] TTS prewarm complete.")
        else:
            print(f"[BOOT] TTS prewarm partial: {success_count}/{len(files_to_prewarm)} files created")
    except Exception as e:
        print(f"[BOOT] TTS prewarm failed: {e}")

# ======= ASR / language ID =======
def transcribe_file(local_wav_path: str) -> tuple[str,str,float]:
    transcribe = _get_whisper_impl()
    if not transcribe:
        logger.warning("Local Whisper disabled or not installed; skipping local transcription.")
        # Return empty result to trigger fallback
        return "", "en", 0.0
    
    # Use the available Whisper implementation
    return transcribe(local_wav_path)

BRAND_FALLBACKS = {
    "nike": "nike shoes",
    "adidas": "adidas shoes",
    "new balance": "new balance shoes",
    "levi": "levi jeans",
    "levis": "levi jeans",
    "apple": "iphone",
    "playstation": "playstation console",
    "xbox": "xbox console",
    "airpods": "airpods",
}

def brand_coerce(noisy_text: str) -> str | None:
    t = (noisy_text or "").lower()
    t = t.replace("'s", "s").replace("'s", "s")
    for brand, mapped in BRAND_FALLBACKS.items():
        if brand in t:
            return mapped
    return None

# --- Store info brain (env-overridable) ---
STORE_NAME     = os.getenv("STORE_NAME", "the store")
STORE_HOURS    = os.getenv("STORE_HOURS", "Mon–Sat 9am–9pm, Sun 10am–6pm")
STORE_ADDRESS  = os.getenv("STORE_ADDRESS", "123 Main St")
STORE_CITY     = os.getenv("STORE_CITY", "")
STORE_STATE    = os.getenv("STORE_STATE", "")
STORE_ZIP      = os.getenv("STORE_ZIP", "")
STORE_PHONE    = os.getenv("STORE_PHONE", "(555) 123-4567")
RETURNS_POLICY = os.getenv("RETURNS_POLICY", "Most items within 30 days with receipt.")

# Holiday configuration
HOLIDAYS_CLOSED = os.getenv("HOLIDAYS_CLOSED", "Christmas Day, Thanksgiving Day, New Year's Day, Easter Sunday")
HOLIDAYS_SPECIAL_HOURS = os.getenv("HOLIDAYS_SPECIAL_HOURS", "Christmas Eve: 9am-6pm, New Year's Eve: 9am-6pm")

# Timeout configuration (in seconds)
CALL_TIMEOUT_SECONDS = int(os.getenv("CALL_TIMEOUT_SECONDS", "120"))  # 2 minutes default

# ---------- Hours parsing helpers (for concise "open/close" answers) ----------
_DAY_NAMES = ["mon","tue","wed","thu","fri","sat","sun"]
_DAY_ALIASES = {
    "mon":"mon","monday":"mon",
    "tue":"tue","tues":"tue","tuesday":"tue",
    "wed":"wed","weds":"wed","wednesday":"wed",
    "thu":"thu","thur":"thu","thurs":"thu","thursday":"thu",
    "fri":"fri","friday":"fri",
    "sat":"sat","saturday":"sat",
    "sun":"sun","sunday":"sun",
}

def _norm_dash(s: str) -> str:
    return s.replace("–","-").replace("—","-")

def _parse_time_word(w: str) -> str | None:
    """
    Accepts '8am', '9 pm', '10:30am', '7:15 pm'. Returns normalized '8am', '10:30am', etc.
    """
    w = w.strip().lower().replace(" ", "")
    # Insert ':' if like '930pm' -> '9:30pm'
    if re.fullmatch(r"\d{3,4}(am|pm)", w):
        hh = w[:-4] if len(w)==5 else w[:-3]  # handle 3 or 4 digits + am/pm
        ampm = w[-2:]
        if len(hh) == 3:
            h, m = hh[0], hh[1:]
        else:
            h, m = hh[:2], hh[2:]
        try:
            h = str(int(h))
            m = f"{int(m):02d}"
            return f"{h}:{m}{ampm}"
        except:
            return None
    # Already in h(:mm)am/pm
    if re.fullmatch(r"\d{1,2}(:\d{2})?(am|pm)", w):
        # Normalize hour like '08am' -> '8am'
        m = re.match(r"(\d{1,2})(:\d{2})?(am|pm)", w)
        h = str(int(m.group(1)))
        mm = m.group(2) or ""
        ap = m.group(3)
        return f"{h}{mm}{ap}"
    return None

def _parse_time_range(s: str) -> tuple[str|None, str|None]:
    """
    Parses '8am-9pm' or '10:30am - 7pm' -> ('8am','9pm')
    """
    s = s.strip().lower()
    s = _norm_dash(s)
    parts = [p.strip() for p in s.split("-")]
    if len(parts) != 2:
        return (None, None)
    start, end = _parse_time_word(parts[0]), _parse_time_word(parts[1])
    return (start, end)

def _expand_day_range(token: str) -> list[str]:
    """
    'Mon-Sat' -> ['mon','tue','wed','thu','fri','sat']
    'Sun'     -> ['sun']
    """
    token = _norm_dash(token).lower().strip()
    # split commas out first e.g. "Mon-Fri, Sun"
    if "," in token:  # caller shouldn't pass comma here, but be defensive
        out = []
        for t in token.split(","):
            out.extend(_expand_day_range(t))
        return out
    if "-" in token:
        a, b = [t.strip() for t in token.split("-")]
        a = _DAY_ALIASES.get(a, a[:3])
        b = _DAY_ALIASES.get(b, b[:3])
        try:
            ia = _DAY_NAMES.index(a)
            ib = _DAY_NAMES.index(b)
        except ValueError:
            return []
        if ia <= ib:
            return _DAY_NAMES[ia:ib+1]
        # wrap-around (unlikely in retail hours)
        return _DAY_NAMES[ia:] + _DAY_NAMES[:ib+1]
    # single day
    token = _DAY_ALIASES.get(token, token[:3])
    return [token] if token in _DAY_NAMES else []

def _parse_store_hours_to_map(hours_str: str) -> dict[str, tuple[str|None, str|None]]:
    """
    Converts 'Mon–Sat 8am–9pm, Sun 9am–7pm' into:
      {'mon':('8am','9pm'), ... 'sat':('8am','9pm'), 'sun':('9am','7pm')}
    """
    hours_str = _norm_dash(hours_str)
    daymap: dict[str, tuple[str|None,str|None]] = {}
    # Split by commas, each chunk like "Mon-Sat 8am-9pm" or "Sun 9am-7pm"
    chunks = [c.strip() for c in re.split(r",\s*", hours_str) if c.strip()]
    for ch in chunks:
        # Find day part (words) and time part (numbers)
        m = re.match(r"([A-Za-z\- ]+)\s+([0-9:apmAPM ]+-[0-9:apmAPM ]+)", ch)
        if not m:
            continue
        daytok, timerange = m.group(1).strip(), m.group(2).strip()
        open_t, close_t = _parse_time_range(timerange)
        days = []
        for dpart in [dt.strip() for dt in daytok.split("&")]:
            days.extend(_expand_day_range(dpart))
        for d in days:
            daymap[d] = (open_t, close_t)
    return daymap

def _today_daykey() -> str:
    # Use server local weekday; if you want store local tz, adjust here.
    import datetime as _dt
    return _DAY_NAMES[_dt.datetime.now().weekday()]

def _is_today_holiday() -> tuple[bool, str]:
    """
    Check if today is a holiday. Returns (is_holiday, holiday_name).
    """
    import datetime as dt
    today = dt.datetime.now()
    
    # Simple holiday detection (you can expand this)
    holidays = {
        (12, 25): "Christmas Day",
        (11, 24): "Thanksgiving Day",  # Approximate - Thanksgiving is 4th Thursday
        (1, 1): "New Year's Day",
        # Add more holidays as needed
    }
    
    month_day = (today.month, today.day)
    if month_day in holidays:
        return True, holidays[month_day]
    
    return False, ""

def _format_hours_for_speech(hours_str: str) -> str:
    """
    Convert abbreviated day names to full names for better speech.
    Example: "Mon–Sat 9am–9pm, Sun 10am–6pm" -> "Monday through Saturday 9am to 9pm, Sunday 10am to 6pm"
    """
    # Day name mappings
    day_map = {
        "Mon": "Monday",
        "Tue": "Tuesday", 
        "Wed": "Wednesday",
        "Thu": "Thursday",
        "Fri": "Friday",
        "Sat": "Saturday",
        "Sun": "Sunday"
    }
    
    # Replace day abbreviations
    result = hours_str
    for abbrev, full in day_map.items():
        result = result.replace(abbrev, full)
    
    # Add connecting words for ranges
    result = result.replace("Monday–Saturday", "Monday through Saturday")
    result = result.replace("Tuesday–Saturday", "Tuesday through Saturday")
    result = result.replace("Wednesday–Saturday", "Wednesday through Saturday")
    result = result.replace("Thursday–Saturday", "Thursday through Saturday")
    result = result.replace("Friday–Saturday", "Friday through Saturday")
    
    # Add "to" for time ranges
    result = result.replace("–", " to ")
    
    return result

def _format_address_for_speech(address_str: str) -> str:
    """
    Format address for natural speech.
    Example: "123 Main St NE, Portland, OR" -> "123 Main Street North East, Portland, Oregon"
    """
    # Common street abbreviations to full names
    street_map = {
        "St": "Street",
        "St.": "Street",
        "Ave": "Avenue", 
        "Ave.": "Avenue",
        "Blvd": "Boulevard",
        "Blvd.": "Boulevard",
        "Dr": "Drive",
        "Dr.": "Drive",
        "Ln": "Lane",
        "Ln.": "Lane",
        "Rd": "Road",
        "Rd.": "Road",
        "Ct": "Court",
        "Ct.": "Court",
        "Pl": "Place",
        "Pl.": "Place",
        "Way": "Way",
        "Cir": "Circle",
        "Cir.": "Circle",
        "Hwy": "Highway",
        "Hwy.": "Highway",
        "Pkwy": "Parkway",
        "Pkwy.": "Parkway",
        "Ter": "Terrace",
        "Ter.": "Terrace",
        "Sq": "Square",
        "Sq.": "Square",
        "Apt": "Apartment",
        "Apt.": "Apartment",
        "Ste": "Suite",
        "Ste.": "Suite",
        "Unit": "Unit",
        "Fl": "Floor",
        "Fl.": "Floor",
        "Rm": "Room",
        "Rm.": "Room"
    }
    
    # Directional abbreviations
    directional_map = {
        "N": "North",
        "S": "South", 
        "E": "East",
        "W": "West",
        "NE": "North East",
        "NW": "North West",
        "SE": "South East",
        "SW": "South West",
        "N.": "North",
        "S.": "South",
        "E.": "East", 
        "W.": "West",
        "NE.": "North East",
        "NW.": "North West",
        "SE.": "South East",
        "SW.": "South West"
    }
    
    # State abbreviations
    state_map = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
        "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
        "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
        "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
        "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
        "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
        "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
        "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
        "DC": "District of Columbia", "PR": "Puerto Rico", "VI": "Virgin Islands", "GU": "Guam",
        "MP": "Northern Mariana Islands", "AS": "American Samoa"
    }
    
    # Replace abbreviations in order: directionals first, then states, then streets
    # This prevents conflicts like "NE" being expanded to "Nebraska" instead of "North East"
    result = address_str
    
    # Replace directional abbreviations first (use word boundaries)
    for abbrev, full in directional_map.items():
        result = re.sub(r'\b' + re.escape(abbrev) + r'\b', full, result)
    
    # Replace state abbreviations (use word boundaries)
    for abbrev, full in state_map.items():
        result = re.sub(r'\b' + re.escape(abbrev) + r'\b', full, result)
    
    # Replace street abbreviations (use word boundaries)
    for abbrev, full in street_map.items():
        result = re.sub(r'\b' + re.escape(abbrev) + r'\b', full, result)
    
    # Clean up any remaining periods that were left behind
    result = re.sub(r'\s+\.', '', result)  # Remove periods that are preceded by whitespace
    result = re.sub(r'\.(?=\s|$)', '', result)  # Remove periods that are followed by whitespace or end of string
    
    return result

def _add_polite_signoff(base_response: str) -> str:
    """
    Add a polite spoken signoff. Return pure text only; do not append URLs.
    """
    # Prefer template text if available
    if SHARED_DATA_AVAILABLE:
        t = shared_data.get_dialogue_template("general", "anything_else")
        if t:
            return f"{base_response} {t}"
    # Fallback phrase
    return f"{base_response} Is there anything else I can help you with today?"

def _is_followup_response(text: str) -> bool:
    """
    Check if the text is a response to "anything else?" question.
    Returns True for "no" responses, False for "yes" responses.
    """
    t = (text or "").lower().strip()
    
    # Negative responses (no, that's all, etc.)
    negative_words = ["no", "nope", "nah", "not really", "that's all", "all set", "goodbye", "bye", "thanks", "thank you", "that's it", "nothing else", "i'm good", "i'm all set"]
    
    # Positive responses (yes, sure, etc.)
    positive_words = ["yes", "yeah", "yep", "sure", "okay", "ok", "uh huh", "uh-huh", "absolutely", "definitely", "of course"]
    
    # If the text contains department/direction words, treat as a new question FIRST
    # so we don't accidentally hang up when they say "no, put the manager on the phone".
    product_indicators = [
        "find", "looking for", "need", "want", "where", "bag", "item", "product", "thing",
        "manager", "supervisor", "pharmacy", "connect", "transfer", "put", "get", "speak", "talk"
    ]
    if any(word in t for word in product_indicators):
        return False
    
    # If it's a question or contains question words, treat as a new question (not a yes/no response)
    question_words = ["what", "when", "where", "who", "why", "how", "which", "do you", "can you", "will you", "are you", "is there", "do they", "does it", "have", "any"]
    if any(word in t for word in question_words):
        return False
    
    # Check for negative responses (exact word matches)
    if any(word == t for word in negative_words):
        return True
    
    # Check for negative phrases (contains these words)
    if any(word in t for word in negative_words):
        return True
    
    # Check for positive responses (exact word matches)
    if any(word == t for word in positive_words):
        return False
    
    # Check for positive phrases (contains these words)
    if any(word in t for word in positive_words):
        return False
    
    # If it starts with a positive word followed by a question, treat as a new question
    words = t.split()
    if len(words) >= 2:
        if words[0] in positive_words and any(word in t for word in question_words):
            return False
    
    # If the text is longer than 2 words and doesn't contain negative words, treat as a new question
    if len(t.split()) > 2 and not any(word in t for word in negative_words):
        return False
    
    # Default: treat as negative (most people say "no" or just hang up)
    return True

def _closing_today(hours_str: str) -> str | None:
    mp = _parse_store_hours_to_map(hours_str or "")
    today = _today_daykey()
    if today in mp and mp[today][1]:
        return mp[today][1]
    return None

def _opening_today(hours_str: str) -> str | None:
    mp = _parse_store_hours_to_map(hours_str or "")
    today = _today_daykey()
    if today in mp and mp[today][0]:
        return mp[today][0]
    return None
# --------------------------------------------------------------------

INTENT_RX = {
    "hours":   re.compile(r"\b(hours?|open|close|closing|opening|what time.*(open|close))\b", re.I),
    "address": re.compile(r"\b(address|where.*located|location|directions)\b", re.I),
    "phone":   re.compile(r"\b(phone|number|call you|telephone|contact)\b", re.I),
    "returns": re.compile(r"\b(return|refund|exchange|policy)\b", re.I),
    "goodbye": re.compile(r"\b(no|nope|nah|not really|that's all|all set|goodbye|bye|thanks|thank you|that's it|nothing else)\b", re.I),
}

# --- STRICT RETURNS GUARD (prevents brand collisions like "carhartt beanie") ---
RETURNS_KEYWORDS_CORE = {"return", "returns", "refund", "exchange", "policy"}
RETURNS_CONTEXT_HINTS = {"policy", "receipt", "receiptless", "window", "days", "how", "can", "do", "past", "without"}

def _looks_like_returns(utterance: str) -> bool:
    """
    Only treat as a returns intent if we find BOTH:
      - a returns keyword, and
      - at least one context hint
    """
    toks = set((utterance or "").lower().split())
    return bool(toks & RETURNS_KEYWORDS_CORE) and bool(toks & RETURNS_CONTEXT_HINTS)

def detect_store_info_intent(text: str) -> tuple[str | None, str | None]:
    """
    Detects simple store-info Qs and returns (intent, spoken_line).
    Special-case: concise open/close if we can parse today's hours.
    NOTE: returns intent is STRICT to avoid 'carhartt beanie' collisions.
    """
    t = (text or "").lower().strip()

    # If this utterance looks like a direct department request (e.g., manager), do NOT treat
    # it as store-info. Let department routing handle it first.
    try:
        if _check_direct_department_request(t):
            return None, None
    except Exception:
        # If helper not yet available, continue with store-info checks
        pass
    
    # Get current store info from shared data
    try:
        store_info = shared_data.get_store_info()
        current_store_name = store_info.get('name', STORE_NAME)
        current_store_hours = store_info.get('hours', STORE_HOURS)
        current_store_phone = store_info.get('phone', STORE_PHONE)
        current_store_address = store_info.get('address', STORE_ADDRESS)
        current_holiday_hours = store_info.get('holiday_hours') or os.getenv("HOLIDAYS_SPECIAL_HOURS", "")
    except:
        # Fallback to environment variables if shared data is not available
        current_store_name = STORE_NAME
        current_store_hours = STORE_HOURS
        current_store_phone = STORE_PHONE
        current_store_address = STORE_ADDRESS
        current_holiday_hours = os.getenv("HOLIDAYS_SPECIAL_HOURS", "")

    if INTENT_RX["hours"].search(t):
        # Check for senior hours first
        if "senior" in t and ("hour" in t or "shopping" in t):
            formatted_hours = _format_hours_for_speech(current_store_hours)
            return "hours", _add_polite_signoff(f"We don't have special senior shopping hours, but here are our normal business hours: {formatted_hours}.")
        
        # If they ask about both Sunday AND holidays, give a combined answer
        if ("sunday" in t or "sun" in t) and "holiday" in t:
            closed_list = HOLIDAYS_CLOSED.split(", ")
            if len(closed_list) <= 4:
                # If 4 or fewer holidays, list them all
                closed_short = ", ".join(closed_list)
            else:
                # If more than 4, list first 3 and say "and others"
                closed_short = ", ".join(closed_list[:3]) + " and others"
            return "hours", _add_polite_signoff(f"Yes, we're open on Sundays from 10am to 6pm. For holidays, we're open most with regular hours, but closed on {closed_short}.")
        
        # If they specifically ask about Sunday only
        if "sunday" in t or "sun" in t:
            return "hours", _add_polite_signoff("Yes, we're open on Sundays from 10am to 6pm.")
        
        # If they specifically ask about holidays only
        if "holiday" in t:
            # Prefer the dashboard-configured holiday hours message if present
            if current_holiday_hours and current_holiday_hours.strip():
                return "hours", _add_polite_signoff(current_holiday_hours.strip())

            # Otherwise, fall back to dynamic check and defaults
            is_holiday, holiday_name = _is_today_holiday()
            if is_holiday:
                if holiday_name in HOLIDAYS_CLOSED:
                    return "hours", _add_polite_signoff(f"Today is {holiday_name} and we are closed.")
                else:
                    return "hours", _add_polite_signoff(f"Today is {holiday_name} and we're open with regular hours.")

            closed_list = HOLIDAYS_CLOSED.split(", ")
            if len(closed_list) <= 4:
                closed_short = ", ".join(closed_list)
            else:
                closed_short = ", ".join(closed_list[:3]) + " and others"
            return "hours", _add_polite_signoff(f"We're open most holidays with regular hours, but closed on {closed_short}. For specific holiday hours, please call ahead.")
        
        # If they specifically ask about closing time
        if "close" in t or "closing" in t or "tonight" in t:
            close_t = _closing_today(current_store_hours)
            if close_t:
                return "hours", _add_polite_signoff(f"we close at {close_t}.")
        
        # If they specifically ask about opening time
        if "open" in t or "opening" in t or "tomorrow morning" in t:
            open_t = _opening_today(current_store_hours)
            if open_t:
                return "hours", _add_polite_signoff(f"we open at {open_t}.")
        
        # If they ask for hours today, give today's specific hours
        if "today" in t:
            open_t = _opening_today(current_store_hours)
            close_t = _closing_today(current_store_hours)
            if open_t and close_t:
                return "hours", _add_polite_signoff(f"today we're open from {open_t} to {close_t}.")
        
        # Default: give full hours with speech-friendly formatting
        formatted_hours = _format_hours_for_speech(current_store_hours)
        return "hours", _add_polite_signoff(f"{current_store_name} hours are {formatted_hours}.")

    if INTENT_RX["address"].search(t):
        # Check if they also asked about directions
        directions_requested = any(word in t.lower() for word in ["how", "get", "directions", "drive", "walk", "bus", "train"])
        
        # Use the current address from shared data
        full_address = current_store_address
        
        # Format for speech
        formatted_address = _format_address_for_speech(full_address)
        
        if directions_requested:
            return "address", _add_polite_signoff(f"Our address is {formatted_address}. We're located in the downtown area, easily accessible by car, bus, or walking. You can use any GPS app to get turn-by-turn directions to our location.")
        else:
            return "address", _add_polite_signoff(f"Our address is {formatted_address}.")
    if INTENT_RX["phone"].search(t):
        return "phone", _add_polite_signoff(f"You can reach us at {current_store_phone}.")

    # STRICT gate for returns
    if _looks_like_returns(t):
        return "returns", f"Our return policy is: {RETURNS_POLICY}"

    # Check for goodbye/negative responses
    if INTENT_RX["goodbye"].search(t):
        return "goodbye", "Thanks for calling, have a nice day!"

    return (None, None)

# ---------- Response Sanitizer to prevent questions/upsell ----------
QUESTIONY_TRIGGERS = [
    "would you like", "do you want", "can i", "can we", "should i",
    "shall i", "would you", "are you interested", "interested in",
    "how about", "could i", "could we", "want me to"
]

def _coerce_statement(resp: str, department: str | None) -> str:
    s = (resp or "").strip()
    s = s.replace("?", "").strip()
    low = s.lower()

    def connect_line(dept: str | None) -> str:
        if dept and dept in store_config["departments"]:
            return f"Connecting you with {dept} now. Thanks for calling."
        return "Connecting you with Customer Service now. Thanks for calling."

    if any(tr in low for tr in QUESTIONY_TRIGGERS) or low.startswith(
        ("would ", "do you ", "can ", "should ", "shall ", "are you ", "could ")
    ):
        return connect_line(department)

    words = s.split()
    if len(words) < 6 or len(words) > 18:
        return connect_line(department)

    return s
# --------------------------------------------------------------------

def repair_transcript(noisy_text: str) -> str:
    # 0) Normalize once
    raw = (noisy_text or "").strip().lower()
    raw = re.sub(r"[^\w\s\-]", "", raw)

    # 1) Single-word whitelist: accept and pass through
    if raw in SINGLE_WORD_ALLOW:
        return raw
    # 1b) If it's a single token and not a trivial filler/greeting, accept it
    toks = raw.split()
    if len(toks) == 1 and raw and raw not in STOP_SINGLEWORD:
        return raw

    # 2) Brand/phrase coercions
    mapped = brand_coerce(raw)
    if mapped:
        return mapped

    # 3) Regex repairs
    t = raw
    for pat, repl in REPAIR_PATTERNS:
        t = re.sub(pat, repl, t, flags=re.I)

    if t in SINGLE_WORD_ALLOW:
        return t

    # 4) LLM cleanup as a backstop
    try:
        prompt = f"""
You fix garbled phone ASR into the clean item/intent a caller likely said for a retail store.

Rules:
- Return ONLY the corrected short phrase (2–10 words). No quotes, no punctuation, no commentary.
- Accept common single items like "charger", "paper".
- If it's clearly a greeting or filler only, return exactly: unclear

Noisy ASR: {noisy_text}
"""
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.2
        )
        out = (resp.choices[0].message.content or "").strip().lower()
        out = out.strip().strip(".").strip(",")
        if out in SINGLE_WORD_ALLOW:
            return out
        if 2 <= len(out.split()) <= 10 and out != "unclear":
            return out
        return "unclear"
    except Exception:
        return "unclear"

def generate_response(transcript: str, lang: str = "en"):
    """
    Produce a natural final line and a department.
    Always speak the department; include a short item if safe.
    """
    start_time = time.time()
    print(f"[DEBUG] generate_response called with: '{transcript}'")
    raw = transcript or ""
    
    normalize_start = time.time()
    item_raw = normalize_item_phrase(raw)
    normalize_time = time.time() - normalize_start
    print(f"[DEBUG] normalize_item_phrase result: '{item_raw}' (took {normalize_time:.3f}s)")

    # HARD GUARD: If this is actually a direct department request (e.g., manager),
    # skip product classification entirely and route immediately.
    dept_check_start = time.time()
    try:
        dept_direct = _check_direct_department_request(raw) or _check_direct_department_request(item_raw)
    except Exception:
        dept_direct = None
    dept_check_time = time.time() - dept_check_start
    print(f"[TIMING] Department check took {dept_check_time:.3f}s")
    
    if dept_direct:
        dept_name = dept_direct
        if dept_name == "manager" and 'SHARED_DATA_AVAILABLE' in globals() and SHARED_DATA_AVAILABLE:
            line = shared_data.get_dialogue_template("general", "connect_manager") or "I'll connect you to the manager now."
        else:
            # Keep line concise in final path
            line = f"I'll connect you to {dept_name} now."
        total_time = time.time() - start_time
        print(f"[TIMING] generate_response total time (direct dept): {total_time:.3f}s")
        return line, dept_name

    # Check for pharmacy queries first
    if PHARMACY_AVAILABLE:
        pharmacy_start = time.time()
        pharmacy_response = _handle_pharmacy_query(item_raw)
        pharmacy_time = time.time() - pharmacy_start
        print(f"[TIMING] Pharmacy check took {pharmacy_time:.3f}s")
        if pharmacy_response:
            total_time = time.time() - start_time
            print(f"[TIMING] generate_response total time (pharmacy): {total_time:.3f}s")
            return pharmacy_response
    
    # Check for coupon queries
    if COUPON_AVAILABLE:
        coupon_response = _handle_coupon_query(item_raw)
        if coupon_response:
            return coupon_response
    
    # Check for inventory queries
    if INVENTORY_AVAILABLE:
        inventory_response = _handle_inventory_query(item_raw)
        if inventory_response:
            return inventory_response
    
    # Check for store hours query
    if re.search(r"\b(?:store hours|hours|open|closed|when are you open|what time|business hours)\b", item_raw.lower()):
        return "Our store hours are 7 AM to 10 PM, seven days a week.", "Customer Service"

    # Extract just the product name from the caller's speech first
    product_name = _extract_product_name(item_raw)
    print(f"[DEBUG] _extract_product_name: '{item_raw}' -> '{product_name}'")
    
    # Record requested item for analytics (best-effort)
    try:
        if product_name:
            record_item_request(product_name)
    except Exception:
        pass

    # 1) Rule-based dept with internet search fallback (use product_name, not full phrase)
    dept, used_internet_search = classify_department_with_internet_fallback(product_name)

    # 2) Keyword fallback (only if internet search wasn't used)
    if not dept and not used_internet_search:
        dept = _guess_department_from_keywords(product_name)

    # 3) Final fallback
    if not dept:
        # Force internet search as last resort if we have a product name
        if product_name and should_use_internet_search(product_name):
            print(f"[SEARCH] Forcing internet search for '{product_name}' as last resort")
            result = search_product_online(product_name)
            dept = result.get("department") or "Customer Service"
            used_internet_search = True
        else:
            dept = "Customer Service"
    
    # Store whether internet search was used for this response
    generate_response.last_used_internet_search = used_internet_search

    if product_name:
        line = f"Thanks. I'll connect you to {dept} about {product_name}."
    else:
        line = f"Thanks. I'll connect you to {dept} now."

    total_time = time.time() - start_time
    print(f"[TIMING] generate_response total time (full flow): {total_time:.3f}s")
    return line, dept

def _format_price_clearly(price: float) -> str:
    """Format price as clear dollars and cents"""
    # Handle floating point precision issues by converting to cents first
    total_cents = round(price * 100)
    dollars = total_cents // 100
    cents = total_cents % 100
    
    if price >= 100:
        if cents == 0:
            return f"${dollars} dollars"
        else:
            return f"${dollars} dollars and {cents} cents"
    elif price >= 10:
        if cents == 0:
            return f"${dollars} dollars"
        else:
            return f"${dollars} dollars and {cents} cents"
    else:
        if dollars == 0:
            return f"{cents} cents"
        elif cents == 0:
            return f"{dollars} dollars"
        else:
            return f"{dollars} dollars and {cents} cents"

def _extract_product_name(speech: str) -> str:
    """Extract just the product name from caller's speech by removing common filler phrases"""
    if not speech:
        return speech
    
    speech_lower = speech.lower().strip()
    
    # Common filler phrases to remove from the beginning
    filler_prefixes = [
        "i need", "i want", "i'm looking for", "i am looking for",
        "do you have", "do you carry", "can you help me find",
        "i need some", "i want some", "i need the", "i want the",
        "hey", "hi", "hello", "excuse me",
        "i need to find", "i want to find", "i'm trying to find",
        "i need to get", "i want to get", "i'm trying to get",
        "i need to buy", "i want to buy", "i'm trying to buy",
        "i need to purchase", "i want to purchase",
        "i need to pick up", "i want to pick up",
        "i need to grab", "i want to grab",
        "i need to get some", "i want to get some",
        "i need to find some", "i want to find some",
        "i need to buy some", "i want to buy some",
        "i need to purchase some", "i want to purchase some",
        "i need to pick up some", "i want to pick up some",
        "i need to grab some", "i want to grab some",
        # Add correction phrases
        "no, i'm looking for", "no i'm looking for", "no, i am looking for", "no i am looking for",
        "no, i need", "no i need", "no, i want", "no i want",
        "no, do you have", "no do you have", "no, do you carry", "no do you carry",
        "actually, i'm looking for", "actually i'm looking for", "actually, i am looking for", "actually i am looking for",
        "actually, i need", "actually i need", "actually, i want", "actually i want",
        "i meant", "i said", "it's", "its"
    ]
    
    # Remove filler prefixes
    for prefix in filler_prefixes:
        if speech_lower.startswith(prefix):
            # Remove the prefix and any leading whitespace
            cleaned = speech[len(prefix):].strip()
            # If we still have content, return it
            if cleaned:
                return cleaned
    
    # If no prefix matched, return the original speech
    return speech

# -------------------------------------------------------------
# Item request tracking for Analytics (Most Requested Items)
# -------------------------------------------------------------
MOST_REQUESTED_FILE = os.path.join("data", "most_requested_items.json")
MOST_REQUESTED_COUNTS = {}
MOST_REQUESTED_HIDDEN = set()
MOST_REQUESTED_LOCK = None

try:
    import threading  # threading likely already imported elsewhere; safe to re-import
    MOST_REQUESTED_LOCK = threading.Lock()
except Exception:
    MOST_REQUESTED_LOCK = None

def _load_most_requested_items():
    global MOST_REQUESTED_COUNTS, MOST_REQUESTED_HIDDEN
    try:
        if os.path.exists(MOST_REQUESTED_FILE):
            with open(MOST_REQUESTED_FILE, "r") as f:
                data = json.load(f)
                MOST_REQUESTED_COUNTS = data.get("items", {}) or {}
                hidden_list = data.get("hidden", []) or []
                MOST_REQUESTED_HIDDEN = set([str(x).strip().lower() for x in hidden_list if isinstance(x, str)])
    except Exception as e:
        print(f"[ANALYTICS] Failed to load most requested items: {e}")

def _save_most_requested_items():
    try:
        os.makedirs(os.path.dirname(MOST_REQUESTED_FILE), exist_ok=True)
        with open(MOST_REQUESTED_FILE, "w") as f:
            json.dump({
                "items": MOST_REQUESTED_COUNTS,
                "hidden": sorted(list(MOST_REQUESTED_HIDDEN)),
                "updated_at": time.time()
            }, f)
    except Exception as e:
        print(f"[ANALYTICS] Failed to save most requested items: {e}")

def record_item_request(item_name: str):
    if not item_name:
        return
    normalized = (item_name or "").strip().lower()
    if not normalized:
        return
    # Avoid counting department names as items
    department_terms = {"pharmacy", "grocery", "electronics", "customer service", "pet supplies", "home and garden", "health and beauty"}
    if normalized in department_terms:
        return
    try:
        if MOST_REQUESTED_LOCK:
            with MOST_REQUESTED_LOCK:
                MOST_REQUESTED_COUNTS[normalized] = int(MOST_REQUESTED_COUNTS.get(normalized, 0)) + 1
        else:
            MOST_REQUESTED_COUNTS[normalized] = int(MOST_REQUESTED_COUNTS.get(normalized, 0)) + 1
        _save_most_requested_items()
    except Exception as e:
        print(f"[ANALYTICS] Failed to record item '{normalized}': {e}")

# Initialize on import
try:
    _load_most_requested_items()
except Exception:
    pass

def hide_item(name: str):
    if not name:
        return
    normalized = str(name).strip().lower()
    if not normalized:
        return
    try:
        if MOST_REQUESTED_LOCK:
            with MOST_REQUESTED_LOCK:
                MOST_REQUESTED_HIDDEN.add(normalized)
        else:
            MOST_REQUESTED_HIDDEN.add(normalized)
        _save_most_requested_items()
    except Exception as e:
        print(f"[ANALYTICS] Failed to hide item '{normalized}': {e}")

def unhide_item(name: str):
    if not name:
        return
    normalized = str(name).strip().lower()
    try:
        if MOST_REQUESTED_LOCK:
            with MOST_REQUESTED_LOCK:
                MOST_REQUESTED_HIDDEN.discard(normalized)
        else:
            MOST_REQUESTED_HIDDEN.discard(normalized)
        _save_most_requested_items()
    except Exception as e:
        print(f"[ANALYTICS] Failed to unhide item '{normalized}': {e}")

def is_item_hidden(name: str) -> bool:
    if not name:
        return False
    return str(name).strip().lower() in MOST_REQUESTED_HIDDEN

def _handle_pharmacy_query(item_raw: str) -> tuple[str, str] | None:
    """
    Handle pharmacy-related queries like prescription refills, status checks, etc.
    Returns (response_line, department) or None if not a pharmacy query.
    """
    if not item_raw:
        return None
    
    item_lower = item_raw.lower()
    
    # Check for pharmacy query keywords
    pharmacy_keywords = [
        "refill", "prescription", "rx", "medication", "pharmacist",
        "status", "ready", "transfer", "consultation", "drug", "pill", "medicine",
        "dosage", "side effect", "interaction", "copay", "insurance", "delivery",
        "same as last time", "last time", "as soon as last time", "assess last time"
    ]
    
    # BROAD MATCHING: If it contains pharmacy-specific phrases, treat as pharmacy query
    # This catches ASR mishearings and variations, but is more specific
    pharmacy_phrases = ["last time", "same as last time", "refill", "prescription refill", "rx refill"]
    if any(phrase in item_lower for phrase in pharmacy_phrases):
        is_pharmacy_query = True
        print(f"[PHARMACY] Pharmacy phrase match triggered for: '{item_raw}'")
    
    # SHORT RESPONSE: If we're in a pharmacy context and the response is short/partial,
    # treat it as a pharmacy query (catches ASR mishearings)
    elif len(item_raw.split()) <= 3 and any(word in item_lower for word in ["refill", "prescription", "rx", "medication", "pill"]):
        is_pharmacy_query = True
        print(f"[PHARMACY] Short pharmacy response match triggered for: '{item_raw}'")
    
    else:
        is_pharmacy_query = any(keyword in item_lower for keyword in pharmacy_keywords)
        print(f"[PHARMACY] Keyword match result: {is_pharmacy_query} for '{item_raw}'")
    
    if not is_pharmacy_query:
        return None
    
    # Handle pharmacy query
    if PHARMACY_AVAILABLE:
        pharmacy_result = handle_pharmacy_query(item_raw)
        if pharmacy_result:
            # Check if this is a "clarify" response (unknown query)
            if "not sure what you're asking" in pharmacy_result.message.lower() or "clarify" in pharmacy_result.message.lower():
                # This is a clarification request - let the AI classification system handle it
                print(f"[PHARMACY] Clarification needed for '{item_raw}', falling back to AI classification")
                return None
            
            # For pharmacy queries, we want to provide the response directly
            # rather than routing to staff, so customers can continue the conversation
            return (pharmacy_result.message, "Pharmacy")
    
    return None

def _handle_coupon_query(item_raw: str) -> tuple[str, str] | None:
    """
    Handle coupon-related queries like discount lookups, promotional offers, etc.
    Returns (response_line, department) or None if not a coupon query.
    """
    if not item_raw:
        return None
    
    # Handle coupon query
    if COUPON_AVAILABLE:
        coupon_response = handle_coupon_query(item_raw)
        if coupon_response:
            # Check if this is a specific coupon request with an item we can infer
            item_lower = item_raw.lower()
            
            # Try to infer the department from the specific item
            inferred_dept = None
            if any(keyword in item_lower for keyword in ["cucumber", "tomato", "apple", "banana", "lettuce", "carrot", "onion", "produce"]):
                inferred_dept = "produce"
            elif any(keyword in item_lower for keyword in ["bread", "cake", "pastry", "cookie"]):
                inferred_dept = "bakery"
            elif any(keyword in item_lower for keyword in ["milk", "cheese", "yogurt", "butter"]):
                inferred_dept = "dairy"
            elif any(keyword in item_lower for keyword in ["meat", "chicken", "beef", "pork", "fish"]):
                inferred_dept = "meat"
            
            if inferred_dept:
                # Return the specific department instead of Customer Service
                print(f"[COUPON] Detected specific item '{item_raw}' -> department '{inferred_dept}'")
                return (coupon_response, inferred_dept)
            else:
                # For general coupon queries, we want to continue the conversation
                # so customers can ask for specific items
                return (coupon_response, "Customer Service")
    
    return None

def _handle_inventory_query(item_raw: str) -> tuple[str, str] | None:
    """
    Handle inventory-related queries like stock checks, price checks, etc.
    Returns (response_line, department) or None if not an inventory query.
    """
    if not item_raw:
        return None
    
    item_lower = item_raw.lower()
    
    # Check for inventory query keywords
    inventory_keywords = [
        "in stock", "out of stock", "have", "carry", "sell", "available",
        "price", "cost", "how much", "how many", "quantity", "amount",
        "where is", "location", "aisle", "shelf", "find", "locate"
    ]
    
    is_inventory_query = any(keyword in item_lower for keyword in inventory_keywords)
    
    if not is_inventory_query:
        return None
    
    # Record requested item for analytics
    try:
        requested_item_clean = _extract_product_name(item_raw)
        record_item_request(requested_item_clean)
    except Exception:
        pass

    # Search inventory using shared data first, then fallback to inventory system
    search_result = None
    
    if SHARED_DATA_AVAILABLE:
        try:
            # Search in shared inventory data
            inventory_item = shared_data.get_inventory_by_name(item_raw)
            if inventory_item:
                # Create a simple search result object
                class SimpleSearchResult:
                    def __init__(self, item):
                        self.found = True
                        self.items = [item]
                        self.suggestions = []
                
                search_result = SimpleSearchResult(inventory_item)
        except Exception as e:
            print(f"[WARNING] Error searching shared inventory: {e}")
    
    # Fallback to inventory system if shared data not available or item not found
    if not search_result:
        search_result = search_inventory(item_raw)
    
    if not search_result or not search_result.found:
        # Item not found in inventory - generate simulated response for grocery items
        # Check if this looks like a grocery item query
        grocery_keywords = [
            "bread", "milk", "cheese", "eggs", "chips", "soda", "cereal", "fruit", 
            "vegetable", "meat", "chicken", "beef", "pork", "fish", "yogurt", "butter",
            "juice", "water", "snack", "candy", "chocolate", "cookies", "crackers",
            "pasta", "rice", "sauce", "condiment", "spice", "herb", "flour", "sugar",
            "oil", "vinegar", "soup", "can", "frozen", "ice cream", "dairy", "produce"
        ]
        
        is_grocery_query = any(keyword in item_lower for keyword in grocery_keywords)
        
        if is_grocery_query:
            # Generate realistic simulated response
            item_name, department, price, quantity = generate_simulated_inventory_response(item_raw)
            
            # Add some variety to responses with clear dollar formatting
            import random
            
            # Format price as dollars and cents
            price_text = _format_price_clearly(price)
            
            response_variants = [
                f"Yes, {item_name} is currently {price_text}.",
                f"{item_name} is {price_text} right now.",
                f"The price for {item_name} is {price_text}.",
                f"{item_name} is on sale for {price_text}.",
                f"We have {item_name} for {price_text}."
            ]
            
            # Sometimes mention stock levels
            if quantity <= 5:
                response_variants.extend([
                    f"{item_name} is {price_text}, but we're running low on stock.",
                    f"{item_name} is {price_text} - only a few left!"
                ])
            elif quantity <= 15:
                response_variants.extend([
                    f"{item_name} is {price_text} and we have good stock.",
                    f"{item_name} is {price_text} - plenty available."
                ])
            
            response = random.choice(response_variants)
            
            return (response, department)
        else:
            # Not a grocery item - provide suggestions or route to customer service
            suggestions = search_result.suggestions if search_result else []
            if suggestions:
                suggestion_text = f" Did you mean {suggestions[0]}?"
            else:
                suggestion_text = ""
            
            return (
                f"I'm sorry, I couldn't find {item_raw} in our inventory.{suggestion_text} Let me connect you to Customer Service to help you further.",
                "Customer Service"
            )
    
    # Item found - provide inventory information
    item = search_result.items[0]  # Use first match
    
    # Handle shared data vs inventory system data
    if SHARED_DATA_AVAILABLE and hasattr(item, 'get'):
        # Shared data format
        in_stock = item.get('stock_quantity', 0) > 0
        quantity = item.get('stock_quantity', 0)
        price = item.get('price', 0)
        department = item.get('department', 'Unknown')
        location = item.get('location', 'Unknown location')
    else:
        # Inventory system format
        in_stock, quantity = check_stock(item.sku)
        price = get_price(item.sku)
        department = item.department
        location = f"aisle {item.aisle}, shelf {item.shelf}" if hasattr(item, 'aisle') else "Unknown location"
    
    # Build response based on query type
    if any(word in item_lower for word in ["price", "cost", "how much"]):
        if price:
            # Format price clearly
            price_text = _format_price_clearly(price)
            
            return (
                f"{item.name} is {price_text}. It's located in {department}, {location}.",
                department
            )
        else:
            return (
                f"I found {item.name} in {department}, but I don't have the current price. Let me connect you to {department} for pricing information.",
                department
            )
    
    elif any(word in item_lower for word in ["in stock", "have", "carry", "available", "how many", "quantity"]):
        if in_stock:
            if quantity <= 5:
                stock_status = f"limited stock - only {quantity} left"
            elif quantity <= 20:
                stock_status = f"in stock - {quantity} available"
            else:
                stock_status = "in stock"
            
            return (
                f"{item.name} is {stock_status}. It's located in {department}, {location}.",
                department
            )
        else:
            return (
                f"I'm sorry, {item.name} is currently out of stock. Let me connect you to {department} to check when it will be available again.",
                department
            )
    
    elif any(word in item_lower for word in ["where", "location", "aisle", "shelf", "find", "locate"]):
        return (
            f"{item.name} is located in {department}, {location}.",
            department
        )
    
    else:
        # General inventory info
        if in_stock:
            stock_info = f"in stock with {quantity} available" if quantity <= 20 else "in stock"
            
            # Format price clearly
            price_text = _format_price_clearly(price)
            
            return (
                f"{item.name} is {stock_info}. It's {price_text} and located in {department}, {location}.",
                department
            )
        else:
            # Format price clearly for out of stock items
            price_text = _format_price_clearly(price)
            
            return (
                f"{item.name} is currently out of stock. It's normally {price_text} and located in {department}, {location}.",
                department
            )

def download_twilio_recording(recording_url: str, out_path: str):
    ensure_static_dir()
    url_try = [recording_url + ".wav", recording_url + ".mp3"]
    last_exc = None
    for u in url_try:
        try:
            r = requests.get(u, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=60)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(r.content)
            return out_path
        except Exception as e:
            last_exc = e
            continue
    raise last_exc

# ======= Simple multilingual yes/no =======
YES_ALIASES_EN = {
    "yes","yeah","yep","yup","yess","sure","ok","okay","alright","right",
    "correct","affirmative","absolutely","definitely","sounds good","works for me",
    "go ahead","please do","that's right","thats right","that is right","indeed","for sure","mmhmm","mhm","uh-huh","uhhuh","yea",
    # NEW:
    "exactly","thats it","thats what i said"
}
NO_ALIASES_EN = {
    "no","nope","nah","negative","not really","not quite","dont","do not",
    "stop","cancel","no thanks","no thank you","that's wrong","thats wrong","incorrect","rather not","pass"
}
YES_ALIASES_ES = {"si","sí","claro","correcto","vale"}
NO_ALIASES_ES  = {"no","negativo","nada","para nada"}

def _normalize_text(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = t.lower().strip()
    for ch in [".", ",", "!", "?", ";", ":", "\"", "'", "’"]:
        t = t.replace(ch, "")
    t = t.replace("uh huh", "uh-huh").replace("mm hmm", "mm-hmm").replace("mmhm", "mm-hmm")
    return " ".join(t.split())

# ===== 4a: Affirmation shortcut (exact-match, normalized) =====
AFFIRMATION_SET = {
    "that's right","thats right","exactly","correct","right",
    "yeah","yep","yup","ok","okay","mm-hmm","uh-huh","indeed"
}
def is_affirmation(text: str) -> bool:
    return _normalize_text(text) in AFFIRMATION_SET
# =============================================================

def _contains_alias(text_norm: str, aliases: set[str]) -> bool:
    for a in aliases:
        pattern = r"\b" + re.escape(a) + r"\b"
        if re.search(pattern, text_norm):
            return True
    return False

def interpret_confirmation(text: str, lang: str = "en") -> str:
    t = _normalize_text(text)
    if not t:
        return "unclear"
    if (lang or "en").startswith("es"):
        if _contains_alias(t, YES_ALIASES_ES): return "yes"
        if _contains_alias(t, NO_ALIASES_ES):  return "no"
    else:
        if _contains_alias(t, YES_ALIASES_EN): return "yes"
        if _contains_alias(t, NO_ALIASES_EN):  return "no"
    # backstop: tiny LLM check (English-biased; safe for short replies)
    try:
        prompt = f"""Classify if the user's short reply implies yes, no, or unclear.
Return only JSON: {{ "label": "yes"|"no"|"unclear" }}
Reply: "{text}" """
        resp = client.chat_completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0
        ) if hasattr(client, "chat_completions") else client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0
        )
        out = (resp.choices[0].message.content or "").strip()
        data = json.loads(out)
        lbl = (data.get("label") or "").lower()
        return lbl if lbl in ("yes","no","unclear") else "unclear"
    except Exception:
        return "unclear"

# ======= YES + DETAIL HANDLING =======
YES_PREFIXES_EN = {"yes","yeah","yep","yup","ok","okay","correct","that's right","thats right","that is right","exactly","right","mm-hmm","uh-huh"}
YES_PREFIXES_ES = {"si","sí","claro","correcto","vale","así es","exacto"}

def yes_plus_detail(reply_text: str, lang: str = "en") -> str:
    """
    If the reply starts with a yes-like word but contains extra content,
    return that trailing detail (e.g., 'yeah, the drink' -> 'the drink').
    Otherwise return "".
    """
    if not isinstance(reply_text, str) or not reply_text.strip():
        return ""
    t_raw = reply_text.strip()
    t = t_raw.lower().strip()

    prefixes = YES_PREFIXES_ES if (lang or "en").startswith("es") else YES_PREFIXES_EN

    pref = None
    for p in sorted(prefixes, key=len, reverse=True):
        if t == p or t.startswith(p + " "):
            pref = p
            break
        if t.startswith(p + ",") or t.startswith(p + "."):
            pref = p
            break
    if not pref:
        return ""

    detail = t[len(pref):].lstrip(" ,.:;!-—–")
    if not detail:
        return ""

    junk = {
        "thats what i said","that's what i said","what i said",
        "exactly","right","correct","yeah","si","sí"
    }
    if detail in junk:
        return ""
    
        # If the "detail" itself is just an affirmation, drop it
    det_norm = _normalize_text(detail)
    if det_norm in {"thats right","thats correct","correct","right","exactly","yes","yeah","yep","ok","okay"}:
        return ""

    return detail
# =====================================

STOPWORDS = {
    "i","im","i'm","i'm","id","am","a","an","the","for","to","of","on","in","at",
    "please","just","like","that","this","it","is","was","were","be","been","being","do","did",
    "does","and","or","but","so","then","than","with","you","your","yours","my","mine","we","us",
    "our","ours","me","him","her","them","they","their","theirs","not","no","yeah","yes","yep",
    "nope","okay","ok","alright","right","actually","instead","rather","meant","said","looking",
    "searching","trying","need","want","get","got","buy","find","finding","for a","for the",
    "buddy","pal","friend","dude","man","sir","maam","miss","mister","mrs","mr","dr","professor",
    "is","are","was","were","will","would","could","should","might","may","can","must"
}

def extract_item_phrase(reply_text: str) -> str | None:
    if not isinstance(reply_text, str):
        return None
    # NEW: ignore classic affirmation phrasings to avoid junk extraction
    t_norm = _normalize_text(reply_text or "")
    if re.search(r"\b(yes|yeah|yep|ok|okay|correct|exactly|thats right|thats it|thats what i said)\b", t_norm):
        return None
    
    # Additional check: if the text starts with affirmation phrases, ignore it
    t_lower = reply_text.lower().strip()
    affirmation_starts = [
        "thats right", "that's right", "thats correct", "that's correct",
        "thats it", "that's it", "thats true", "that's true",
        "yes", "yeah", "yep", "ok", "okay", "correct", "exactly"
    ]
    for phrase in affirmation_starts:
        if t_lower.startswith(phrase):
            return None
    
    # Additional check: if it's just a single common word, ignore it
    single_word_stopwords = {"is", "are", "was", "were", "will", "would", "could", "should", "might", "may", "can", "must", "yes", "no", "ok", "okay"}
    if t_lower in single_word_stopwords:
        return None

    t = reply_text.lower()
    
    # Enhanced patterns for corrections and clarifications
    patterns = [
        # "No, I'm looking for surge" -> "surge"
        r"(?:no[, ]+\s*)?(?:i'?m\s+)?looking\s+for\s+(?:a|an|the)?\s*([a-z0-9\- ]{1,})",
        # "I need surge" -> "surge"
        r"(?:i\s+)?need\s+(?:a|an|the)?\s*([a-z0-9\- ]{1,})",
        # "I want surge" -> "surge"
        r"(?:i\s+)?want\s+(?:a|an|the)?\s*([a-z0-9\- ]{1,})",
        # "I meant surge" -> "surge"
        r"(?:i\s+)?meant\s+(?:a|an|the)?\s*([a-z0-9\- ]{1,})",
        # "I said surge" -> "surge"
        r"(?:i\s+)?said\s+(?:a|an|the)?\s*([a-z0-9\- ]{1,})",
        # "Actually surge" -> "surge"
        r"actually\s+(?:a|an|the)?\s*([a-z0-9\- ]{1,})",
        # "Instead surge" -> "surge"
        r"instead\s+(?:a|an|the)?\s*([a-z0-9\- ]{1,})",
        # "It's surge" -> "surge"
        r"(?:it'?s|i'?m|i am)\s+(?:a|an|the)?\s*([a-z0-9\- ]{1,})",
    ]
    
    for p in patterns:
        m = re.search(p, t)
        if m:
            cand = " ".join(m.group(1).strip().split())
            # Remove common stopwords but keep single words
            tokens = [w for w in cand.split() if w not in STOPWORDS]
            cand = " ".join(tokens).strip()
            # Return even single words for corrections (like "surge")
            if cand:
                return cand
    
    # Fallback: extract meaningful chunks
    words = [w for w in re.sub(r"[^a-z0-9\- ]", " ", t).split() if w and w not in STOPWORDS]
    best = ""
    for n in range(4, 1, -1):
        for i in range(0, max(0, len(words) - n + 1)):
            chunk = " ".join(words[i:i+n])
            if len(chunk) > len(best):
                best = chunk
        if best: break
    return best or None

# ======= Operator intent detection =======
OPERATOR_PATTERNS = [
    r"\boperator\b", r"\bhuman\b", r"\breal person\b", r"\bagent\b", r"\battendant\b",
    r"\brepresentative\b", r"\blive\b", r"\btalk to (?:someone|somebody|a person)\b",
    r"\blet me talk\b", r"\bspeak to (?:someone|somebody|a person)\b", r"\bconnect me\b",
    r"\bcustomer service\b", r"\breceptionist\b", r"\bfront desk\b"
]

def wants_operator(text: str) -> bool:
    t = (text or "").lower()
    for p in OPERATOR_PATTERNS:
        if re.search(p, t):
            return True
    return False

def _check_direct_department_request(text: str) -> str | None:
    """
    Check if the caller is directly requesting a specific department.
    Returns the department name if found, None otherwise.
    """
    if not text:
        return None
    
    t = text.lower().strip()

    # Global hard rule: any mention of manager (or synonyms) routes to manager
    if any(x in t for x in ["manager", "supervisor", "superintendent"]):
        print(f"[DEPT_SKIP] Hard-match manager keyword in: '{text}'")
        return "manager"
    
    # Direct department requests
    department_patterns = {
        "grocery": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:grocery|groceries)\b",
            r"\b(?:grocery|groceries)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:grocery|groceries)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:grocery|groceries)\b",
        ],
        "electronics": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:electronics|electronic)\b",
            r"\b(?:electronics|electronic)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:electronics|electronic)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:electronics|electronic)\b",
        ],
        "clothing": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:clothing|clothes|apparel)\b",
            r"\b(?:clothing|clothes|apparel)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:clothing|clothes|apparel)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:clothing|clothes|apparel)\b",
        ],
        "pharmacy": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:pharmacist|pharm|pharma|drug store|drugstore|medicine|meds|prescription|rx)\b",
            r"\b(?:pharmacist|pharm|pharma|drug store|drugstore)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:pharmacist|pharm|pharma|drug store|drugstore)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:pharmacist|pharm|pharma|drug store|drugstore)\b",
            r"\b(?:talk to|speak to|speak with)\s+(?:pharmacist|pharm|pharma)\b",
            r"\b(?:refill|pick up|pickup)\s+(?:prescription|rx|medicine|meds)\b",
            r"\b(?:prescription|rx)\s+(?:ready|pickup|pick up|refill)\b",
        ],
        "bakery": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:bakery|baker)\b",
            r"\b(?:bakery|baker)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:bakery|baker)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:bakery|baker)\b",
        ],
        "deli": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:deli|deli counter)\b",
            r"\b(?:deli|deli counter)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:deli|deli counter)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:deli|deli counter)\b",
        ],
        "home and garden": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:home and garden|home & garden|garden|home)\b",
            r"\b(?:home and garden|home & garden|garden|home)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:home and garden|home & garden|garden|home)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:home and garden|home & garden|garden|home)\b",
        ],
        "health and beauty": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:health and beauty|beauty|health)\b",
            r"\b(?:health and beauty|beauty|health)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:health and beauty|beauty|health)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:health and beauty|beauty|health)\b",
        ],
        "pet supplies": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:pet supplies|pets|pet)\b",
            r"\b(?:pet supplies|pets|pet)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:pet supplies|pets|pet)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:pet supplies|pets|pet)\b",
        ],
        "customer service": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to)\s+(?:customer service|service)\b",
            r"\b(?:customer service|service)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+in\s+(?:customer service|service)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:customer service|service)\b",
        ],
        "manager": [
            r"\b(?:i need|i want|i'm looking for|looking for|help with|connect me to|speak to|talk to|put|get)\s+(?:manager|supervisor|superintendent)\b",
            r"\b(?:i need|i want)\s+to\s+(?:speak to|talk to|put|get)\s+(?:manager|supervisor|superintendent)\b",
            r"\b(?:put|get)\s+(?:the\s+)?(?:manager|supervisor|superintendent)\s+(?:on\s+the\s+phone|on\s+phone|on\s+line)\b",
            r"\b(?:manager|supervisor|superintendent)\s+(?:department|section|area)\b",
            r"\b(?:i need|i want)\s+help\s+from\s+(?:manager|supervisor|superintendent)\b",
            r"\b(?:can you|will you)\s+(?:connect|transfer)\s+me\s+to\s+(?:manager|supervisor|superintendent)\b"
        ]
    }
    
    # Check each department pattern
    for dept_name, patterns in department_patterns.items():
        for pattern in patterns:
            if re.search(pattern, t):
                if dept_name == "pharmacy":
                    print(f"[DEPT_SKIP] Detected direct department request: '{text}' -> {dept_name}")
                    return dept_name
                print(f"[DEPT_SKIP] Detected direct department request: '{text}' -> {dept_name}")
                return dept_name
    
    # Also check for simple department names (e.g., just "electronics" or "grocery")
    simple_departments = {
        "grocery": r"\b(?:grocery|groceries)\b",
        "electronics": r"\b(?:electronics|electronic)\b", 
        "clothing": r"\b(?:clothing|clothes|apparel)\b",
        "pharmacy": r"\b(?:pharmacist|pharm|pharma|drug store|drugstore|medicine|meds|prescription|rx)\b",
        "pharmacy_greeting": r"\b(?:pharmacy)\b",
        "bakery": r"\b(?:bakery|baker)\b",
        "deli": r"\b(?:deli|deli counter)\b",
        "home and garden": r"\b(?:home and garden|home & garden|garden|home)\b",
        "health and beauty": r"\b(?:health and beauty|beauty|health)\b",
        "pet supplies": r"\b(?:pet supplies|pets|pet)\b",
        "customer service": r"\b(?:customer service|service)\b",
        "manager": r"\b(?:manager|supervisor|superintendent)\b"
    }
    
    for dept_name, pattern in simple_departments.items():
        if re.search(pattern, t):
            if dept_name == "pharmacy":
                print(f"[DEPT_SKIP] Detected simple department request: '{text}' -> {dept_name}")
                return dept_name
            print(f"[DEPT_SKIP] Detected simple department request: '{text}' -> {dept_name}")
            return dept_name
    
    return None

# ======= NEW: Extract product name for confirmation =======
def extract_product_for_confirm(phrase: str, context: str = "confirm") -> str:
    """
    Extracts product name with context-aware behavior:
    
    Context "confirm" (first confirmation): 
    - "do you carry horizon organic milk?" -> "do you carry horizon organic milk"
    - More natural, keeps most of original phrase
    
    Context "dept_choice" or "followup":
    - "do you carry horizon organic milk?" -> "horizon organic milk"
    - Clean product name only
    
    Returns the appropriately cleaned phrase for the context.
    """
    if not isinstance(phrase, str):
        return phrase
    
    t = phrase.lower().strip()
    
    # For first confirmation, be more conservative - keep most of the phrase
    if context == "confirm":
        # Only remove very obvious filler words at the beginning
        filler_words = [
            r"^(?:um|uh|well|so|like|you know|i mean)\s+",
            r"^(?:actually|basically|literally|honestly)\s+",
        ]
        
        for pattern in filler_words:
            t = re.sub(pattern, "", t)
        
        # Remove trailing punctuation but keep the core phrase
        t = re.sub(r"[?.,!;:]$", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        
        return t
    
    # For department choice and followup, extract just the product name
    else:
        # Common question patterns to remove
        question_patterns = [
            r"^(?:do you|can you|will you|would you)\s+(?:carry|have|sell|stock|carry|offer|provide)\s*",
            r"^(?:where can i find|where do you keep|where is|where are)\s*",
            r"^(?:i'm looking for|i need|i want|i'm trying to find|looking for)\s*",
            r"^(?:do you know if you|can you tell me if you)\s+(?:carry|have|sell)\s*",
            r"^(?:are you able to|is it possible to)\s+(?:get|find|locate)\s*",
            r"^(?:i was wondering if you|i'm wondering if you)\s+(?:carry|have|sell)\s*",
        ]
        
        # Remove question patterns
        for pattern in question_patterns:
            t = re.sub(pattern, "", t)
        
        # Remove punctuation FIRST (so trailing patterns can match properly)
        t = re.sub(r"[?.,!;:]", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        
        # Remove trailing question phrases (like "do you have those?")
        # More general approach - look for question patterns at the end
        trailing_questions = [
            # Remove "do you have/carry/sell those/them/it/this/that" patterns
            r"\s+do you\s+(?:have|carry|sell)\s+(?:those|them|it|this|that)\s*$",
            r"\s+can you\s+(?:have|carry|sell)\s+(?:those|them|it|this|that)\s*$",
            r"\s+will you\s+(?:have|carry|sell)\s+(?:those|them|it|this|that)\s*$",
            r"\s+would you\s+(?:have|carry|sell)\s+(?:those|them|it|this|that)\s*$",
            
            # Remove "do you have/carry/sell" patterns
            r"\s+do you\s+(?:have|carry|sell)\s*$",
            r"\s+can you\s+(?:have|carry|sell)\s*$",
            r"\s+will you\s+(?:have|carry|sell)\s*$",
            r"\s+would you\s+(?:have|carry|sell)\s*$",
            
            # Remove "do you/can you" patterns
            r"\s+do you\s*$",
            r"\s+can you\s*$",
            r"\s+will you\s*$",
            r"\s+would you\s*$",
            
            # Remove "can you help" patterns
            r"\s+can you\s+help\s*$",
            r"\s+will you\s+help\s*$",
            r"\s+would you\s+help\s*$",
        ]
        
        for pattern in trailing_questions:
            t = re.sub(pattern, "", t)
        
        # Remove common filler words at the beginning
        filler_words = [
            r"^(?:um|uh|well|so|like|you know|i mean)\s+",
            r"^(?:actually|basically|literally|honestly)\s+",
            r"^(?:the|a|an)\s+",  # Remove leading articles
        ]
        
        for pattern in filler_words:
            t = re.sub(pattern, "", t)
        
        # Final cleanup
        t = re.sub(r"\s+", " ", t).strip()
        
        # If we ended up with nothing at all, return original
        if len(t.split()) == 0:
            return phrase.strip()
        
        return t

# ======= NEW: Spanish suspicion heuristic =======
SPANISH_MARKERS = {
    "sí","si","hola","buenos días","buenas tardes","buenas noches","gracias","por favor",
    "perdón","disculpa","dónde","numero","número","porque","por qué","necesito","busco","quiero",
    "hablas español","en español","ayuda","producto","precio","dame","llámame","tienda"
}
SPANISH_LETTERS = "áéíóúñü¡¿"

def is_probably_spanish(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    # obvious accented letters or inverted punctuation
    if any(ch in t for ch in SPANISH_LETTERS):
        return True
    # common words/phrases
    for w in SPANISH_MARKERS:
        if re.search(rf"\b{re.escape(w)}\b", t):
            return True
    return False

# === NEW: localize confirm phrase we SPEAK back ===
def localize_for_confirm(phrase: str, target_lang: str, context: str = "confirm") -> str:
    """
    Returns the phrase in the language we want to SPEAK back to the caller
    (for the confirm prompt only). Keeps it short and neutral.

    - If target_lang startswith('es'):
        * if it already looks Spanish, return as-is
        * else, translate/paraphrase briefly into Spanish
    - Else, return as-is (English path)
    """
    # NEW: Extract product name with context-aware behavior
    clean_phrase = extract_product_for_confirm(phrase, context)
    
    tl = (target_lang or "en").lower()
    if tl.startswith("es"):
        # already looks Spanish? just use it
        if is_probably_spanish(clean_phrase):
            return clean_phrase.strip()

        try:
            prompt = f"""Translate or paraphrase briefly into Spanish for a retail store item/intent.
- Keep it short (2–10 words), natural, lowercase.
- No quotes, no punctuation at the end, no commentary.
- If it's greetings only, return: unclear

Text: {clean_phrase}"""
            resp = client.chat_completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.2
            ) if hasattr(client, "chat_completions") else client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.2
            )
            out = (resp.choices[0].message.content or "").strip().lower()
            out = out.strip().strip(".").strip(",")
            if out and out != "unclear":
                return out
        except Exception:
            pass
    return clean_phrase.strip()
# ============================================

JOBS = {}

# Tracks job_ids that already got the initial tiny chirp during the "no meta" race.
INITIAL_CHIRPED = set()

def record_args(action_url: str, max_len: int, timeout_secs: int, beep_override: bool | None = None):
    return dict(
        action=action_url,
        method="POST",
        maxLength=max_len,
        timeout=timeout_secs,
        trim="trim-silence",
        playBeep=(RECORD_BEEP if beep_override is None else beep_override),
        finishOnKey=""
    )

def _choose_operator_number(dept: str | None) -> str | None:
    if dept and dept in DEPT_DIAL_MAP:
        return DEPT_DIAL_MAP.get(dept)
    if "Customer Service" in DEPT_DIAL_MAP:
        return DEPT_DIAL_MAP.get("Customer Service")
    return OPERATOR_NUMBER or None

# ===== NEW helpers for gather-first flow =====
def _primary_lang_code(lang: str) -> str:
    return "es-US" if (lang or "en").startswith("es") else "en-US"

def quick_lang_guess(text: str, default: str="en") -> str:
    t = (text or "").lower()
    if is_probably_spanish(t):
        return "es"
    return default

def prepare_reply(job_id: str, local_wav_path: str, base_url: str):
    try:
        raw, lang_detected, lang_prob = transcribe_file(local_wav_path)
        
        # If Whisper is not available, fall back to Twilio Gather
        if not raw and not USE_LOCAL_WHISPER:
            logger.warning("Local Whisper not available; falling back to Twilio Gather for job %s", job_id)
            response_url = tts_line_url("Sorry, I couldn't process that recording. Please say what you need.", None, base_url, job_id, "Fallback")
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "phase": "followup_ready",
                "department": None,
                "waiting_for_followup": True,
                "fallback_to_gather": True
            })
            return
        # decide language
        caller_lang = lang_detected if lang_prob >= 0.70 else "en"
        repaired = repair_transcript(raw)
        # NEW: flag possible Spanish even if we defaulted to English
        suspect_es = (
            (lang_detected.startswith("es") and lang_prob < 0.95) or
            is_probably_spanish(raw) or
            is_probably_spanish(repaired)
        )
        print(f"[ASR] raw='{raw}'  repaired='{repaired}'  lang={lang_detected} p={lang_prob:.2f} suspect_es={suspect_es}")

        # NEW: non-item store info? answer immediately and end
        intent, info_line = detect_store_info_intent(raw) if raw else (None, None)
        if not intent:
            intent, info_line = detect_store_info_intent(repaired)
        if intent and info_line:
            out_name = f"{CACHE_SUBDIR}/info_{intent}_{job_id}.mp3"
            response_url = tts_line_url(info_line, out_name, base_url, job_id, "Store Info")
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "phase": "followup_ready",
                "department": None,
                "waiting_for_followup": True
            })
            print(f"[JOB {job_id}] store-info intent='{intent}' -> waiting for followup response")
            return

        # Operator escape on first utterance
        if wants_operator(raw) or wants_operator(repaired):
            op_num = _choose_operator_number(None)
            if op_num:
                spoken = msg("connecting_operator", caller_lang)
                out_name = f"{CACHE_SUBDIR}/op_{job_id}.mp3"
                response_url = tts_line_url(spoken, out_name, base_url)
                update_state(job_id, {
                    "ready": True,
                    "phase": "operator_ready",
                    "needs_confirm": False,
                    "response_url": response_url,
                    "op_number": op_num,
                    "caller_lang": caller_lang,
                    "suspect_spanish": suspect_es,
                })
                print(f"[JOB {job_id}] operator -> dialing {op_num}")
                return
            
        # === Aisle question short-circuit ===
        if is_aisle_question(raw) or is_aisle_question(repaired):
            item_q = extract_aisle_item(raw) or extract_aisle_item(repaired)
            if item_q:
                locs = locations_for_item(item_q)
                line = speak_aisle_answer(item_q, locs, caller_lang)
                out_name = f"{CACHE_SUBDIR}/aisle_{job_id}.mp3"
                response_url = tts_line_url(line, out_name, base_url)
                update_state(job_id, {
                    "ready": True,
                    "needs_confirm": False,
                    "response_url": response_url,
                    "phase": "final_ready",
                    "department": None
                })
                print(f"[JOB {job_id}] aisle -> item='{item_q}' locs={locs}")
                return

        if repaired != "unclear":
            confirm_prefix = msg("confirm_prefix", caller_lang)
            voice_phrase = localize_for_confirm(repaired, caller_lang)  # NEW: speak localized phrase
            confirm_line = f"{confirm_prefix} {voice_phrase}?"
            confirm_url = tts_line_url(confirm_line, None, base_url, job_id, "Confirm")
            if not confirm_url or confirm_url == "None":
                # Fallback to cached yes/no prompt only
                confirm_url = tts_line_url(msg("yes_no", caller_lang), None, base_url, job_id, "ConfirmFallback")
            time.sleep(0.25)
            update_state(job_id, {
                "ready": True,
                "needs_confirm": True,
                "confirm_url": confirm_url,
                "heard_text": repaired,               # canonical for logic/routing
                "heard_text_voice": voice_phrase,     # localized for speaking
                "confirm_done": False,
                "phase": "confirm",
                "bg_played": False,
                "correction_hops": 0,
                "caller_lang": caller_lang,
                "suspect_spanish": suspect_es,
                "confirm_round": 0,   # start round counter
            })
            print(f"[JOB {job_id}] confirm -> {confirm_url} heard='{repaired}' voice='{voice_phrase}' lang={caller_lang} suspect_es={suspect_es}")
            return

        spoken = random.choice([
            msg("reask", "en") if caller_lang=="en" else msg("reask", caller_lang),
            msg("reask_cap", "en") if caller_lang=="en" else msg("reask_cap", caller_lang),
        ])
        response_url = tts_line_url(spoken, None, base_url, job_id, "Clarify")
        update_state(job_id, {
            "ready": True,
            "needs_confirm": False,
            "needs_clarify": True,
            "response_url": response_url,
            "heard_text": raw or "",
            "department": None,
            "phase": "clarify",
            "bg_played": False,
            "caller_lang": caller_lang,
            "suspect_spanish": suspect_es,
        })
        print(f"[JOB {job_id}] clarify -> {response_url} (heard='{raw}') lang={caller_lang} suspect_es={suspect_es}")
    except Exception as e:
        response_url = tts_line_url(msg("err_global","en"), None, base_url, job_id, "Error")
        update_state(job_id, {
            "ready": True, "needs_confirm": False,
            "response_url": response_url, "needs_clarify": False, "phase": "error"
        })
        print(f"[JOB {job_id}] error -> {e}\n{traceback.format_exc()}")

def prepare_reply_from_recording(job_id: str, recording_url: str, base_url: str):
    try:
        ensure_static_dir()
        local_wav = os.path.join(app.static_folder, f"last_call_{job_id}.wav")
        download_twilio_recording(recording_url, local_wav)
        prepare_reply(job_id, local_wav, base_url)
    except Exception as e:
        response_url = tts_line_url(msg("err_global","en"), None, base_url, job_id, "Error")
        update_state(job_id, {
            "ready": True, "needs_confirm": False,
            "response_url": response_url, "needs_clarify": False, "phase": "error"
        })
        print(f"[JOB {job_id}] error(during download) -> {e}\n{traceback.format_exc()}")

# ---------- NEW HELPERS (paste once) ----------

AFFIRMATIONS = {
    "yes","yeah","yep","correct","right","that is right","that's right",
    "affirmative","sure","uh huh","exactly","you got it","that's correct","that's correct"
}

def is_affirmation(text: str) -> bool:
    s = (text or "").strip().lower()
    # normalize punctuation/apostrophes
    s = s.replace("'","")
    return s in AFFIRMATIONS or s.endswith(", buddy.") and s.replace(", buddy.", "") in AFFIRMATIONS

# Common brand/phrase repairs BEFORE intent classification
REPAIR_PATTERNS = [
    (r"\b(car ?hart|car ?hard|car heart|car hat|carhard|carhart)\b", "carhartt"),
    (r"\bpeda?r bread\b", "pita bread"),
    (r"\bgyro(s)?\b", "gyros"),
    (r"\b4k roku stick\b", "roku 4k stick"),
]

def normalize_item_phrase(s: str) -> str:
    if not s:
        return s
    t = s.lower().strip()
    # if ASR hallucinated "return <something>", but caller likely said a brand like carhartt
    # only treat as a returns intent if the phrase actually mentions policy/receipt/window
    if t.startswith("return ") and not re.search(r"\b(policy|receipt|window|days|refund|exchange)\b", t):
        t = t.replace("return ", "", 1).strip()
    for pat, repl in REPAIR_PATTERNS:
        t = re.sub(pat, repl, t, flags=re.I)
    # trim trailing filler tokens
    t = re.sub(r"[?.!]+$", "", t).strip()
    return t

# Single-word nouns we should treat as VALID items (don't call them "unclear")
SINGLE_WORD_ALLOW = {
	"charger","paper","toothpaste","beanie","cap","hat","shoes","bread","pita","roku","stick","diapers","printer","binder","markers",
	"coupon","coupons","grocery","groceries"
}

# Single-word fillers/greetings that should not be treated as items
STOP_SINGLEWORD = {
	"hi","hello","hey","thanks","thank you","bye","goodbye","yo","sup","okay","ok","please"
}

# Best-guess department fallback by keyword
def _guess_department_from_keywords(item: str) -> str | None:
    t = (item or "").lower()
    # prefer specific hits first
    if any(k in t for k in ["roku","tv","television","hdmi","ps5","xbox","charger","charging","usb","4k"]):
        return "Electronics"
    if any(k in t for k in ["paper","notebook","binder","pen","pencil","marker","printer","ink","toner"]):
        return "Office and Stationery"
    # Avoid mapping "candy bar" to Bakery: candy/chocolate should be Grocery
    if any(k in t for k in ["pita","bakery","baguette","loaf"]):
        return "Bakery"
    if any(k in t for k in ["candy","chocolate","chocolate bar","candy bar","snack bar","granola bar","protein bar"]):
        return "Grocery"
    if any(k in t for k in ["toothpaste","toothbrush","shampoo","soap","deodorant","crest","lotion","razor","diapers"]):
        return "Health and Beauty"
    if any(k in t for k in ["beanie","knit cap","carhartt","jacket","shirt","pants","nike","shoes","hoodie","socks"]):
        return "Clothing"
    if any(k in t for k in ["return","refund","exchange"]):
        return "Customer Service"
    return None

# ---- Ambiguous items that live in multiple departments ----
# Add phrases in lowercase; match is substring-based.
AMBIGUOUS_ITEMS = {
    # bakery vs grocery
    "pita": ["Bakery", "Grocery"],
    "pita bread": ["Bakery", "Grocery"],
    "bread": ["Bakery", "Grocery"],
    "baguette": ["Bakery", "Grocery"],
    # examples to expand later if you want:
    # "rotisserie chicken": ["Deli", "Grocery"],
    # "sushi": ["Deli", "Grocery"],
}

def department_candidates(item: str) -> list[str]:
    """
    Returns a de-duplicated list of possible departments for the item.
    Uses comprehensive grocery routing if available, plus existing rules/keywords.
    """
    if not item:
        return []
    t = (item or "").lower().strip()
    cands: list[str] = []

    # 1) Use comprehensive grocery routing if available
    if GROCERY_ROUTING_AVAILABLE:
        grocery_cands = get_grocery_department_candidates(t)
        for dept in grocery_cands:
            if dept not in cands:
                cands.append(dept)
        # If we found grocery departments, return them
        if cands:
            return cands

    # 2) explicit ambiguities by substring (fallback)
    for key, opts in AMBIGUOUS_ITEMS.items():
        if key in t:
            for d in opts:
                if d not in cands:
                    cands.append(d)

    # 3) your existing rule-based/keyword paths
    d_rule = classify_department_rule_based(t)
    if d_rule and d_rule not in cands:
        cands.append(d_rule)
    d_kw = _guess_department_from_keywords(t)
    if d_kw and d_kw not in cands:
        cands.append(d_kw)

    # 4) fallback
    if not cands:
        cands.append("Customer Service")

    return cands

# ---- Aisle index & aisle intent helpers ----
# Minimal example map; extend as you like (can be moved to env or JSON later)
AISLE_INDEX = {
    # aisles
    "toothpaste": ["aisle 5"],
    "paper towels": ["aisle 8"],
    "printer paper": ["aisle 12"],
    "markers": ["aisle 12"],
    "bread": ["aisle 10"],    # shelf bread location
    "pita": ["aisle 10"],
    "pita bread": ["aisle 10"],
    # departments (we merge these automatically if they also exist in AMBIGUOUS_ITEMS)
    # e.g., bakery/deli, etc.
}

# Reuse existing ambiguous department map you already have:
# AMBIGUOUS_ITEMS = { "pita": ["Bakery","Grocery"], ... }

AISLE_RX = re.compile(
    r"\b(what|which)\s+(aisle|isle)\b|\b(aisle|isle)\s*(number)?\b|where\s+.*\baisle\b",
    re.I
)

def is_aisle_question(text: str) -> bool:
    return bool(AISLE_RX.search((text or "")))

def extract_aisle_item(q: str) -> str:
    """
    Pull the item from an aisle question like:
      - "what aisle is pita bread"
      - "which aisle for toothpaste"
      - "what aisle is the pita bread located in"
    Falls back to normalize_item_phrase() if regex misses.
    """
    t = (q or "").lower().strip()
    t = re.sub(r"[?.!]+$", "", t)
    # common forms
    patterns = [
        r"(?:what|which)\s+(?:aisle|isle)\s+(?:is|for)\s+(?:the\s+)?(.+)$",
        r"(?:what|which)\s+(?:aisle|isle)\s+(?:can\s+i\s+find|has)\s+(?:the\s+)?(.+)$",
        r"(?:which|what).*\b(?:aisle|isle)\b.*\bfor\s+(?:the\s+)?(.+)$",
        r"(?:what|which).*\b(?:aisle|isle)\b.*\bis\s+(?:the\s+)?(.+)$",
        r"(?:where).*\b(?:aisle|isle)\b.*\b(?:for|with)\s+(?:the\s+)?(.+)$",
    ]
    for p in patterns:
        m = re.search(p, t)
        if m:
            cand = m.group(1).strip()
            # strip trailing prepositions like "in", "at", "on"
            cand = re.sub(r"\b(in|at|on|located|located in)$", "", cand).strip()
            # clean with your existing normalizer
            return normalize_item_phrase(cand)
    # fallback: remove the word "aisle" and try to normalize
    t2 = re.sub(r"\b(what|which)\s+(aisle|isle)\b", "", t)
    t2 = re.sub(r"\b(aisle|isle)\b", "", t2)
    return normalize_item_phrase(t2)

def locations_for_item(item: str) -> list[str]:
    """
    Merge aisle numbers from AISLE_INDEX + department placements from AMBIGUOUS_ITEMS.
    Deduplicate while preserving order.
    """
    if not item:
        return []
    key = item.lower().strip()

    locs = []

    # direct/partial hits from AISLE_INDEX
    for k, arr in AISLE_INDEX.items():
        if k in key or key in k:
            for a in arr:
                if a not in locs:
                    locs.append(a)

    # department placements from ambiguity map
    for k, depts in AMBIGUOUS_ITEMS.items():
        if k in key or key in k:
            for d in depts:
                if d not in locs:
                    locs.append(d)

    return locs

def speak_aisle_answer(item: str, locs: list[str], lang: str = "en") -> str:
    if not locs:
        return (f"I don't have an aisle for {item} yet." if not lang.startswith("es")
                else f"No tengo el pasillo para {item} todavía.")
    # join nicely: "aisle 10 and in the Bakery"
    if len(locs) == 1:
        where = locs[0]
        return (f"{item} is in {where}." if not lang.startswith("es")
                else f"{item} está en {where}.")
    # two or more
    last = locs[-1]
    first = ", ".join(locs[:-1])
    conj = " and " if not lang.startswith("es") else " y "
    return (f"{item} is in {first}{conj}{last}."
            if not lang.startswith("es")
            else f"{item} está en {first}{conj}{last}.")

# ---------- END NEW HELPERS ----------

# ===== NEW: prepare reply from text (Gather-first path) =====
def prepare_reply_from_text(job_id: str, raw_text: str, base_url: str):
    """Mirror of prepare_reply() but starting from text (Gather)."""
    asr_start_time = time.time()
    try:
        # lightweight language pick
        lang_start = time.time()
        lang_detected = quick_lang_guess(raw_text, DEFAULT_LANG)
        lang_prob = 0.75 if lang_detected == "es" else 0.60  # heuristic confidences
        caller_lang = lang_detected if lang_prob >= 0.70 else "en"
        lang_time = time.time() - lang_start

        repair_start = time.time()
        repaired = repair_transcript(raw_text)
        repair_time = time.time() - repair_start

        suspect_es = (
            caller_lang.startswith("es")
            or is_probably_spanish(raw_text)
            or is_probably_spanish(repaired)
        )
        print(f"[ASR-GATHER] raw='{raw_text}' repaired='{repaired}' lang={caller_lang} suspect_es={suspect_es}")

        # TOP-PRIORITY: any mention of "coupon" routes to coupon flow
        text_l = (raw_text or "").lower()
        repaired_l = (repaired or "").lower()
        # HARD PRIORITY: "pharmacy" goes to pharmacy greeting, "pharmacist" goes to direct connection
        # This creates a clear hierarchy: pharmacy first, then pharmacist within pharmacy flow
        if "pharmacy" in text_l or "pharmacy" in repaired_l:
            # Just saying "pharmacy" - go to pharmacy greeting for prescription queries
            # Let the normal flow handle this through generate_response
            pass
        elif "pharmacist" in text_l or "pharmacist" in repaired_l:
            # Direct request for pharmacist - connect immediately
            dept_name = "pharmacy"
            if SHARED_DATA_AVAILABLE:
                line = (
                    shared_data.get_dialogue_template("pharmacy", "connect_pharmacist")
                    or shared_data.get_dialogue_template("pharmacy", "connect_pharmacy_staff")
                    or "I'll connect you to our pharmacist now."
                )
            else:
                line = "I'll connect you to our pharmacist now."
            response_url = tts_line_url(line, None, base_url, job_id, "DeptSkip")
            if not response_url or response_url == "None":
                response_url = tts_line_url("I'll connect you to an associate who can help with that.", None, base_url, job_id, "DeptSkipFallback")
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "phase": "final_ready",
                "department": dept_name,
                "caller_lang": caller_lang,
                "suspect_spanish": suspect_es,
            })
            print(f"[JOB {job_id}] department-skip -> {dept_name} (pharmacist direct request)")
            return
        if "coupon" in text_l or "coupon" in repaired_l:
            # Speak the coupons intro and enter coupon follow-up gather
            spoken, dept = generate_response("coupons", caller_lang)
            response_url = tts_line_url(spoken, None, base_url, job_id, "Coupon Intro")
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "needs_clarify": False,
                "department": dept,
                "phase": "coupon_followup",
                "caller_lang": caller_lang,
                "suspect_spanish": suspect_es,
            })
            print(f"[JOB {job_id}] coupon-intent -> coupon_followup (dept={dept})")
            return

        # PRIORITY: direct department requests should bypass store-info
        dept_check_start = time.time()
        department_skip = _check_direct_department_request(raw_text) or _check_direct_department_request(repaired)
        dept_check_time = time.time() - dept_check_start
        print(f"[TIMING] Department detection took {dept_check_time:.3f}s")
        if department_skip:
            dept_name = department_skip
            # Special handling for pharmacy_greeting - go to pharmacy greeting, not direct connection
            if dept_name == "pharmacy_greeting":
                if SHARED_DATA_AVAILABLE:
                    line = shared_data.get_dialogue_template("pharmacy", "pharmacy_greeting") or "Thanks for calling the pharmacy. I can help with prescription refills, medical supply inventory, etc. How can I help?"
                else:
                    line = "Thanks for calling the pharmacy. I can help with prescription refills, medical supply inventory, etc. How can I help?"
                response_url = tts_line_url(line, None, base_url, job_id, "PharmacyGreeting")
                if not response_url or response_url == "None":
                    response_url = tts_line_url("Thanks for calling the pharmacy. I can help with prescription refills, medical supply inventory, etc. How can I help?", None, base_url, job_id, "PharmacyGreetingFallback")
                update_state(job_id, {
                    "ready": True,
                    "needs_confirm": False,
                    "response_url": response_url,
                    "phase": "pharmacy_followup",
                    "department": "pharmacy",
                    "caller_lang": caller_lang,
                    "suspect_spanish": suspect_es,
                })
                print(f"[JOB {job_id}] pharmacy_greeting -> pharmacy_followup (greeting, not direct connection)")
                return
            # Use dashboard template for manager/pharmacy phrasing if available
            elif SHARED_DATA_AVAILABLE and dept_name == "manager":
                line = shared_data.get_dialogue_template("general", "connect_manager") or "I'll connect you to the manager now."
            elif SHARED_DATA_AVAILABLE and dept_name == "pharmacy":
                line = (
                    shared_data.get_dialogue_template("pharmacy", "connect_pharmacist")
                    or shared_data.get_dialogue_template("pharmacy", "connect_pharmacy_staff")
                    or "I'll connect you to our pharmacist now."
                )
            else:
                line = f"I'll connect you to {dept_name} now."
            response_url = tts_line_url(line, None, base_url, job_id, "DeptSkip")
            if not response_url or response_url == "None":
                response_url = tts_line_url("I'll connect you to an associate who can help with that.", None, base_url, job_id, "DeptSkipFallback")
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "phase": "final_ready",
                "department": dept_name,
                "caller_lang": caller_lang,
                "suspect_spanish": suspect_es,
            })
            print(f"[JOB {job_id}] department-skip -> {dept_name} (no confirmation needed)")
            return

        # Store-info? Only if not a department request
        intent, info_line = detect_store_info_intent(raw_text) if raw_text else (None, None)
        if not intent:
            intent, info_line = detect_store_info_intent(repaired)
        if intent and info_line:
            # Use text-based caching; avoid job-specific filenames
            response_url = tts_line_url(info_line, None, base_url, job_id, "StoreInfo")
            if not response_url or response_url == "None":
                # Fallback to prewarmed phrase to avoid pending state
                response_url = tts_line_url("Our store hours are 7 AM to 10 PM, seven days a week.", None, base_url, job_id, "StoreInfoFallback")
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "phase": "followup_ready",
                "department": None,
                "waiting_for_followup": True
            })
            print(f"[JOB {job_id}] store-info intent='{intent}' -> waiting for followup response")
            return

        # NEW: Department skip logic - if caller directly requests a department, skip confirmation
        department_skip = _check_direct_department_request(raw_text) or _check_direct_department_request(repaired)
        if department_skip:
            dept_name = department_skip
            # Special handling for pharmacy_greeting - go to pharmacy greeting, not direct connection
            if dept_name == "pharmacy_greeting":
                if SHARED_DATA_AVAILABLE:
                    line = shared_data.get_dialogue_template("pharmacy", "pharmacy_greeting") or "Thanks for calling the pharmacy. I can help with prescription refills, medical supply inventory, etc. How can I help?"
                else:
                    line = "Thanks for calling the pharmacy. I can help with prescription refills, medical supply inventory, etc. How can I help?"
                response_url = tts_line_url(line, None, base_url, job_id, "PharmacyGreeting")
                if not response_url or response_url == "None":
                    response_url = tts_line_url("Thanks for calling the pharmacy. I can help with prescription refills, medical supply inventory, etc. How can I help?", None, base_url, job_id, "PharmacyGreetingFallback")
                update_state(job_id, {
                    "ready": True,
                    "needs_confirm": False,
                    "response_url": response_url,
                    "phase": "pharmacy_followup",
                    "department": "pharmacy",
                    "caller_lang": caller_lang,
                    "suspect_spanish": suspect_es,
                })
                print(f"[JOB {job_id}] pharmacy_greeting -> pharmacy_followup (greeting, not direct connection)")
                return
            if SHARED_DATA_AVAILABLE and dept_name == "manager":
                line = shared_data.get_dialogue_template("general", "connect_manager") or "I'll connect you to the manager now."
            elif SHARED_DATA_AVAILABLE and dept_name == "pharmacy":
                line = (
                    shared_data.get_dialogue_template("pharmacy", "connect_pharmacist")
                    or shared_data.get_dialogue_template("pharmacy", "connect_pharmacy_staff")
                    or "I'll connect you to our pharmacist now."
                )
            else:
                line = f"I'll connect you to {dept_name} now."
            # Use text-based caching; avoid job-specific filenames
            response_url = tts_line_url(line, None, base_url, job_id, "DeptSkip")
            if not response_url or response_url == "None":
                # Fallback to prewarmed generic connection line
                response_url = tts_line_url("I'll connect you to an associate who can help with that.", None, base_url, job_id, "DeptSkipFallback")
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "phase": "final_ready",
                "department": dept_name,
                "caller_lang": caller_lang,
                "suspect_spanish": suspect_es,
            })
            print(f"[JOB {job_id}] department-skip -> {dept_name} (no confirmation needed)")
            return

        if wants_operator(raw_text) or wants_operator(repaired):
            op_num = _choose_operator_number(None)
            if op_num:
                spoken = msg("connecting_operator", caller_lang)
                out_name = f"{CACHE_SUBDIR}/op_{job_id}.mp3"
                response_url = tts_line_url(spoken, out_name, base_url)
                update_state(job_id, {
                    "ready": True,
                    "phase": "operator_ready",
                    "needs_confirm": False,
                    "response_url": response_url,
                    "op_number": op_num,
                    "caller_lang": caller_lang,
                    "suspect_spanish": suspect_es,
                })
                print(f"[JOB {job_id}] operator(GATHER) -> dialing {op_num}")
                return
            
        # === Aisle question short-circuit (Gather path) ===
        if is_aisle_question(raw_text) or is_aisle_question(repaired):
            item_q = extract_aisle_item(raw_text) or extract_aisle_item(repaired)
            if item_q:
                locs = locations_for_item(item_q)
                line = speak_aisle_answer(item_q, locs, caller_lang)
                out_name = f"{CACHE_SUBDIR}/aisle_{job_id}.mp3"
                response_url = tts_line_url(line, out_name, base_url)
                update_state(job_id, {
                    "ready": True,
                    "needs_confirm": False,
                    "response_url": response_url,
                    "phase": "final_ready",
                    "department": None
                })
                print(f"[JOB {job_id}] aisle(GATHER) -> item='{item_q}' locs={locs}")
                return

        if repaired != "unclear":
            confirm_prefix = msg("confirm_prefix", caller_lang)
            voice_phrase = localize_for_confirm(repaired, caller_lang)
            confirm_line = f"{confirm_prefix} {voice_phrase}?"
            confirm_url = tts_line_url(confirm_line, None, base_url, job_id, "Confirm")
            if not confirm_url or confirm_url == "None":
                confirm_url = tts_line_url(msg("yes_no", caller_lang), None, base_url, job_id, "ConfirmFallback")
            time.sleep(0.15)
            update_state(job_id, {
                "ready": True,
                "needs_confirm": True,
                "confirm_url": confirm_url,
                "heard_text": repaired,
                "heard_text_voice": voice_phrase,
                "confirm_done": False,
                "phase": "confirm",
                "bg_played": False,
                "correction_hops": 0,
                "caller_lang": caller_lang,
                "suspect_spanish": suspect_es,
                "confirm_round": 0,
            })
            print(f"[JOB {job_id}] confirm(GATHER) -> {confirm_url} heard='{repaired}' voice='{voice_phrase}' lang={caller_lang} suspect_es={suspect_es}")
            return

        # unclear -> ask again
        spoken = random.choice([
            msg("reask", "en") if caller_lang=="en" else msg("reask", caller_lang),
            msg("reask_cap", "en") if caller_lang=="en" else msg("reask_cap", caller_lang),
        ])
        response_url = tts_line_url(spoken, None, base_url, job_id, "Clarify")
        update_state(job_id, {
            "ready": True,
            "needs_confirm": False,
            "needs_clarify": True,
            "response_url": response_url,
            "heard_text": raw_text or "",
            "department": None,
            "phase": "clarify",
            "bg_played": False,
            "caller_lang": caller_lang,
            "suspect_spanish": suspect_es,
        })
        print(f"[JOB {job_id}] clarify(GATHER) -> {response_url} heard='{raw_text}' lang={caller_lang} suspect_es={suspect_es}")
        
        # Log total ASR processing time
        asr_total_time = time.time() - asr_start_time
        print(f"[TIMING] ASR total processing time: {asr_total_time:.3f}s (lang: {lang_time:.3f}s, repair: {repair_time:.3f}s)")
        return
        
    except Exception as e:
        print(f"[PREPARE_REPLY_FROM_TEXT] Exception -> {e}\n{traceback.format_exc()}")
        # Fallback to error response
        spoken = msg("err_global", "en")
        response_url = tts_line_url(spoken, None, base_url, job_id, "Error")
        update_state(job_id, {
            "ready": True,
            "needs_confirm": False,
            "response_url": response_url,
            "phase": "final_ready",
            "department": None
        })
        print(f"[JOB {job_id}] error(GATHER) -> {response_url}")
        return

        # unclear -> ask again
        spoken = random.choice([
            msg("reask", "en") if caller_lang=="en" else msg("reask", caller_lang),
            msg("reask_cap", "en") if caller_lang=="en" else msg("reask_cap", caller_lang),
        ])
        response_url = tts_line_url(spoken, None, base_url, job_id, "Clarify")
        update_state(job_id, {
            "ready": True,
            "needs_confirm": False,
            "needs_clarify": True,
            "response_url": response_url,
            "heard_text": raw_text or "",
            "department": None,
            "phase": "clarify",
            "bg_played": False,
            "caller_lang": caller_lang,
            "suspect_spanish": suspect_es,
        })
        print(f"[JOB {job_id}] clarify(GATHER) -> {response_url} heard='{raw_text}' lang={caller_lang} suspect_es={suspect_es}")

    except Exception as e:
        response_url = tts_line_url(msg("err_global","en"), None, base_url, job_id, "Error")
        update_state(job_id, {
            "ready": True, "needs_confirm": False,
            "response_url": response_url, "needs_clarify": False, "phase": "error"
        })
        print(f"[JOB {job_id}] error(GATHER) -> {e}\n{traceback.format_exc()}")

def prepare_final_route(job_id: str, base_url: str, confirmed_text: str):
    try:
        caller_lang = load_state(job_id) or {}
        caller_lang = caller_lang.get("caller_lang","en")
        item = confirmed_text or ""

        # NEW: check for multiple department candidates
        cands = department_candidates(item)
        
        # NEW: Check if this is a specific coupon request with an item we can infer
        if len(cands) > 1:
            # Check if this is a coupon request with a specific item
            item_lower = item.lower()
            if "coupon" in item_lower and any(keyword in item_lower for keyword in ["cucumber", "tomato", "apple", "banana", "bread", "milk", "cheese", "meat", "chicken", "beef"]):
                # Try to infer the department from the specific item
                inferred_dept = None
                if any(keyword in item_lower for keyword in ["cucumber", "tomato", "apple", "banana", "lettuce", "carrot", "onion"]):
                    inferred_dept = "produce"
                elif any(keyword in item_lower for keyword in ["bread", "cake", "pastry", "cookie"]):
                    inferred_dept = "bakery"
                elif any(keyword in item_lower for keyword in ["milk", "cheese", "yogurt", "butter"]):
                    inferred_dept = "dairy"
                elif any(keyword in item_lower for keyword in ["meat", "chicken", "beef", "pork", "fish"]):
                    inferred_dept = "meat"
                
                if inferred_dept:
                    # Skip department choice and go straight to coupon processing
                    print(f"[JOB {job_id}] inferred dept '{inferred_dept}' for coupon request '{item}'")
                    
                    # Create a direct coupon response
                    coupon_response = f"Here are the current {inferred_dept} coupons available. "
                    
                    # Get coupons for the inferred department
                    try:
                        from coupon_system import CouponQuery, CouponManager
                        query = CouponQuery(category=inferred_dept, search_terms=item)
                        coupon_manager = CouponManager()
                        applicable_coupons = coupon_manager.search_coupons(query)
                        
                        if applicable_coupons:
                            coupon_response += coupon_manager.format_coupon_response(applicable_coupons, query)
                        else:
                            coupon_response += f"I don't see any specific {inferred_dept} coupons for {item} right now, but you can check our weekly ad for current specials."
                    except Exception as e:
                        print(f"[COUPON ERROR] {e}")
                        coupon_response += f"I can help you find {inferred_dept} coupons. Please check our weekly ad or ask a store associate for current specials."
                    
                    out_name = f"{CACHE_SUBDIR}/direct_coupon_{job_id}.mp3"
                    response_url = tts_line_url(coupon_response, out_name, base_url, job_id, "Direct Coupon")
                    
                    update_state(job_id, {
                        "ready": True,
                        "needs_confirm": False,
                        "response_url": response_url,
                        "needs_clarify": False,
                        "department": inferred_dept,
                        "phase": "final_ready"
                    })
                    print(f"[JOB {job_id}] direct coupon -> {inferred_dept} for '{item}'")
                    return
            
            # Ask the caller which dept they prefer
            opts_spoken = " o ".join(cands) if caller_lang.startswith("es") else " or ".join(cands)
            # NEW: Extract just the product name for cleaner department choice prompt
            clean_item = extract_product_for_confirm(item, "dept_choice")
            prompt = (
                f"For {clean_item}, we have {opts_spoken}. Which department do you prefer?"
                if not caller_lang.startswith("es") else
                f"Para {clean_item}, tenemos {opts_spoken}. ¿Qué departamento prefiere?"
            )
            out_name = f"{CACHE_SUBDIR}/dept_prompt_{job_id}.mp3"
            prompt_url = tts_line_url(prompt, out_name, base_url)

            update_state(job_id, {
                "ready": True,                 # ready to play the dept prompt
                "needs_confirm": False,
                "needs_dept_choice": True,     # NEW branch handled in /result
                "dept_prompt_url": prompt_url,
                "dept_options": cands,
                "heard_text": item,
                "phase": "dept_clarify",
                "caller_lang": caller_lang,
                "dept_attempt": 0,
            })
            print(f"[JOB {job_id}] dept-choice -> {cands} for item='{item}'")
            return

        # Single department -> produce final line + finish
        # NEW: Clean the item name for the final response to avoid repeating question words
        clean_item = extract_product_for_confirm(item, "dept_choice")
        print(f"[DEBUG] extract_product_for_confirm: '{item}' -> '{clean_item}'")
        spoken, department = generate_response(clean_item, caller_lang)
        # If Pharmacy department, speak the connect line (from dashboard template) and end the call
        if department == "Pharmacy":
            try:
                if SHARED_DATA_AVAILABLE:
                    spoken = (
                        shared_data.get_dialogue_template("pharmacy", "connect_pharmacist")
                        or shared_data.get_dialogue_template("pharmacy", "connect_pharmacy_staff")
                        or "I'll connect you to our pharmacist now."
                    )
                else:
                    spoken = "I'll connect you to our pharmacist now."
            except Exception:
                spoken = "I'll connect you to our pharmacist now."
        
        # Check if internet search was used and add notification
        if hasattr(generate_response, 'last_used_internet_search') and generate_response.last_used_internet_search:
            # Internet search was used, but just proceed with normal flow
            print(f"[JOB {job_id}] internet_search_complete -> {department} for '{clean_item}'")
            # Continue to normal flow below
        # For Pharmacy, we now finalize like any other department (no follow-up gather)
        pharmacy_prompt = False
        
        # SPECIAL: If department is Customer Service and it's a coupon query that asks for department,
        # trigger department choice for coupons
        coupon_prompt = (
            department == "Customer Service" and (
                "what department are you shopping in" in spoken.lower() or
                "department are you shopping" in spoken.lower()
            )
        )
        
        # Generate response URL AFTER pharmacy override
        response_url = tts_line_url(spoken, None, base_url, job_id, "Final Response")
        
        if pharmacy_prompt:
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "needs_clarify": False,
                "department": department,
                "phase": "pharmacy_followup"
            })
        elif coupon_prompt:
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "needs_clarify": False,
                "department": department,
                "phase": "coupon_followup"
            })
        else:
            update_state(job_id, {
                "ready": True,
                "needs_confirm": False,
                "response_url": response_url,
                "needs_clarify": department in (None, "null"),
                "department": department,
                "phase": "final_ready"
            })
        print(f"[JOB {job_id}] final -> {response_url} clarify=False dept={department} lang={caller_lang}")
    except Exception as e:
        response_url = tts_line_url(msg("err_global","en"), None, base_url, job_id, "Error")
        update_state(job_id, {
            "ready": True, "needs_confirm": False,
            "response_url": response_url, "needs_clarify": False, "phase": "error"
        })
        print(f"[JOB {job_id}] error(final) -> {e}\n{traceback.format_exc()}")

@app.route("/", methods=["GET"])
def home():
    return "Flask is running and reachable."

@app.get("/state")
def state_debug():
    job_id = request.args.get("job","")
    return (state_get(job_id) or {"status":"missing"}), 200, {"Content-Type":"application/json"}

# Serve cached TTS files directly with correct MIME and caching
@app.route("/static/tts_cache/<path:fname>")
def serve_tts_cache(fname):
    cache_dir = os.path.join(app.root_path, "static", "tts_cache")
    full = os.path.join(cache_dir, fname)
    if not os.path.isfile(full):
        # return a plain 404, NOT TwiML
        resp = make_response(b"Not found", 404)
        resp.headers["Content-Type"] = "text/plain; charset=utf-8"
        return resp

    # Guess MIME (fallback to audio/mpeg)
    mime, _ = mimetypes.guess_type(full)
    if not mime:
        mime = "audio/mpeg"

    resp = make_response(send_from_directory(cache_dir, fname, conditional=True))
    resp.headers["Content-Type"] = mime
    # Allow Twilio to cache between polls
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp

@app.route("/pharmacy_followup", methods=["GET", "POST"])
def pharmacy_followup():
    try:
        job_id = request.args.get("job") or request.form.get("job")
        vr = VoiceResponse()
        if not job_id or not load_state(job_id):
            twiml_play_tts(vr, "Sorry, there was an error. Goodbye.", "err_no_job3.mp3")
            vr.hangup()
            print(f"[PHARMACY] TwiML(no job)->\n{str(vr)}")
            return xml_response(vr)

        meta = load_state(job_id)
        base_url = get_base_url()
        caller_lang = meta.get("caller_lang", "en")

        # Check if this is a timeout (no speech detected)
        if not request.form.get("SpeechResult"):
            line = "I didn't hear a response. Please call back and try again. Goodbye."
            response_url = tts_line_url(line, None, base_url, job_id, "Pharmacy Timeout")
            vr.play(response_url)
            vr.hangup()
            clear_state(job_id)
            print(f"[PHARMACY] TwiML(timeout)->\n{str(vr)}")
            return xml_response(vr)
        
        # Pull recognized speech
        raw_text = (request.form.get("SpeechResult") or "").strip()
        repaired = repair_transcript(raw_text)
        
        print(f"[PHARMACY] raw='{raw_text}' repaired='{repaired}' lang={caller_lang}")
        print(f"[PHARMACY] Speech confidence: {request.form.get('Confidence', 'unknown')}")
        print(f"[PHARMACY] Speech timeout: {request.form.get('SpeechTimeout', 'unknown')}")
        
        # If no speech detected, give a helpful message and end
        if not raw_text:
            line = "I didn't catch that. Please call back and try again. Goodbye."
            response_url = tts_line_url(line, None, base_url, job_id, "Pharmacy No Speech")
            vr.play(response_url)
            vr.hangup()
            clear_state(job_id)
            print(f"[PHARMACY] TwiML(no speech)->\n{str(vr)}")
            return xml_response(vr)

        # For pharmacy follow-ups, prefer raw text if it contains numbers (phone/RX numbers)
        # or if the repaired version is "unclear" (repair function was too aggressive)
        # since repair_transcript can be too aggressive with numbers and filler words
        if any(char.isdigit() for char in raw_text) or repaired == "unclear":
            input_text = raw_text
        else:
            input_text = repaired or raw_text
            
        # If we previously asked "anything else?", interpret a yes/no first
        if meta.get("asked_anything_else"):
            lowered = input_text.lower()
            yes_terms = [
                "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "please", "go ahead",
                "one more", "another", "i have another", "i have a question", "i have more"
            ]
            no_terms = [
                "no", "nope", "nah", "nothing", "nothing else", "that's it", "that is it",
                "all set", "we're good", "we are good", "i'm good", "im good", "no thank you",
                "no thanks", "that'll be all", "that will be all"
            ]
            if any(term in lowered for term in no_terms):
                # Say goodbye and end
                goodbye_text = "Thanks for calling, have a nice day!"
                bye_url = tts_line_url(goodbye_text, None, base_url, job_id, "Pharmacy Goodbye")
                if bye_url:
                    vr.play(bye_url)
                vr.hangup()
                clear_state(job_id)
                print(f"[PHARMACY] TwiML(goodbye)->\n{str(vr)}")
                return xml_response(vr)
            if any(term in lowered for term in yes_terms):
                # Stay in pharmacy flow and gather another request
                follow_text = "Okay. What else can I help you with in the pharmacy?"
                follow_url = tts_line_url(follow_text, None, base_url, job_id, "Pharmacy WhatElse")
                if follow_url:
                    vr.play(follow_url)
                g = Gather(**gather_kwargs({
                    "action": f"{base_url}/pharmacy_followup?job={job_id}",
                    "method": "POST",
                    "language": "es-US" if caller_lang.startswith("es") else "en-US",
                    "timeout": 10,
                    "profanity_filter": True,
                    "barge_in": True,
                }))
                vr.append(g)
                meta["asked_anything_else"] = False
                print(f"[PHARMACY] TwiML(yes -> keep gathering)->\n{str(vr)}")
                return xml_response(vr)
            # Not a clear yes/no; continue normal processing and clear the flag
            meta["asked_anything_else"] = False

        # Play hold music immediately to indicate processing
        vr.play(HOLDY_CLARIFY_CDN)
        
        # Check if this is a direct request for a pharmacist (should connect and hangup)
        input_lower = input_text.lower()
        pharmacist_requests = [
            "pharmacist", "talk to pharmacist", "speak to pharmacist", "connect me to pharmacist",
            "i need a pharmacist", "can i talk to a pharmacist", "i want to talk to a pharmacist",
            "put me through to a pharmacist", "transfer me to a pharmacist", "pharmacist please"
        ]
        
        if any(phrase in input_lower for phrase in pharmacist_requests):
            # Direct request for pharmacist - connect and hangup
            if SHARED_DATA_AVAILABLE:
                line = (
                    shared_data.get_dialogue_template("pharmacy", "connect_pharmacist")
                    or shared_data.get_dialogue_template("pharmacy", "connect_pharmacy_staff")
                    or "I'll connect you to our pharmacist now."
                )
            else:
                line = "I'll connect you to our pharmacist now."
            
            response_url = tts_line_url(line, None, base_url, job_id, "Pharmacy Direct Connect")
            vr.play(response_url)
            vr.hangup()
            clear_state(job_id)
            print(f"[PHARMACY] Direct pharmacist request -> connecting and hanging up")
            return xml_response(vr)
        
        # Build a one-shot line using the same handler and keep the convo short
        print(f"[PHARMACY] Processing input_text: '{input_text}'")
        line, dept = generate_response(input_text, caller_lang)
        print(f"[PHARMACY] Generated response: line='{line}', dept='{dept}'")
        response_url = tts_line_url(line, None, base_url, job_id, "Pharmacy Followup")
        
        # Play the response after hold music
        vr.play(response_url)

        # Determine whether this was a completion-style line; only then ask "anything else"
        completion_markers = [
            "i'll process the refill", "refill processed", "ready for pickup", "is ready", "i found your prescription",
            "has", "queued", "done", "completed"
        ]
        ask_anything_else = any(marker in (line or "").lower() for marker in completion_markers)

        if ask_anything_else:
            try:
                anything_else_text = shared_data.get_dialogue_template("general", "anything_else") if SHARED_DATA_AVAILABLE else None
            except Exception:
                anything_else_text = None
            if not anything_else_text:
                anything_else_text = "Is there anything else I can help you with today?"
            anything_else_url = tts_line_url(anything_else_text, None, base_url, job_id, "Pharmacy AnythingElse")
            if anything_else_url:
                vr.play(anything_else_url)
            meta["asked_anything_else"] = True
        else:
            meta["asked_anything_else"] = False

        g = Gather(**gather_kwargs({
            "action": f"{base_url}/pharmacy_followup?job={job_id}",
            "method": "POST",
            "language": "es-US" if caller_lang.startswith("es") else "en-US",
            "timeout": 10,
            "profanity_filter": True,
            "barge_in": True,
        }))
        vr.append(g)

        # Keep job context for continued pharmacy dialogue
        meta.update({
            "ready": True,
            "needs_confirm": False,
            "needs_clarify": False,
            "department": "Pharmacy",
            "phase": "pharmacy_followup",
            "response_url": response_url,
        })
        print(f"[PHARMACY] TwiML(pharmacy follow-up gather)->\n{str(vr)}")
        return xml_response(vr)
    except Exception as e:
        vr = VoiceResponse()
        twiml_play_tts(vr, msg("err_global","en"), "pharm_err.mp3")
        vr.hangup()
        print(f"[PHARMACY] Exception -> {e}\n{traceback.format_exc()}")
        return xml_response(vr)

@app.route("/coupon_followup", methods=["GET", "POST"])
def coupon_followup():
    try:
        job_id = request.args.get("job") or request.form.get("job")
        vr = VoiceResponse()
        if not job_id or not load_state(job_id):
            twiml_play_tts(vr, "Sorry, there was an error. Goodbye.", "err_no_job3.mp3")
            vr.hangup()
            print(f"[COUPON] TwiML(no job)->\n{str(vr)}")
            return xml_response(vr)

        meta = load_state(job_id)
        base_url = get_base_url()
        caller_lang = meta.get("caller_lang", "en")

        # Check if this is a timeout (no speech detected)
        if not request.form.get("SpeechResult"):
            twiml_play_tts(vr, "I didn't hear a response. Please call back and try again. Goodbye.", "no_speech.mp3")
            vr.hangup()
            print(f"[COUPON] TwiML(no speech)->\n{str(vr)}")
            return xml_response(vr)

        # Get the speech input
        raw_text = request.form.get("SpeechResult", "")
        repaired = repair_transcript(raw_text)
        
        print(f"[COUPON] raw='{raw_text}' repaired='{repaired}' lang={caller_lang}")
        print(f"[COUPON] Speech confidence: {request.form.get('Confidence', 'unknown')}")
        print(f"[COUPON] Speech timeout: {request.form.get('SpeechTimeout', 'unknown')}")

        # Process the input for coupon-specific queries
        input_text = repaired or raw_text
        
        # Handle the coupon follow-up query - treat as department choice
        if COUPON_AVAILABLE:
            # Map common department responses to coupon categories
            dept_mapping = {
                # Grocery & Food
                "grocery": "grocery",
                "pantry": "pantry",
                "food": "grocery",
                "cereal": "cereal",
                "breakfast": "breakfast",
                "pasta": "pantry",
                "canned": "pantry",
                "coffee": "pantry",
                "tea": "pantry",
                "beverages": "pantry",
                "soda": "pantry",
                "pop": "pantry",
                "juice": "pantry",
                "water": "pantry",
                "energy drink": "pantry",
                
                # Dairy
                "dairy": "dairy", 
                "milk": "dairy",
                "cheese": "dairy",
                "yogurt": "dairy",
                "eggs": "dairy",
                
                # Meat & Seafood
                "meat": "meat",
                "beef": "meat",
                "chicken": "meat",
                "pork": "meat",
                "fish": "meat",
                "seafood": "meat",
                "salmon": "meat",
                
                # Produce
                "produce": "produce",
                "fruits": "produce",
                "vegetables": "produce",
                "organic": "produce",
                "berries": "produce",
                "apples": "produce",
                
                # Frozen
                "frozen": "frozen",
                "pizza": "frozen",
                "ice cream": "frozen",
                "frozen vegetables": "frozen",
                
                # Bakery
                "bakery": "bakery",
                "bread": "bakery",
                "cake": "bakery",
                "pastry": "bakery",
                "bagels": "bakery",
                "donuts": "bakery",
                
                # Household & Cleaning
                "cleaning": "cleaning",
                "household": "cleaning",
                "toilet paper": "cleaning",
                "paper towels": "cleaning",
                "laundry": "cleaning",
                "detergent": "cleaning",
                
                # Beauty & Personal Care
                "beauty": "beauty",
                "personal care": "beauty",
                "shampoo": "beauty",
                "toothpaste": "beauty",
                "deodorant": "beauty",
                "hair care": "beauty",
                
                # Office & Stationery
                "sharpie": "office_stationery",
                "pen": "office_stationery",
                "pens": "office_stationery",
                "office": "office_stationery",
                "school": "office_stationery",
                "supplies": "office_stationery",
                "stationery": "office_stationery",
                
                # Electronics
                "electronics": "electronics",
                "tech": "electronics",
                "phone": "electronics",
                "charger": "electronics",
                "headphones": "electronics",
                "hdmi": "electronics",
                "cable": "electronics",
                "hdmi cable": "electronics",
                
                # Clothing
                "clothing": "clothing",
                "clothes": "clothing",
                "shoes": "clothing",
                "apparel": "clothing",
                "fashion": "clothing",
                
                # Toys & Games
                "toys": "toys",
                "games": "toys",
                "board games": "toys",
                "puzzles": "toys",
                
                # Home & Furniture
                "home": "home",
                "furniture": "home",
                "decor": "home",
                "sofa": "home",
                "chair": "home",
                
                # Baby & Kids
                "baby": "baby",
                "diapers": "baby",
                "formula": "baby",
                "kids": "baby",
                "infant": "baby",
                
                # Garden
                "garden": "garden",
                "plants": "garden",
                "flowers": "garden",
                "garden tools": "garden",
                
                # Automotive
                "auto": "automotive",
                "automotive": "automotive",
                "car parts": "automotive",
                "motor oil": "automotive",
                "oil": "automotive"
            }
            
            # Play immediate hold music and redirect to processing
            vr.play(HOLDY_CLARIFY_CDN)
            import urllib.parse
            encoded_input = urllib.parse.quote(input_text)
            vr.redirect(public_url(f"/coupon_process?job={job_id}&input={encoded_input}"))
            print(f"[COUPON] TwiML(immediate hold)->\n{str(vr)}")
            return xml_response(vr)
    except Exception as e:
        vr = VoiceResponse()
        twiml_play_tts(vr, "Sorry, there was an error processing your coupon request. Please try again.", "coupon_err.mp3", job_id, "Coupon Exception")
        vr.hangup()
        print(f"[COUPON] Exception -> {e}\n{traceback.format_exc()}")
        return xml_response(vr)

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/credits", methods=["GET"])
def credits():
    """Get current credit usage summary"""
    summary = credit_tracker.get_daily_summary()
    return json.dumps(summary, indent=2), 200, {"Content-Type": "application/json"}

@app.route("/credits/<job_id>", methods=["GET"])
def credits_call(job_id):
    """Get credit usage for a specific call"""
    summary = credit_tracker.get_call_summary(job_id)
    return json.dumps(summary, indent=2), 200, {"Content-Type": "application/json"}

@app.route("/credits/services", methods=["GET"])
def credits_services():
    """Get breakdown of credit usage by service"""
    breakdown = credit_tracker.get_service_breakdown()
    return json.dumps(breakdown, indent=2), 200, {"Content-Type": "application/json"}

@app.route("/coupon_process", methods=["GET", "POST"])
def coupon_process():
	try:
		vr = VoiceResponse()
		job_id = request.args.get("job") or request.form.get("job")
		if job_id:
			vr.redirect(public_url(f"/sms_consent?job={job_id}"), method="POST")
		else:
			vr.redirect(public_url("/sms_consent"), method="POST")
		return xml_response(vr)
	except Exception:
		vr = VoiceResponse()
		vr.pause(length=0)
		return xml_response(vr)

@app.route("/coupon_replay", methods=["GET", "POST"])
def coupon_replay():
    try:
        job_id = request.args.get("job") or request.form.get("job")
        vr = VoiceResponse()
        if not job_id or not load_state(job_id):
            twiml_play_tts(vr, "Sorry, there was an error. Goodbye.", "err_no_job3.mp3", job_id, "Coupon Replay Error")
            vr.hangup()
            print(f"[COUPON_REPLAY] TwiML(no job)->\n{str(vr)}")
            return xml_response(vr)

        meta = load_state(job_id)
        
        # Check if there's a cached coupon response
        if "cached_coupon_response" in meta:
            # Play the cached coupon response again
            vr.play(meta["cached_coupon_response"])
            
            # Ask again if they want to hear it again
            replay_prompt = "To hear these coupons again, say repeat or press any key."
            replay_url = tts_line_url(replay_prompt, f"{CACHE_SUBDIR}/coupon_replay_{job_id}.mp3", get_base_url(), job_id, "Coupon Replay")
            vr.play(replay_url)
            
            # Gather for another replay request
            g = Gather(**gather_kwargs({
                "input": "speech dtmf",
                "action": abs_url(url_for("coupon_replay", job=job_id)),
                "method": "POST",
                "language": "en-US",
                "timeout": 5,
                "profanity_filter": True,
                "barge_in": True
            }))
            vr.append(g)
            
            print(f"[COUPON_REPLAY] TwiML(replay)->\n{str(vr)}")
            return xml_response(vr)
        else:
            # No cached response, just hang up
            twiml_play_tts(vr, "Thanks for calling!", "thanks.mp3", job_id, "Coupon Replay Thanks")
            vr.hangup()
            clear_state(job_id)
            print(f"[COUPON_REPLAY] TwiML(no cache)->\n{str(vr)}")
            return xml_response(vr)
            
    except Exception as e:
        vr = VoiceResponse()
        twiml_play_tts(vr, "Sorry, there was an error. Goodbye.", "replay_err.mp3", job_id, "Coupon Replay Exception")
        vr.hangup()
        print(f"[COUPON_REPLAY] Exception -> {e}\n{traceback.format_exc()}")
        return xml_response(vr)

def _result_poll_url(base_url: str, job_id: str, meta: dict) -> str:
    cnt = meta.get("polls", 0) + 1
    meta["polls"] = cnt
    return public_url(f"/result?job={job_id}&n={cnt}&t={int(time.time()*1000)}")

@app.post("/result")
def result():
    job_id = request.args.get("job", "") or request.form.get("job", "")
    n = int(request.args.get("n", "0") or 0)
    t = request.args.get("t", "")

    st = state_get(job_id)
    status = st.get("status")
    reply_url = st.get("reply_url", "")

    vr = VoiceResponse()

    # MISSING state: re-gather
    if not st or not status:
        current_app.logger.info("[RESULT] missing job=%s n=%d", job_id, n)
        # Play greeting and gather
        greet_url = public_url("/static/tts_cache/1a99e9963544b45c.mp3")  # or your greeting
        vr.play(greet_url)
        vr.gather(
            action=public_url("/handle_gather"),
            method="POST",
            input="speech dtmf",
            speech_model="phone_call",
            speech_timeout="5",
            timeout="5",
            barge_in=True,
            profanity_filter=False,
            action_on_empty_result=True
        )
        return xml_response(vr)

    # PENDING state: poll with hold audio
    if status == "working" or not reply_url:
        current_app.logger.info("[RESULT] pending job=%s n=%d reply_url=%s", job_id, n, reply_url)
        
        # Cap polling at MAX_RESULT_POLLS
        if n >= MAX_RESULT_POLLS:
            vr.say("Still working, please call back shortly.")
            vr.hangup()
            return xml_response(vr)
        
        # Play hold audio and redirect
        hold_url = HOLDY_MID_CDN or public_url("/static/tts_cache/holdy_tiny.mp3")
        vr.play(hold_url)
        vr.redirect(public_url(f"/result?job={job_id}&n={n+1}&t={int(time.time())}"), method="POST")
        return xml_response(vr)

    # DONE state: play reply and hangup
    if status == "done" and reply_url:
        current_app.logger.info("[RESULT] done job=%s n=%d reply_url=%s", job_id, n, reply_url)
        vr.play(reply_url)
        vr.hangup()
        return xml_response(vr)

    # Fallback: should not reach here
    current_app.logger.warning("[RESULT] unknown state job=%s status=%s", job_id, status)
    vr.say("Sorry, something went wrong.")
    vr.hangup()
    return xml_response(vr)






@app.route("/followup_response", methods=["GET", "POST"])
def followup_response():
    try:
        job_id = request.args.get("job") or request.form.get("job")
        vr = VoiceResponse()
        if not job_id or not load_state(job_id):
            twiml_play_tts(vr, "Sorry, there was an error. Goodbye.", "err_no_job_followup.mp3")
            vr.hangup()
            print(f"[FOLLOWUP] TwiML(no job)->\n{str(vr)}")
            return xml_response(vr)

        meta = load_state(job_id)
        caller_lang = meta.get("caller_lang","en")
        
        # Get the customer's response
        raw_text = request.form.get("SpeechResult", "")
        
        # For follow-up responses, we need to preserve context for yes/no detection
        # but still clean it for processing
        cleaned_text = (raw_text or "").strip().lower()
        cleaned_text = re.sub(r"[^\w\s\-]", "", cleaned_text)
        
        # Use repair_transcript for item extraction if needed
        repaired = repair_transcript(raw_text) if raw_text else ""
        
        print(f"[FOLLOWUP] raw='{raw_text}' cleaned='{cleaned_text}' repaired='{repaired}' lang={caller_lang}")
        
        # Check if they said "no" or similar (use cleaned text for better detection)
        if _is_followup_response(cleaned_text):
            # They said "no" - say goodbye and hang up
            # Play holdy MP3 first to let caller know we're processing
            vr.play("https://mantis-snake-7285.twil.io/assets/holdy_clarify.mp3")
            
            goodbye_msg = "Thanks for calling, have a nice day!"
            out_name = f"{CACHE_SUBDIR}/goodbye_{job_id}.mp3"
            response_url = tts_line_url(goodbye_msg, out_name, get_base_url())
            vr.play(response_url)
            vr.hangup()
            clear_state(job_id)
            
            # Schedule credit tracking after call ends
            schedule_end_credit_tracking(job_id, delay_seconds=60)
            
            print(f"[FOLLOWUP] TwiML(goodbye)->\n{str(vr)}")
            return xml_response(vr)
        else:
            # They said "yes" or something else - treat as a new question
            # Reset the job state and process as a new request
            meta.update({
                "ready": False,
                "phase": "first_hold",
                "polls": 0,
                "waiting_for_followup": False
            })
            save_state(job_id, meta)
            
            # Process the new question using the normal flow
            # Reset the job state and process as a new request
            meta.update({
                "ready": False,
                "phase": "first_hold",
                "polls": 0,
                "waiting_for_followup": False
            })
            save_state(job_id, meta)
            
            # Use the normal prepare_reply_from_text flow
            threading.Thread(
                target=prepare_reply_from_text,
                args=(job_id, repaired, get_base_url()),
                daemon=True
            ).start()
            
            # Redirect to result polling
            vr.redirect(_result_poll_url(get_base_url(), job_id, meta), method="POST")
            print(f"[FOLLOWUP] TwiML(new question)->\n{str(vr)}")
            return xml_response(vr)
            
    except Exception as e:
        print(f"[FOLLOWUP] Exception -> {e}\n{traceback.format_exc()}")
        vr = VoiceResponse()
        twiml_play_tts(vr, "Thanks for calling, have a nice day!", "tts_cache/goodbye_error.mp3")
        vr.hangup()
        print(f"[FOLLOWUP] TwiML(error)->\n{str(vr)}")
        return xml_response(vr)

@app.route("/holdy_then_result", methods=["GET", "POST"])
def holdy_then_result():
    """Play holdy MP3 then redirect to result polling"""
    try:
        job_id = request.args.get("job") or request.form.get("job")
        if not job_id or not load_state(job_id):
            vr = VoiceResponse()
            twiml_play_tts(vr, "Sorry, there was an error. Goodbye.", "err_no_job2.mp3")
            vr.hangup()
            print(f"[HOLDY] TwiML(no job)->\n{str(vr)}")
            return xml_response(vr)
        
        meta = load_state(job_id)
        
        # Play holdy MP3, then redirect to result polling
        vr = VoiceResponse()
        vr.play("https://mantis-snake-7285.twil.io/assets/holdy_clarify.mp3")
        vr.redirect(_result_poll_url(get_base_url(), job_id, meta), method="POST")
        print(f"[HOLDY] TwiML(play then redirect)->\n{str(vr)}")
        return xml_response(vr)
        
    except Exception as e:
        print(f"[HOLDY] Exception -> {e}")
        vr = VoiceResponse()
        twiml_play_tts(vr, "Thanks for calling, have a nice day!", "goodbye_error.mp3")
        vr.hangup()
        print(f"[HOLDY] TwiML(error)->\n{str(vr)}")
        return xml_response(vr)

@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    try:
        job_id = request.args.get("job") or request.form.get("job")
        vr = VoiceResponse()
        if not job_id or not load_state(job_id):
            twiml_play_tts(vr, "Sorry, there was an error. Goodbye.", "err_no_job2.mp3")
            vr.hangup()
            print(f"[CONFIRM] TwiML(no job)->\n{str(vr)}")
            return xml_response(vr)

        meta = load_state(job_id)
        caller_lang = meta.get("caller_lang","en")

        if meta.get("confirm_done"):
            vr.redirect(_result_poll_url(get_base_url(), job_id, meta), method="POST")
            print(f"[CONFIRM] TwiML(already)->\n{str(vr)}")
            return xml_response(vr)

        # Prefer Gather speech result (FAST PATH)
        speech = request.form.get("SpeechResult") or request.args.get("SpeechResult")
        if speech:
            reply = speech
            print(f"[CONFIRM HEARD via Gather] '{reply}'")
        else:
            # Fallback: Twilio <Record>
            recording_url = request.form.get("RecordingUrl") or request.args.get("RecordingUrl")
            if not recording_url:
                twiml_play_tts(vr, msg("err_confirm", caller_lang), "didnt_catch_confirm.mp3")
                g = Gather(**gather_kwargs({
                    "action": abs_url(url_for("confirm", job=job_id)),
                    "method": "POST",
                    "language": "es-US" if caller_lang.startswith("es") else "en-US",
                    "timeout": max(1, CONF_TIMEOUT),
                    "profanity_filter": True,
                    "barge_in": True
                }))
                # Repeat short prompt inside gather to allow interruption
                prompt_line = msg("yes_no", caller_lang)
                g.play(tts_line_url(prompt_line, "tts_cache/yes_or_no.mp3" if caller_lang=="en" else f"{CACHE_SUBDIR}/yes_no_{caller_lang}.mp3", get_base_url()))
                vr.append(g)
                print(f"[CONFIRM] TwiML(re-ask gather)->\n{str(vr)}")
                return xml_response(vr)
            local_wav = os.path.join(app.static_folder, "confirm.wav")
            download_twilio_recording(recording_url, local_wav)
            reply, _, _ = transcribe_file(local_wav)
            print(f"[CONFIRM HEARD via Record] '{reply}'")
            
            # If Whisper is not available and no transcription, fall back to Gather
            if not reply and not USE_LOCAL_WHISPER:
                logger.warning("Local Whisper not available for confirm; falling back to Gather")
                vr = VoiceResponse()
                g = Gather(**gather_kwargs({
                    "action": abs_url(url_for("confirm", job=job_id)),
                    "method": "POST",
                    "language": "es-US" if caller_lang.startswith("es") else "en-US",
                    "timeout": max(1, CONF_TIMEOUT),
                    "profanity_filter": True,
                    "barge_in": True
                }))
                prompt_line = msg("yes_no", caller_lang)
                g.play(tts_line_url(prompt_line, "tts_cache/yes_or_no.mp3" if caller_lang=="en" else f"{CACHE_SUBDIR}/yes_no_{caller_lang}.mp3", get_base_url()))
                vr.append(g)
                print(f"[CONFIRM] TwiML(whisper fallback)->\n{str(vr)}")
                return xml_response(vr)

        # Operator request during confirm?
        if wants_operator(reply):
            op_num = _choose_operator_number(meta.get("department"))
            if op_num:
                spoken = msg("connecting_operator", caller_lang)
                out_name = f"{CACHE_SUBDIR}/op_{job_id}.mp3"
                response_url = tts_line_url(spoken, out_name, get_base_url())
                meta.update({
                    "confirm_done": True,
                    "needs_confirm": False,
                    "ready": True,
                    "phase": "operator_ready",
                    "op_number": op_num,
                    "response_url": response_url
                })
                save_state(job_id, meta)
                vr.redirect(_result_poll_url(get_base_url(), job_id, meta), method="POST")
                print(f"[CONFIRM] Operator requested -> dialing {op_num}")
                return xml_response(vr)

        heard_text = meta.get("heard_text", "")

        # ---- YES + DETAIL detection (e.g., "yeah, the drink") ----
        ydetail = yes_plus_detail(reply, caller_lang)
        ydetail_candidate = ""
        if ydetail:
            ydetail_candidate = (extract_item_phrase(ydetail) or "").strip()
            if not ydetail_candidate or len(ydetail_candidate.split()) < 1:
                rc = repair_transcript(ydetail)
                if rc not in ("", "unclear"):
                    ydetail_candidate = rc.strip()
            if (not ydetail_candidate or len(ydetail_candidate.split()) < 2) and re.search(r"\bdrink\b", ydetail):
                base = heard_text.strip()
                if base:
                    ydetail_candidate = f"{base} drink"

        # Now interpret yes/no
        yn = interpret_confirmation(reply, caller_lang)

        # Strong guard: if the reply contains a classic affirmation phrase, force YES
        norm_reply_all = _normalize_text(reply)
        if re.search(r"\bthats right\b", norm_reply_all) or re.search(r"\bthats it\b", norm_reply_all):
            yn = "yes"

        # 4a: exact-match affirmation override if ASR was fuzzy
        if yn == "unclear" and is_affirmation(reply):
            yn = "yes"

        # ===== EARLY YES SHORT-CIRCUIT (only if no extra detail) =====
        if yn == "yes" and not ydetail_candidate:
            meta.update({
                "confirm_done": True,
                "needs_confirm": False,
                "ready": False,
                "in_final": True,
                "phase": "final_pending",
                "mid_hold_played": True,
                "bg_played": bool(HOLD_BG_CDN),
                "last_hold_at": time.time(),
                "correction_hops": 0,
            })
            save_state(job_id, meta)
            print(f"[CONFIRM] YES -> starting final routing for job={job_id}")

            threading.Thread(
                target=prepare_final_route,
                args=(job_id, get_base_url(), heard_text),
                daemon=True
            ).start()

            vr.play(HOLD_BG_CDN or HOLDY_MID_CDN)
            vr.redirect(_result_poll_url(get_base_url(), job_id, meta), method="POST")
            print(f"[CONFIRM] TwiML(yes immediate hold)->\n{str(vr)}")
            return xml_response(vr)
        # ============================================================

        def _tokenize(s: str) -> set[str]:
            return set([w for w in re.sub(r"[^a-z0-9\- ]", " ", (s or "").lower()).split() if w])

        extracted = (extract_item_phrase(reply) or "").strip()
        candidate_llm = repair_transcript(reply)
        candidate_llm = candidate_llm if candidate_llm not in ("", "unclear") else ""

        heard_tokens = _tokenize(heard_text)
        ext_tokens   = _tokenize(extracted)
        llm_tokens   = _tokenize(candidate_llm)

        def _score(tokens: set[str]) -> int:
            if not tokens:
                return -1
            return len(tokens) + len(tokens - heard_tokens)

        scores = {"extracted": _score(ext_tokens), "llm": _score(llm_tokens)}

        # Never treat pure affirmations as item corrections (expanded)
        _affirmation_tokens = {
            "yes","yeah","yep","yup","ok","okay","alright","right","correct","exactly",
            "thats","that's","thats right","that's right","thats correct","that's correct",
            "mm-hmm","uh-huh","indeed","sure"
        }

        def _is_pure_affirmation(s: str) -> bool:
            s = _normalize_text(s)
            if not s:
                return False
            # exact known phrases
            if s in _affirmation_tokens:
                return True
            # common two-word forms like "that's correct", "that's right"
            if s in {"thats correct","thats right","thats it","thats true","thats fine"}:
                return True
            # allow leading yes-like token then punctuation only
            parts = s.split()
            if len(parts) <= 3 and all(p in _affirmation_tokens for p in parts):
                return True
            return False

        if _is_pure_affirmation(candidate_llm):
            candidate_llm = ""
        if _is_pure_affirmation(extracted):
            extracted = ""

        candidate = extracted if scores["extracted"] >= scores["llm"] else candidate_llm

        # If user provided "yes + detail", prefer that over other candidates
        if ydetail_candidate:
            candidate = ydetail_candidate

        norm_reply = _normalize_text(reply)

        # NEW: treat "i said" as correction only if not "that's what i said"
        has_correction_language = bool(
            re.search(r"\b(no|not|actually|instead|i meant)\b", norm_reply)
            or (re.search(r"\bi said\b", norm_reply) and not re.search(r"\bthats what i said\b", norm_reply))
            or re.search(r"\b(en realidad|mejor)\b", norm_reply)
        )
        if re.search(r"\bthats what i said\b", norm_reply):
            has_correction_language = False

        # Treat "yes + detail" as a correction intent
        if ydetail_candidate:
            has_correction_language = True

        is_informative = bool(candidate) and candidate != heard_text and len(candidate.split()) >= 1
        correction_intent = (yn == "no") or has_correction_language or (is_informative and yn == "unclear")

        if correction_intent and is_informative:
            hops = int(meta.get("correction_hops", 0)) + 1
            if hops > CORRECTION_HOPS_MAX:
                meta.update({"confirm_done": True, "needs_confirm": False, "phase": "reask", "bg_played": False})
                save_state(job_id, meta)
                twiml_play_tts(vr, msg("reask_cap", caller_lang), "tts_cache/reask_cap.mp3" if caller_lang=="en" else f"{CACHE_SUBDIR}/reask_cap_{caller_lang}.mp3")
                # NEW: use Gather for fresh item if enabled
                if USE_GATHER_MAIN:
                    call_id = job_id  # Use job_id as call_id for consistency
                    g = Gather(**gather_kwargs({
                        "action": abs_url(url_for("handle_gather", call_id=call_id, t0=int(time.time()))),
                        "method": "POST",
                        "language": _primary_lang_code(caller_lang),
                        "timeout": CONF_TIMEOUT,
                        "profanity_filter": True,
                        "barge_in": True
                    }))
                    vr.append(g)
                else:
                    vr.record(**record_args(abs_url(url_for("handle")), MAIN_MAXLEN, MAIN_TIMEOUT, beep_override=False))
                print(f"[CONFIRM] Hit correction hop cap ({CORRECTION_HOPS_MAX}); re-asking.")
                return xml_response(vr)

            meta.update({
                "heard_text": candidate,
                "confirm_done": True,
                "needs_confirm": False,
                "ready": False,
                "in_final": True,
                "phase": "final_pending",
                "mid_hold_played": True,
                "bg_played": bool(HOLD_BG_CDN),
                "last_hold_at": time.time(),
                "correction_hops": hops,
            })
            save_state(job_id, meta)
            print(f"[CONFIRM] ACCEPT corrected item -> {candidate} (hop {hops}/{CORRECTION_HOPS_MAX}); routing final")

            threading.Thread(
                target=prepare_final_route,
                args=(job_id, get_base_url(), candidate),
                daemon=True
            ).start()

            vr.play(HOLD_BG_CDN or HOLDY_MID_CDN)
            vr.redirect(_result_poll_url(get_base_url(), job_id, meta), method="POST")
            return xml_response(vr)

        # unclear -> ask again (localized) with barge-in
        prompt_line = msg("yes_no", caller_lang)
        g = Gather(**gather_kwargs({
            "action": abs_url(url_for("confirm", job=job_id)),
            "method": "POST",
            "language": "es-US" if caller_lang.startswith("es") else "en-US",
            "timeout": max(1, CONF_TIMEOUT),
            "profanity_filter": True,
            "barge_in": True
        }))
        g.play(tts_line_url(prompt_line, "tts_cache/yes_or_no.mp3" if caller_lang=="en" else f"{CACHE_SUBDIR}/yes_no_{caller_lang}.mp3", get_base_url()))
        vr.append(g)
        print(f"[CONFIRM] TwiML(unclear + gather)->\n{str(vr)}")
        return xml_response(vr)

    except Exception as e:
        print(f"[CONFIRM] Exception -> {e}\n{traceback.format_exc()}")
        vr = VoiceResponse()
        twiml_play_tts(vr, msg("err_confirm","en"), "tts_cache/err_confirm.mp3")
        vr.hangup()
        print(f"[CONFIRM] TwiML(error)->\n{str(vr)}")
        return xml_response(vr)

# Diagnostic routes for A/B testing Twilio Gather behavior
if DIAG_TWILIO:
    @app.route("/diag/voice", methods=["POST"])
    def diag_voice():
        """
        Minimal, vendor-recommended Gather that Twilio should succeed with.
        No greeting first, no nesting complexity.
        """
        from twilio.twiml.voice_response import VoiceResponse, Gather
        vr = VoiceResponse()
        kwargs = gather_kwargs()
        kwargs.update({
            "input": "speech dtmf",
            "language": os.getenv("GATHER_LANGUAGE","en-US"),
            "method": "POST",
            "action": abs_url(url_for("diag_handle")),
            "timeout": int(os.getenv("GATHER_TIMEOUT","7")),
        })
        g = Gather(**kwargs)
        # Short "I'm listening" tone if exists (non-blocking)
        earcon = static_file_url("tts_cache/reprompt_listening.mp3")
        g.play(earcon)
        vr.append(g)
        return xml_response(vr)

    @app.route("/diag/handle", methods=["POST"])
    def diag_handle():
        _log_twilio_request("DIAG_HANDLE")
        from twilio.twiml.voice_response import VoiceResponse
        vr = VoiceResponse()
        sr = (request.form.get("SpeechResult") or "").strip()
        dg = (request.form.get("Digits") or "").strip()
        if sr:
            # Prove we received speech by echoing a short confirmation.
            # Use Play static TTS cache if you prefer; Say is fine for diag.
            vr.say(f"Received speech of length {len(sr)}. Thank you.")
        elif dg:
            vr.say(f"Received digits {dg}. Thank you.")
        else:
            vr.say("No speech or digits detected.")
        return xml_response(vr)

    @app.route("/debug/headers", methods=["GET","POST"])
    def debug_headers():
        _log_twilio_request("DEBUG_HEADERS")
        return "ok", 200

@app.get("/healthz")
def healthz():
    return {"ok": True, "app": "app.py", "diag": DIAG_TWILIO}, 200

@app.get("/whoami")
def whoami():
    return f"Loaded from app.py, DIAG_TWILIO={DIAG_TWILIO}, BUILD={BUILD_ID}", 200

@app.post("/debug_echo")
def debug_echo():
    # Echo what this server actually receives from Twilio (or curl)
    current_app.logger.info("[ECHO] headers=%s", dict(request.headers))
    current_app.logger.info("[ECHO] form=%s", dict(request.form))
    return jsonify({
        "headers": dict(request.headers),
        "form": dict(request.form),
        "args": dict(request.args),
        "method": request.method
    }), 200

@app.post("/twiml-selftest")
def twiml_selftest():
    from twilio.twiml.voice_response import VoiceResponse
    vr = VoiceResponse()
    vr.play(public_url("/static/tts_cache/no_recording.mp3"))
    return app.response_class(response=str(vr), status=200, mimetype="text/xml")

@app.route("/voice", methods=["POST", "GET"])
def voice_post():
    log_twilio_webhook("VOICE")
    _log_twilio_request("VOICE")
    # Generate unique call ID for credit tracking
    call_id = str(uuid.uuid4())
    
    # Log credit usage at start of call
    log_call_credits(call_id, "start")
    
    # Greeting in DEFAULT_LANG (detection happens after first caller audio)
    # Prefer dashboard store greeting if available; fall back to dialogue template
    greet_text = None
    try:
        if SHARED_DATA_AVAILABLE:
            info = shared_data.get_store_info() or {}
            greet_text = (info.get('greeting_message') or '').strip()
    except Exception:
        greet_text = None
    if not greet_text:
        greet_text = msg("greet", DEFAULT_LANG)
    # Use text-based caching so dashboard updates take effect immediately
    cached = play_cached(greet_text)
    greet_url = cached if cached else tts_line_url(greet_text, None, get_base_url())
    print(f"[VOICE] greet_url -> {greet_url} (lang={DEFAULT_LANG}, gather_main={USE_GATHER_MAIN})")

    vr = VoiceResponse()
    # Audio sources sanity: honor GREETING_URL env override if present
    greeting_url = os.getenv("GREETING_URL", "")
    if greeting_url.startswith("https://"):
        vr.play(greeting_url)
    else:
        vr.play(public_url(greet_url))  # your greeting url builder already logs this
    
    vr.gather(
        input="speech dtmf",
        speechModel="phone_call",
        speechTimeout="5",
        timeout="5",
        bargeIn=True,
        profanityFilter=False,
        actionOnEmptyResult=True,
        method="POST",
        action=public_url("/handle_gather")
    )
    
    # Log final TwiML if DIAG_TWILIO is enabled
    if DIAG_TWILIO:
        current_app.logger.info("[TWIML /voice]\n%s", vr.to_xml())
    
    return xml_response(vr)

# ===== NEW: first utterance Gather handler =====
def build_confirmation_audio_url(text: str) -> str:
    """Build a confirmation audio URL for the given text"""
    try:
        # Use existing TTS functionality to create audio
        cached = play_cached(text)
        if cached:
            return cached
        # Fallback to TTS line URL
        return tts_line_url(text, None, get_base_url())
    except Exception:
        # Ultimate fallback
        return public_url("static/tts_cache/no_recording.mp3")

def start_async_processing(job_id: str, text: str):
    def _work():
        with app.app_context():
            try:
                # Update status to processing
                update_state(job_id, {"status": "processing", "last_update": time.time()})
                
                # TODO: call your existing routing/LLM/TTS and produce a final mp3 URL reachable by Twilio
                final_url = build_confirmation_audio_url(text)  # use your existing function; if not present, create it to return /static/tts_cache/...mp3
                
                # Update with completion
                update_state(job_id, {
                    "status": "done", 
                    "ready": True, 
                    "play_url": final_url,
                    "answer_text": f"Got it: {text}",
                    "last_update": time.time()
                })
                logger.info("[STATE] async processing completed job=%s", job_id)
            except Exception as e:
                logger.exception("[STATE] ERROR in async processing job=%s", job_id)
                # extreme fallback: safe mp3 that exists
                fallback = public_url("static/tts_cache/holdy_tiny.mp3")
                update_state(job_id, {
                    "status": "error", 
                    "ready": True, 
                    "play_url": fallback,
                    "last_update": time.time()
                })
    threading.Thread(target=_work, daemon=True).start()

def save_state_and_start_async_process(speech: str, digits: str) -> str:
    text = (speech or digits or "").strip()
    job_id = str(uuid.uuid4())

    # initial state
    state_set(job_id, {"status": "working", "heard": text})

    def _worker(jid: str, utter: str):
        try:
            # tiny think time to simulate work
            time.sleep(0.5)
            # build reply line + turn it into a public MP3 url
            say = f"You said: {utter or 'nothing'}."
            mp3_url = tts_line_url(say) or public_url("/static/tts_cache/holdy_tiny.mp3")
            state_set(jid, {"status": "done", "heard": utter, "reply_url": mp3_url})
        except Exception as e:
            current_app.logger.exception("[JOB] worker failed for %s: %s", jid, e)
            state_set(jid, {"status": "error", "error": str(e)})

    threading.Thread(target=_worker, args=(job_id, text), daemon=True).start()
    return job_id

@app.post("/handle")
def handle():
    # optional deep webhook logging if you have log_twilio_webhook
    try:
        log_twilio_webhook("HANDLE")
    except Exception:
        pass

    form = request.form or {}
    speech = (form.get("SpeechResult") or "").strip()
    digits = (form.get("Digits") or "").strip()
    conf   = form.get("Confidence")
    try:
        conf = float(conf) if conf is not None else 0.0
    except Exception:
        conf = 0.0

    current_app.logger.info(
        "[GATHER] route=/handle keys=%s speech=%r digits=%r conf=%.3f",
        list(form.keys()), speech, digits, conf
    )

    # If Twilio sent anything at all, treat as input
    if speech or digits:
        job_id = save_state_and_start_async_process(speech, digits)
        tw = VoiceResponse()
        tw.redirect(public_url(f"/result?job={job_id}"), method="POST")
        return xml_response(tw)

    # No input -> reprompt (DO NOT hang up)
    tw = VoiceResponse()
    # keep your reprompt asset; allow mapping to Twilio Asset via HOLD_URL if defined
    hold_url = os.getenv("HOLD_URL", "")  # optional override to Twilio Asset
    if hold_url.startswith("https://"):
        tw.play(hold_url)
    else:
        tw.play(public_url("/static/tts_cache/reprompt_listening.mp3"))
    tw.gather(
        action=public_url("/handle"),
        method="POST",
        input="speech dtmf",
        speech_model="phone_call",
        speech_timeout="3",
        barge_in=True,
        profanity_filter=False,
        action_on_empty_result=True
    )
    return xml_response(tw)

@app.post("/handle_gather")
def handle_gather():
    form = request.form
    speech = form.get("SpeechResult", "").strip()
    digits = form.get("Digits", "").strip()

    if VOICE_SAFE_MODE:
        vr = VoiceResponse()
        vr.say(f"Heard: {speech or digits or 'nothing'}")
        return xml_response(vr)

    job_id = save_state_and_start_async_process(speech, digits)
    vr = VoiceResponse()
    vr.redirect(public_url(f"/result?job={job_id}"), method="POST")
    return xml_response(vr)
    
@app.route("/dept_choice", methods=["POST"])
def dept_choice():
    try:
        job_id = request.args.get("job") or request.form.get("job")
        vr = VoiceResponse()
        if not job_id or not load_state(job_id):
            twiml_play_tts(vr, msg("err_confirm","en"), "tts_cache/err_dept_choice.mp3")
            vr.hangup()
            return xml_response(vr)

        meta = load_state(job_id)
        caller_lang = meta.get("caller_lang","en")
        options = meta.get("dept_options", [])
        item = meta.get("heard_text","")

        # Prefer Gather speech
        reply = request.form.get("SpeechResult") or request.args.get("SpeechResult") or ""
        reply_n = (reply or "").lower().strip()
        print(f"[DEPT_CHOICE HEARD] '{reply}' options={options}")

        chosen = None
        for opt in options:
            if re.search(rf"\b{re.escape(opt.lower())}\b", reply_n):
                chosen = opt
                break

        # Simple synonyms
        if not chosen:
            if "bakery" in reply_n:
                chosen = "Bakery" if "Bakery" in options else chosen
            if "grocery" in reply_n or "groceries" in reply_n:
                chosen = "Grocery" if "Grocery" in options else chosen
            if "deli" in reply_n:
                chosen = "Deli" if "Deli" in options else chosen
            if "electronics" in reply_n:
                chosen = "Electronics" if "Electronics" in options else chosen
            if "clothing" in reply_n:
                chosen = "Clothing" if "Clothing" in options else chosen
            if "customer service" in reply_n or "service" in reply_n:
                chosen = "Customer Service" if "Customer Service" in options else chosen

        if not chosen:
            # Re-ask the same prompt with a quick hint
            hint = (
                f"Please say {', '.join(options[:-1])} or {options[-1]}."
                if not caller_lang.startswith("es") else
                f"Por favor diga {', '.join(options[:-1])} o {options[-1]}."
            )
            g = Gather(**gather_kwargs({
                "action": abs_url(url_for("dept_choice", job=job_id)),
                "method": "POST",
                "language": "es-US" if caller_lang.startswith("es") else "en-US",
                "timeout": max(1, CONF_TIMEOUT),
                "profanity_filter": True,
                "barge_in": True
            }))
            # Replay the original dept prompt then the hint
            if meta.get("dept_prompt_url"):
                g.play(meta["dept_prompt_url"])
            g.play(tts_line_url(hint, f"{CACHE_SUBDIR}/dept_hint_{job_id}.mp3", get_base_url()))
            vr.append(g)
            print(f"[DEPT_CHOICE] unclear -> re-asking")
            return xml_response(vr)

        # We have a department -> build final speak + end
        # Extract just the product name from the caller's speech
        product_name = _extract_product_name(item or "")
        if product_name:
            spoken = (
                f"Thanks. I'll connect you to {chosen} about {product_name}."
                if not caller_lang.startswith("es") else
                f"Gracias. Le conecto con {chosen} sobre {product_name}."
            )
        else:
            spoken = (
                f"Thanks. I'll connect you to {chosen} now."
                if not caller_lang.startswith("es") else
                f"Gracias. Le conecto con {chosen} ahora."
            )

        out_name = f"{CACHE_SUBDIR}/response_{job_id}.mp3"
        response_url = tts_line_url(spoken, out_name, get_base_url())
        meta.update({
            "ready": True,
            "needs_dept_choice": False,
            "response_url": response_url,
            "department": chosen,
            "phase": "final_ready"
        })
        save_state(job_id, meta)

        vr.redirect(_result_poll_url(get_base_url(), job_id, meta), method="POST")
        print(f"[DEPT_CHOICE] chosen={chosen} -> finalizing")
        return xml_response(vr)

    except Exception as e:
        print(f"[DEPT_CHOICE] Exception -> {e}\n{traceback.format_exc()}")
        vr = VoiceResponse()
        twiml_play_tts(vr, msg("err_confirm","en"), "tts_cache/err_dept_choice2.mp3")
        vr.hangup()
        return xml_response(vr)

@app.route("/handle", methods=["GET", "POST"])
def handle_recording():
    try:
        recording_url = request.form.get("RecordingUrl") or request.args.get("RecordingUrl")
        if not recording_url:
            vr = VoiceResponse()
            twiml_play_tts(vr, msg("no_record","en"), "tts_cache/no_recording.mp3")
            vr.hangup()
            print(f"[HANDLE] TwiML(no rec)->\n{str(vr)}")
            return xml_response(vr)

        job_id = str(uuid.uuid4())
        save_state(job_id, {
            "ready": False,
            "phase": "first_hold",
            "created_at": time.time(),
            "polls": 0,
            "last_hold_at": 0,
            "bg_played": False,
            "mid_hold_played": False,
            "correction_hops": 0,
            "caller_lang": DEFAULT_LANG,
            "suspect_spanish": False,
        })

        threading.Thread(
            target=prepare_reply_from_recording,
            args=(job_id, recording_url, get_base_url()),
            daemon=True
        ).start()

        vr = VoiceResponse()
        vr.redirect(_result_poll_url(get_base_url(), job_id, load_state(job_id)), method="POST")
        print(f"[HANDLE] TwiML ->\n{str(vr)}")
        return xml_response(vr)

    except Exception as e:
        print(f"[HANDLE] Exception -> {e}\n{traceback.format_exc()}")
        vr = VoiceResponse()
        twiml_play_tts(vr, "Sorry, we hit a snag.", "tts_cache/err_handle.mp3")
        vr.hangup()
        print(f"[HANDLE] TwiML(error)->\n{str(vr)}")
        return xml_response(vr)

@app.route("/tw_asset_canary", methods=["POST", "GET"])
def tw_asset_canary():
    vr = VoiceResponse()
    vr.play(HOLDY_TINY_CDN)
    vr.hangup()
    print(f"[CANARY] /tw_asset_canary -> play {HOLDY_TINY_CDN}")
    return xml_response(vr)

@app.route("/tw_local_canary", methods=["POST", "GET"])
def tw_local_canary():
    try:
        url = tts_line_url("Canary check.", f"{CACHE_SUBDIR}/canary.mp3")
    except Exception as e:
        print(f"[CANARY] TTS error -> {e}")
        # Fallback to a known cached line under tts_cache, not root greet.mp3
        url = static_file_url(f"{CACHE_SUBDIR}/err_global.mp3")
    vr = VoiceResponse()
    vr.play(url)
    vr.hangup()
    print(f"[CANARY] /tw_local_canary -> play {url}")
    return xml_response(vr)

@app.route("/tw_xml_canary", methods=["POST","GET"])
def tw_xml_canary():
    vr = VoiceResponse()
    vr.say("xml canary ok")
    vr.hangup()
    return xml_response(vr)

@app.route("/tw_record_canary", methods=["POST", "GET"])
def tw_record_canary():
    vr = VoiceResponse()
    vr.say("Beep. Say anything for a second.")
    vr.record(
        action=abs_url(url_for("tw_record_done")),
        method="POST",
        maxLength=3,
        timeout=1,
        trim="trim-silence",
        playBeep=True,
        finishOnKey=""
    )
    vr.say("No audio received. Bye.")
    vr.hangup()
    print(f"[CANARY] /tw_record_canary -> waiting for recording, callback to /tw_record_done")
    return xml_response(vr)

@app.route("/tw_record_done", methods=["POST", "GET"])
def tw_record_done():
    rec_url = request.form.get("RecordingUrl") or request.args.get("RecordingUrl")
    print(f"[CANARY] /tw_record_done RecordingUrl={rec_url}")
    vr = VoiceResponse()
    if rec_url:
        vr.say("Got the recording. Bye.")
    else:
        vr.say("No recording URL seen. Bye.")
    vr.hangup()
    return xml_response(vr)

@app.errorhandler(Exception)
def _global_error(e):
    print(f"[GLOBAL] Unhandled -> {e}\n{traceback.format_exc()}")
    try:
        if has_request_context() and request.path.startswith("/static/"):
            return ("Not found", 404)
    except Exception:
        pass
    vr = VoiceResponse()
    twiml_play_tts(vr, msg("err_global","en"), "tts_cache/err_global.mp3")
    vr.hangup()
    print(f"[GLOBAL] TwiML(error)->\n{str(vr)}")
    return xml_response(vr), 200

# ---- SMS helper ----
def send_sms(to_number: str, body: str) -> bool:
	try:
		sid = (TWILIO_SID or "").strip()
		token = (TWILIO_TOKEN or "").strip()
		if not sid or not token or not to_number:
			print(f"[SMS] Missing credentials or destination. to='{to_number}' sid_set={bool(sid)} token_set={bool(token)}")
			return False
		url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
		data = {"To": to_number, "Body": body}
		print(f"[SMS DEBUG] Body to send: {body}")
		if TWILIO_MESSAGING_SERVICE_SID:
			data["MessagingServiceSid"] = TWILIO_MESSAGING_SERVICE_SID
		elif TWILIO_FROM_NUMBER:
			data["From"] = TWILIO_FROM_NUMBER
		else:
			print("[SMS] Neither TWILIO_MESSAGING_SERVICE_SID nor TWILIO_FROM_NUMBER is set.")
			return False
		r = requests.post(url, data=data, auth=(sid, token), timeout=30)
		ok = 200 <= r.status_code < 300
		if not ok:
			print(f"[SMS] Twilio error {r.status_code}: {r.text}")
		else:
			print("[SMS] Message queued successfully")
		return ok
	except Exception as e:
		print(f"[SMS] Exception sending SMS: {e}")
		return False

# ---- Coupon SMS helper ----
def send_coupon_sms(to_number: str) -> bool:
	"""Send a simple coupon SMS using Messaging Service if available, otherwise From number."""
	# Prefer dashboard-configured SMS body, fallback to default
	try:
		if SHARED_DATA_AVAILABLE:
			templates = shared_data.get_dialogue_templates() or {}
			body = templates.get("coupons", {}).get("sms_body") or "Thanks! Here are today's coupons: …"
		else:
			body = "Thanks! Here are today's coupons: …"
	except Exception:
		body = "Thanks! Here are today's coupons: …"
	return send_sms(to_number, body)

# ---- Consent logging / GitHub integration ----
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
CONSENT_REPO = os.getenv("CONSENT_REPO", "mikewfilm/consent-log").strip()
CONSENT_BRANCH = os.getenv("CONSENT_BRANCH", "main").strip()
CONSENT_JSON_PATH = os.getenv("CONSENT_JSON_PATH", "consent-log.json").strip()
CONSENT_WORKFLOW_PATH = os.getenv("CONSENT_WORKFLOW_PATH", ".github/workflows/build.yml").strip()
CONSENT_GENERATOR_PATH = os.getenv("CONSENT_GENERATOR_PATH", "generate_index.py").strip()
CONSENT_PAGES_DIR = os.getenv("CONSENT_PAGES_DIR", "docs").strip()
CONSENT_URL = os.getenv("CONSENT_URL", "https://consent-service-9381.twil.io/voice-consent").strip()

class ConsentLogger:
	def __init__(self):
		self.local_path = os.path.join(os.path.dirname(__file__), "consent_log_local.json")
		self._ensure_local()
	
	def _ensure_local(self):
		try:
			if not os.path.exists(self.local_path):
				with open(self.local_path, "w") as f:
					json.dump({"entries": []}, f)
		except Exception as e:
			print(f"[CONSENT] Failed to init local log: {e}")
	
	def _load_local(self) -> dict:
		try:
			with open(self.local_path, "r") as f:
				return json.load(f)
		except Exception:
			return {"entries": []}
	
	def _save_local(self, data: dict):
		try:
			with open(self.local_path, "w") as f:
				json.dump(data, f, indent=2)
		except Exception as e:
			print(f"[CONSENT] Failed to save local log: {e}")
	
	def record(self, phone: str, method: str, transcript: str | None, job_id: str):
		entry = {
			"timestamp": datetime.utcnow().isoformat() + "Z",
			"phone": phone,
			"method": method,
			"speech_text": (transcript or "").strip() if transcript else None,
			"job_id": job_id,
			"scope": "coupon_sms",
		}
		blob = self._load_local()
		blob.setdefault("entries", []).append(entry)
		self._save_local(blob)
		# Best-effort push to GitHub
		self._push_to_github(entry)
	
	def _gh_api(self, method: str, url: str, **kwargs):
		if not GITHUB_TOKEN:
			raise RuntimeError("GITHUB_TOKEN not set")
		headers = kwargs.pop("headers", {})
		headers.update({
			"Authorization": f"Bearer {GITHUB_TOKEN}",
			"Accept": "application/vnd.github+json",
		})
		return requests.request(method, url, headers=headers, timeout=60, **kwargs)
	
	def _get_file(self, path: str):
		url = f"https://api.github.com/repos/{CONSENT_REPO}/contents/{path}?ref={CONSENT_BRANCH}"
		r = self._gh_api("GET", url)
		if r.status_code == 200:
			return r.json()
		return None
	
	def _put_file(self, path: str, content_str: str, message: str, sha: str | None = None):
		url = f"https://api.github.com/repos/{CONSENT_REPO}/contents/{path}"
		payload = {
			"message": message,
			"content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
			"branch": CONSENT_BRANCH,
		}
		if sha:
			payload["sha"] = sha
		r = self._gh_api("PUT", url, json=payload)
		if r.status_code not in (200,201):
			raise RuntimeError(f"GitHub PUT failed {r.status_code}: {r.text}")
		return r.json()
	
	def _ensure_repo_scaffold(self):
		# Ensure workflow and generator exist
		try:
			wf = self._get_file(CONSENT_WORKFLOW_PATH)
			gen = self._get_file(CONSENT_GENERATOR_PATH)
			wf_content = self._workflow_yaml()
			gen_content = self._generator_py()
			if not wf:
				self._put_file(CONSENT_WORKFLOW_PATH, wf_content, "Add consent log workflow")
			if not gen:
				self._put_file(CONSENT_GENERATOR_PATH, gen_content, "Add consent index generator")
		except Exception as e:
			print(f"[CONSENT] Scaffold ensure failed: {e}")
	
	def _push_to_github(self, latest_entry: dict):
		if not GITHUB_TOKEN:
			print("[CONSENT] GITHUB_TOKEN not set; skipping remote update")
			return
		try:
			self._ensure_repo_scaffold()
			# Fetch current JSON
			existing = self._get_file(CONSENT_JSON_PATH)
			entries = []
			sha = None
			if existing and isinstance(existing, dict):
				sha = existing.get("sha")
				try:
					content_decoded = base64.b64decode(existing.get("content", "").encode("utf-8")).decode("utf-8")
					remote = json.loads(content_decoded or "{}")
					entries = remote.get("entries", [])
				except Exception:
					entries = []
			entries.append(latest_entry)
			new_json = json.dumps({"entries": entries}, indent=2)
			self._put_file(CONSENT_JSON_PATH, new_json, "Log SMS consent", sha)
			# Also (re)generate index.html content and push into docs/
			index_html = self._render_index(entries)
			pages_path = f"{CONSENT_PAGES_DIR}/index.html"
			pages_existing = self._get_file(pages_path)
			pages_sha = pages_existing.get("sha") if pages_existing else None
			self._put_file(pages_path, index_html, "Update consent index", pages_sha)
		except Exception as e:
			print(f"[CONSENT] Remote update failed: {e}")
	
	def _render_index(self, entries: list[dict]) -> str:
		rows = []
		for e in reversed(entries):
			rows.append(
				f"<tr><td>{e.get('timestamp','')}</td><td>{e.get('phone','')}</td><td>{e.get('method','')}</td><td>{(e.get('speech_text') or '').replace('<','&lt;').replace('>','&gt;')}</td><td>{e.get('job_id','')}</td></tr>"
			)
		html = f"""
<!doctype html>
<html><head><meta charset='utf-8'><title>Consent Log</title>
<style>body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:8px}} th{{background:#f4f4f4;text-align:left}}</style>
</head><body>
<h1>Consent Log</h1>
<p>Entries: {len(entries)}</p>
<table>
<thead><tr><th>Timestamp (UTC)</th><th>Phone</th><th>Method</th><th>Speech</th><th>Job ID</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</body></html>
"""
		return html
	
	def _workflow_yaml(self) -> str:
		return """
name: Build consent index

on:
  push:
    branches: [ "main" ]
    paths:
      - 'consent-log.json'
      - 'generate_index.py'
      - '.github/workflows/build.yml'

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - run: python generate_index.py
      - name: Commit updated index
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: Update consent index
          branch: main
		""".strip()
	
	def _generator_py(self) -> str:
		return '''
import json, os
from datetime import datetime

ROOT = os.path.dirname(__file__)
json_path = os.path.join(ROOT, 'consent-log.json')
docs_dir = os.path.join(ROOT, 'docs')
os.makedirs(docs_dir, exist_ok=True)

entries = []
if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        try:
            data = json.load(f)
            entries = data.get('entries', [])
        except Exception:
            entries = []

rows = []
for e in reversed(entries):
    ts = e.get('timestamp','')
    phone = e.get('phone','')
    method = e.get('method','')
    speech = (e.get('speech_text') or '').replace('<','&lt;').replace('>','&gt;')
    job = e.get('job_id','')
    rows.append(f"<tr><td>{ts}</td><td>{phone}</td><td>{method}</td><td>{speech}</td><td>{job}</td></tr>")

html = f"""
<!doctype html>
<html><head><meta charset='utf-8'><title>Consent Log</title>
<style>body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:8px}} th{{background:#f4f4f4;text-align:left}}</style>
</head><body>
<h1>Consent Log</h1>
<p>Entries: {len(entries)}</p>
<table>
<thead><tr><th>Timestamp (UTC)</th><th>Phone</th><th>Method</th><th>Speech</th><th>Job ID</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</body></html>
"""

with open(os.path.join(docs_dir, 'index.html'), 'w') as f:
    f.write(html)
		'''.strip()

consent_logger = ConsentLogger()

# ---------- CONSENT FLOW (drop-in patch) ----------
from flask import request, make_response, url_for
from twilio.twiml.voice_response import VoiceResponse, Gather

CONSENT_URL = os.getenv("CONSENT_URL", "https://consent-service-9381.twil.io/voice-consent")

# Map CallSid -> job_id
CALLSID_TO_JOB: dict[str, str] = {}
CALLSID_TO_FROM: dict[str, str] = {}

# ===== INTERNET SEARCH FUNCTIONS =====

def search_product_online(product_name: str) -> dict:
    """
    Search for product information online and return department classification.
    Uses existing department structure from grocery_departments.py for better classification.
    Returns a dict with 'department', 'confidence', and 'description'.
    """
    try:
        # Clean the product name for search
        search_query = f"{product_name} grocery store department"
        
        # Use Google search to find relevant information (collect URLs and then fetch titles)
        search_results = []
        try:
            for url in search(search_query, num_results=8):
                search_results.append(url)
        except Exception as e:
            print(f"[SEARCH ERROR] Google search failed: {e}")
            return {'department': 'Customer Service', 'confidence': 0.1, 'description': 'Search failed'}

        if not search_results:
            return {'department': 'Customer Service', 'confidence': 0.1, 'description': 'Unable to find information online'}

        # Import department keywords from grocery_departments.py
        from grocery_departments import (
            PRODUCE_TERMS, DAIRY_TERMS, MEAT_SEAFOOD_TERMS, FROZEN_TERMS, 
            HEALTH_BEAUTY_TERMS, HOUSEHOLD_TERMS, HARDWARE_TERMS, ELECTRONICS_TERMS,
            CLOTHING_TERMS, SPORTING_GOODS_TERMS, TOYS_GAMES_TERMS, ARTS_CRAFTS_TERMS,
            GARDEN_CENTER_TERMS, BOOKS_MEDIA_TERMS, PHARMACY_TERMS
        )

        # Department scoring based on existing structure
        department_scores = {
            'Grocery': 0,
            'Health & Beauty': 0,
            'Household': 0,
            'Customer Service': 0
        }
        
        product_lower = product_name.lower()

        # Score based on product name matching existing department keywords
        if any(term in product_lower for term in PRODUCE_TERMS.split('|')):
            department_scores['Grocery'] += 3
        if any(term in product_lower for term in DAIRY_TERMS.split('|')):
            department_scores['Grocery'] += 3
        if any(term in product_lower for term in MEAT_SEAFOOD_TERMS.split('|')):
            department_scores['Grocery'] += 3
        if any(term in product_lower for term in FROZEN_TERMS.split('|')):
            department_scores['Grocery'] += 3
        if any(term in product_lower for term in HEALTH_BEAUTY_TERMS.split('|')):
            department_scores['Health & Beauty'] += 3
        if any(term in product_lower for term in HOUSEHOLD_TERMS.split('|')):
            department_scores['Household'] += 3
        if any(term in product_lower for term in PHARMACY_TERMS.split('|')):
            department_scores['Health & Beauty'] += 4  # Higher weight for pharmacy items

        # Boost scores based on search result URLs and page titles
        import urllib.parse
        for url in search_results[:5]:
            u = url.lower()
            netloc = urllib.parse.urlparse(u).netloc
            
            # Domain-based hints
            if any(k in netloc for k in ['walgreens', 'cvs', 'riteaid', 'rite-aid', 'boots', 'watsons', 'pharmacy']):
                department_scores['Health & Beauty'] += 3
            if any(k in netloc for k in ['kroger', 'albertsons', 'safeway', 'wegmans', 'wholefoods', 'whole-foods', 'aldi', 'foodlion', 'publix', 'grocery']):
                department_scores['Grocery'] += 2
            if any(k in netloc for k in ['homedepot', 'home-depot', 'lowes', 'hardware']):
                department_scores['Household'] += 2
            
            # URL path hints
            if any(k in u for k in ['pharmacy', 'beauty', 'health', 'personal-care', 'personal_care', 'sexual', 'family-planning', 'lubricant', 'condom', 'feminine', 'intimate']):
                department_scores['Health & Beauty'] += 4
            if any(k in u for k in ['grocery', 'food', 'pantry', 'beverage', 'produce', 'dairy', 'meat', 'frozen']):
                department_scores['Grocery'] += 3
            if any(k in u for k in ['clean', 'laundry', 'household', 'cleaning', 'paper', 'detergent']):
                department_scores['Household'] += 3
            
            # Title hints (fetch quickly with short timeout)
            try:
                r = requests.get(url, timeout=2, headers={'User-Agent': 'Mozilla/5.0'})
                if r.ok:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    title = (soup.title.string if soup.title and soup.title.string else '').lower()
                    text = f"{title}"
                    
                    # Check against department keywords in titles
                    if any(term in text for term in HEALTH_BEAUTY_TERMS.split('|')):
                        department_scores['Health & Beauty'] += 4
                    if any(term in text for term in PHARMACY_TERMS.split('|')):
                        department_scores['Health & Beauty'] += 5
                    if any(term in text for term in PRODUCE_TERMS.split('|')):
                        department_scores['Grocery'] += 3
                    if any(term in text for term in DAIRY_TERMS.split('|')):
                        department_scores['Grocery'] += 3
                    if any(term in text for term in HOUSEHOLD_TERMS.split('|')):
                        department_scores['Household'] += 3
            except Exception:
                pass

        # Determine the best department
        best_department = max(department_scores, key=department_scores.get)
        
        # Special handling for health/beauty items that might be misclassified
        if any(term in product_lower for term in ['lubricant', 'lube', 'condom', 'intimate', 'sexual', 'family planning', 'feminine', 'personal care']):
            best_department = 'Health & Beauty'
            department_scores['Health & Beauty'] += 5
        
        confidence = min(department_scores[best_department] / 8, 0.95)  # Cap at 95% confidence

        if confidence < 0.3:
            best_department = 'Customer Service'
            confidence = 0.1

        print(f"[SEARCH CLASSIFICATION] {product_name} -> {best_department} (confidence: {confidence:.2f})")

        return {
            'department': best_department,
            'confidence': confidence,
            'description': f'Found information about {product_name} online'
        }
        
    except Exception as e:
        print(f"[SEARCH ERROR] {e}")
        return {'department': 'Customer Service', 'confidence': 0.1, 'description': 'Search failed'}

def should_use_internet_search(product_name: str) -> bool:
    """
    Determine if we should use internet search for this product.
    Returns True if the product is likely to be found online.
    """
    # Skip very short or generic terms
    if len(product_name.strip()) < 3:
        return False
    
    # Skip common words that won't help
    generic_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
    if product_name.lower().strip() in generic_words:
        return False
    
    return True

def _abs(url):  # helper for absolute URLs
	if url.startswith("http"): return url
	return request.url_root.rstrip("/") + url

def get_consent_prompt_url(job: str) -> str:
	"""Return absolute URL to consent prompt MP3, using generic cached version.

	- Always use generic consent_prompt_generic.mp3 for consistency and caching
	- If missing, generate it via TTS helper
	- Fallback to generic yes_or_no.mp3
	"""
	# Always use generic consent prompt for caching
	relpath = "tts_cache/consent_prompt_generic.mp3"
	abs_path = os.path.join(app.static_folder, relpath)
	
	# If file already exists, return absolute URL
	if os.path.exists(abs_path):
		return static_file_url(relpath)

	# Try to generate via TTS using our existing helper
	try:
		line = "I can text you today's coupons. May I send a text now? Please say yes or no."
		url = tts_line_url(line, f"{CACHE_SUBDIR}/consent_prompt_generic.mp3", get_base_url(), job, "Consent")
		if url and url != "None":
			return url
	except Exception:
		pass

	# Fallback to generic asset
	return static_file_url("tts_cache/yes_or_no.mp3")

@app.route("/sms_consent", methods=["POST"])
def sms_consent():
	job = request.args.get("job", "")
	call_sid = request.form.get("CallSid") or request.args.get("CallSid")
	if call_sid and job:
		CALLSID_TO_JOB[call_sid] = job
		from_number = request.form.get("From") or request.args.get("From") or request.values.get("From")
		if from_number:
			CALLSID_TO_FROM[call_sid] = from_number
		app.logger.info(f"[CONSENT] map CallSid={call_sid} -> job={job} from={CALLSID_TO_FROM.get(call_sid,'')}")

	mp3 = build_consent_prompt(job or "nojob")  # your single-voice "text" line

	# Use local consent handling instead of external service
	action_url = abs_url(url_for("consent_continue"))
	if job:
		action_url += f"?job={job}"
	app.logger.info(f"[CONSENT] Using local consent URL: '{action_url}'")
	print(f"[DEBUG] action_url set to: {action_url}")

	vr = VoiceResponse()
	with vr.gather(
		input="speech",
		language="en-US",
		barge_in=True,
		method="POST",
		action=action_url
	) as g:
		# Always use absolute, publicly reachable URL for Twilio
		abs_mp3 = mp3 if mp3.startswith("http") else static_file_url(mp3)
		g.play(abs_mp3)

	return xml_response(vr)

@app.route("/post_consent", methods=["POST", "GET"])
def post_consent():
	job = request.args.get("job", "")
	tw = VoiceResponse()
	# Silent response so only ElevenLabs audio is heard during consent
	return xml_response(tw)
# ---------- END PATCH ----------

def build_consent_thanks(job: str, consent: str) -> str:
	text = ("Thanks—I'll send that text now." if consent == "yes"
			else "No problem, I won't send a text.")
	# Use generic cache key instead of job-specific
	cache_key = "consent_thanks_yes" if consent == "yes" else "consent_thanks_no"
	return tts_cached(f"{cache_key}.mp3", text)

@app.route("/consent_continue", methods=["GET", "POST"])
def consent_continue():
	# Get consent from speech input or direct parameter
	speech_result = request.values.get("SpeechResult", "").lower().strip()
	consent_raw = (request.values.get("consent") or speech_result or "").lower().strip()
	call_sid = request.values.get("CallSid")
	job = (request.values.get("job") or CALLSID_TO_JOB.get(call_sid))
	# Get the phone number from the call data
	from_number = request.values.get("From") or request.values.get("from") or (CALLSID_TO_FROM.get(call_sid) if call_sid else None)  # caller's number

	# Robust yes/no parsing
	lower = consent_raw
	yes_hints = ("yes", "yeah", "yep", "sure", "ok", "okay", "affirmative", "that's right", "that is right", "uh huh", "uh-huh")
	no_hints = ("no", "nope", "nah", "negative")
	consent_yes = any(h in lower for h in yes_hints)
	if any(h in lower for h in no_hints):
		consent_yes = False

	try:
		if job and consent_yes:
			if not from_number and call_sid:
				from_number = CALLSID_TO_FROM.get(call_sid)
			if from_number:
				app.logger.info(f"[CONSENT] Sending SMS to {from_number} for job {job}")
				send_coupon_sms(from_number)
			else:
				app.logger.warning(f"[CONSENT] No from number available for job {job}; skipping SMS send but confirming")
			mp3 = build_consent_thanks(job, "yes")
		elif job and not consent_yes:
			mp3 = build_consent_thanks(job, "no")
		else:
			# Fallback: be graceful even if we somehow lack a job or phone number
			app.logger.warning(f"[CONSENT] Missing data: job={job}, from_number={from_number}, consent={consent_raw}")
			mp3 = static_file_url('tts_cache/err_global.mp3')

		vr = VoiceResponse()
		play_url = mp3 if mp3.startswith("http") else static_file_url(mp3)
		vr.play(play_url)
		vr.hangup()
		return xml_response(vr)
	except Exception:
		app.logger.exception("Consent finalize failed")
		vr = VoiceResponse()
		vr.play(static_file_url('tts_cache/err_global.mp3'))
		vr.hangup()
		return xml_response(vr)

def build_consent_prompt(job: str | None) -> str:
	# one coherent sentence so the prosody matches
	prompt_text = (
		"I can send a text with your coupons now. "
		"Is it okay if I send a text to this number? Please say yes or no."
	)
	# Use generic cache key instead of job-specific
	return tts_cached("consent_prompt_generic.mp3", prompt_text)

def tts_cached(filename: str, text: str) -> str:
	"""Generate/cache TTS to a known filename under tts_cache and return absolute URL."""
	# Normalize to tts_cache/<filename>
	relpath = filename if filename.startswith(f"{CACHE_SUBDIR}/") else f"{CACHE_SUBDIR}/{filename}"
	url = tts_line_url(text, relpath, get_base_url())
	return url if url and url != "None" else static_file_url(relpath)

# ========== API ENDPOINTS FOR DASHBOARD INTEGRATION ==========

@app.route("/api/store-info", methods=["GET"])
def api_get_store_info():
    """Get store information"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        store_info = shared_data.get_store_info()
        return jsonify(store_info)
    except Exception as e:
        app.logger.error(f"Error getting store info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/store-info", methods=["PUT"])
def api_update_store_info():
    """Update store information"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        shared_data.update_store_info(data)
        return jsonify({"success": True, "message": "Store info updated successfully"})
    except Exception as e:
        app.logger.error(f"Error updating store info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/departments", methods=["GET"])
def api_get_departments():
    """Get all departments"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        departments = shared_data.get_departments()
        return jsonify(departments)
    except Exception as e:
        app.logger.error(f"Error getting departments: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/departments", methods=["POST"])
def api_add_department():
    """Add a new department"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        shared_data.add_department(data)
        return jsonify({"success": True, "message": "Department added successfully"})
    except Exception as e:
        app.logger.error(f"Error adding department: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/departments/<int:dept_id>", methods=["PUT"])
def api_update_department(dept_id):
    """Update a department"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        success = shared_data.update_department(dept_id, data)
        if success:
            return jsonify({"success": True, "message": "Department updated successfully"})
        else:
            return jsonify({"error": "Department not found"}), 404
    except Exception as e:
        app.logger.error(f"Error updating department: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/inventory", methods=["GET"])
def api_get_inventory():
    """Get all inventory items"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        inventory = shared_data.get_inventory()
        return jsonify(inventory)
    except Exception as e:
        app.logger.error(f"Error getting inventory: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/inventory", methods=["POST"])
def api_add_inventory_item():
    """Add a new inventory item"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        shared_data.add_inventory_item(data)
        return jsonify({"success": True, "message": "Inventory item added successfully"})
    except Exception as e:
        app.logger.error(f"Error adding inventory item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/inventory/<int:item_id>", methods=["PUT"])
def api_update_inventory_item(item_id):
    """Update an inventory item"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        success = shared_data.update_inventory_item(item_id, data)
        if success:
            return jsonify({"success": True, "message": "Inventory item updated successfully"})
        else:
            return jsonify({"error": "Inventory item not found"}), 404
    except Exception as e:
        app.logger.error(f"Error updating inventory item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/coupons", methods=["GET"])
def api_get_coupons():
    """Get all coupons"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        coupons = shared_data.get_coupons()
        return jsonify(coupons)
    except Exception as e:
        app.logger.error(f"Error getting coupons: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/coupons", methods=["POST"])
def api_add_coupon():
    """Add a new coupon"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        shared_data.add_coupon(data)
        return jsonify({"success": True, "message": "Coupon added successfully"})
    except Exception as e:
        app.logger.error(f"Error adding coupon: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/voice-templates", methods=["GET"])
def api_get_voice_templates():
    """Get all voice templates"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        templates = shared_data.get_voice_templates()
        return jsonify(templates)
    except Exception as e:
        app.logger.error(f"Error getting voice templates: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/voice-templates", methods=["POST"])
def api_add_voice_template():
    """Add a new voice template"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        shared_data.add_voice_template(data)
        return jsonify({"success": True, "message": "Voice template added successfully"})
    except Exception as e:
        app.logger.error(f"Error adding voice template: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    """Get system settings"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        settings = shared_data.get_settings()
        return jsonify(settings)
    except Exception as e:
        app.logger.error(f"Error getting settings: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/settings", methods=["PUT"])
def api_update_settings():
    """Update system settings"""
    if not SHARED_DATA_AVAILABLE:
        return jsonify({"error": "Shared data not available"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        shared_data.update_settings(data)
        return jsonify({"success": True, "message": "Settings updated successfully"})
    except Exception as e:
        app.logger.error(f"Error updating settings: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/usage", methods=["GET"])
def api_get_usage():
    """Get usage statistics"""
    try:
        print(f"[API DEBUG] Starting usage API call")
        
        # Get basic credit tracker data (if available)
        try:
            credit_data = credit_tracker.get_daily_summary()
            service_data = credit_tracker.get_service_breakdown()
        except NameError:
            credit_data = {"total_credits": 0, "active_calls": 0, "date": "Unknown"}
            service_data = {}
        
        # Get TTS cache statistics (if available)
        try:
            cache_stats = CACHE_MANAGER.get_stats()
        except NameError:
            cache_stats = {
                "total_cached_files": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate_percent": 0,
                "tts_calls": 0,
                "total_chars_synthesized": 0,
                "cache_dir": "static/tts_cache"
            }
        
        # Get ElevenLabs API information
        elevenlabs_info = {}
        if ELEVENLABS_API_KEY:
            print(f"[API DEBUG] ElevenLabs API key found, length: {len(ELEVENLABS_API_KEY)}")
            try:
                # Check ElevenLabs API for subscription info
                headers = {
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                }
                
                # Get subscription info
                subscription_response = requests.get(
                    "https://api.elevenlabs.io/v1/user/subscription",
                    headers=headers,
                    timeout=10
                )
                
                if subscription_response.status_code == 200:
                    subscription_data = subscription_response.json()
                    elevenlabs_info = {
                        "api_key_set": True,
                        "api_key_length": len(ELEVENLABS_API_KEY[:8]) + 3,  # Show first 8 chars + "..."
                        "voice_id": ELEVENLABS_VOICE_ID or "Default",
                        "subscription": {
                            "tier": subscription_data.get("tier", "Unknown"),
                            "character_count": subscription_data.get("character_count", 0),
                            "character_limit": subscription_data.get("character_limit", 0),
                            "can_extend_character_limit": subscription_data.get("can_extend_character_limit", False),
                            "allowed_to_extend_character_limit": subscription_data.get("allowed_to_extend_character_limit", False),
                            "next_character_count_reset_unix": subscription_data.get("next_character_count_reset_unix", 0),
                            "voice_limit": subscription_data.get("voice_limit", 0),
                            "professional_voice_limit": subscription_data.get("professional_voice_limit", 0),
                            "can_extend_voice_limit": subscription_data.get("can_extend_voice_limit", False),
                            "can_use_instant_voice_cloning": subscription_data.get("can_use_instant_voice_cloning", False),
                            "can_use_professional_voice_limit": subscription_data.get("can_use_professional_voice_limit", False)
                        }
                    }
                else:
                    elevenlabs_info = {
                        "api_key_set": True,
                        "api_key_length": len(ELEVENLABS_API_KEY[:8]) + 3,
                        "voice_id": ELEVENLABS_VOICE_ID or "Default",
                        "subscription": None,
                        "error": f"API Error: {subscription_response.status_code}"
                    }
            except Exception as e:
                elevenlabs_info = {
                    "api_key_set": True,
                    "api_key_length": len(ELEVENLABS_API_KEY[:8]) + 3,
                    "voice_id": ELEVENLABS_VOICE_ID or "Default",
                    "subscription": None,
                    "error": f"Connection error: {str(e)}"
                }
        else:
            elevenlabs_info = {
                "api_key_set": False,
                "api_key_length": 0,
                "voice_id": "Not set",
                "subscription": None
            }
        
        # Top requested items (sorted desc)
        try:
            items_sorted = sorted((MOST_REQUESTED_COUNTS or {}).items(), key=lambda x: x[1], reverse=True)
            # Filter out hidden items
            visible = [(k, v) for (k, v) in items_sorted if not is_item_hidden(k)]
            top_items = [{"name": k, "count": v} for k, v in visible[:20]]
            hidden_items = sorted(list(MOST_REQUESTED_HIDDEN))
        except Exception:
            top_items = []
            hidden_items = []

        return jsonify({
            "credit_tracker": credit_data,
            "service_breakdown": service_data,
            "elevenlabs": elevenlabs_info,
            "cache_stats": cache_stats,
            "top_items": top_items,
            "hidden_items": hidden_items
        })
    except Exception as e:
        app.logger.error(f"Error getting usage: {e}")
        return jsonify({"error": str(e)}), 500

# Hide/unhide endpoints
@app.route("/api/items/hide", methods=["POST"])
def api_hide_item():
    try:
        data = request.get_json(force=True) or {}
        name = data.get("name", "")
        hide_item(name)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/items/unhide", methods=["POST"])
def api_unhide_item():
    try:
        data = request.get_json(force=True) or {}
        name = data.get("name", "")
        unhide_item(name)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Dashboard-triggered cache refresh so updated dialogue templates (e.g., coupon SMS) are used immediately
@app.route("/api/update-cache", methods=["POST"])
def api_update_cache():
    try:
        if SHARED_DATA_AVAILABLE:
            _ = shared_data.get_dialogue_templates()
            _ = shared_data.get_store_info()  # ensure greeting/store info refresh
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", "5003"))
    prewarm_tts_files()
    
    # Log ASR configuration
    if USE_GATHER_MAIN:
        print(f"[ASR] Primary: Twilio Gather ASR (USE_GATHER_MAIN=True)")
    else:
        print(f"[ASR] Primary: Local recording fallback (USE_GATHER_MAIN=False)")
    
    if USE_LOCAL_WHISPER:
        if FasterWhisper is not None:
            print(f"[ASR] Local Whisper: faster-whisper available (model={WHISPER_MODEL_NAME})")
        elif WhisperLegacy is not None:
            print(f"[ASR] Local Whisper: openai-whisper available (model={WHISPER_MODEL_NAME})")
        else:
            print(f"[ASR] Local Whisper: ENABLED but no implementation available")
    else:
        print(f"[ASR] Local Whisper: DISABLED (USE_LOCAL_WHISPER=0)")
    
    print(f"[GATHER] language={GATHER_LANGUAGE} enhanced={GATHER_ENHANCED} timeout={GATHER_TIMEOUT} speechTimeout={GATHER_SPEECH_TIMEOUT} hints={GATHER_HINTS}")
    
    print(f"Starting Flask on 0.0.0.0:{PORT}")
    log_effective_config()
    app.run(host="0.0.0.0", port=PORT, debug=False)