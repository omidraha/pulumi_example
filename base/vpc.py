import pulumi_aws.ec2
from pulumi import log, ResourceOptions
import pulumi_awsx

from base.const import CLUSTER_TAG, AVAILABILITY_ZONE_NAMES, DEPLOY_NAME_PREFIX


def create_eip():
    log.info('[base.vpc.create_eip]')
    name = f'eip{DEPLOY_NAME_PREFIX}'
    eip = pulumi_aws.ec2.Eip(
        name,
        tags={
            "Name": name
        },
    )
    return eip


# VPC
def create_vpc(eip):
    log.info('[base.vpc.create_vpc]')
    name = f'vpc{DEPLOY_NAME_PREFIX}'
    cidr_block = '172.16.0.0/16'
    vpc = pulumi_awsx.ec2.Vpc(
        name,
        cidr_block=cidr_block,
        subnet_specs=[
            pulumi_awsx.ec2.SubnetSpecArgs(
                type=pulumi_awsx.ec2.SubnetType.PRIVATE,
                tags={
                    CLUSTER_TAG: "owned",
                    'kubernetes.io/role/internal-elb': '1',
                    'vpc': f'{name}',
                },
            ),
            pulumi_awsx.ec2.SubnetSpecArgs(
                type=pulumi_awsx.ec2.SubnetType.PUBLIC,
                tags={
                    CLUSTER_TAG: "owned",
                    'kubernetes.io/role/elb': '1',
                    'vpc': f'{name}',
                },
            ),
        ],
        availability_zone_names=AVAILABILITY_ZONE_NAMES,
        nat_gateways=pulumi_awsx.ec2.NatGatewayConfigurationArgs(
            strategy=pulumi_awsx.ec2.NatGatewayStrategy.SINGLE,
            elastic_ip_allocation_ids=[eip.id],
        ),
        tags={"Name": name},
        opts=ResourceOptions(depends_on=[eip]),
    )
    return vpc
