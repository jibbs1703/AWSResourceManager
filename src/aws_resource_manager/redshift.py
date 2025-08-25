import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from aws_resource_manager.logs import get_logger

logger = get_logger()


class RedshiftHandler:
    @classmethod
    def credentials(cls) -> "RedshiftHandler":
        """
        Retrieves AWS credentials from a hidden environment file.
        """
        load_dotenv()
        secret = os.getenv("ACCESS_SECRET")
        access = os.getenv("ACCESS_KEY")
        region = os.getenv("REGION")

        return cls(secret, access, region)

    def __init__(self, secret, access, region) -> None:
        """
        Initializes the RedshiftHandler class with user credentials
        and creates the AWS Redshift client.
        """
        self.client = boto3.client("redshift",
                                   aws_access_key_id=access,
                                   aws_secret_access_key=secret,
                                   region_name=region)

    def list_clusters(self) -> list:
        """Lists all available Redshift clusters."""
        try:
            response = self.client.describe_clusters()
            return [cluster["ClusterIdentifier"] for cluster in response["Clusters"]]
        except ClientError as e:
            logger.error(f"Error listing clusters: {e}")
            return None

    def create_cluster(self, cluster_identifier: str,
                       node_type: str, db_name: str,
                       master_username: str, master_password: str) -> None:
        """Creates a new Redshift cluster."""
        try:
            self.client.create_cluster(
                ClusterIdentifier=cluster_identifier,
                NodeType=node_type,
                DBName=db_name,
                MasterUsername=master_username,
                MasterUserPassword=master_password
            )
            logger.info(f"Redshift cluster {cluster_identifier} created successfully.")
        except ClientError as e:
            logger.error(f"Error creating cluster {cluster_identifier}: {e}")

    def delete_cluster(self, cluster_identifier: str) -> None:
        """Deletes an existing Redshift cluster."""
        try:
            self.client.delete_cluster(
                ClusterIdentifier=cluster_identifier,
                SkipFinalClusterSnapshot=True
            )
            logger.info(f"Redshift cluster {cluster_identifier} deleted successfully.")
        except ClientError as e:
            logger.error(f"Error deleting cluster {cluster_identifier}: {e}")

    def list_databases(self, cluster_identifier: str) -> list:
        """Lists databases in a Redshift cluster."""
        try:
            response = self.client.describe_clusters(ClusterIdentifier=cluster_identifier)
            return [db["DBName"] for db in response["Clusters"]]
        except ClientError as e:
            logger.error(f"Error listing databases in cluster {cluster_identifier}: {e}")
            return None

    def modify_cluster(self, cluster_identifier: str, new_node_type: str) -> None:
        """Modifies a Redshift cluster's node type."""
        try:
            self.client.modify_cluster(
                ClusterIdentifier=cluster_identifier,
                NodeType=new_node_type
            )
            logger.info(
                f"Modified Redshift cluster {cluster_identifier} to node type "
                f"{new_node_type}."
            )
        except ClientError as e:
            logger.error(f"Error modifying cluster {cluster_identifier}: {e}")

    def pause_cluster(self, cluster_identifier: str) -> None:
        """Pauses a Redshift cluster to save costs."""
        try:
            self.client.pause_cluster(ClusterIdentifier=cluster_identifier)
            logger.info(f"Paused Redshift cluster {cluster_identifier}.")
        except ClientError as e:
            logger.error(f"Error pausing cluster {cluster_identifier}: {e}")

    def resume_cluster(self, cluster_identifier: str) -> None:
        """Resumes a paused Redshift cluster."""
        try:
            self.client.resume_cluster(ClusterIdentifier=cluster_identifier)
            logger.info(f"Resumed Redshift cluster {cluster_identifier}.")
        except ClientError as e:
            logger.error(f"Error resuming cluster {cluster_identifier}: {e}")

    def get_cluster_status(self, cluster_identifier: str) -> str:
        """Retrieves the status of a Redshift cluster."""
        try:
            response = self.client.describe_clusters(ClusterIdentifier=cluster_identifier)
            return response["Clusters"][0]["ClusterStatus"]
        except ClientError as e:
            logger.error(f"Error getting status of cluster {cluster_identifier}: {e}")
            return None

    def list_snapshots(self, cluster_identifier: str) -> list:
        """Lists snapshots for a Redshift cluster."""
        try:
            response = self.client.describe_cluster_snapshots(ClusterIdentifier=cluster_identifier)
            return [snapshot["SnapshotIdentifier"] for snapshot in response["Snapshots"]]
        except ClientError as e:
            logger.error(f"Error listing snapshots for cluster {cluster_identifier}: {e}")
            return None

    def restore_snapshot(self, snapshot_identifier: str, new_cluster_identifier: str) -> None:
        """Restores a Redshift cluster from a snapshot."""
        try:
            self.client.restore_from_cluster_snapshot(
                SnapshotIdentifier=snapshot_identifier,
                ClusterIdentifier=new_cluster_identifier
            )
            logger.info(
                f"Restored snapshot {snapshot_identifier} to new cluster "
                f"{new_cluster_identifier}."
            )
        except ClientError as e:
            logger.error(f"Error restoring snapshot {snapshot_identifier}: {e}")
