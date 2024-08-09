from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    Duration,
    BundlingOptions,
    RemovalPolicy,
)
from aws_cdk.aws_ec2 import (
    Vpc,
    Subnet,
    SecurityGroup,
)
import os
from typing import Optional, List
from ..config_base import ConfigBase


class PythonLambdaFunction(_lambda.Function):

    def __init__(
        self,
        stack: Stack,
        config: ConfigBase,
        entry: str,
        handler: str,
        function_name: Optional[str] = None,
        id: Optional[str] = None,
        description: Optional[str] = None,
        vpc: Optional[Vpc] = None,
        vpc_subnets: Optional[List[Subnet]] = None,
        security_groups: Optional[List[SecurityGroup]] = None,
        role: Optional[iam.IRole] = None,
        events: Optional[List[_lambda.IEventSource]] = None,
        layers: Optional[List[_lambda.ILayerVersion]] = None,
        runtime: Optional[_lambda.Runtime] = _lambda.Runtime.PYTHON_3_11,
        architecture: Optional[_lambda.Architecture] = _lambda.Architecture.X86_64,
        **kwargs,
    ):
        """Creates a python aws lamdba function, including packaging from requirements.txt, with sensible defaults.

        Args:
            stack [Stack]: CDK stack
            config [ConfigBase]: configuration object
            entry [str]: full path to the lambda function directory e.g. "<project>/service/lamdbas/my_function"
            handler [str]: name of the handler function e.g. index.handler, where `index.py` has a function `handler`
            function_name [Optional[str]]: name of the lambda function
            id [Optional[str]]: name to give the lambda function in the stack
            description [Optional[str]]: short description of the lambda function
            role [Optional[iam.IRole]]: IAM role for the lambda function
            vpc [Optional[Vpc]]: Id of VPC to connect lambda to
            vpc_subnets [Optional[List[Subnet]]: when configured with VPC, the subnets to use
            security_groups [Optional[List[SecurityGroup]]: optional list of security groups for lambda
            events [Optional[List[_lambda.IEventSource]]]: list of event sources to trigger the lambda function
            layers [Optional[List[_lambda.ILayerVersion]]]: list of lambda layers to include in the function, e.g. utils, power tools
            runtime [Optional[_lambda.Runtime]]: lambda runtime, default is python 3.11
            architecture [Optional[_lambda.Architecture]]: lambda architecture, default is X86_64
            **kwargs: any other kwargs to pass down to cdk construct (see https://github.com/aws/aws-cdk/tree/main/packages/aws-cdk-lib/aws-lambda)
        """
        if id is None:
            id = f"{config.stack_name}-lambda-function"
        if function_name is None:
            function_name = (
                f"{config.stack_name}-{os.path.split(entry)[-1].replace('_', '-')}"
            )
        super().__init__(
            stack,
            id=id,
            function_name=function_name,
            description=description,
            runtime=runtime,
            architecture=architecture,
            code=_lambda.Code.from_asset(
                path=entry,
                bundling=BundlingOptions(
                    image=runtime.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            handler=handler,
            role=role,
            vpc=vpc,
            vpc_subnets=vpc_subnets,
            security_groups=security_groups,
            memory_size=kwargs.pop("memory_size", 1024),
            timeout=kwargs.pop("timeout", Duration.minutes(5)),
            logging_format=_lambda.LoggingFormat.JSON,
            system_log_level_v2=_lambda.SystemLogLevel.INFO,
            application_log_level_v2=_lambda.ApplicationLogLevel.INFO,
            insights_version=_lambda.LambdaInsightsVersion.VERSION_1_0_229_0,
            tracing=_lambda.Tracing.ACTIVE,
            events=events,
            environment={
                **kwargs.pop("environment", {}),
                "POWERTOOLS_METRICS_NAMESPACE": config.service,
                "POWERTOOLS_SERVICE_NAME": config.stack_name,
            },
            layers=layers,
            **kwargs,
        )

        if vpc is not None:
            self.role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                )
            )

            self.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "ec2:AssignPrivateIpAddresses",
                        "ec2:CreateNetworkInterface",
                        "ec2:DeleteNetworkInterface",
                        "ec2:DescribeNetworkInterfaces",
                        "ec2:UnassignPrivateIpAddresses",
                    ],
                    resources=[
                        "*"
                    ],  # aws examples have all, but we might want to narrow to current vpc arn
                )
            )

        if config.cw_alarm_to_slack_function_arn is not None:
            # Add a cloudwatch alarm for any lambda error, and send alerts to slack when alarm triggered.
            error_metric = self.metric_errors(
                period=Duration.minutes(1),
                statistic=cloudwatch.Stats.SUM,
            )
            error_alarm = error_metric.create_alarm(
                self,
                id=f"{function_name}-error-count",
                alarm_name=f"{function_name}-error-count",
                evaluation_periods=1,
                threshold=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            )
            error_alarm.apply_removal_policy(RemovalPolicy.DESTROY)
            alert_fn = _lambda.Function.from_function_arn(
                stack,
                f"{function_name}-alert-lambda",
                config.cw_alarm_to_slack_function_arn,
            )
            error_alarm.add_alarm_action(cloudwatch_actions.LambdaAction(alert_fn))


