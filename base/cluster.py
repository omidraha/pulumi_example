import pulumi_eks
from pulumi import log, ResourceOptions


def create_cluster(vpc):
    log.info('[base.cluster.create_cluster]')
    cluster = pulumi_eks.Cluster(
        'cluster',
        vpc_id=vpc.vpc_id,
        public_subnet_ids=vpc.public_subnet_ids,
        private_subnet_ids=vpc.private_subnet_ids,
        create_oidc_provider=True,
        skip_default_node_group=False,
        instance_type="t2.small",
        desired_capacity=1,
        min_size=1,
        max_size=1,
        instance_roles=None,
        enabled_cluster_log_types=[
            "api",
            "audit",
            "authenticator",
        ],
        node_associate_public_ip_address=False,
        vpc_cni_options=pulumi_eks.VpcCniOptionsArgs(
            warm_ip_target=1,
        ),
        opts=ResourceOptions(depends_on=[vpc]),
    )
    return cluster
