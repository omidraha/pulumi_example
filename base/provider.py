import pulumi_kubernetes as kubernetes
from pulumi import log

from base.const import DEPLOY_NAME_PREFIX


def create_provider(cluster):
    log.info('[base.provider.create_provider]')
    provider = kubernetes.Provider(
        f'provider{DEPLOY_NAME_PREFIX}',
        kubeconfig=cluster.kubeconfig,
        enable_server_side_apply=True,
    )
    return provider
