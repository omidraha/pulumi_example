import pulumi_kubernetes as kubernetes

from base.const import DOMAINS
from const import GRAFANA_ADMIN, GRAFANA_PASS

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
    Host {DOMAINS[0]}
    port 443
    Uri /api/prom/push
    tls on
    tls.verify on
    HTTP_USER {GRAFANA_ADMIN}
    HTTP_PASSWD {GRAFANA_PASS}
"""



def create_fluent_bit(fbc, namespace):
    """
    :param fbc:
    :param namespace:
    :return:
    """
    fb = kubernetes.helm.v3.Release(
        "fluent-bit",
        kubernetes.helm.v3.ReleaseArgs(
            chart="fluent-bit",
            version="0.37.1",
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
):
    """
    :param namespace:
    :param annotations:
    :param arn:
    :return:
    """
    gf = kubernetes.helm.v3.Release(
        "grafana",
        kubernetes.helm.v3.ReleaseArgs(
            chart="grafana",
            version="6.58.9",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://grafana.github.io/helm-charts"
            ),
            namespace=namespace.metadata.name,
            values={
                "adminUser": GRAFANA_ADMIN,
                "adminPassword": GRAFANA_PASS,
                "ingress": {
                    "enabled": True,
                    "annotations": annotations,
                    "labels": {
                        "app": "ingress-gf",
                    },
                    "hosts": DOMAINS[0],
                    "path": '/',
                    "path_type": "Prefix"
                }
            },
        ),
    )
    return gf
