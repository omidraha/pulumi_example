import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log

from base.const import DEPLOY_NAME_PREFIX


def create_ingress_nginx(
        namespace,
        provider,
        values=None,
):
    """
    @see: https://kubernetes.github.io/ingress-nginx/developer-guide/code-overview/#helm-chart
    @see: https://github.com/kubernetes/ingress-nginx/tree/main/charts/ingress-nginx
    @sse: https://github.com/kubernetes/ingress-nginx/blob/main/charts/ingress-nginx/values.yaml
    :return:
    """
    log.info('[devops_sdk.ingress.create_ingress_nginx]')
    chart = kubernetes.helm.v3.Release(
        f"ingress-nginx{DEPLOY_NAME_PREFIX}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="ingress-nginx",
            version="4.8.3",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://kubernetes.github.io/ingress-nginx"
            ),
            namespace=namespace.metadata.name,
            values=values or {
                "logLevel": "debug",
                "replicaCount": "1",
                "controller": {
                    "kind": "DaemonSet",
                    "service": {
                        "type": "NodePort"
                    },
                    "dnsPolicy": "ClusterFirstWithHostNet",
                    "hostNetwork": "true",
                    # @see: https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/#allow-snippet-annotations
                    # @see: https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/#server-snippet
                    "allowSnippetAnnotations": True,
                },
            },
        ),
        opts=provider and pulumi.ResourceOptions(
            provider=provider,
            parent=namespace
        )
    )
    return chart


def create_ingress_mixed(
        namespace,
        provider,
        services,
        annotations,
        name_prefix,
        domains,
        ingress_class_name,
        ingress_secret_name,
        ingress_domains_tls,
):
    """
    :param namespace:
    :param provider:
    :param services: list of service
    :param annotations:
    :param name_prefix:
    :param domains: list of domains
    :param ingress_class_name:
    :param ingress_secret_name:
    :param ingress_domains_tls:
    :return:
    @note: services and domains SHOULD correspond.:
        services = [app1.src, app2.src]
        domains = [app1.domain, app2.domain]
    """
    log.info(f'[devops_sdk.ingress.create_ingress_mixed] ingress_domains_tls:{ingress_domains_tls}')

    name = f"ingress{name_prefix}"
    rules = []
    for index, service in enumerate(services):
        if isinstance(service, list):
            service_name = service[0]
            service_port = service[1]
        else:
            service_name = service.metadata.name
            service_port = service.spec.apply(lambda spec: spec.ports[0].port if spec and spec.ports else None)

        ingress_path_args = kubernetes.networking.v1.HTTPIngressPathArgs(
            path="/",
            path_type="Prefix",
            backend=kubernetes.networking.v1.IngressBackendArgs(
                service=kubernetes.networking.v1.IngressServiceBackendArgs(
                    name=service_name,
                    port=kubernetes.networking.v1.ServiceBackendPortArgs(
                        number=service_port,
                    ),
                ),
            ),
        )
        for domain in domains[index]:
            rules_item = [kubernetes.networking.v1.IngressRuleArgs(
                host=domain,
                http=kubernetes.networking.v1.HTTPIngressRuleValueArgs(
                    paths=[ingress_path_args],
                ),
            )]
            rules.extend(rules_item)

    ingress = kubernetes.networking.v1.Ingress(
        name,
        metadata=kubernetes.meta.v1.ObjectMetaArgs(
            namespace=namespace.metadata.name,
            annotations=annotations,
            labels={
                'app': name,
            },
        ),
        spec=kubernetes.networking.v1.IngressSpecArgs(
            rules=rules,
            ingress_class_name=ingress_class_name,
            tls=ingress_secret_name and [kubernetes.networking.v1.IngressTLSArgs(
                secret_name=ingress_secret_name,
                hosts=ingress_domains_tls,
            )],
        ),
        opts=pulumi.ResourceOptions(provider=provider)
    )
    log.info('[devops_sdk.ingress.create_ingress] ingress created')
    return ingress
