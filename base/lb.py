import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log

from base.const import DEPLOY_NAME_PREFIX


def create_metal_lb(
        namespace,
        provider,
):
    """
    @see: https://artifacthub.io/packages/helm/metallb/metallb
    @see: https://metallb.universe.tf/installation/#installation-with-helm
    :return:
    """
    log.info('[devops_sdk.lb.create_metal_lb]')
    chart = kubernetes.helm.v3.Release(
        f"metallb{DEPLOY_NAME_PREFIX}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="metallb",
            version="0.13.12",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://metallb.github.io/metallb"
            ),
            namespace=namespace.metadata.name,
            values={
                "controller":
                    {
                        "logLevel": "debug",
                     },
                "speaker":
                    {
                        "logLevel": "debug",
                    },
            },
        ),
        opts=provider and pulumi.ResourceOptions(
            provider=provider,
            parent=namespace
        )
    )
    return chart

