"""Credentials Module for AWS Resource Manager"""

import os

from dotenv import load_dotenv


def get_credentials():
        """
        Retrieves AWS credentials from a hidden environment file.

        This class method accesses the user's AWS secret and access
        keys stored in an environment file. If a region is specified,
        the methods within the S3Handler class will execute in that region.
        Otherwise, AWS will assign a default region.

        :return: An instance of the S3Handler class initialized with
        the user's credentials and specified region
        """
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        region = os.getenv("REGION")

        if not all([aws_access_key_id, aws_secret_access_key, region]):
            load_dotenv()
            aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            region = os.getenv("REGION")

        if not all([aws_access_key_id, aws_secret_access_key, region]):
            raise ValueError("All credentials not found in environment variables.")

        return aws_access_key_id, aws_secret_access_key, region


if __name__ == "__main__":
    get_credentials()
