from base.cluster import create_cluster
from base.namespace import create_namespace
from base.provider import create_provider
from base.vpc import create_eip, create_vpc
from pv.const import NAMESPACE_NAME
from pv.pv import create_pv, create_pvc


def up():
    eip = create_eip()
    vpc = create_vpc(eip)
    cluster = create_cluster(vpc)
    provider = create_provider(cluster)
    namespace = create_namespace(
        provider, NAMESPACE_NAME
    )
    pv = create_pv(namespace)
    pvc = create_pvc(namespace, pv)
