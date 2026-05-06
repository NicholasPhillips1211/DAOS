def test_root_endpoint(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Intelligent DataOps Platform"
