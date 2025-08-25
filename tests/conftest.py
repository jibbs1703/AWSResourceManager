"""This module contains default fixtures for tests."""

import warnings
from unittest.mock import MagicMock, patch

import pytest

from src.aws_resource_manager.s3 import S3Handler


@pytest.fixture(autouse=True)
def silence_specific_deprecation_warnings():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "datetime.datetime.utcnow.*", DeprecationWarning)
        yield


@pytest.fixture
def s3handler_mock():
    with patch("src.aws_resource_manager.s3.boto3.client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        handler = S3Handler()
        handler.client = mock_instance
        yield handler
