from app import app, CONSENT_URL


def test_coupon_process_redirects_only():
    c = app.test_client()
    r = c.post('/coupon_process')
    xml = r.get_data(as_text=True)
    assert r.status_code == 200
    # Only a Redirect to /sms_consent and no intro/thanks assets
    assert '<Response>' in xml and '</Response>' in xml
    assert xml.count('<Redirect') == 1
    assert '/sms_consent' in xml
    assert 'coupon_sms_intro' not in xml
    assert 'consent_thanks' not in xml


def test_sms_consent_shape():
    c = app.test_client()
    r = c.post('/sms_consent', data={'job': 't1'})
    xml = r.get_data(as_text=True)
    assert r.status_code == 200
    # Exactly one Gather
    assert xml.count('<Gather') == 1
    assert xml.count('</Gather>') == 1
    # Gather action
    assert f'action="{CONSENT_URL}"' in xml
    # Exactly one prompt: either one Play or one Say, not both
    plays = xml.count('<Play>')
    says = xml.count('<Say>')
    assert (plays + says) == 1
    # Followed by Redirect to /continue
    assert xml.count('<Redirect') >= 1
    assert '/continue' in xml


def test_continue_is_valid():
    c = app.test_client()
    r = c.post('/continue')
    xml = r.get_data(as_text=True)
    assert r.status_code == 200
    assert '<Response>' in xml and '</Response>' in xml

