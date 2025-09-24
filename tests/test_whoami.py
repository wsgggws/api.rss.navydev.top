import pytest


@pytest.mark.asyncio
async def test_whoami(client):
    response = await client.get("/whoami")
    assert response.status_code == 200
    assert response.json() == {"whoami": "api.rss.navydev.top"}
