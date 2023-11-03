import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log

from base.const import DEPLOY_NAME_PREFIX, REGION


def create_postgres_standalone(
        provider,
        namespace,
        storage_class,
):
    """
    :param provider:
    :param namespace:
    :param storage_class:
    :return:
    @see: https://artifacthub.io/packages/helm/bitnami/postgresql
    """
    log.info('[base.postgres.create_postgres_standalone]')
    db = kubernetes.helm.v3.Release(
        f"postgres-standalone{DEPLOY_NAME_PREFIX}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="postgresql",
            version="13.1.5",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://charts.bitnami.com/bitnami"
            ),
            namespace=namespace.metadata.name,
            values={
                "logLevel": "debug",
                "replicaCount": 1,
                "region": REGION,
                "architecture": "standalone",
                "primary": {
                    "persistence": {
                        "enabled": True,
                        "size": "3Gi",
                        "storageClass": storage_class,
                    }
                },
                "readReplicas": {
                    "replicaCount": 0
                },
                "auth": {
                    "enabled": False
                },
                "fullnameOverride": "postgres",
            },
        ),
        pulumi.ResourceOptions(
            provider=provider,
            parent=namespace,
        )
    )
    return db
