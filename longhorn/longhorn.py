import pulumi
from pulumi_kubernetes.apps.v1 import DaemonSet, DaemonSetSpecArgs, DaemonSetUpdateStrategyArgs
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.core.v1 import PodTemplateSpecArgs, PodSpecArgs, ContainerArgs, SecurityContextArgs
from pulumi_kubernetes.core.v1 import Namespace
import pulumi_kubernetes as kubernetes

from base.const import DEPLOY_NAME_PREFIX, REGION

iscsi_cmd = """
OS=$(grep -E "^ID_LIKE=" /etc/os-release | cut -d '=' -f 2); 
if [[ -z "${OS}" ]]; then OS=$(grep -E "^ID=" /etc/os-release | cut -d '=' -f 2); fi; 
if [[ "${OS}" == *"debian"* ]]; then 
    sudo apt-get update -q -y && sudo apt-get install -q -y open-iscsi && sudo systemctl -q enable iscsid && sudo systemctl start iscsid && sudo modprobe iscsi_tcp; 
elif [[ "${OS}" == *"suse"* ]]; then 
    sudo zypper --gpg-auto-import-keys -q refresh && sudo zypper --gpg-auto-import-keys -q install -y open-iscsi && sudo systemctl -q enable iscsid && sudo systemctl start iscsid && sudo modprobe iscsi_tcp; 
else 
    sudo yum makecache -q -y && sudo yum --setopt=tsflags=noscripts install -q -y iscsi-initiator-utils && echo "InitiatorName=$(/sbin/iscsi-iname)" > /etc/iscsi/initiatorname.iscsi && sudo systemctl -q enable iscsid && sudo systemctl start iscsid && sudo modprobe iscsi_tcp; 
fi && 
if [ $? -eq 0 ]; then echo "iscsi install successfully"; else echo "iscsi install failed error code $?"; fi
"""

nfs_cmd = """
OS=$(grep -E "^ID_LIKE=" /etc/os-release | cut -d '=' -f 2);
if [[ -z "${OS}" ]]; then OS=$(grep -E "^ID=" /etc/os-release | cut -d '=' -f 2); fi;
if [[ "${OS}" == *"debian"* ]]; then
    sudo apt-get update -q -y && sudo apt-get install -q -y nfs-common && sudo modprobe nfs;
elif [[ "${OS}" == *"suse"* ]]; then
    sudo zypper --gpg-auto-import-keys -q refresh && sudo zypper --gpg-auto-import-keys -q install -y nfs-client && sudo modprobe nfs;
else
    sudo yum makecache -q -y && sudo yum --setopt=tsflags=noscripts install -q -y nfs-utils && sudo modprobe nfs;
fi &&
if [ $? -eq 0 ]; then echo "nfs install successfully"; else echo "nfs install failed error code $?"; fi
"""


def create_longhorn_iscsi():
    longhorn_iscsi_installation = DaemonSet(
        f"longhorn-iscsi{DEPLOY_NAME_PREFIX}",
        metadata={
            "labels": {
                "app": "longhorn-iscsi-installation",
            },
            "annotations": {
                "command": iscsi_cmd,
            },
        },
        spec=DaemonSetSpecArgs(
            selector=LabelSelectorArgs(
                match_labels={
                    "app": "longhorn-iscsi-installation"
                }),
            template=PodTemplateSpecArgs(
                metadata=ObjectMetaArgs(
                    labels={
                        "app": "longhorn-iscsi-installation"
                    }
                ),
                spec=PodSpecArgs(
                    host_network=True,
                    host_pid=True,
                    init_containers=[
                        ContainerArgs(
                            name="iscsi-installation",
                            command=["nsenter", "--mount=/proc/1/ns/mnt", "--", "bash",
                                     "-c", iscsi_cmd],
                            image="alpine:3.17",
                            security_context=SecurityContextArgs(privileged=True),
                        )
                    ],
                    containers=[
                        ContainerArgs(
                            name="sleep",
                            image="registry.k8s.io/pause:3.1"
                        )
                    ]
                ),
            ),
            update_strategy=DaemonSetUpdateStrategyArgs(type="RollingUpdate"),
        ),
    )


def create_longhorn_nfs():
    longhorn_nfs_installation = DaemonSet(
        f"longhorn-nfs{DEPLOY_NAME_PREFIX}",
        metadata=ObjectMetaArgs(
            name="longhorn-nfs-installation",
            labels={
                "app": "longhorn-nfs-installation",
            },
            annotations={
                "command": nfs_cmd,
            }),
        spec=DaemonSetSpecArgs(
            selector=LabelSelectorArgs(match_labels={"app": "longhorn-nfs-installation"}),
            template=PodTemplateSpecArgs(
                metadata=ObjectMetaArgs(
                    labels={"app": "longhorn-nfs-installation"}
                ),
                spec=PodSpecArgs(
                    host_network=True,
                    host_pid=True,
                    init_containers=[
                        ContainerArgs(
                            name="nfs-installation",
                            command=["nsenter", "--mount=/proc/1/ns/mnt", "--", "bash",
                                     "-c", nfs_cmd],
                            image="alpine:3.12",
                            security_context=SecurityContextArgs(privileged=True),
                        )
                    ],
                    containers=[
                        ContainerArgs(
                            name="sleep",
                            image="registry.k8s.io/pause:3.1"
                        )
                    ],
                ),
            ),
            update_strategy=DaemonSetUpdateStrategyArgs(type="RollingUpdate"),
        ),

    )


def create_longhorn(
        provider,
        replica,
):
    """
    :param provider:
    :param replica:
    :return:

    """
    namespace = Namespace(
        f"longhorn-system{DEPLOY_NAME_PREFIX}",
        metadata={"name": "longhorn-system"},
        opts=pulumi.ResourceOptions(provider=provider)
    )
    chart = kubernetes.helm.v3.Release(
        f"longhorn{DEPLOY_NAME_PREFIX}",
        kubernetes.helm.v3.ReleaseArgs(
            chart="longhorn",
            version="1.5.1",
            repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
                repo="https://charts.longhorn.io"
            ),
            namespace=namespace.metadata.name,
            values={
                "logLevel": "debug",
                "region": REGION,
                "persistence": {
                    "defaultClassReplicaCount": replica,
                    "defaultNodeSelector": {
                        "tier": "log"
                    },
                },
                'defaultSettings': {
                    'systemManagedComponentsNodeSelector': {
                        "tier": "log"
                    }
                },
                'longhornManager': {
                    'nodeSelector': {
                        "tier": "log"
                    }
                },
                'longhornUI': {
                    'nodeSelector': {
                        "tier": "log"
                    }
                },
                'longhornDriver': {
                    'nodeSelector': {
                        "tier": "log"
                    }
                },
            },
        ),
        pulumi.ResourceOptions(
            provider=provider,
            parent=namespace
        )
    )


def setup(provider):
    """
    :param provider:
    :return:
    """
    create_longhorn_iscsi()
    create_longhorn_nfs()
    create_longhorn(
        provider=provider,
        replica=3
    )
