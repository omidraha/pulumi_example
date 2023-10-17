import pulumi_eks
import pulumi_aws
from pulumi import log, ResourceOptions
from base.const import DEPLOY_NAME_PREFIX, NODE_AMI_ID
from base.const import NAMESPACE_NAME
from base.namespace import create_namespace
from base.provider import create_provider
from base.security_group import create_security_group
from base.utils import get_public_keys
from base.vpc import create_eip, create_vpc
import pulumi


def create_node_group(
        cluster,
        vpc,
        security_group,
        node_public_key=None,
):
    ingress_rule = pulumi_aws.ec2.SecurityGroupRule(
        f'node-group-security-group-rule{DEPLOY_NAME_PREFIX}',
        type="ingress",
        from_port=0,
        to_port=65535,
        protocol="tcp",
        security_group_id=cluster.node_security_group.id,
        source_security_group_id=security_group.id,
        description="Allow nodes to communicate with control plane (EKS cluster)"
    )

    instance_role = pulumi_aws.iam.Role(
        f'node-group-role{DEPLOY_NAME_PREFIX}',
        assume_role_policy=pulumi.Output.from_input(
            """{
                                       "Version": "2012-10-17",
                                       "Statement": [
                                           {
                                               "Action": "sts:AssumeRole",
                                               "Principal": {
                                                   "Service": "ec2.amazonaws.com"
                                               },
                                               "Effect": "Allow",
                                               "Sid": ""
                                           }
                                       ]
                                     }"""
        ))

    instance_profile = pulumi_aws.iam.InstanceProfile(
        f'node-group-instance-profile{DEPLOY_NAME_PREFIX}',
        role=instance_role.name
    )

    node_group = pulumi_eks.NodeGroup(
        f'node-group{DEPLOY_NAME_PREFIX}',
        ami_id=NODE_AMI_ID,
        cluster=cluster,
        cluster_ingress_rule=ingress_rule,
        desired_capacity=2,
        instance_profile=instance_profile,
        instance_type='t2.small',
        max_size=2,
        min_size=2,
        node_associate_public_ip_address=True,
        node_public_key=node_public_key.public_key,
        node_security_group=security_group,
        node_subnet_ids=vpc.public_subnet_ids,
        labels={'ondemand': 'true'},
    )

    return node_group


def create_cluster(
        vpc,
        security_group=None,
):
    log.info('[base.cluster.create_cluster]')
    cluster = pulumi_eks.Cluster(
        f'cluster{DEPLOY_NAME_PREFIX}',
        vpc_id=vpc.vpc_id,
        public_subnet_ids=vpc.public_subnet_ids,
        private_subnet_ids=vpc.private_subnet_ids,
        create_oidc_provider=True,
        skip_default_node_group=True,
        instance_roles=None,
        enabled_cluster_log_types=[
            "api",
            "audit",
            "authenticator",
        ],
        cluster_security_group=security_group,
        opts=ResourceOptions(depends_on=[vpc]),
    )
    return cluster


def setup():
    public_keys = get_public_keys()
    eip = create_eip()
    vpc = create_vpc(eip)
    security_group = create_security_group(vpc)
    cluster = create_cluster(
        vpc,
        security_group,
    )
    provider = create_provider(cluster)
    namespace = create_namespace(provider, NAMESPACE_NAME)
    create_node_group(
        cluster,
        vpc,
        security_group,
        public_keys[0],
    )
    pulumi.export("kubeconfig", cluster.kubeconfig)
