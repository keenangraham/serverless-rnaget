#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from serverless_rnaget.config import config
from serverless_rnaget.resources.existing import ExistingResources
from serverless_rnaget.gateway.api import API as RNAGetAPI


ENVIRONMENT = cdk.Environment(
    account=config['account'],
    region=config['region'],
)

app = cdk.App()

existing_resources = ExistingResources(
    app,
    'ExistingResources',
    env=ENVIRONMENT,
)

rnaget_api = RNAGetAPI(
    app,
    'RNAGetAPIStack',
    existing_resources=existing_resources,
    env=ENVIRONMENT,
)

app.synth()
