def test_root_redirects_to_condominium_list(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response["Location"] == "/condominios/"
