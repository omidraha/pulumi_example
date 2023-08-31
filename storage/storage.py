import pulumi_kubernetes as kubernetes
from pulumi import ResourceOptions


def create_sc(namespace):
    """
    :param namespace:
    :return:
    options:
        volume_binding_mode:
            WaitForFirstConsumer
            Immediate
    """
    storage_class = kubernetes.storage.v1.StorageClass(
        "sc",
        metadata={
            'namespace': namespace.metadata.name,
        },
        provisioner="kubernetes.io/no-provisioner",
        volume_binding_mode="Immediate",
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
        'pv',
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
    return kubernetes.core.v1.PersistentVolumeClaim(
        'pvc',
        metadata={
            'namespace': namespace.metadata.name,
        },
        spec={
            "access_modes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": "5Gi"
                }
            },
            "selector": {
                "match_labels": {
                    "name": "storage-data"
                }
            },
            'storage_class_name': sc.metadata.name,
        },
        opts=ResourceOptions(depends_on=[sc]),
    )
