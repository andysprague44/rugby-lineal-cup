from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy,
)
from typing import List


class S3Bucket(s3.Bucket):

    def __init__(
        self,
        stack: Stack,
        id: str,
        bucket_name: str,
        role_arns: List[str] = None,
    ):
        """
        Creates an internal, private S3 bucket with standard, secure defaults.

        Args:
            stack: CDK stack
            config: ConfigBase configuration object, containing the stack name and other settings
            id: id for the cdk stack / cloud formation template
            bucket_name: name of the bucket
            role_arns: list of ARNs of IAM roles to grant read/write/delete access to the bucket
        """
        super().__init__(
            stack,
            id,
            bucket_name=bucket_name,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
        )
        role_arns = role_arns or []
        for role_arn in role_arns:
            role = iam.Role.from_role_arn(
                stack,
                f"{self.bucket_name.replace('/', '-')}-sso-role-{role_arn.split('/')[-1]}",
                role_arn,
                add_grants_to_resources=True,
                mutable=False,
            )
            self.grant_read_write(role)
            self.grant_delete(role)
