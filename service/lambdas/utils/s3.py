import json
import boto3
import botocore
import pydantic
from aws_lambda_powertools import Logger
from typing import List

logger = Logger()

__s3_client = None


class S3LinealWorldTitleEntity(pydantic.BaseModel):
    id: str


def __get_client() -> boto3.client:
    global __s3_client
    __s3_client = __s3_client or boto3.client(
        "s3",
        config=botocore.client.Config(
            connect_timeout=2,
            read_timeout=5,
            retries={"max_attempts": 3},
        ),
    )
    return __s3_client


def write(
    s3_bucket: str,
    s3_path: str,
    s3_entity: S3LinealWorldTitleEntity,
) -> None:
    """Writes record to s3.

    Args:
        s3_path (str): the s3 path to write to
        s3_entity (S3LinealWorldTitleEntity): the record to write

    Returns:
        None
    """
    try:
        client = __get_client()
        client.put_object(
            Body=s3_entity.model_dump_json(exclude_none=True, indent=4),
            Bucket=s3_bucket,
            Key=s3_path,
        )
    except Exception as ex:
        logger.error(f"Failed to write {s3_entity.event_id=} to s3: {ex}")
        raise


def download(
    s3_bucket: str,
    s3_path: str,
) -> S3LinealWorldTitleEntity:
    """Downloads a record from s3 and returns a S3LinealWorldTitleEntity pydantic model.

    Args:
        s3_path (str): the s3 path to download

    Returns:
        S3LinealWorldTitleEntity: the record as a pydantic model
    """
    try:
        client = __get_client()
        obj = client.get_object(
            Bucket=s3_bucket,
            Key=s3_path,
        )
        str_contents = obj["Body"].read().decode("utf-8")
        contents = json.loads(str_contents)
        model = S3LinealWorldTitleEntity(**contents)
        return model
    except json.JSONDecodeError as json_ex:
        logger.error(f"File {s3_path=} does not contain valid json: {ex}")
        raise ValueError(f"Not valid json '{s3_path}': {json_ex}") from json_ex
    except Exception as ex:
        logger.error(f"Failed to download {s3_path=} to s3: {ex}")
        raise


def list(
    s3_bucket: str,
    prefix: str = None,
    suffix: str = None,
) -> List[str]:
    """List paths in s3 bucket with the given prefix, and optional suffix.

    Args:
        prefix (str, optional): the prefix to search for. Defaults to None.
        suffix (str, optional): the suffix to search for, including file extension. Defaults to None.

    Returns:
        List[str]: list of s3 paths
    """
    try:
        client = __get_client()
        objects = client.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=prefix,
        )
        paths = [obj["Key"] for obj in objects.get("Contents", [])]
        if suffix:
            paths = [p for p in paths if p.endswith(suffix)]
        return paths
    except Exception as ex:
        logger.error(f"Failed to list {s3_bucket=} with prefix {prefix=}: {ex}")
        raise


def delete(
    s3_bucket: str,
    s3_path: str,
) -> None:
    """Deletes the s3 object at the given path. If the path does not exist, no error is raised.

    Args:
        s3_path (str): the path to delete

    Returns:
        None
    """
    try:
        client = __get_client()
        client.delete_object(
            Bucket=s3_bucket,
            Key=s3_path,
        )
    except Exception as ex:
        logger.error(f"Failed to delete {s3_path=} from s3: {ex}")
        raise
