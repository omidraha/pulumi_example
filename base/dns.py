import os

import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log

from base.const import DEPLOY_NAME_PREFIX, REGION


def create_external_dns(
        namespace,
        provider
):
    """
    :param namespace:
    :param provider:
    :return:
    """
    log.info('[base.dns.create_external_dns]')
    external_dns = kubernetes.helm.v3.Release(
        f"external-dns{DEPLOY_NAME_PREFIX}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="external-dns",
            version="6.20.4",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://charts.bitnami.com/bitnami"
            ),
            namespace=namespace.metadata.name,
            values={
                "logLevel": "debug",
                'provider': 'cloudflare',
                'sources': ['ingress'],
                'domainFilters': ['example.com', ],
                "cloudflare": {
                    "email": os.environ.get('CLOUDFLARE_EMAIL'),
                    "apiToken": os.environ.get('CLOUDFLARE_API_TOKEN'),
                    'cloudflare-dns-records-per-page': '5000',
                    'proxied': False,
                },
                "replicaCount": "1",
                "region": REGION,
            },
        ),
        pulumi.ResourceOptions(
            provider=provider,
            parent=namespace,
            depends_on=[namespace]
        ),
    )
    return external_dns
