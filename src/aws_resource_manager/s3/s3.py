import io
import os
from io import StringIO

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from src.aws_resource_manager.s3.logger import configure_logger

logger = configure_logger()


class S3Handler:
    @classmethod
    def credentials(cls)-> "S3Handler":
        """
        Retrieves AWS credentials from a hidden environment file.

        This class method accesses the user's AWS secret and access
        keys stored in an environment file. If a region is specified,
        the methods within the S3Handler class will execute in that region.
        Otherwise, AWS will assign a default region.

        :return: An instance of the S3Handler class initialized with
        the user's credentials and specified region
        """
        load_dotenv()
        secret = os.getenv("ACCESS_SECRET")
        access = os.getenv("ACCESS_KEY")
        region = os.getenv("REGION")

        return cls(secret, access, region)

    def __init__(self, secret, access, region) -> None:
        """
        Initializes the S3Handler class with user credentials and creates
        the AWS S3 client.

        This constructor method initializes the S3Handler class using the
        provided secret and access keys. It creates an AWS S3 client using
        the boto3 library. If no region is specified, AWS assigns the default
        region identified via aws-cli. The created client is available for
        subsequent methods within the class.

        :param secret: User's AWS secret key loaded from the environment file
        :param access: User's AWS access key loaded from the environment file
        :param region: User's AWS region loaded from the environment file

        Returns: None
        """
        if region is None:
            self.client = boto3.client(
                "s3", aws_access_key_id=access, aws_secret_access_key=secret
            )
        else:
            self.location = {"LocationConstraint": region}
            self.client = boto3.client(
                "s3",
                aws_access_key_id=access,
                aws_secret_access_key=secret,
                region_name=region,
            )

    def list_buckets(self) -> list:
        """
        Retrieves and returns a list of bucket names available in the user's
        AWS account.

        :return: A list of the S3 bucket names, or None if an error occurs.
        """
        try:
            response = self.client.list_buckets()
            buckets = response["Buckets"]
            all_buckets = [bucket["Name"] for bucket in buckets]
            logger.info(f"This account contains the following buckets: {all_buckets}")
            return all_buckets

        except Exception as e:  # noqa: BLE001
            logger.error(f"An error occurred while listing buckets: {e}")
            return None

        except self.client.exceptions.ClientError as e:
            logger.error(f"An AWS client error occurred: {e}")
            return None

    def create_bucket(self, bucket_name: str) -> None:
        """
        Creates an S3 bucket in the user's AWS account.

        This method creates a new S3 bucket in the region specified during the
        instantiation of the class. If the bucket name has already been used,
        it will not create a new bucket. If no region is specified, the bucket
        is created in the default S3 region.

        :param bucket_name: Name of the bucket to be created

        Returns: None
        """
        try:
            if bucket_name in self.list_buckets():
                logger.info(f"The bucket {bucket_name} already exists")
            else:
                logger.info("A new bucket will be created in your AWS account")
                self.client.create_bucket(
                    Bucket=bucket_name, CreateBucketConfiguration=self.location)
                logger.info(f"The bucket {bucket_name} has been successfully created")

        except ClientError as e:
            logger.error(f"An AWS client error occurred while creating S3 bucket {bucket_name}: {e}")  # noqa: E501

        except Exception as e:  # noqa: BLE001
            logger.error(f"An error occurred while creating the bucket: {e}")
    
    def delete_bucket(self, bucket_name: str) -> None:
        """
        Deletes an empty bucket in the user's S3 account.

        Parameters:
        bucket_name (str): The name of the bucket to be deleted.

        Returns:
        None

        Raises:
        ClientError: If the bucket is not empty, does not exist, or if there are 
        insufficient permissions to delete the bucket.

        """
        try:
            logger.info(f"Deleting S3 bucket {bucket_name}")
            self.client.delete_bucket(Bucket=bucket_name)
            logger.info(f"S3 bucket {bucket_name} deleted successfully.")
        except ClientError as e:
            logger.error(f"Error deleting S3 bucket {bucket_name}: {e}")

    def check_object_exists(self, bucket_name:str, object_name:str):
        """
        Checks if an object exists in the S3 bucket.

        :param object_name: The name of the object to check
        :return: True if the object exists, False otherwise
        """
        try:
            logger.info(f"Checking if object {object_name} exists in bucket {bucket_name}")
            self.client.head_object(Bucket=bucket_name, Key=object_name)
            logger.info(f"Object {object_name} exists in bucket {bucket_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Object {object_name} not found in bucket {bucket_name}")
            else:
                logger.error(f"Error checking if object {object_name} exists in S3: {e}")
            return False

    def list_objects(self, bucket_name: str) -> list:
        """
        Lists the objects in an S3 bucket.

        :param bucket_name: Name of the S3 bucket.
        :return: List of object keys if successful, None otherwise.
        """
        try:
            response = self.client.list_objects_v2(Bucket=bucket_name)

            if 'Contents' in response:
                object_keys = [obj['Key'] for obj in response['Contents']]
                logger.info(
                    f"Objects in bucket '{bucket_name}': {object_keys}")
                return object_keys
            else:
                logger.info(f"No objects found in bucket '{bucket_name}'.")
                return []

        except ClientError as e:
            logger.error(f"Client Error listing objects: {e}")
            return None

        except Exception as e:
            logger.exception(f"Unexpected error listing objects: {e}")
            return None

    def delete_object(self, bucket_name:str, object_name:str, folder="")-> None:
        """
        Deletes an object from the S3 bucket.

        :param object_name: The name of the object to delete
        """
        try:
            logger.info(f"Deleting object {object_name} from bucket {bucket_name}")
            self.client.delete_object(Bucket=bucket_name, Key=f"{folder}{object_name}")
            logger.info(f"Object {object_name} deleted from bucket {bucket_name}")
        except ClientError as e:
            self.logger.error(f"Error deleting object {object_name} from S3: {e}")

    def generate_presigned_url(self, bucket_name:str, object_name:str, 
                               expiration:int=600)->str:
        """
        Generates a pre-signed URL to access an S3 object in the specified bucket.

        This method creates a pre-signed URL that allows temporary access to an S3 object
        without requiring AWS credentials. The URL can be shared with others to grant 
        access to the object for a limited time.

        :param bucket_name: The name of the S3 bucket containing the object.
        :param object_name: The key (name) of the S3 object to be accessed.
        :param expiration: The expiration time in seconds for the pre-signed URL 
                        (default is 600 seconds or 10 minutes).
        :return: A pre-signed URL as a string that provides temporary access to the S3 object.
        :raises: ClientError if there is an error generating the pre-signed URL.

        """
        try:
            logger.info(f"Generating pre-signed URL for {object_name} in  bucket {bucket_name}")
            url = self.client.generate_presigned_url('get_object',
                                                 Params={'Bucket': bucket_name, 'Key': object_name},
                                                 ExpiresIn=expiration)
            logger.info(f"Generated pre-signed URL for object {object_name}")
            return url
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL for {object_name}: {e}")
            return None

    def upload_file(self, bucket_name:str, filename:str, file:io.BytesIO, folder:str=""):
        """
        Uploads a file to an S3 bucket.
        Parameters:
        - bucket_name (str): The name of the target S3 bucket.
        - filename (str): The name of the file to be uploaded.
        - file (io.BytesIO): The file object to be uploaded.
        - folder (str, optional): The folder path within the S3 bucket.
          Default is an empty string.

        Returns: None
        """
        try:
            self.client.put_object(Bucket=bucket_name,
                                   Key=f"{folder}{filename}",
                                   Body=file.getvalue())
            logger.info(
                f"File {filename} uploaded successfully to {bucket_name}/{folder}"
            )
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error uploading file to S3: {str(e)}")

    def download_file(self, bucket_name:str, object_name:str, file_name:str) -> None:
        """
        Downloads a file from an S3 bucket in the user's AWS account.

        :param bucket_name: Name of the bucket to download the file from
        :param object_name: Name of the file to download from the S3 bucket
        :param file_name: Name of the file to save the downloaded content to
        :return: None
        """
        try:
            self.client.download_file(bucket_name, object_name, file_name)
            logger.info(
                f"File '{object_name}' downloaded successfully from bucket"
                  "'{bucket_name}' to '{file_name}'."
            )

        except ClientError as e:
            logger.error(f"Client Error downloading file: {e}")

        except Exception as e:
            logger.exception(f"Unexpected error downloading file: {e}")

    def read_file(self, bucket_name: str, object_name: str):
        """
        Reads a file from an S3 bucket in the user's AWS account and returns its contents.

        :param bucket_name: Name of the bucket to read the file from.
        :param object_name: Name of the file to read from the S3 bucket.
        :return: An object containing the file's contents, or None if an error occurs.
        """
        try:
            response = self.client.list_objects_v2(Bucket=bucket_name)
            if 'Contents' not in response or not any(
                    obj['Key'] == object_name for obj in response['Contents']):
                logger.info(
                    f"The specified key '{object_name}' does not exist in bucket '{bucket_name}'."
                )
                return "File not in bucket"

            response = self.client.get_object(Bucket=bucket_name,
                                              Key=object_name)
            file_content = StringIO(response['Body'].read().decode('utf-8'))
            logger.info(
                f"File '{object_name}' read successfully from bucket '{bucket_name}'."
            )
            return file_content

        except ClientError as e:
            logger.error(f"Client Error reading file: {e}")
            return None

        except Exception as e:
            logger.exception(f"Unexpected error reading file: {e}")
            return None

    def delete_file(self, bucket_name:str, file_name:str):
        """
        Deletes a file from an S3 bucket in the user's AWS account.

        :param bucket_name: Name of the bucket to access the file.
        :param object_name: Name of the file to delete from the S3 bucket.
        :return: Message indicating the result of the deletion.
        """
        try:
            self.client.delete_object(Bucket=bucket_name, Key=file_name)
            logger.info(
                f"The file '{file_name}' has been deleted from the bucket '{bucket_name}'."
            )
            return f"The file '{file_name}' has been deleted from the bucket '{bucket_name}'."

        except ClientError as e:
            logger.error(f"Client Error deleting file: {e}")
            return (f"Client Error: Unable to delete the file '{file_name}' "
                    f"from the bucket '{bucket_name}'.")

        except Exception as e:
            logger.exception(f"Unexpected error deleting file: {e}")
            return (f"Error: Unexpected error occurred while deleting the file '{file_name}'"
                     "from the bucket '{bucket_name}'.")
  
    def copy_object(self, source_bucket:str, source_object:str,
                    destination_bucket:str, destination_object:str)-> None:
        """
        Copy an object from one S3 location to another.

        :param source_bucket: The source S3 bucket
        :param source_object: The source object key
        :param destination_object: The destination object key
        """
        try:
            logger.info(
                f"Copying object from s3://{source_bucket}/{source_object}"
                f"to s3://{destination_bucket}/{destination_object}")
            self.client.copy_object(Bucket=destination_bucket,
                                CopySource={'Bucket': source_bucket, 'Key': source_object},
                                Key=destination_object)
            logger.info(f"Object copied to s3://{destination_bucket}/{destination_object}")
        except ClientError as e:
            logger.error(
                f"Error copying object from s3://{source_bucket}/{source_object}"
                f"to s3://{destination_bucket}/{destination_object}: {e}")

    def move_object(self, source_bucket:str, source_object:str,
                    destination_bucket:str, destination_object:str) ->None:
        """
        Move an object (copy and then delete original).

        :param source_bucket: The source S3 bucket
        :param source_object: The source object key
        :param destination_object: The destination object key
        """
        self.copy_object(source_bucket=source_bucket, source_object=source_object, 
                         destination_bucket=destination_bucket,
                         destination_object=destination_object)
        self.delete_object(bucket_name=source_bucket, object_name=source_object)

    def list_objects_by_prefix(self, bucket_name:str, prefix:str):
        """
        List objects in the bucket by prefix (like a folder).

        :param prefix: The prefix to filter by (like "folder/")
        """
        try:
            logger.info(f"Listing objects with prefix '{prefix}' in s3://{bucket_name}")
            response = self.client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            if 'Contents' in response:
                for obj in response['Contents']:
                    logger.info(f"Object: {obj['Key']} (Last modified: {obj['LastModified']})")
            else:
                logger.info(f"No objects found with prefix '{prefix}' in s3://{bucket_name}")
        except ClientError as e:
            logger.error(f"Error listing objects by prefix in S3: {e}")

    def set_object_acl(self,bucket_name:str, object_name:str, acl:str):
        """
        Set ACL (Access Control List) for an object.

        :param object_name: The object name
        :param acl: The ACL to set (e.g., 'private', 'public-read')
        """
        try:
            logger.info(f"Setting ACL {acl} for object {object_name}")
            self.client.put_object_acl(Bucket=bucket_name, Key=object_name, ACL=acl)
            logger.info(f"ACL set to {acl} for object {object_name}")
        except ClientError as e:
            logger.error(f"Error setting ACL for object {object_name}: {e}")

    def get_object_metadata(self, bucket_name:str, object_name:str):
        """
        Retrieve metadata for an object (e.g., size, content-type, etc.).

        :param object_name: The name of the object
        :return: Metadata dictionary or None if not found
        """
        try:
            logger.info(f"Getting metadata for object {object_name}")
            metadata = self.client.head_object(Bucket=bucket_name, Key=object_name)
            logger.info(f"Metadata for {object_name}: {metadata}")
            return metadata
        except ClientError as e:
            logger.error(f"Error retrieving metadata for object {object_name}: {e}")
            return None

    def enable_versioning(self, bucket_name:str):
        """
        Enable versioning for the S3 bucket.
        """
        try:
            logger.info(f"Enabling versioning for bucket {bucket_name}")
            self.client.put_bucket_versioning(Bucket=bucket_name,
                                          VersioningConfiguration={'Status': 'Enabled'})
            logger.info(f"Versioning enabled for bucket {bucket_name}")
        except ClientError as e:
            logger.error(f"Error enabling versioning for bucket {bucket_name}: {e}")

    def disable_versioning(self, bucket_name:str):
        """
        Disable versioning for the S3 bucket.
        """
        try:
            logger.info(f"Disabling versioning for bucket {bucket_name}")
            self.client.put_bucket_versioning(Bucket=bucket_name,
                                          VersioningConfiguration={'Status': 'Suspended'})
            logger.info(f"Versioning disabled for bucket {bucket_name}")
        except ClientError as e:
            logger.error(f"Error disabling versioning for bucket {bucket_name}: {e}")

    def restore_archived_object(self, bucket_name:str, object_name:str):
        """
        Restore an archived object (from Glacier) to standard storage class.

        :param object_name: The name of the object to restore
        """
        try:
            logger.info(f"Restoring archived object {object_name}")
            self.client.restore_object(Bucket=bucket_name, Key=object_name,
                                   RestoreRequest={'Days': 1,
                                    'GlacierJobParameters': {'Tier': 'Standard'}})
            logger.info(f"Object {object_name} restore requested.")
        except ClientError as e:
            logger.error(f"Error restoring archived object {object_name}: {e}")

    def set_bucket_cors_policy(self, bucket_name:str, cors_rules):
        """
        Set a CORS (Cross-Origin Resource Sharing) policy for the bucket.

        :param cors_rules: The CORS configuration rules
        """
        try:
            logger.info(f"Setting CORS policy for bucket {bucket_name}")
            self.client.put_bucket_cors(
                Bucket=bucket_name, CORSConfiguration={'CORSRules': cors_rules})
            logger.info(f"CORS policy set for bucket {bucket_name}")
        except ClientError as e:
            logger.error(f"Error setting CORS policy for bucket {bucket_name}: {e}")

    def get_bucket_encryption(self, bucket_name:str):
        """
        Retrieves the encryption configuration for the specified S3 bucket.

        Parameters:
        bucket_name (str): The name of the bucket for which to retrieve the 
        encryption configuration.

        Returns:
        dict: The encryption configuration of the bucket, or None if there was an error.

        Raises:
        ClientError: If there is an error retrieving the encryption configuration.

        """
        try:
            logger.info(f"Getting encryption configuration for bucket {bucket_name}")
            encryption = self.client.get_bucket_encryption(Bucket=bucket_name)
            logger.info(f"Encryption configuration for bucket {bucket_name}: {encryption}")
            return encryption
        except ClientError as e:
            logger.error(f"Error retrieving encryption configuration for bucket {bucket_name}: {e}")
            return None


# Example usage:
def main():  
    # Instantiate the S3Handler
    s3_handler = S3Handler.credentials()

    # Use new functionalities:
    s3_handler.copy_object('source-bucket', 'source-object.txt',
                           'destination-bucket', 'destination-object.txt')
    s3_handler.set_object_acl('bucket-name','object.txt', 'public-read')
    metadata = s3_handler.get_object_metadata('bucket-name','object.txt')
    print(metadata)
    s3_handler.enable_versioning('bucket-name')
    s3_handler.set_bucket_cors_policy('bucket-name',[{
        'AllowedOrigins': ['*'],
        'AllowedMethods': ['GET', 'POST'],
        'AllowedHeaders': ['*']
    }])


if __name__ == "__main__":
    main()