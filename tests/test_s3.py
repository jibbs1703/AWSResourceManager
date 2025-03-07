"""Tests for the S3 module of the AWS Resource Manager package."""

from botocore.exceptions import ClientError

from src.aws_resource_manager.s3.s3 import S3Handler


def test_s3_connection():
    """
    Simple AWS S3 connection test.

    This function tests the connection to AWS S3 by listing the buckets.
    If the connection is successful, the function will return True.
    If the connection fails, it will print the error message and return False.
    """
    try:
        s3_connection = S3Handler.credentials()
        s3_connection.list_buckets()
        assert True  # noqa: B011, S101
    except ClientError as e:
        print(f"S3 connection failed: {e}")
        assert False  # noqa: B011, S101


if __name__ == "__main__":
    test_s3_connection()
