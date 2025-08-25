"""Tests for the Credentials Module of the AWS Resource Manager Package."""

from unittest import mock

import pytest

from src.aws_resource_manager.credentials import get_credentials


@pytest.mark.unit
def test_get_credentials_from_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_access_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_secret_key")
    monkeypatch.setenv("REGION", "us-east-2")
    creds = get_credentials()
    assert creds == ("test_access_key", "test_secret_key", "us-east-2")


@pytest.mark.unit
def test_get_credentials_load_dotenv(monkeypatch):
    # Unset env vars to force load_dotenv
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("REGION", raising=False)

    with mock.patch("os.getenv", side_effect=["dotenv_access", "dotenv_secret", "dotenv_region"]):
        creds = get_credentials()
        assert creds == ("dotenv_access", "dotenv_secret", "dotenv_region")


@pytest.mark.unit
def test_get_credentials_missing(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("REGION", raising=False)

    with mock.patch("src.aws_resource_manager.credentials.load_dotenv"), \
         mock.patch("os.getenv", side_effect=[None, None, None, None, None, None]):
        with pytest.raises(ValueError, match="All credentials not found in environment variables."):
            get_credentials()
