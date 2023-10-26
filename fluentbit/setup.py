from base.cluster import create_cluster
from base.provider import create_provider
from base.vpc import create_eip, create_vpc
from fluentbit.fluentbit import setup


def up():
    eip = create_eip()
    vpc = create_vpc(eip)
    cluster = create_cluster(vpc)
    provider = create_provider(cluster)
    setup(provider, storage_class="longhorn")


