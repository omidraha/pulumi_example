import __init__
from app.app import create_app
from base.cluster import create_cluster
from base.const import NAMESPACE_NAME
from base.namespace import create_namespace
from base.provider import create_provider
from base.vpc import create_eip, create_vpc
import pulumi

from linkerd import setup


def up():
    eip = create_eip()
    vpc = create_vpc(eip)
    cluster = create_cluster(vpc)
    provider = create_provider(cluster)
    namespace = create_namespace(provider, NAMESPACE_NAME)
    create_app()
    setup(provider)
    pulumi.export("kubeconfig", cluster.kubeconfig)


up()
