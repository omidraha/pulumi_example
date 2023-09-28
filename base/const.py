import os
from pathlib import Path

DEP_MODE = 'exp'
DEPLOY_NAME_PREFIX = '-exp'

CLUSTER_NAME = "cluster"
CLUSTER_TAG = "kubernetes.io/cluster/example"
NAMESPACE_NAME = 'exp'

AVAILABILITY_ZONE_NAMES = [
    'us-west-2a',
    'us-west-2b',
]

DOMAINS = ['log.example.com']

ANNOTATIONS = {
    "kubernetes.io/ingress.class": "alb",
    "alb.ingress.kubernetes.io/target-type": "ip",
    "alb.ingress.kubernetes.io/scheme": "internet-facing",
    'external-dns.alpha.kubernetes.io/hostname': ','.join(DOMAINS),
    'alb.ingress.kubernetes.io/listen-ports': '[{"HTTPS":443}, {"HTTP":80}]',
    'alb.ingress.kubernetes.io/ssl-redirect': '443',
    'alb.ingress.kubernetes.io/load-balancer-attributes': 'idle_timeout.timeout_seconds=600',
    'alb.ingress.kubernetes.io/target-group-attributes':
        'stickiness.enabled=true,stickiness.lb_cookie.duration_seconds=60',
    'alb.ingress.kubernetes.io/group.name': 'ingress',
}

REGION = "us-west-2"

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

BASE_PATH = (str(Path(__file__).resolve().parent.parent))
NODE_AMI_ID = "ami-0bce9ab1f1be3282a"
