import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from src.aws_resource_manager.ec2.logger import configure_logger

logger = configure_logger()


class EC2Handler:
    @classmethod
    def credentials(cls) -> "EC2Handler":
        """
        Retrieves AWS credentials from a hidden environment file.

        This class method accesses the user's AWS secret and access
        keys stored in an environment file. If a region is specified,
        the methods within the EC2Handler class will execute in that region.
        Otherwise, AWS will assign a default region.

        :return: An instance of the EC2Handler class initialized with
        the user's credentials and specified region
        """
        load_dotenv()
        secret = os.getenv("ACCESS_SECRET")
        access = os.getenv("ACCESS_KEY")
        region = os.getenv("REGION")

        return cls(secret, access, region)

    def __init__(self, secret, access, region) -> None:
        """
        Initializes the EC2Handler class with user credentials and creates
        the AWS EC2 client.

        This constructor method initializes the EC2Handler class using the
        provided secret and access keys. It creates an AWS EC2 client using
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
                "ec2", aws_access_key_id=access, aws_secret_access_key=secret
            )
        else:
            self.client = boto3.client(
                "ec2",
                aws_access_key_id=access,
                aws_secret_access_key=secret,
                region_name=region,
            )

    def create_instance(
        self,
        ami_id: str,
        instance_type: str,
        key_name: str,
        security_group_ids: list[str] = None,
        min_count: int = 1,
        max_count: int = 1,
        tags: list[dict[str, str]] = None,
    ) -> str:
        """
        Create an EC2 instance.

        :param ami_id: The ID of the AMI to launch.
        :param instance_type: The instance type.
        :param key_name: The name of the key pair.
        :param security_group_ids: A list of security group IDs.
        :param min_count: The minimum number of instances to launch.
        :param max_count: The maximum number of instances to launch.
        :param tags: A list of tags to associate with the instance.
        :return: The ID of the created instance.
        """
        try:
            logger.info(f"Creating EC2 instance: {ami_id}, {instance_type}, KeyPair: {key_name}")
            response = self.client.run_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                MinCount=min_count,
                MaxCount=max_count,
                KeyName=key_name,
                SecurityGroupIds=security_group_ids,
                TagSpecifications=(
                    [{"ResourceType": "instance", "Tags": tags or []}] if tags else []
                ),
            )
            instance_id = response["Instances"][0]["InstanceId"]
            logger.info(f"Instance {instance_id} created.")
            return instance_id
        except ClientError as e:
            logger.error(f"Error creating EC2 instance: {e}")
            return None

    def stop_instance(self, instance_id: str) -> None:
        """
        Stop an EC2 instance.

        :param instance_id: The ID of the instance to stop.
        """
        try:
            logger.info(f"Stopping EC2 instance {instance_id}")
            response = self.client.stop_instances(InstanceIds=[instance_id])
            logger.info(
                f"Stopping Instance {instance_id}. Current state: "
                f"{response['StoppingInstances'][0]['CurrentState']['Name']}"
            )
        except ClientError as e:
            logger.error(f"Error stopping EC2 instance {instance_id}: {e}")

    def start_instance(self, instance_id: str) -> None:
        """
        Start an EC2 instance.

        :param instance_id: The ID of the instance to start.
        """
        try:
            logger.info(f"Starting EC2 instance {instance_id}")
            response = self.client.start_instances(InstanceIds=[instance_id])
            logger.info(
                f"Starting Instance {instance_id}. Current state: "
                f"{response['StartingInstances'][0]['CurrentState']['Name']}"
            )
        except ClientError as e:
            logger.error(f"Error starting EC2 instance {instance_id}: {e}")

    def reboot_instance(self, instance_id: str) -> None:
        """
        Reboot an EC2 instance.

        :param instance_id: The ID of the instance to reboot.
        """
        try:
            logger.info(f"Rebooting EC2 instance {instance_id}")
            self.client.reboot_instances(InstanceIds=[instance_id])
            logger.info(f"Instance {instance_id} has been rebooted.")
        except ClientError as e:
            logger.error(f"Error rebooting EC2 instance {instance_id}: {e}")

    def terminate_instance(self, instance_id: str) -> None:
        """
        Terminate an EC2 instance.

        :param instance_id: The ID of the instance to terminate.
        """
        try:
            logger.info(f"Terminating EC2 instance {instance_id}")
            response = self.client.terminate_instances(InstanceIds=[instance_id])
            logger.info(
                f"Terminating Instance {instance_id}. Current state: "
                f"{response['TerminatingInstances'][0]['CurrentState']['Name']}"
            )
        except ClientError as e:
            logger.error(f"Error terminating EC2 instance {instance_id}: {e}")

    def describe_instance(self, instance_id: str) -> dict:
        """
        Describe an EC2 instance and return detailed information.

        :param instance_id: The ID of the instance to describe.
        :return: A dictionary containing the instance details.
        """
        try:
            logger.info(f"Describing EC2 instance {instance_id}")
            response = self.client.describe_instances(InstanceIds=[instance_id])
            instance_details = response["Reservations"][0]["Instances"][0]
            logger.info(f"Instance {instance_id} details: {instance_details}")
            return instance_details
        except ClientError as e:
            logger.error(f"Error describing EC2 instance {instance_id}: {e}")
            return None

    def get_instance_status(self, instance_id: str) -> str:
        """
        Get the status of a specific EC2 instance (running, stopped, etc.)

        :param instance_id: The ID of the instance.
        :return: The current status of the instance.
        """
        try:
            logger.info(f"Getting status of EC2 instance {instance_id}")
            response = self.client.describe_instance_status(InstanceIds=[instance_id])
            if response["InstanceStatuses"]:
                status = response["InstanceStatuses"][0]["InstanceState"]["Name"]
                logger.info(f"Instance {instance_id} is in state: {status}.")
                return status
            else:
                logger.warning(f"Instance {instance_id} does not have any status information.")
                return "No status info available"
        except ClientError as e:
            logger.error(f"Error getting status of EC2 instance {instance_id}: {e}")
            return None

    def create_ami(
        self, instance_id: str, name: str, description: str = "Created from EC2Handler"
    ) -> str:
        """
        Create an AMI from an EC2 instance.

        :param instance_id: The ID of the instance to create the AMI from.
        :param name: The name of the AMI.
        :param description: The description of the AMI.
        :return: The ID of the created AMI.
        """
        try:
            logger.info(f"Creating AMI from EC2 instance {instance_id}, AMI name: {name}")
            response = self.client.create_image(
                InstanceId=instance_id,
                Name=name,
                Description=description,
                NoReboot=True,
            )
            ami_id = response["ImageId"]
            logger.info(f"AMI {ami_id} created from instance {instance_id}.")
            return ami_id
        except ClientError as e:
            logger.error(f"Error creating AMI from EC2 instance {instance_id}: {e}")
            return None

    def modify_instance_type(self, instance_id: str, new_instance_type: str) -> None:
        """
        Modify the instance type of a running EC2 instance.

        :param instance_id: The ID of the instance to modify.
        :param new_instance_type: The new instance type.
        """
        try:
            logger.info(f"Modifying instance {instance_id} to new type {new_instance_type}")
            self.client.modify_instance_attribute(
                InstanceId=instance_id, InstanceType={"Value": new_instance_type}
            )
            logger.info(f"Instance {instance_id} type modified to {new_instance_type}.")
        except ClientError as e:
            logger.error(f"Error modifying instance type for {instance_id}: {e}")

    def attach_volume(self, instance_id, volume_id, device):
        """
        Attach an EBS volume to an EC2 instance.
        """
        try:
            logger.info(
                f"Attaching volume {volume_id} to instance {instance_id} on device {device}"
            )
            self.client.attach_volume(InstanceId=instance_id, VolumeId=volume_id, Device=device)
            logger.info(
                f"Volume {volume_id} attached to instance {instance_id} on device {device}."
            )
        except ClientError as e:
            logger.error(f"Error attaching volume {volume_id} to instance {instance_id}: {e}")

    def detach_volume(self, instance_id, volume_id):
        """
        Detach an EBS volume from an EC2 instance.
        """
        try:
            logger.info(f"Detaching volume {volume_id} from instance {instance_id}")
            self.client.detach_volume(InstanceId=instance_id, VolumeId=volume_id)
            logger.info(f"Volume {volume_id} detached from instance {instance_id}.")
        except ClientError as e:
            logger.error(f"Error detaching volume {volume_id} from instance {instance_id}: {e}")

    def create_key_pair(self, key_name):
        """
        Create a new EC2 key pair.
        """
        try:
            logger.info(f"Creating EC2 key pair {key_name}")
            response = self.client.create_key_pair(KeyName=key_name)
            logger.info(f"Key pair {key_name} created.")
            return response["KeyMaterial"]
        except ClientError as e:
            logger.error(f"Error creating key pair {key_name}: {e}")
            return None

    def delete_key_pair(self, key_name):
        """
        Delete an EC2 key pair.
        """
        try:
            logger.info(f"Deleting EC2 key pair {key_name}")
            self.client.delete_key_pair(KeyName=key_name)
            logger.info(f"Key pair {key_name} deleted.")
        except ClientError as e:
            logger.error(f"Error deleting key pair {key_name}: {e}")

    def describe_key_pairs(self):
        """
        Describe all EC2 key pairs in the account.
        """
        try:
            logger.info("Describing EC2 key pairs")
            response = self.client.describe_key_pairs()
            key_pairs = response["KeyPairs"]
            if key_pairs:
                for key in key_pairs:
                    logger.info(
                        f"Key Name: {key['KeyName']}, Key Fingerprint: {key['KeyFingerprint']}"
                    )
            else:
                logger.warning("No key pairs found.")
            return key_pairs
        except ClientError as e:
            logger.error(f"Error describing EC2 key pairs: {e}")
            return []


# Example usage
def main():
    # Create EC2Handler instance
    ec2_handler = EC2Handler.credentials()

    # Example EC2 operations
    instance_id = ec2_handler.create_instance("ami-0c55b159cbfafe1f0", "t2.micro", "your-key-name")
    if instance_id:
        ec2_handler.get_instance_status(instance_id)
        ec2_handler.start_instance(instance_id)
        ec2_handler.stop_instance(instance_id)
        ec2_handler.reboot_instance(instance_id)
        ec2_handler.terminate_instance(instance_id)


if __name__ == "__main__":
    main()
