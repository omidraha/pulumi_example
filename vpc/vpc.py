import pulumi_aws

from base.const import CLUSTER_TAG, AVAILABILITY_ZONE_NAMES


# VPC
def create_vpc():
    vpc = pulumi_aws.ec2.Vpc(
        'vpc',
        tags={"Name": "vpc"},
        cidr_block='12.0.0.0/16',
    )
    return vpc


def create_public_subnet(vpc):
    public_subnet = pulumi_aws.ec2.Subnet(
        "pub-subnet",
        vpc_id=vpc.id,
        availability_zone=AVAILABILITY_ZONE_NAMES[0],
        tags={
            'Name': f"pub-subnet",
            CLUSTER_TAG: "owned",
            'kubernetes.io/role/elb': '1',
        },
        cidr_block='12.0.1.0/24',
        map_public_ip_on_launch=True,
        assign_ipv6_address_on_creation=False,
    )
    return [public_subnet]


def create_private_subnet(vpc):
    private_subnets = []
    for i, az in enumerate(AVAILABILITY_ZONE_NAMES[1:2], start=1):
        private_subnet = pulumi_aws.ec2.Subnet(
            f"pv-subnet-{i}",
            vpc_id=vpc.id,
            availability_zone=az,
            tags={
                'Name': f"pv-subnet-{i}",
                CLUSTER_TAG: "owned",
                'kubernetes.io/role/internal-elb': '1',
            },
            cidr_block='12.0.2.0/24',
            map_public_ip_on_launch=False,
            assign_ipv6_address_on_creation=False,
        )
        private_subnets.append(private_subnet)
    return private_subnets


def create_internet_gateway(vpc):
    igw = pulumi_aws.ec2.InternetGateway(
        "ig",
        vpc_id=vpc.id,
        tags={
            'Name': f"ig",
        },
    )
    return igw


def create_route_table(vpc, igw):
    rt = pulumi_aws.ec2.RouteTable(
        "rt",
        vpc_id=vpc.id,
        routes=[pulumi_aws.ec2.RouteTableRouteArgs(
            cidr_block='0.0.0.0/0',
            gateway_id=igw.id,
        )],
        tags={
            'Name': "rt",
        },
    )
    return rt


def create_route_table_association(rt, subnets):
    for index, subnet in enumerate(subnets):
        pulumi_aws.ec2.RouteTableAssociation(
            f"rta-{index}",
            route_table_id=rt.id,
            subnet_id=subnet.id,
        )

