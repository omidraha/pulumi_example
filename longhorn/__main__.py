import __init__
from base.cluster import create_cluster
from base.const import NAMESPACE_NAME
from base.namespace import create_namespace
from base.provider import create_provider
from base.utils import get_public_keys
from base.vpc import create_eip, create_vpc
import pulumi

import longhorn
from pod import create_pod
from storage.storage import create_sc, create_pvc


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
    longhorn.setup(provider)
    sc = create_sc(
        namespace,
        provisioner="driver.longhorn.io",
        allow_volume_expansion=True,
        parameters={
            "numberOfReplicas": "3",
            "staleReplicaTimeout": "2880",
            "fromBackup": "",
            "fsType": "ext4"
        }
    )
    pvc = create_pvc(namespace, sc)
    create_pod(namespace, pvc)

    pulumi.export("kubeconfig", cluster.kubeconfig)


up()
