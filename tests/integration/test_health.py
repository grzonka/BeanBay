def test_health(client):
    """Verify the /health endpoint returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
