import pulumi_eks

from base.const import CLUSTER_NAME

AVAILABILITY_ZONE_NAMES = [
    'us-west-2a',
    'us-west-2b',
    'us-west-2c'
]


# Cluster
def create_cluster(vpc, public_subnet, private_subnet, eks_worker_role):
    cluster = pulumi_eks.Cluster(
        CLUSTER_NAME,
        vpc_id=vpc.id,
        public_subnet_ids=[item.id for item in public_subnet],
        private_subnet_ids=[item.id for item in private_subnet],
        create_oidc_provider=True,
        skip_default_node_group=False,
        instance_type="t2.micro",
        desired_capacity=1,
        min_size=1,
        max_size=1,
        instance_role=eks_worker_role,
        role_mappings=[
            {
                'groups': ['system:bootstrappers', 'system:nodes'],
                'rolearn': eks_worker_role.arn,
                'username': 'system:node:{{EC2PrivateDNSName}}',
            }
        ],
        enabled_cluster_log_types=[
            "api",
            "audit",
            "authenticator",
        ],
        node_associate_public_ip_address=False,
        vpc_cni_options=pulumi_eks.VpcCniOptionsArgs(
            warm_ip_target=5,
        ),
    )
    return cluster
