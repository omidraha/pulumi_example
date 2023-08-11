from cluster import create_cluster
from iam import create_cluster_iam
from vpc import create_vpc, create_public_subnet, create_private_subnet, create_internet_gateway, create_route_table, \
    create_route_table_association


def up():
    vpc = create_vpc()
    public_subnet = create_public_subnet(vpc)
    private_subnet = create_private_subnet(vpc)
    ig = create_internet_gateway(vpc)
    rt = create_route_table(vpc, ig)
    create_route_table_association(rt, public_subnet + private_subnet)
    eks_worker_role = create_cluster_iam()
    cluster = create_cluster(vpc, public_subnet, private_subnet, eks_worker_role)
    return cluster

