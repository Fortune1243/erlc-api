def test_import():
    import erlc_api

    assert erlc_api is not None
    assert erlc_api.ERLCClient is not None
    assert erlc_api.ERLCError is not None
    assert erlc_api.ModelDecodeError is not None
    assert erlc_api.Player is not None
    assert erlc_api.EventWebhookRouter is not None
    assert erlc_api.WebhookEventType is not None
    assert erlc_api.decode_event_webhook_payload is not None
    assert erlc_api.verify_event_webhook_signature is not None


def test_import_subpackages():
    import erlc_api.discord
    import erlc_api.utils
    import erlc_api.web

    assert erlc_api.discord is not None
    assert erlc_api.utils is not None
    assert erlc_api.web is not None
