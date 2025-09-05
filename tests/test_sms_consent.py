import re
from app import app, CONSENT_URL


def test_sms_consent_twiml_shape():
    client = app.test_client()
    resp = client.post('/sms_consent', data={'job': 'test-job-123'})
    assert resp.status_code == 200
    xml = resp.get_data(as_text=True)

    # Exactly one Gather
    assert xml.count('<Gather') == 1
    assert xml.count('</Gather>') == 1

    # At most one Play or Say prompt
    plays = xml.count('<Play>')
    says = xml.count('<Say>')
    assert (plays + says) <= 1

    # Gather action must be CONSENT_URL
    m = re.search(r'<Gather[^>]*action="([^"]+)"', xml)
    assert m, f"No Gather action in TwiML: {xml}"
    assert m.group(1) == CONSENT_URL

    # Must end with a Redirect to /continue (POST)
    assert '<Redirect method="POST">' in xml
    assert '/continue' in xml


