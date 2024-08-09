import logging
import os
from aws_cdk import (
    Stack,
    aws_events as events,
    Duration,
)
from .constructs.lambda_function import (
    PythonLambdaLayerVersion,
    LambdaRole,
    PythonLambdaFunction,
)
from constructs import Construct
from cdk.config import Config
from .constructs.s3 import S3Bucket
from .constructs.vpc import MyVpc, MySecurityGroup

logger = logging.getLogger(__name__)

source_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, "service")
)


class ServiceStack(Stack):
    """CDK stack for the lineal-rugby service"""

    def __init__(
        self, scope: Construct, stack_id: str, config: Config, **kwargs
    ) -> None:
        super().__init__(scope, stack_id, env=config.env, **kwargs)
        self.config = config

        ##### S3 #####
        s3_bucket = S3Bucket(
            self,
            bucket_id="lineal-rugby-bucket",
            bucket_name="lineal-rugby",
            role_arns=config.iam_role_arns,
        )

        ##### VPC, SUBNETS, SECURITY GROUPS #####
        if config.vpc_id is not None:
            vpc = MyVpc.resolve_vpc(
                self,
                config=config,
                vpc_id=config.vpc_id,
            )
            subnets = MyVpc.resolve_subnets(
                self,
                config=config,
                subnet_ids=config.subnet_ids,
            )
            security_groups = MySecurityGroup.resolve_security_groups(
                self,
                config=config,
                vpc=vpc,
                sg_ids=config.security_group_ids,
            )
        else:
            vpc = None
            subnets = None
            security_groups = None

        ##### LAMDBA HANDLERS #####
        lambda_role = LambdaRole(
            self,
            config,
            s3_bucket_arns=[s3_bucket.bucket_arn],
        )

        powertools_layer = PythonLambdaLayerVersion.lambda_powertools(
            stack=self,
            config=config,
        )

        etl_function = PythonLambdaFunction(
            stack=self,
            config=config,
            id=f"ptl-school-signup-handler",
            entry=os.path.join(source_dir, "lambdas", "lineal_worl_title_etl"),
            description="update website data with latest results",
            role=lambda_role,
            handler="index.handler",
            vpc=vpc,
            vpc_subnets=subnets,
            security_groups=security_groups,
            memory_size=256,
            timeout=Duration.seconds(30),
            environment={
                "S3_BUCKET": s3_bucket.bucket_name,
            },
            events=[
                # See https://medium.com/geekculture/schedule-aws-lambda-invocations-with-eventbridge-and-aws-cdk-fbd7e4e670bb
                events.Rule(
                    self,
                    id="event-bridge-rule",
                    schedule=events.Schedule.rate(Duration.hours(1)),
                    description="Trigger the `lineal-rugby` lambda function",
                )
            ],
            layers=[powertools_layer],
        )
