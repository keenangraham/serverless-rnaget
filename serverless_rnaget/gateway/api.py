from aws_cdk import aws_apigateway
from aws_cdk import aws_lambda
from aws_cdk.aws_lambda_python import PythonFunction
from aws_cdk import core as cdk
from aws_cdk import aws_route53
from aws_cdk import aws_route53_targets

from aws_solutions_constructs import aws_apigateway_lambda


FUNCTION_REGISTRY = {}

RESOURCES = {
    ('projects', 'projects'): {
        ('{project_id}', 'project_id'): {},
        ('filters', 'project_filters'): {},
    },
    ('studies', 'studies'): {
        ('{studies_id}', 'studies_id'): {},
        ('filters', 'study_filters'): {},
    },
    ('expressions', 'expression_ids'): {
        ('formats', 'expressions_formats'): {},
        ('units', 'expressions_units'): {},
        ('ticket', 'expressions_ticket'): {},
        ('{expression_id}', None): {
            ('ticket', 'expressions_id_ticket'): {},
            ('bytes', 'expressions_id_bytes'): {},
        },
        ('bytes', 'expressions_bytes'): {},
        ('filters', 'expressions_filters'): {},
    },
    ('service-info', 'service_info'): {},
}

VPC_LAMBDAS = [
    'expressions_bytes',
]


def make_lambda_in_vpc(context, name, entry='serverless_rnaget/lambdas/', index='rnaget.py'):
    return PythonFunction(
        context,
        name,
        entry=entry,
        index=index,
        handler=name,
        runtime=aws_lambda.Runtime.PYTHON_3_8,
        vpc=context.existing_resources.internal_network.vpc,
        security_group=context.existing_resources.internal_network.security_group,
        allow_public_subnet=True,
    )


def make_lambda(context, name, entry='serverless_rnaget/lambdas/', index='rnaget.py'):
    return PythonFunction(
        context,
        name,
        entry=entry,
        index=index,
        handler=name,
        runtime=aws_lambda.Runtime.PYTHON_3_8,
    )


def make_lambda_factory(context, name):
    if name in VPC_LAMBDAS:
        return make_lambda_in_vpc(context, name)
    return make_lambda(context,name)


def make_api_gateway_to_lambda(context, name, lambda_):
    return aws_apigateway_lambda.ApiGatewayToLambda(
        context,
        name,
        existing_lambda_obj=lambda_,
        api_gateway_props=aws_apigateway.RestApiProps(
            default_method_options=aws_apigateway.MethodOptions(
                authorization_type=aws_apigateway.AuthorizationType.NONE,
            ),
            domain_name=aws_apigateway.DomainNameOptions(
                certificate=context.existing_resources.encode_api_domain.domain_certificate,
                domain_name=f'rnaget.{context.existing_resources.encode_api_domain.domain_name}',
            ),
        )
    )


def make_handler(context, name):
    lambda_ = make_lambda_factory(context, f'{name}')
    FUNCTION_REGISTRY[name] = lambda_
    return aws_apigateway.LambdaIntegration(
        lambda_
    )


def add_resources_and_handlers(context, resources, root, action='GET'):
    for (parent_resource, parent_handler), children_resources in resources.items():
        parent = root.add_resource(parent_resource)
        if parent_handler:
            handler = make_handler(context, parent_handler)
            parent.add_method(action, handler)
        add_resources_and_handlers(context, children_resources, parent, action)
    return root


def add_custom_domain_alias_to_api(context):
    return aws_route53.ARecord(
        context,
        'CustomDomainToApi',
        zone=context.existing_resources.encode_api_domain.hosted_zone,
        target=aws_route53.RecordTarget.from_alias(
            aws_route53_targets.ApiGateway(
                context.gateway
            )
        ),
        record_name=f'rnaget.{context.existing_resources.encode_api_domain.domain_name}',
    )


class API(cdk.Stack):

    def __init__(self, scope, construct_id, existing_resources, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.existing_resources = existing_resources
        self.default_lambda = make_lambda(
            self,
            'default',
        )
        self.gateway_to_lambda = make_api_gateway_to_lambda(
            self,
            'RNAGetAPI',
            self.default_lambda,
        )
        self.gateway = self.gateway_to_lambda.api_gateway
        self.resources = add_resources_and_handlers(
            self,
            RESOURCES,
            self.gateway.root
        )
        self.alias_record = add_custom_domain_alias_to_api(self)
