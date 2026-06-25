from core.config import settings


def test_settings():
    assert settings.Hello_URL == "This is test hello", "there is an error with env settings"
    return {"success message"}

print(test_settings())