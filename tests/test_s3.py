"""Tests for the S3 module of the AWS Resource Manager package."""

import io
import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.aws_resource_manager.s3 import S3Handler


@pytest.mark.unit
@pytest.mark.parametrize(
    "env_vars, expected_secret, expected_access, expected_region",
    [
        (
            {"AWS_ACCESS_KEY": "A", "AWS_SECRET_ACCESS_KEY": "S", "AWS_REGION": "R"},
            "S", "A", "R"
        ),
        (
            {"AWS_ACCESS_KEY": None, "AWS_SECRET_ACCESS_KEY": None, "AWS_REGION": None},
            "S2", "A2", "R2"
        ),
    ]
)
def test_credentials(monkeypatch, env_vars, expected_secret, expected_access, expected_region):
    # Patch os.getenv to return values from env_vars
    def getenv_side_effect(key):
        return env_vars.get(key)
    monkeypatch.setattr(os, "getenv", getenv_side_effect)

    # Patch load_dotenv and os.getenv for second call
    with patch("src.aws_resource_manager.s3.os.getenv") as mock_env:
        # For the first case, all env vars are present, so load_dotenv should not be called
        if all(env_vars.values()):
            mock_env.side_effect = getenv_side_effect
        else:
            # For the second case, simulate .env loading
            def getenv_after_load(key):
                mapping = {"AWS_ACCESS_KEY": "A2",
                           "AWS_SECRET_ACCESS_KEY": "S2",
                           "AWS_REGION": "R2"}
                return mapping.get(key)
            mock_env.side_effect = getenv_after_load

        with patch("src.aws_resource_manager.s3.S3Handler.__init__",
                   return_value=None) as mock_init:
            S3Handler.credentials()
            mock_init.assert_called_with(expected_secret, expected_access, expected_region)


@pytest.mark.unit
def test_init_with_region():
    with patch("src.aws_resource_manager.s3.boto3.client") as mock_boto:
        handler = S3Handler("secret", "access", "region")
        assert hasattr(handler, "client")
        assert handler.location == {"LocationConstraint": "region"}
        mock_boto.assert_called_with(
            "s3",
            aws_access_key_id="access",
            aws_secret_access_key="secret",
            region_name="region",
        )


@pytest.mark.unit
def test_init_without_region():
    with patch("src.aws_resource_manager.s3.boto3.client") as mock_boto:
        handler = S3Handler("secret", "access", None)
        assert hasattr(handler, "client")
        mock_boto.assert_called_with(
            "s3",
            aws_access_key_id="access",
            aws_secret_access_key="secret",
        )


@pytest.mark.unit
def test_list_buckets_success(s3handler_mock):
    s3handler_mock.client.list_buckets.return_value = {
        "Buckets": [{"Name": "bucket1"}, {"Name": "bucket2"}]
    }
    buckets = s3handler_mock.list_buckets()
    assert buckets == ["bucket1", "bucket2"]


@pytest.mark.unit
def test_list_buckets_error(s3handler_mock):
    s3handler_mock.client.list_buckets.side_effect = Exception("fail")
    buckets = s3handler_mock.list_buckets()
    assert buckets is None


@pytest.mark.unit
def test_create_bucket_already_exists(s3handler_mock):
    s3handler_mock.list_buckets = MagicMock(return_value=["mybucket"])
    s3handler_mock.create_bucket("mybucket")
    s3handler_mock.client.create_bucket.assert_not_called()


@pytest.mark.unit
def test_create_bucket_new(s3handler_mock):
    s3handler_mock.list_buckets = MagicMock(return_value=[])
    s3handler_mock.create_bucket("newbucket")
    s3handler_mock.client.create_bucket.assert_called_once()


@pytest.mark.unit
def test_delete_bucket_success(s3handler_mock):
    s3handler_mock.delete_bucket("bucket1")
    s3handler_mock.client.delete_bucket.assert_called_with(Bucket="bucket1")


@pytest.mark.unit
def test_check_object_exists_true(s3handler_mock):
    s3handler_mock.client.head_object.return_value = {}
    assert s3handler_mock.check_object_exists("bucket", "obj") is True


@pytest.mark.unit
def test_check_object_exists_false(s3handler_mock):
    error = ClientError({"Error": {"Code": "404"}}, "head_object")
    s3handler_mock.client.head_object.side_effect = error
    assert s3handler_mock.check_object_exists("bucket", "obj") is False


@pytest.mark.unit
def test_list_objects_with_contents(s3handler_mock):
    s3handler_mock.client.list_objects_v2.return_value = {
        "Contents": [{"Key": "a.txt"}, {"Key": "b.txt"}]
    }
    result = s3handler_mock.list_objects("bucket")
    assert result == ["a.txt", "b.txt"]


