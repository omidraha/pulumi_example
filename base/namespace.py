import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log


def create_namespace(provider, name, labels=None):
    """
    :param provider:
    :param name:
    :param labels:
    :return:
    """
    log.info('[base.namespace.create_namespace]')
    metadata = {
        "name": name,
    }
    if labels:
        metadata.update({'labels': labels})
    namespace = kubernetes.core.v1.Namespace(
        name,
        metadata=metadata,
        opts=pulumi.ResourceOptions(
            provider=provider,
            parent=provider,
        )
    )
    return namespace
