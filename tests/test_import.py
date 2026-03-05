def test_import():
    import erlc_api

    assert erlc_api is not None
    assert erlc_api.ERLCClient is not None
    assert erlc_api.ERLCError is not None
