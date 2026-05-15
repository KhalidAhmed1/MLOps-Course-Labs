"""Settings / configuration helpers."""

from churn_api.settings import Settings, get_settings


def test_get_settings_returns_singleton():
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second


def test_settings_default_registered_model_name():
    get_settings.cache_clear()
    s = Settings()
    assert s.registered_model_name == "Bank_Churn_Classifier"
    assert s.champion_alias == "champion"