@pytest.mark.unit
def test_list_objects_empty(s3handler_mock):
    s3handler_mock.client.list_objects_v2.return_value = {}
    result = s3handler_mock.list_objects("bucket")
    assert result == []


@pytest.mark.unit
def test_delete_object(s3handler_mock):
    s3handler_mock.delete_object("bucket", "obj")
    s3handler_mock.client.delete_object.assert_called_with(Bucket="bucket", Key="obj")


@pytest.mark.unit
def test_generate_presigned_url_success(s3handler_mock):
    s3handler_mock.client.generate_presigned_url.return_value = "http://url"
    url = s3handler_mock.generate_presigned_url("bucket", "obj")
    assert url == "http://url"


@pytest.mark.unit
def test_upload_file_success(s3handler_mock):
    file_obj = io.BytesIO(b"data")
    s3handler_mock.upload_file("bucket", "file.txt", file_obj)
    s3handler_mock.client.put_object.assert_called()


@pytest.mark.unit
def test_download_file_success(s3handler_mock):
    s3handler_mock.download_file("bucket", "obj", "local.txt")
    s3handler_mock.client.download_file.assert_called_with("bucket", "obj", "local.txt")


@pytest.mark.unit
def test_read_file_found(s3handler_mock):
    s3handler_mock.client.list_objects_v2.return_value = {"Contents": [{"Key": "file.txt"}]}
    s3handler_mock.client.get_object.return_value = {"Body": io.BytesIO(b"hello")}
    result = s3handler_mock.read_file("bucket", "file.txt")
    assert result.read() == "hello"


@pytest.mark.unit
def test_read_file_not_found(s3handler_mock):
    s3handler_mock.client.list_objects_v2.return_value = {}
    result = s3handler_mock.read_file("bucket", "nofile.txt")
    assert result == "File not in bucket"


@pytest.mark.unit
def test_delete_file_success(s3handler_mock):
    msg = s3handler_mock.delete_file("bucket", "file.txt")
    assert "deleted from the bucket" in msg


@pytest.mark.unit
def test_copy_object(s3handler_mock):
    s3handler_mock.copy_object("src", "obj", "dst", "dstobj")
    s3handler_mock.client.copy_object.assert_called_with(
        Bucket="dst",
        CopySource={"Bucket": "src", "Key": "obj"},
        Key="dstobj"
    )


@pytest.mark.unit
def test_move_object(s3handler_mock):
    s3handler_mock.copy_object = MagicMock()
    s3handler_mock.delete_object = MagicMock()
    s3handler_mock.move_object("src", "obj", "dst", "dstobj")
    s3handler_mock.copy_object.assert_called_once()
    s3handler_mock.delete_object.assert_called_once()


@pytest.mark.unit
def test_set_object_acl(s3handler_mock):
    s3handler_mock.set_object_acl("bucket", "obj", "public-read")
    s3handler_mock.client.put_object_acl.assert_called_with(Bucket="bucket",
    Key="obj", ACL="public-read")


@pytest.mark.unit
def test_get_object_metadata_success(s3handler_mock):
    s3handler_mock.client.head_object.return_value = {"ContentLength": 123}
    meta = s3handler_mock.get_object_metadata("bucket", "obj")
    assert meta == {"ContentLength": 123}


@pytest.mark.unit
def test_enable_versioning(s3handler_mock):
    s3handler_mock.enable_versioning("bucket")
    s3handler_mock.client.put_bucket_versioning.assert_called_with(
        Bucket="bucket", VersioningConfiguration={"Status": "Enabled"}
    )


@pytest.mark.unit
def test_disable_versioning(s3handler_mock):
    s3handler_mock.disable_versioning("bucket")
    s3handler_mock.client.put_bucket_versioning.assert_called_with(
        Bucket="bucket", VersioningConfiguration={"Status": "Suspended"}
    )


@pytest.mark.unit
def test_restore_archived_object(s3handler_mock):
    s3handler_mock.restore_archived_object("bucket", "obj")
    s3handler_mock.client.restore_object.assert_called()


@pytest.mark.unit
def test_set_bucket_cors_policy(s3handler_mock):
    rules = [{"AllowedOrigins": ["*"], "AllowedMethods": ["GET"], "AllowedHeaders": ["*"]}]
    s3handler_mock.set_bucket_cors_policy("bucket", rules)
    s3handler_mock.client.put_bucket_cors.assert_called_with(
        Bucket="bucket", CORSConfiguration={"CORSRules": rules}
    )


@pytest.mark.unit
def test_get_bucket_encryption_success(s3handler_mock):
    s3handler_mock.client.get_bucket_encryption.return_value = {"Rules": []}
    result = s3handler_mock.get_bucket_encryption("bucket")
    assert result == {"Rules": []}
