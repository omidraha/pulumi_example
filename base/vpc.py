import pulumi_aws.ec2
from pulumi import log, ResourceOptions
import pulumi_awsx

from base.const import CLUSTER_TAG, AVAILABILITY_ZONE_NAMES


def create_eip(deploy_name_prefix=None):
    log.info('[base.vpc.create_eip]')
    eip = pulumi_aws.ec2.Eip(
        'eip',
        tags={"Name": 'eip'},
    )
    return eip


# VPC
def create_vpc(eip):
    log.info('[base.vpc.create_vpc]')
    name = 'vpc'
    cidr_block = ''
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


def get_vpcs():
    """
    :return:
    Example:
         vpcs.ids: [
            'vpc-0ad0ce310ef05ae66',
            'vpc-0b4f3199c9b017437',
            'vpc-05fba5d0f6c030b93'
         ]
    """
    log.info('[base.vpc.get_vpc]')
    vpc_items = pulumi_aws.ec2.get_vpcs()
    vpcs = list()
    for vpc_id in vpc_items.ids:
        vpc = pulumi_aws.ec2.get_vpc(id=vpc_id)
        vpc_name = vpc.tags.get("Name")
        if vpc_name in VPC_NAMES:
            vpcs.append(vpc)

    return vpcs
