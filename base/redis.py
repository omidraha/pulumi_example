import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log

from base.const import DEPLOY_NAME_PREFIX, REGION


def create_redis_standalone(
        provider,
        namespace,
        storage_class,
):
    """
    :param provider:
    :param namespace:
    :param storage_class:
    :return:
    @see: https://artifacthub.io/packages/helm/bitnami/redis
    """
    log.info('[base.redis.create_redis]')
    redis = kubernetes.helm.v3.Release(
        f"redis-standalone{DEPLOY_NAME_PREFIX}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="redis",
            version="17.13.2",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://charts.bitnami.com/bitnami"
            ),
            namespace=namespace.metadata.name,
            values={
                "logLevel": "debug",
                "region": REGION,
                "architecture": "standalone",
                "master": {
                    "persistence": {
                        "enabled": True,
                        "size": "2Gi",
                        "storageClass": storage_class,
                    }
                },
                "replica": {
                    "replicaCount": 0
                },
                "auth": {
                    "enabled": False
                },
                "fullnameOverride": "redis",
            },
        ),
        pulumi.ResourceOptions(
            provider=provider,
            parent=namespace,
        )
    )
    return redis
