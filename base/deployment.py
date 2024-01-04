import pulumi
import pulumi_kubernetes as kubernetes
from pulumi import log

from base.utils import dict_to_k8n_env_var_args


def create_deployment(
        provider,
        image_url,
        image_tag,
        env,
        metadata,
        app_name,
        app_labels,
        ports=None,
        init_script: list = None,
        n_replicas=1,
        command=None,
        health_check=False,
):
    """
    :param provider:
    :param image_url: Url of image
    :param image_tag:
    :param env: The key,value of environment values
    :param metadata:
    :param app_name:
    :param app_labels:
    :param ports: list of (port, port_name) tuples for exposed ports
    :param init_script:
    :param n_replicas:
    :param command:
    :param health_check:
    :return:
    """
    # @note: Set default container port
    log.info('[base.deployment.create_deployment] '
             f'app_name:{app_name}')
    if ports is None:
        ports = [(80, 'http')]
    container_port_args = [kubernetes.core.v1.ContainerPortArgs(
        name=port_name,
        container_port=int(port),
    ) for (port, port_name) in ports]
    init_containers = [kubernetes.core.v1.ContainerArgs(
        name=f'{app_name}-init-{index}',
        image=f"{image_url}:{image_tag}" if type(image_url) == str else image_url.apply(
            lambda value: f"{value}:{image_tag}"),
        image_pull_policy='Always',
        ports=container_port_args,
        env=dict_to_k8n_env_var_args(env),
        command=["/bin/sh", "-c", script],
    ) for index, script in enumerate(init_script)] if init_script else None
    liveness_probe = kubernetes.core.v1.ProbeArgs(
        http_get=kubernetes.core.v1.HTTPGetActionArgs(
            path="/healthz",
            port=ports[0][0],
        ),
        initial_delay_seconds=5,
        period_seconds=5
    ) if health_check else None
    container = kubernetes.core.v1.ContainerArgs(
        name=app_name,
        image=f"{image_url}:{image_tag}" if type(image_url) == str else image_url.apply(
            lambda value: f"{value}:{image_tag}"),
        image_pull_policy='Always',
        ports=container_port_args,
        env=dict_to_k8n_env_var_args(env),
        command=command,
        liveness_probe=liveness_probe,
    )
    topology_spread_constraints = kubernetes.core.v1.TopologySpreadConstraintArgs(
        max_skew=1,
        topology_key='kubernetes.io/hostname',
        when_unsatisfiable='DoNotSchedule',
        label_selector=kubernetes.meta.v1.LabelSelectorArgs(
            match_labels=app_labels,
        ),
    )

    dep = kubernetes.apps.v1.Deployment(
        app_name,
        metadata=metadata,
        spec=kubernetes.apps.v1.DeploymentSpecArgs(
            replicas=n_replicas,
            selector=kubernetes.meta.v1.LabelSelectorArgs(
                match_labels=app_labels,
            ),
            template=kubernetes.core.v1.PodTemplateSpecArgs(
                metadata=metadata,
                spec=kubernetes.core.v1.PodSpecArgs(
                    containers=[container],
                    init_containers=init_containers,
                    topology_spread_constraints=[topology_spread_constraints]
                ),
            ),
        ),
        opts=pulumi.ResourceOptions(provider=provider),
    )
    log.info('[base.deployment.create_deployment] dep created')
    return dep
