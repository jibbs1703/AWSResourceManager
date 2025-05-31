"""Tests for the S3 module of the AWS Resource Manager package."""

import io
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.aws_resource_manager.s3 import S3Handler


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


@pytest.fixture
def s3handler_mock():
    with patch("src.aws_resource_manager.s3.boto3.client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        handler = S3Handler("secret", "access", "region")
        handler.client = mock_instance
        yield handler


def test_list_buckets_success(s3handler_mock):
    s3handler_mock.client.list_buckets.return_value = {
        "Buckets": [{"Name": "bucket1"}, {"Name": "bucket2"}]
    }
    buckets = s3handler_mock.list_buckets()
    assert buckets == ["bucket1", "bucket2"]


def test_list_buckets_error(s3handler_mock):
    s3handler_mock.client.list_buckets.side_effect = Exception("fail")
    buckets = s3handler_mock.list_buckets()
    assert buckets is None


def test_create_bucket_already_exists(s3handler_mock):
    s3handler_mock.list_buckets = MagicMock(return_value=["mybucket"])
    s3handler_mock.create_bucket("mybucket")
    s3handler_mock.client.create_bucket.assert_not_called()


def test_create_bucket_new(s3handler_mock):
    s3handler_mock.list_buckets = MagicMock(return_value=[])
    s3handler_mock.create_bucket("newbucket")
    s3handler_mock.client.create_bucket.assert_called_once()


def test_delete_bucket_success(s3handler_mock):
    s3handler_mock.delete_bucket("bucket1")
    s3handler_mock.client.delete_bucket.assert_called_with(Bucket="bucket1")


def test_check_object_exists_true(s3handler_mock):
    s3handler_mock.client.head_object.return_value = {}
    assert s3handler_mock.check_object_exists("bucket", "obj") is True


def test_check_object_exists_false(s3handler_mock):
    error = ClientError({"Error": {"Code": "404"}}, "head_object")
    s3handler_mock.client.head_object.side_effect = error
    assert s3handler_mock.check_object_exists("bucket", "obj") is False


def test_list_objects_with_contents(s3handler_mock):
    s3handler_mock.client.list_objects_v2.return_value = {
        "Contents": [{"Key": "a.txt"}, {"Key": "b.txt"}]
    }
    result = s3handler_mock.list_objects("bucket")
    assert result == ["a.txt", "b.txt"]


def test_list_objects_empty(s3handler_mock):
    s3handler_mock.client.list_objects_v2.return_value = {}
    result = s3handler_mock.list_objects("bucket")
    assert result == []


def test_delete_object(s3handler_mock):
    s3handler_mock.delete_object("bucket", "obj")
    s3handler_mock.client.delete_object.assert_called_with(Bucket="bucket", Key="obj")


def test_generate_presigned_url_success(s3handler_mock):
    s3handler_mock.client.generate_presigned_url.return_value = "http://url"
    url = s3handler_mock.generate_presigned_url("bucket", "obj")
    assert url == "http://url"


def test_upload_file_success(s3handler_mock):
    file_obj = io.BytesIO(b"data")
    s3handler_mock.upload_file("bucket", "file.txt", file_obj)
    s3handler_mock.client.put_object.assert_called()


def test_download_file_success(s3handler_mock):
    s3handler_mock.download_file("bucket", "obj", "local.txt")
    s3handler_mock.client.download_file.assert_called_with("bucket", "obj", "local.txt")


def test_read_file_found(s3handler_mock):
    s3handler_mock.client.list_objects_v2.return_value = {"Contents": [{"Key": "file.txt"}]}
    s3handler_mock.client.get_object.return_value = {"Body": io.BytesIO(b"hello")}
    result = s3handler_mock.read_file("bucket", "file.txt")
    assert result.read() == "hello"


def test_read_file_not_found(s3handler_mock):
    s3handler_mock.client.list_objects_v2.return_value = {}
    result = s3handler_mock.read_file("bucket", "nofile.txt")
    assert result == "File not in bucket"


def test_delete_file_success(s3handler_mock):
    msg = s3handler_mock.delete_file("bucket", "file.txt")
    assert "deleted from the bucket" in msg


def test_copy_object(s3handler_mock):
    s3handler_mock.copy_object("src", "obj", "dst", "dstobj")
    s3handler_mock.client.copy_object.assert_called_with(
        Bucket="dst",
        CopySource={"Bucket": "src", "Key": "obj"},
        Key="dstobj"
    )


def test_move_object(s3handler_mock):
    s3handler_mock.copy_object = MagicMock()
    s3handler_mock.delete_object = MagicMock()
    s3handler_mock.move_object("src", "obj", "dst", "dstobj")
    s3handler_mock.copy_object.assert_called_once()
    s3handler_mock.delete_object.assert_called_once()


def test_set_object_acl(s3handler_mock):
    s3handler_mock.set_object_acl("bucket", "obj", "public-read")
    s3handler_mock.client.put_object_acl.assert_called_with(Bucket="bucket",
    Key="obj", ACL="public-read")


def test_get_object_metadata_success(s3handler_mock):
    s3handler_mock.client.head_object.return_value = {"ContentLength": 123}
    meta = s3handler_mock.get_object_metadata("bucket", "obj")
    assert meta == {"ContentLength": 123}


def test_enable_versioning(s3handler_mock):
    s3handler_mock.enable_versioning("bucket")
    s3handler_mock.client.put_bucket_versioning.assert_called_with(
        Bucket="bucket", VersioningConfiguration={"Status": "Enabled"}
    )


def test_disable_versioning(s3handler_mock):
    s3handler_mock.disable_versioning("bucket")
    s3handler_mock.client.put_bucket_versioning.assert_called_with(
        Bucket="bucket", VersioningConfiguration={"Status": "Suspended"}
    )


def test_restore_archived_object(s3handler_mock):
    s3handler_mock.restore_archived_object("bucket", "obj")
    s3handler_mock.client.restore_object.assert_called()


def test_set_bucket_cors_policy(s3handler_mock):
    rules = [{"AllowedOrigins": ["*"], "AllowedMethods": ["GET"], "AllowedHeaders": ["*"]}]
    s3handler_mock.set_bucket_cors_policy("bucket", rules)
    s3handler_mock.client.put_bucket_cors.assert_called_with(
        Bucket="bucket", CORSConfiguration={"CORSRules": rules}
    )


def test_get_bucket_encryption_success(s3handler_mock):
    s3handler_mock.client.get_bucket_encryption.return_value = {"Rules": []}
    result = s3handler_mock.get_bucket_encryption("bucket")
    assert result == {"Rules": []}