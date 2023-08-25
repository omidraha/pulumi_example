import pulumi_kubernetes as kubernetes
from pulumi import log


def create_provider(cluster):
    log.info('[base.provider.create_provider]')
    provider = kubernetes.Provider(
        'provider',
        kubeconfig=cluster.kubeconfig,
        enable_server_side_apply=True,
    )
    return provider
