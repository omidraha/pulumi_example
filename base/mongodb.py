import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log


def create_mongodb_standalone(
        provider,
        namespace,
        name_prefix,
        region,
        db_user,
        db_password,
        db_name,
        storage_class,
        size,
):
    """
    :param provider:
    :param namespace:
    :param name_prefix:
    :param region:
    :param db_user:
    :param db_password:
    :param db_name:
    :param storage_class:
    :param size:
    :return:
    @see: https://artifacthub.io/packages/helm/bitnami/mongodb
    """
    log.info('[base.mongodb.create_mongodb_standalone]')
    db = kubernetes.helm.v3.Release(
        f"mongodb-standalone{name_prefix}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="mongodb",
            version="14.1.0",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://charts.bitnami.com/bitnami"
            ),
            namespace=namespace.metadata.name,
            values={
                "logLevel": "debug",
                "replicaCount": 1,
                "region": region,
                "architecture": "standalone",
                "persistence": {
                    "enabled": True,
                    "size": size,
                    "storageClass": storage_class,
                },
                "auth": {
                    "enabled": True,
                    "databases": db_name,
                    "usernames": db_user,
                    "passwords": db_password
                },
                "fullnameOverride": "mongodb",
            },
        ),
        pulumi.ResourceOptions(
            provider=provider,
            parent=namespace,
        )
    )
    return db
