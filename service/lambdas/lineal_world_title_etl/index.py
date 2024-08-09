from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    EventBridgeEvent,
)

try:
    from .config import Config
    from service.lambdas.utils import s3, secret_manager
except:
    # no relative imports from top level when deployed to lamdba
    from config import Config

    # no 'service.lambdas' when deployed to lamdba
    from utils import s3, secret_manager  # type: ignore


logger = Logger()
tracer = Tracer()
config = Config()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@event_source(data_class=EventBridgeEvent)
def handler(event: EventBridgeEvent, context: LambdaContext) -> dict:
    """Handle ETL from a scheduled trigger from event bridge.

    Returns:
        dict: of `statusCode` and `body`
    """
    logger.info(f"Received event: {event}, context: {context}")

    # TODO add code!
    files = s3.list(config.S3_BUCKET)
    logger.info(f"Files in bucket: {files}")

    logger.info(f"Function completed succesfully!")
    return {
        "statusCode": 200,
        "body": files,
    }
