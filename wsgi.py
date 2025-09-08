import logging
logging.basicConfig(level=logging.DEBUG)
from flask import Flask

app = Flask(__name__)

@app.get("/")
def root():
    return "OK"

@app.get("/healthz")
def healthz():
    return "OK"
