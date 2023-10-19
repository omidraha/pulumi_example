import pulumi_eks
from pulumi import log, ResourceOptions
from base.const import DEPLOY_NAME_PREFIX, NODE_AMI_ID


def create_cluster(
        vpc,
        node_public_key=None,
        node_user_data=None,
):
    log.info('[base.cluster.create_cluster]')
    cluster = pulumi_eks.Cluster(
        f'cluster{DEPLOY_NAME_PREFIX}',
        vpc_id=vpc.vpc_id,
        public_subnet_ids=vpc.public_subnet_ids,
        private_subnet_ids=vpc.private_subnet_ids,
        create_oidc_provider=True,
        skip_default_node_group=False,
        instance_type="c5d.xlarge",
        desired_capacity=3,
        min_size=3,
        max_size=3,
        instance_roles=None,
        enabled_cluster_log_types=[
            "api",
            "audit",
            "authenticator",
        ],
        node_associate_public_ip_address=True,
        node_ami_id=NODE_AMI_ID,
        vpc_cni_options=pulumi_eks.VpcCniOptionsArgs(
            warm_ip_target=2,
        ),
        node_public_key=node_public_key.public_key,
        node_user_data=node_user_data,
        opts=ResourceOptions(depends_on=[vpc]),
    )
    return cluster
