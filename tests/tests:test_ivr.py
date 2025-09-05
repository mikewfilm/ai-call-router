import os
import re
import yaml
import pytest
from flask import Flask
from app import app  # Your Flask app should expose `app`

def load_scenarios():
    with open("tests/scenarios.yaml", "r") as f:
        return yaml.safe_load(f)

def client():
    return app.test_client()

def post_voice(c, text: str):
    # Simulate Twilio Voice webhook POST (form-encoded)
    return c.post(
        "/voice",
        data={
            "CallSid": "CA_TEST",
            "From": "+19998887777",
            "To": "+15555550000",
            # If you use speech-to-text, many frameworks pass text as 'SpeechResult' or similar
            "SpeechResult": text,
            "TranscriptionText": text,
        },
        content_type="application/x-www-form-urlencoded",
    )

def assert_say_contains(twiml: str, phrases):
    body_lower = twiml.lower()
    for p in phrases:
        assert p.lower() in body_lower, f"Expected phrase '{p}' not found in <Say>: {twiml}"

def has_dial_number(twiml: str):
    return '<Dial' in twiml and ('number="' in twiml or "<Number>" in twiml)

def has_record(twiml: str):
    return "<Record" in twiml or "<Record/>" in twiml

@pytest.mark.parametrize("scenario", load_scenarios())
def test_scenarios(scenario):
    c = client()

    # Optional context flags (e.g., force after-hours mode)
    ctx = scenario.get("context", {})
    if ctx.get("force_after_hours"):
        os.environ["BUSINESS_HOURS_MODE"] = "closed"

    resp = post_voice(c, scenario["intent"])
    assert resp.status_code == 200, f"/voice returned {resp.status_code}"
    twiml = resp.data.decode("utf-8").strip()

    # Basic TwiML sanity
    assert twiml.startswith("<?xml") or "<Response" in twiml, "Not TwiML?"
    assert "<Response" in twiml, "Missing <Response> root"

    exp = scenario.get("expected", {})

    # Check text content in <Say>
    if "say_contains" in exp:
        assert_say_contains(twiml, exp["say_contains"])

    # Route checks (you can satisfy these with either labels or direct <Dial>)
    if exp.get("route_to_label"):
        # For label-driven routing, your app could add a comment or <Say> tag noting it
        # e.g., <!-- route: pharmacy --> or <Say>Routing to pharmacy</Say>
        assert exp["route_to_label"].lower() in twiml.lower(), f"Expected route label {exp['route_to_label']} in TwiML"

        # Also allow direct Dial as valid routing
        assert has_dial_number(twiml), f"Expected a <Dial> for route_to_label={exp['route_to_label']}"

    if exp.get("dial_any"):
        assert has_dial_number(twiml), "Expected some <Dial> to a human"

    if exp.get("record"):
        assert has_record(twiml), "Expected <Record> for voicemail"

    if exp.get("clarify_or_route"):
        # Pass if we either ask a clarifying question OR we dial somewhere
        ok = ("did you mean" in twiml.lower() or "which department" in twiml.lower() or has_dial_number(twiml))
        assert ok, "Expected a clarifying prompt or a <Dial>"

    # Reset env flag if we set it
    if ctx.get("force_after_hours"):
        os.environ.pop("BUSINESS_HOURS_MODE", None)