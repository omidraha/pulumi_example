import os

import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log
from pulumi_kubernetes.core.v1 import Namespace

from base.const import DEPLOY_NAME_PREFIX, REGION, BASE_PATH
from base.utils import read_file

CERT_PATH = f'{BASE_PATH}/linkerd/'
ca = os.path.join(CERT_PATH, f'ca.crt')
crt = os.path.join(CERT_PATH, f'issuer.crt')
key = os.path.join(CERT_PATH, f'issuer.key')

def create_linkerd_ns():
    """
    :return:
    """
    log.info('[mon.create_linkerd_ns]')
    ns = Namespace(
        f'linkerd{DEPLOY_NAME_PREFIX}',
        metadata={
            'name': 'linkerd',
        },
    )
    return ns


def create_linkerd_viz_ns():
    """
    :return:
    """
    log.info('[mon.create_linkerd_viz_ns]')
    ns = Namespace(
        f'linkerd-viz{DEPLOY_NAME_PREFIX}',
        metadata={
            'name': 'linkerd-viz',
        },
    )
    return ns


def create_linkerd_crds(
        provider,
        namespace,
):
    """
    :param provider:
    :param namespace:
    :return:
    """
    log.info('[mon.create_linkerd_crds]')
    helm = kubernetes.helm.v3.Release(
        f"linkerd-crds{DEPLOY_NAME_PREFIX}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="linkerd-crds",
            version="1.8.0",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://helm.linkerd.io/stable",
            ),
            namespace=namespace.metadata.name,
            create_namespace=False,
            values={
                "logLevel": "debug",
                "replicaCount": "1",
                "region": REGION,
            },
        ),
        pulumi.ResourceOptions(
            provider=provider,
        )
    )
    return helm


def create_linkerd_control_plane(
        provider,
        namespace,
):
    log.info('[mon.create_linkerd_control_plane]')
    cm = kubernetes.core.v1.ConfigMap(
        f"linkerd-identity-trust-roots{DEPLOY_NAME_PREFIX}",
        metadata={
            'namespace': namespace.metadata.name,
            'name': 'linkerd-identity-trust-roots'
        },
        data={
            'ca-bundle.crt': read_file(ca)
        },
        opts=pulumi.ResourceOptions(provider=provider))
    secret = kubernetes.core.v1.Secret(
        f"linkerd-identity-issuer{DEPLOY_NAME_PREFIX}",
        metadata={
            'namespace': namespace.metadata.name,
            'name': 'linkerd-identity-issuer',
        },
        string_data={
            'tls.crt': read_file(crt),
            'tls.key': read_file(key),
            'ca.crt': read_file(ca),
        },
        type='kubernetes.io/tls',
        opts=pulumi.ResourceOptions(provider=provider)
    )
    helm = kubernetes.helm.v3.Release(
        f"linkerd-control-plane{DEPLOY_NAME_PREFIX}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="linkerd-control-plane",
            version="1.15.0",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://helm.linkerd.io/stable",
            ),
            namespace=namespace.metadata.name,
            values={
                "logLevel": "debug",
                "replicaCount": "1",
                "region": REGION,
                "identity": {
                    "externalCA": True,
                    "issuer": {
                        "scheme": "kubernetes.io/tls"
                    }
                },
                "clusterNetworks": "10.0.0.0/8,11.0.0.0/8,12.0.0.0/8",
                "identityTrustAnchorsPEM": "ca.crt",

            },
        ),
        pulumi.ResourceOptions(
            provider=provider,
            depends_on=[cm, secret]
        )
    )


def create_linkerd_viz(
        provider, namespace
):
    helm = kubernetes.helm.v3.Release(
        f"linkerd-viz{DEPLOY_NAME_PREFIX}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="linkerd-viz",
            version="30.11.0",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://helm.linkerd.io/stable",
            ),
            namespace=namespace.metadata.name,
            values={
                "logLevel": "debug",
                "replicaCount": "1",
                "region": REGION,
            },
        ),
        pulumi.ResourceOptions(
            provider=provider,
        )
    )


def linkerd_setup(provider):
    """
    :param provider:
    :return:
    """
    log.info('[mon.mon_setup]')
    namespace = create_linkerd_ns()
    create_linkerd_crds(
        provider=provider,
        namespace=namespace
    )
    create_linkerd_control_plane(
        provider,
        namespace,
    )
    namespace = create_linkerd_viz_ns()
    create_linkerd_viz(
        provider=provider,
        namespace=namespace
    )
