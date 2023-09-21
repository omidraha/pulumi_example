from pulumi_kubernetes.core.v1 import Namespace, Service, ServiceAccount
from pulumi_kubernetes.apps.v1 import Deployment


def create_app():
    # Create a namespace
    namespace = Namespace(
        "emojivoto",
        metadata={
            "name": "emojivoto",
        }
    )

    # Create the service accounts
    emoji_sa = ServiceAccount(
        "emoji",
        metadata={"namespace": namespace.metadata["name"]}
    )
    voting_sa = ServiceAccount(
        "voting",
        metadata={"namespace": namespace.metadata["name"]}
    )
    web_sa = ServiceAccount(
        "web",
        metadata={"namespace": namespace.metadata["name"]}
    )

    # Services
    emoji_svc = Service(
        "emoji-svc",
        metadata={
            "name": "emoji-svc",
            "namespace": namespace.metadata["name"],
        },
        spec={
            "ports": [
                {"name": "grpc", "port": 8080, "targetPort": 8080},
                {"name": "prom", "port": 8801, "targetPort": 8801},
            ],
            "selector": {"app": "emoji-svc"}  # should point to the `emoji` app
        }
    )
    voting_svc = Service(
        "voting-svc",
        metadata={
            "name": "voting-svc",
            "namespace": namespace.metadata["name"],

        },
        spec={
            "ports": [
                {"name": "grpc", "port": 8080, "targetPort": 8080},
                {"name": "prom", "port": 8801, "targetPort": 8801},
            ],
            "selector": {"app": "voting-svc"}  # should point to the `voting` app
        }
    )

    web_svc = Service(
        "web-svc",
        metadata={
            "name": "web-svc",
            "namespace": namespace.metadata["name"],
        },
        spec={
            "ports": [
                {"name": "http", "port": 80, "targetPort": 8080},
            ],
            "selector": {"app": "web-svc"},  # should point to the `web` app
            "type": "ClusterIP"
        }
    )

    # Create the Emoji deployment
    emoji_deployment = Deployment(
        "emoji",
        metadata={
            "labels": {
                "app.kubernetes.io/name": "emoji",
                "app.kubernetes.io/part-of": "emojivoto",
                "app.kubernetes.io/version": "v11"
            },
            "namespace": namespace.metadata["name"],
        },
        spec={
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "emoji-svc",
                    "version": "v11",
                },
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "emoji-svc",
                        "version": "v11",
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "emoji-svc",
                            "image": "docker.l5d.io/buoyantio/emojivoto-emoji-svc:v11",
                            "ports": [
                                {"containerPort": 8080, "name": "grpc"},
                                {"containerPort": 8801, "name": "prom"},
                            ],
                            "env": [
                                {"name": "GRPC_PORT", "value": "8080"},
                                {"name": "PROM_PORT", "value": "8801"},
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": "100m"
                                }
                            }
                        },
                    ],
                },
            },
        },
    )

    vote_bot_deployment = Deployment(
        "vote-bot",
        metadata={
            "labels": {
                "app.kubernetes.io/name": "emoji",
                "app.kubernetes.io/part-of": "emojivoto",
                "app.kubernetes.io/version": "v11"
            },
            "namespace": namespace.metadata["name"],
        },
        spec={
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "vote-bot",
                    "version": "v11",
                },
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "vote-bot",
                        "version": "v11",
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "vote-bot",
                            "image": "docker.l5d.io/buoyantio/emojivoto-web:v11",
                            "env": [
                                {"name": "WEB_HOST", "value": "web-svc.emojivoto:80"},
                            ],
                            "command": ["emojivoto-vote-bot"],
                            "resources": {
                                "requests": {
                                    "cpu": "100m"
                                }
                            }
                        },
                    ],
                    "serviceAccountName": voting_sa.metadata["name"],
                },
            },
        },
    )

    voting_deployment = Deployment(
        "voting",
        metadata={
            "labels": {
                "app.kubernetes.io/name": "voting",
                "app.kubernetes.io/part-of": "emojivoto",
                "app.kubernetes.io/version": "v11"
            },
            "namespace": namespace.metadata["name"],
        },
        spec={
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "voting-svc",
                    "version": "v11",
                },
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "voting-svc",
                        "version": "v11",
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "voting-svc",
                            "image": "docker.l5d.io/buoyantio/emojivoto-voting-svc:v11",
                            "ports": [
                                {"containerPort": 8080, "name": "grpc"},
                                {"containerPort": 8801, "name": "prom"},
                            ],
                            "env": [
                                {"name": "GRPC_PORT", "value": "8080"},
                                {"name": "PROM_PORT", "value": "8801"},
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": "100m"
                                }
                            }
                        },
                    ],
                    "serviceAccountName": emoji_sa.metadata["name"],
                },
            },
        },
    )

    web_deployment = Deployment(
        "web",
        metadata={
            "labels": {
                "app.kubernetes.io/name": "web",
                "app.kubernetes.io/part-of": "emojivoto",
                "app.kubernetes.io/version": "v11"
            },
            "namespace": namespace.metadata["name"],
        },
        spec={
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "web-svc",
                    "version": "v11",
                },
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "web-svc",
                        "version": "v11",
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "web-svc",
                            "image": "docker.l5d.io/buoyantio/emojivoto-web:v11",
                            "ports": [
                                {"containerPort": 8080, "name": "http"},
                            ],
                            "env": [
                                {"name": "WEB_PORT", "value": "8080"},
                                {"name": "EMOJISVC_HOST", "value": "emoji-svc.emojivoto:8080"},
                                {"name": "VOTINGSVC_HOST", "value": "voting-svc.emojivoto:8080"},
                                {"name": "INDEX_BUNDLE", "value": "dist/index_bundle.js"},
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": "100m"
                                }
                            }
                        },
                    ],
                    "serviceAccountName": web_sa.metadata["name"],
                },
            },
        },
    )
