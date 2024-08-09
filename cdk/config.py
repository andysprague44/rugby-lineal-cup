from typing import Optional, List
from pydantic import Field
import logging

from .config_base import ConfigBase

logger = logging.getLogger(__name__)


class Config(ConfigBase):
    """
    SDLC and shared-resource configuration for CDK app. Initialized from common and SDLC-env specific
    configuration settings in the config directory.
    """

    def __init__(self, stage, **values) -> None:
        super().__init__(service="ptl-signup-service", stage=stage, **values)

    kinesis_stream_ptl_inapp_demo_request_arn: Optional[str] = Field(
        description="ARN of kinesis stream to consume, not optional as we never own creation of a stream in cdk",
        default=None,
    )

    kinesis_stream_ptl_school_signup_arn: Optional[str] = Field(
        description="ARN of kinesis stream to consume, not optional as we never own creation of a stream in cdk",
        default=None,
    )

    kinesis_stream_ptl_school_signup_completed_arn: Optional[str] = Field(
        description="ARN of kinesis stream to consume, not optional as we never own creation of a stream in cdk",
        default=None,
    )

    hs_ptl_inapp_demo_request_form_endpoint: Optional[str] = Field(
        description="Hubspot endpoint to post form data to",
        default=None,
    )

    hs_ptl_school_signup_form_endpoint: Optional[str] = Field(
        description="Hubspot endpoint to post form data to",
        default=None,
    )

    mixpanel_project_id: Optional[int] = Field(
        description="Mixpanel project id",
        default=None,
    )

    glue_catalog_id: Optional[str] = Field(
        description="Glue catalog id",
        default=None,
    )

    slack_disabled: Optional[bool] = Field(
        description="Disable slack notifications",
        default=False,
    )

    mixpanel_disabled: Optional[bool] = Field(
        description="Disable mixpanel integration (to avoid hitting the 60 per hour mixpanel rate limit)",
        default=False,
    )

    mixpanel_delay_seconds: Optional[int] = Field(
        description="Seconds to delay mixpanel augmentation",
        default=None,
    )

    vpc_id: Optional[str] = Field(
        description="id of VPC to grant access to",
        default=None,
    )

    subnet_ids: Optional[List[str]] = Field(
        description="ids of VPC subnets to use",
        default=None,
    )

    security_group_ids: Optional[List[str]] = Field(
        description="ids of security groups to use",
        default=None,
    )

    lambda_retry_attempts: Optional[int] = Field(
        description="Number of times to retry lambda function, total attempts = attempts + 1",
        default=2,
    )
