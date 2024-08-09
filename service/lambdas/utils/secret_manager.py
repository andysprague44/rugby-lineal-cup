import boto3
import botocore
import json

__secretsmanager_client = None


def __get_client() -> boto3.client:
    global __secretsmanager_client
    __secretsmanager_client = __secretsmanager_client or boto3.client(
        "secretsmanager",
        config=botocore.client.Config(
            connect_timeout=2,
            read_timeout=5,
            retries={"max_attempts": 3},
        ),
    )
    return __secretsmanager_client


def __get_secret(secret_name: str) -> str:
    client = __get_client()
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = get_secret_value_response["SecretString"]
    return str(secret)


def get_secret_string(secret_name: str) -> str:
    secret = __get_secret(secret_name)
    return secret


def get_secret_json(secret_name: str) -> dict:
    secret = __get_secret(secret_name)
    try:
        secret_json = json.loads(secret)
    except json.JSONDecodeError:
        raise ValueError(f"Secret '{secret_name}' is not valid json")
    return secret_json
