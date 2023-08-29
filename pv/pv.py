import pulumi_kubernetes as kubernetes


def create_pv(namespace):
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
            'storage_class_name': "storage-base"
        },

    )
    return pv


def create_pvc(namespace):
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
            "volume_name": namespace.metadata.name,
            "storageClassName": "storage-base"
        }
    )
