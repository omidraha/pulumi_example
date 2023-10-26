import pulumi_kubernetes as kubernetes

from base.const import ANNOTATIONS
from base.namespace import create_namespace
from .const import GRAFANA_ADMIN, GRAFANA_PASS, GRAFANA_NAMESPACE_NAME

fb_config_map_data = f"""
[SERVICE]
    Flush         1
    Log_Level     info
    Daemon        off
    Parsers_File  parsers.conf
    HTTP_Server   On
    HTTP_Listen   0.0.0.0
    HTTP_PORT     2020
[INPUT]
    Name      tail
    Path      /var/log/containers/*.log
    Parser    docker
    Tag       kube.*
[FILTER]
    Name        kubernetes
    Match       kube.*
    Kube_URL    https://kubernetes.default.svc:443
    Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
    Kube_Tag_Prefix     kube.var.log.containers.
    Merge_Log           On
    Merge_Log_Key       log_processed
    K8S-Logging.Parser  On
    K8S-Logging.Exclude Off
[OUTPUT]
    Name      loki
    Match     *
    Labels    name=fluent-bit
    host      loki-backend.fluent-bit.svc.cluster.local
    port      3100
    auto_kubernetes_labels on
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
            "fluent-bit.conf": fb_config_map_data
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
    :param arn:
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
    @see: https://grafana.com/docs/loki/latest/installation/helm/install-monolithic/
    @see: https://grafana.com/docs/loki/next/setup/install/helm/reference/
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
                },
                "singleBinary": {
                    "persistence": {
                        'storageClass': storage_class,
                        "size": "1Gi",
                    },
                },
                "read": {
                    "persistence": {
                        'storageClass': storage_class,
                        "size": "1Gi",
                    },
                },
                "write": {
                    "persistence": {
                        'storageClass': storage_class,
                        "size": "1Gi",
                    },
                },
                "backend": {
                    "persistence": {
                        'storageClass': storage_class,
                        "size": "1Gi",
                    },
                },
                "commonConfig": {
                    "replication_factor": 1
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
