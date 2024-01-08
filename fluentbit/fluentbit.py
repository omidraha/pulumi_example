import pulumi_kubernetes as kubernetes

from base.const import ANNOTATIONS
from base.namespace import create_namespace
from .const import GRAFANA_ADMIN, GRAFANA_PASS, GRAFANA_NAMESPACE_NAME

fb_config_map_data = """
[SERVICE]
    Flush             5
    Grace             30
    Log_Level         debug
    Daemon            off
    Parsers_File      parsers.conf
    HTTP_Server       On
    HTTP_Listen       0.0.0.0
    HTTP_Port         2020
[INPUT]
    Name    tail
    Tag     kube.*
    Path        /var/log/containers/*.log    
    Exclude_Path    /var/log/containers/fluent-bit*,/var/log/containers/aws-node*,/var/log/containers/kube-proxy*
    multiline.parser    docker, cri
    Mem_Buf_Limit         100MB
    Refresh_Interval      10
    Skip_Long_Lines       On   
[FILTER]
    Name             kubernetes
    Match            kube.*
    Kube_URL         https://kubernetes.default.svc:443
    Kube_CA_File     /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    Kube_Token_File  /var/run/secrets/kubernetes.io/serviceaccount/token
    Kube_Tag_Prefix  kube.var.log.containers.
    Merge_Log        On
    Merge_Log_Key    log_processed
    K8S-Logging.Parser    On
    K8S-Logging.Exclude   Off    
[OUTPUT]
    Name      loki
    Match     *
    Labels    name=fluent-bit
    host      loki-gateway.fluent-bit.svc.cluster.local
    port      80
    auto_kubernetes_labels on
"""

# parsers.conf
parsers_conf = r"""
[PARSER]
    Name        syslog
    Format          regex
    Regex           ^(?<time>[^ ]* {1,2}[^ ]* [^ ]*) (?<host>[^ ]*) (?<ident>[a-zA-Z0-9_\/\.\-]*)(?:\[(?<pid>[0-9]+)\])?(?:[^\:]*\:)? *(?<message>.*)$
    Time_Key        time
    Time_Format     %b %d %H:%M:%S
[PARSER]
    Name        container_firstline
    Format          regex
    Regex           (?<log>(?<="log":")\S(?!\.).*?)(?<!\\)".*(?<stream>(?<="stream":").*?)".*(?<time>\d{4}-\d{1,2}-\d{1,2}T\d{2}:\d{2}:\d{2}\.\w*).*(?=})
    Time_Key        time
    Time_Format     %Y-%m-%dT%H:%M:%S.%LZ
[PARSER]
    Name   nginx
    Format regex
    Regex Regex ^(?<remote>[^ ]*) (?<host>[^ ]*) (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")
    Time_Key time
    Time_Format %d/%b/%Y:%H:%M:%S %z
[PARSER]
    Name        k8s-nginx-ingress
    Format      regex
    Regex       ^(?<host>[^ ]*) - (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*) "(?<referer>[^\"]*)" "(?<agent>[^\"]*)" (?<request_length>[^ ]*) (?<request_time>[^ ]*) \[(?<proxy_upstream_name>[^ ]*)\] (\[(?<proxy_alternative_upstream_name>[^ ]*)\] )?(?<upstream_addr>[^ ]*) (?<upstream_response_length>[^ ]*) (?<upstream_response_time>[^ ]*) (?<upstream_status>[^ ]*) (?<reg_id>[^ ]*).*$
    Time_Key    time
    Time_Format %d/%b/%Y:%H:%M:%S %z
[PARSER]
    Name cri
    Format regex
    Regex ^(?<time>[^ ]+) (?<stream>stdout|stderr) (?<logtag>[^ ]*) (?<message>.*)$
    Time_Key    time
    Time_Format %Y-%m-%dT%H:%M:%S.%L%z
    Time_Keep   On    
"""


def create_fluent_bit(fbc, namespace):
    """
    :param fbc:
    :param namespace:
    :return:
    @see: https://artifacthub.io/packages/helm/fluent/fluent-bit
    @see: https://github.com/fluent/helm-charts/tree/main/charts/fluent-bit
    @see: https://github.com/fluent/helm-charts/blob/main/charts/fluent-bit/values.yaml
    """
    fb = kubernetes.helm.v3.Release(
        "fluent-bit",
        kubernetes.helm.v3.ReleaseArgs(
            chart="fluent-bit",
            version="0.39.0",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://fluent.github.io/helm-charts"
            ),
            namespace=namespace.metadata.name,
            values={
                "existingConfigMap": fbc.metadata.name
            }
        ),
    )
    return fb


