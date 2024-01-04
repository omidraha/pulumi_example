import os

import pulumi_kubernetes
from pulumi import log
import pulumi
from pulumi_kubernetes.apiextensions import CustomResource

from base.cert_manager import create_cert_manager
from base.const import DEP_MODE, NAMESPACE_NAME, DEPLOY_NAME_PREFIX, REGION
from base.dns import create_external_dns
from base.ingress import create_ingress_nginx
from base.lb import create_metal_lb
from base.namespace import create_namespace
from base.secret import create_secret


class Setup:
    def __init__(
            self,
    ):
        self.namespace = None
        self.env = None
        self.docker_image_registry = None
        self.provider = None
        self.ingress_tls = None
        self.issuer_name = None

    def up(self):
        log.info('[lib.base.Setup.up]')
        log.info(f'[lib.base.Setup.up] DEP_MODE: {DEP_MODE}')
        self.namespace = create_namespace(
            None, NAMESPACE_NAME, labels=None
        )
        create_external_dns(
            namespace=self.namespace,
            provider=self.provider
        )

        cert_ns = create_namespace(
            None, 'cert-manager',
            labels=None
        )

        cert = create_cert_manager(
            namespace=cert_ns,
            provider=self.provider,
            name_prefix=DEPLOY_NAME_PREFIX,
            region=REGION,
        )

        secret = create_secret(
            res_secret_name=f'cert-manager-secret{DEPLOY_NAME_PREFIX}',
            data=None,
            string_data={
                "api-token": os.environ.get('CLOUDFLARE_API_TOKEN'),
            },
            namespace=cert_ns,
        )

        self.issuer_name = f'cert-manager-cluster-issuer{DEPLOY_NAME_PREFIX}'
        issuer = CustomResource(
            self.issuer_name,
            api_version='cert-manager.io/v1',
            kind='ClusterIssuer',
            metadata={
                'name': self.issuer_name,
                'namespace': cert_ns.metadata.name,
            },
            spec={
                'acme': {
                    'email': 'email@example.com',
                    'server': 'https://acme-staging-v02.api.letsencrypt.org/directory',
                    'privateKeySecretRef': {
                        'name': f'cert-manager-cluster-issuer-secret{DEPLOY_NAME_PREFIX}'
                    },
                    'solvers': [{
                        'dns01': {
                            'cloudflare': {
                                'apiTokenSecretRef': {
                                    'name': secret.metadata.name,
                                    'key': 'api-token'
                                }
                            }
                        }
                    }]
                }
            },
            opts=pulumi.ResourceOptions(
                provider=self.provider,
                depends_on=[cert_ns, secret, cert]
            )
        )

        metallb_ns = create_namespace(
            None, 'metallb-system',
            labels=None
        )

        metal_lb = create_metal_lb(
            provider=None,
            namespace=metallb_ns,
        )

        metallb_ip_address_pool = pulumi_kubernetes.apiextensions.CustomResource(
            f"metallb-ip-address-pool{DEPLOY_NAME_PREFIX}",
            api_version="metallb.io/v1beta1",
            kind="IPAddressPool",
            metadata={
                "name": f"metallb-ip-address-pool{DEPLOY_NAME_PREFIX}",
                "namespace": metallb_ns.metadata.name
            },
            spec={
                "addresses": [
                    "3.3.3.3/32",
                ]
            },
            opts=pulumi.ResourceOptions(
                provider=self.provider,
                depends_on=[metallb_ns, metal_lb]
            )
        )
        metallb_l2_advertisement = pulumi_kubernetes.apiextensions.CustomResource(
            f"metallb-l2-advertisement{DEPLOY_NAME_PREFIX}",
            api_version="metallb.io/v1beta1",
            kind="L2Advertisement",
            metadata={
                "name": f"metallb-l2-advertisement{DEPLOY_NAME_PREFIX}",
                "namespace": metallb_ns.metadata.name
            },
            spec={
                "ipAddressPools": [
                    f"metallb-ip-address-pool{DEPLOY_NAME_PREFIX}"
                ]
            },
            opts=pulumi.ResourceOptions(
                provider=self.provider,
                depends_on=[metallb_ip_address_pool]
            )
        )

        create_ingress_nginx(
            provider=None,
            namespace=self.namespace,
            values={
                "logLevel": "debug",
                "replicaCount": "1",
                "controller": {
                    "kind": "DaemonSet",
                },
            },
        )
