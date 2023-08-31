from base.cluster import create_cluster
from base.namespace import create_namespace
from base.provider import create_provider
from base.vpc import create_eip, create_vpc
from storage.const import NAMESPACE_NAME
from storage.storage import create_sc, create_pv_sc, create_pvc


def up():
    eip = create_eip()
    vpc = create_vpc(eip)
    cluster = create_cluster(vpc)
    provider = create_provider(cluster)
    namespace = create_namespace(
        provider, NAMESPACE_NAME
    )
    sc = create_sc(namespace)
    pv = create_pv_sc(namespace, sc)
    pvc = create_pvc(namespace, pv)