def create_fluent_bit_config_map(namespace):
    """
    :param namespace:
    :return:
    """
    fbc = kubernetes.core.v1.ConfigMap(
        "fbc",
        metadata={
            "name": "fluent-bit-config",
            "namespace": namespace.metadata.name,
            "labels": {
                "app": "fluent-bit",
            },
        },
        data={
            "fluent-bit.conf": fb_config_map_data,
            "parsers.conf": parsers_conf,
        },
    )
    return fbc


def create_fluent_bit_bitnami(fbc, namespace):
    """
    :param fbc:
    :param namespace:
    :return:
    """
    fb = kubernetes.helm.v3.Release(
        "fluent-bit",
        kubernetes.helm.v3.ReleaseArgs(
            chart="fluent-bit",
            version="0.5.0",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://charts.bitnami.com/bitnami"
            ),
            namespace=namespace.metadata.name,
            values={
                "forwarder.configMap": fbc.metadata.name,
            }
        ),
    )
    return fb


def create_grafana(
        namespace,
        annotations,
        storage_class,
):
    """
    :param namespace:
    :param annotations:
    :param storage_class:
    :return:
    @see: https://artifacthub.io/packages/helm/grafana/grafana
    """
    gf = kubernetes.helm.v3.Release(
        "grafana",
        kubernetes.helm.v3.ReleaseArgs(
            chart="grafana",
            version="6.61.1",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://grafana.github.io/helm-charts"
            ),
            namespace=namespace.metadata.name,
            values={
                "adminUser": GRAFANA_ADMIN,
                "adminPassword": GRAFANA_PASS,
                # "ingress": {
                #     "enabled": True,
                #     "annotations": annotations,
                #     "labels": {
                #         "app": "ingress-gf",
                #     },
                #     "hosts": DOMAINS[0],
                #     "path": '/',
                #     "path_type": "Prefix"
                # }
                "persistence": {
                    "enabled": True,
                    "size": "1Gi",
                    "storageClassName": storage_class,
                },
                "service": {
                    "port": 7070,
                }
            },
        ),
    )
    return gf


def create_loki(namespace, storage_class):
    """
    :param namespace:
    :param storage_class:
    :return:
    @see: https://artifacthub.io/packages/helm/grafana/loki
    @see: https://grafana.com/docs/loki/next/setup/install/helm/configure-storage/
    @see: https://grafana.com/docs/loki/next/setup/install/helm/install-scalable/
    @see: https://grafana.com/docs/loki/latest/installation/helm/install-monolithic/
    @see: https://grafana.com/docs/loki/next/setup/install/helm/reference/
    @note: Applied nodeSelector: "tier": "log"
    """
    fb = kubernetes.helm.v3.Release(
        "loki",
        kubernetes.helm.v3.ReleaseArgs(
            chart="loki",
            version="5.15.0",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://grafana.github.io/helm-charts"
            ),
            namespace=namespace.metadata.name,
            values={
                "loki": {
                    "auth_enabled": False,
                    "commonConfig": {
                        "replication_factor": 1
                    },
                    "storage": {
                        "type": "filesystem"
                    },
                },
                "singleBinary": {
                    "replicas": 1,
                    "persistence": {
                        'storageClass': storage_class,
                        "size": "5Gi",
                    },
                    'nodeSelector': {
                        "tier": "log"
                    },
                },
                "read": {
                    "persistence": {
                        'storageClass': storage_class,
                        "size": "4Gi",
                    },
                    'nodeSelector': {
                        "tier": "log"
                    },
                },
                "write": {
                    "persistence": {
                        'storageClass': storage_class,
                        "size": "3Gi",
                    },
                    'nodeSelector': {
                        "tier": "log"
                    },
                },
                "backend": {
                    "persistence": {
                        'storageClass': storage_class,
                        "size": "2Gi",
                    },
                    'nodeSelector': {
                        "tier": "log"
                    },
                },
            },
        ),
    )
    return fb


def setup(provider, storage_class):
    namespace = create_namespace(
        provider, GRAFANA_NAMESPACE_NAME
    )
    gf = create_grafana(
        namespace,
        ANNOTATIONS,
        storage_class=storage_class,
    )
    create_loki(namespace, storage_class)
    fbc = create_fluent_bit_config_map(namespace)
    create_fluent_bit(fbc, namespace)
