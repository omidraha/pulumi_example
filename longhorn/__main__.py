import __init__
from base.cluster import create_cluster
from base.const import NAMESPACE_NAME
from base.namespace import create_namespace
from base.provider import create_provider
from base.utils import get_public_keys
from base.vpc import create_eip, create_vpc
import pulumi

from longhorn import setup


def up():
    public_keys = get_public_keys()
    eip = create_eip()
    vpc = create_vpc(eip)
    cluster = create_cluster(
        vpc,
        node_public_key=public_keys[0],
    )
    provider = create_provider(cluster)
    namespace = create_namespace(provider, NAMESPACE_NAME)
    setup(provider)
    pulumi.export("kubeconfig", cluster.kubeconfig)


up()
