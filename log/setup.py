from base.cluster import create_cluster
from base.const import ANNOTATIONS
from base.namespace import create_namespace
from base.provider import create_provider
from base.vpc import create_eip, create_vpc
from log.const import GRAFANA_NAMESPACE_NAME
from log.log import create_fluent_bit_config_map, create_grafana, create_fluent_bit


def up():
    eip = create_eip()
    vpc = create_vpc(eip)
    cluster = create_cluster(vpc)
    provider = create_provider(cluster)
    namespace = create_namespace(
        provider, GRAFANA_NAMESPACE_NAME
    )
    gf = create_grafana(
        namespace,
        ANNOTATIONS,
    )
    fbc = create_fluent_bit_config_map(namespace)
    create_fluent_bit(fbc, namespace)
