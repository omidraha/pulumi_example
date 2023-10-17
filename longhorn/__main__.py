import __init__
from base.cluster import create_cluster
from base.const import NAMESPACE_NAME
from base.namespace import create_namespace
from base.provider import create_provider
from base.security_group import create_security_group
from base.utils import get_public_keys
from base.vpc import create_eip, create_vpc
import pulumi


def setup():
    public_keys = get_public_keys()
    eip = create_eip()
    vpc = create_vpc(eip)
    security_group = create_security_group(vpc)
    cluster = create_cluster(
        vpc,
        security_group,
        public_keys[0],
    )
    provider = create_provider(cluster)
    namespace = create_namespace(provider, NAMESPACE_NAME)
    pulumi.export("kubeconfig", cluster.kubeconfig)


setup()
