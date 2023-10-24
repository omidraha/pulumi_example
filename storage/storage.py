import pulumi_kubernetes as kubernetes
from pulumi import ResourceOptions

from base.const import DEPLOY_NAME_PREFIX


def create_sc(
        namespace,
        allow_volume_expansion=None,
        parameters=None,
        provisioner=None,
):
    """
    :param namespace:
    :param allow_volume_expansion:
    :param provisioner:
    :param parameters:
    :return:
    options:
        volume_binding_mode:
            WaitForFirstConsumer
            Immediate
    """
    storage_class = kubernetes.storage.v1.StorageClass(
        f"sc{DEPLOY_NAME_PREFIX}",
        metadata={
            'namespace': namespace.metadata.name,
        },
        # provisioner="kubernetes.io/no-provisioner",
        provisioner=provisioner,
        allow_volume_expansion=allow_volume_expansion,
        volume_binding_mode="Immediate",
        parameters=parameters,
    )
    return storage_class


def create_pv_sc(namespace, sc):
    """
    :param namespace:
    :param sc:
    :return:
    options:
        access_modes:
            ReadWriteOnce
            ReadWriteMany
    """
    pv = kubernetes.core.v1.PersistentVolume(
        f'pv{DEPLOY_NAME_PREFIX}',
        metadata={
            'namespace': namespace.metadata.name,
            'labels': {
                'name': 'storage-data',
            }
        },
        spec={
            'access_modes': ["ReadWriteOnce"],
            'persistent_volume_reclaim_policy': 'Retain',
            'capacity': {
                "storage": "10Gi"
            },
            'host_path': {
                'path': "/home/ws/storage",
                'type': "DirectoryOrCreate"
            },
            'storage_class_name': sc.metadata.name,
        },
        opts=ResourceOptions(depends_on=[sc]),
    )
    return pv


def create_pvc(namespace, sc):
    """
    :param namespace:
    :param sc:
    :return:
    """
    return kubernetes.core.v1.PersistentVolumeClaim(
        f'pvc{DEPLOY_NAME_PREFIX}',
        metadata={
            'namespace': namespace.metadata.name,
        },
        spec={
            "access_modes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": "2Gi"
                }
            },
            # "selector": {
            #     "match_labels": {
            #         "name": "storage-data"
            #     }
            # },
            'storage_class_name': sc.metadata.name,
        },
        opts=ResourceOptions(depends_on=[sc]),
    )
