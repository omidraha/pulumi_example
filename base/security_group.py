from pulumi_aws import ec2

from base.const import DEPLOY_NAME_PREFIX


def create_security_group(vpc):
    security_group = ec2.SecurityGroup(
        f'security-group{DEPLOY_NAME_PREFIX}',
        description='Enable SSH access',
        ingress=[
            # SSH
            ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=22,
                to_port=22,
                cidr_blocks=["0.0.0.0/0"],
            ),
        ],
        egress=[
            {
                'protocol': '-1',
                'from_port': 0,
                'to_port': 0,
                'cidr_blocks': ['0.0.0.0/0'],
            },
        ],
        vpc_id=vpc.vpc_id,
        tags={"Name": f'security-group{DEPLOY_NAME_PREFIX}'},
    )
    return security_group