class PythonLambdaLayerVersion(_lambda.LayerVersion):

    def __init__(
        self,
        stack: Stack,
        config: ConfigBase,
        entry: str,
        id: Optional[str] = None,
        description: Optional[str] = None,
        runtime: Optional[_lambda.Runtime] = _lambda.Runtime.PYTHON_3_11,
        architecture: Optional[_lambda.Runtime] = _lambda.Architecture.X86_64,
        **kwargs,
    ):
        """Creates a lamdba layer, including packaging from requirements.txt, for shared code in the stack.

        Args:
            stack [Stack]: CDK stack
            config [ConfigBase]: configuration object
            entry [str]: full path to the lambda layer directory e.g. "<project>/service/utils"
            id [Optional[str]]: name to give the lambda layer in the stack
            description [Optional[str]]: short description of the lambda layer
            runtime [Optional[aws_cdk.aws_lambda.Runtime]]: lambda runtime, default is python 3.11
            architecture [Optional[aws_cdk.aws_lambda.Architecture]]: lambda architecture, default is X86_64
            **kwargs: any other kwargs to pass down to cdk construct (see https://github.com/aws/aws-cdk/tree/main/packages/aws-cdk-lib/aws-lambda)
        """
        module_name = os.path.split(entry)[-1]

        if id is None:
            id = f"{config.stack_name}-{module_name.replace('_', '-')}-lambda-layer"

        if description is None:
            description = f"{module_name} lambda layer for stack '{config.stack_name}'"

        super().__init__(
            stack,
            id=id,
            description=description,
            layer_version_name=f"{config.stack_name}-{module_name.replace('_', '-')}-{architecture.to_string()}",
            removal_policy=RemovalPolicy.DESTROY,
            code=_lambda.Code.from_asset(
                entry,
                bundling=BundlingOptions(
                    image=runtime.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        f"pip install -r requirements.txt -t /asset-output/python && cp -au . /asset-output/python/{module_name}",
                    ],
                ),
            ),
            compatible_runtimes=[runtime],
            compatible_architectures=[architecture],
            **kwargs,
        )

    @staticmethod
    def lambda_powertools_layer(
        stack: Stack,
        config: ConfigBase,
        id="lambda-powertools-lambda-layer",
        architecture: _lambda.Architecture = _lambda.Architecture.X86_64,
        layer_version: int = 79,
    ) -> _lambda.LayerVersion:
        """Returns the public AWS Lambda Powertools layer."""
        arch_suffix = (
            "-Arm64"
            if architecture.to_string() == _lambda.Architecture.ARM_64.to_string()
            else ""
        )
        arn = f"arn:aws:lambda:{config.aws_region}:017000801446:layer:AWSLambdaPowertoolsPythonV2{arch_suffix}:{layer_version}"
        return _lambda.LayerVersion.from_layer_version_arn(
            stack,
            id=id,
            layer_version_arn=arn,
        )


class LambdaRole(iam.Role):
    def __init__(
        self,
        scope: Stack,
        config: ConfigBase,
        role_id: Optional[str] = None,
        role_name: Optional[str] = None,
        s3_bucket_arns: Optional[List[str]] = None,
        secret_arns: Optional[List[str]] = None,
    ):

        if role_id is None:
            role_id = f"{config.stack_name}-lambda-role"

        if role_name is None:
            role_name = f"{config.stack_name}-lambda-role"

        super().__init__(
            scope,
            role_id,
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
            ],
        )

        if s3_bucket_arns:
            s3_bucket_arns = set(s3_bucket_arns)
            for bucket_arn in s3_bucket_arns.copy():
                if not bucket_arn.endswith("/*"):
                    s3_bucket_arns.add(f"{bucket_arn}/*")
            s3_bucket_arns = list(s3_bucket_arns)
            s3_policy = iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:Create*",
                    "s3:Put*",
                    "s3:Get*",
                    "s3:Delete*",
                    "s3:List*",
                ],
                resources=s3_bucket_arns,
            )
            self.add_to_policy(s3_policy)

        if secret_arns:
            secrets_policy = iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:Get*", "secretsmanager:Describe*"],
                resources=secret_arns,
            )
            self.add_to_policy(secrets_policy)

    def grant_kinesis_stream(self, stream_arn: str):
        self.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaKinesisExecutionRole"
            )
        )
        self.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "kinesis:DescribeStream",
                    "kinesis:DescribeStreamSummary",
                    "kinesis:GetRecords",
                    "kinesis:GetShardIterator",
                    "kinesis:ListShards",
                    "kinesis:ListStreams",
                    "kinesis:SubscribeToShard",
                ],
                resources=[stream_arn],
            )
        )

    def grant_sqs_queue(self, sqs_queue_arn: str):
        self.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaSQSQueueExecutionRole"
            )
        )
        self.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sqs:SendMessage",
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[sqs_queue_arn],
            )
        )
