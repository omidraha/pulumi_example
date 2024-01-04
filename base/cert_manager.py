import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log


def create_cert_manager(
        namespace,
        provider,
        name_prefix,
        region,
):
    """
    :param namespace:
    :param provider:
    :param name_prefix:
    :param region:
    :return:
    @see: https://cert-manager.io/docs/installation/helm/
    @see: https://artifacthub.io/packages/helm/cert-manager/cert-manager
    """
    log.info('[develop_sdk.cert_manager.create_cert_manager]')
    cert = kubernetes.helm.v3.Release(
        f"cert-manager{name_prefix}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="cert-manager",
            version="1.13.3",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://charts.jetstack.io"
            ),
            namespace=namespace.metadata.name,
            values={
                "logLevel": "debug",
                "region": region,
                'installCRDs': True,
            },
        ),
        pulumi.ResourceOptions(
            provider=provider,
            parent=namespace,
            depends_on=[namespace]
        ),
    )
    return cert

