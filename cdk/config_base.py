from typing import Optional, Dict, List
from aws_cdk import Environment
from pydantic import Field
from pydantic_settings import BaseSettings
import yaml
import logging

logger = logging.getLogger(__name__)


class ConfigBase(BaseSettings):
    """
    Base class for SDLC and shared-resource configuration for CDK app. Initialized from common and SDLC-env specific
    configuration settings in the config directory.
    """

    def __init__(self, **values) -> None:
        super().__init__(**values)
        self._parse_yaml_config(self.stage)
        self._init_tags()

    @property
    def env(self) -> Environment:
        """The CDK environment for this app"""
        return Environment(
            account=self.aws_account,
            region=self.aws_region,
        )

    @property
    def stack_name(self) -> str:
        """Name of the CloudFormation stack"""
        return f"{self.stage_name}-{self.service}"

    @property
    def is_dev(self) -> bool:
        """Whether the current stage is `dev`"""
        return self.stage_name == "dev"

    @property
    def stage_name(self) -> str:
        """Normalized stage name"""
        return self.stage.lower()

    service: str = Field(description="Service name used for stack and resources")

    tags: Optional[Dict[str, str]] = Field(
        description="Optional collection of key/value pairs to tag on stack components",
        default=None,
    )

    stage: Optional[str] = Field(
        description=(
            "SDLC environment of deployment (e.g. `dev`, `qa`, `prod`). "
            "Used as prefix for stack and resources names"
        ),
        default="dev",
    )

    aws_account: Optional[str] = Field(
        description="AWS account for deployment", env="AWS_ACCOUNT", default=None
    )

    aws_region: Optional[str] = Field(
        description="AWS region for deployment", env="AWS_REGION", default="us-east-1"
    )

    iam_role_arns: List[str] = Field(
        description="IAM roles to grant permissions to, for support & testing purposes",
        default=[],
    )

    cw_alarm_to_slack_function_arn: Optional[str] = Field(
        description="arn of the lambda function that sends cloudwatch alarms to slack",
        default=None,
    )

    dry_run: bool = Field(
        default=True,
        description="whether to pass the dry-run flag to the service, indicating a no-op",
    )

    build_dir: str = ".build"

    def _parse_yaml_config(self, stage: str):
        common_config = "config/common.yaml"
        stage_config = f"config/{stage}.yaml"
        for cfg in [common_config, stage_config]:
            try:
                with open(cfg) as f:
                    conf = yaml.load(f, Loader=yaml.SafeLoader) or {}

                    for k, v in conf.items():
                        if v is None:
                            continue
                        setattr(self, k, v)
            except (IOError, TypeError, ValueError) as ex:
                logger.error(f"missing or invalid config file {stage_config}: {ex}")

    def _init_tags(self):
        if self.tags is None:
            self.tags = {}
        self.tags["stack"] = self.stack_name
        self.tags["service"] = self.service
        self.tags["environment"] = self.stage

    class Config:
        """Pydantic internal config"""

        env_prefix = ""
        case_sensitive = False
