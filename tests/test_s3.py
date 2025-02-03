"""Tests for the S3 module of the AWS Resource Manager package.""" 
from src.aws_resource_manager.s3 import S3Handler
from botocore.exceptions import ClientError


def test_s3_connection():
    """Simple AWS S3 connection test"""
    try:
        s3_connection = S3Handler.credentials()
        s3_connection.list_buckets()
        assert True
    except ClientError as e:
        print(f"S3 connection failed: {e}")
        assert False
