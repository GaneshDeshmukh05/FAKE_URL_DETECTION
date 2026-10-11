import pytest

from src.feature_engineering import FEATURE_NAMES, InvalidURLException, extract_features, get_domain, normalise_url


def test_extract_features_is_deterministic_and_complete():
    features = extract_features("https://login.example.com/account?id=42&ref=mail")
    assert tuple(features) == FEATURE_NAMES
    assert features["uses_https"] == 1
    assert features["subdomain_count"] == 1
    assert features["query_param_count"] == 2
    assert features["digit_count"] == 2
    assert features["suspicious_keyword_count"] >= 2


def test_ip_and_punycode_url_features():
    ip_features = extract_features("http://192.168.1.2:8080/login")
    punycode_features = extract_features("https://xn--pple-43d.example/verify")
    assert ip_features["ip_in_url"] == 1
    assert ip_features["has_port"] == 1
    assert punycode_features["has_punycode"] == 1


@pytest.mark.parametrize("value", ["", "ftp://example.com", "http://", "example .com", "https://example.com:not-a-port"])
def test_invalid_urls_are_rejected(value):
    with pytest.raises(InvalidURLException):
        normalise_url(value)


def test_domain_group_key_is_lowercase():
    assert get_domain("HTTPS://WWW.Example.COM/A") == "www.example.com"
