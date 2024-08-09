#!/usr/bin/env python3
import sys

from aws_cdk import Tags
from cdk.config import Config
from cdk.stack import ServiceStack
from aws_cdk import App
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)


def main() -> None:
    app = App()

    stage = app.node.try_get_context("stage") or "dev"
    if stage is None:
        logger.fatal(
            f"missing required `stage` context value. try --context stage=dev|test|prod"
        )
        sys.exit(1)

    conf = Config(stage)

    _stack = ServiceStack(app, conf.stack_name, conf)
    add_tags(app, conf)
    app.synth()


def add_tags(app: App, conf: Config) -> None:
    for key in conf.tags.keys():
        Tags.of(app).add(key=key, value=conf.tags[key])


if __name__ == "__main__":
    main()
