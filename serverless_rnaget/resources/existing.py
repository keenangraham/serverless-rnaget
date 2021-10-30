from aws_cdk import core as cdk
from aws_cdk import aws_ec2
from aws_cdk import aws_elasticsearch
from aws_cdk import aws_certificatemanager
from aws_cdk import aws_route53

from serverless_rnaget.config import config


class InternalNetwork(cdk.Construct):

    def __init__(self, scope, construct_id, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.vpc = aws_ec2.Vpc.from_lookup(
            self,
            'VPC',
            vpc_id=scope.config['vpc_id']
        )
        self.security_group = aws_ec2.SecurityGroup.from_security_group_id(
            self,
            'SG',
            scope.config['security_group_id'],
            mutable=False
        )


class ENCODEAPIDomain(cdk.Construct):

    def __init__(self, scope, construct_id, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.domain_name = scope.config['domain_name']
        self.domain_certificate = aws_certificatemanager.Certificate.from_certificate_arn(
            self,
            'ENCODEAPIDomainCertificate',
            scope.config['domain_certificate_arn'],
        )
        self.hosted_zone = aws_route53.HostedZone.from_lookup(
            self,
            'ENCODEAPIHostedZone',
            domain_name=self.domain_name,
        )


class ExistingResources(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config['existing_resources']
        self.internal_network = InternalNetwork(self, 'VPCSecurity')
        self.elasticsearch = aws_elasticsearch.Domain.from_domain_endpoint(
            self,
            'RNAGetExpressions',
            self.config['elasticsearch'],
        )
        self.encode_api_domain = ENCODEAPIDomain(self, 'ENCODEAPI')
