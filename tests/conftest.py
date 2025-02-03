"""This module contains default fixtures for the aws_resource_manager package tests."""
import warnings
import pytest

@pytest.fixture(autouse=True)
def silence_specific_deprecation_warnings():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "datetime.datetime.utcnow.*", DeprecationWarning)
        yield