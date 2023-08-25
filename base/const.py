CLUSTER_NAME = "example"
CLUSTER_TAG = "kubernetes.io/cluster/example"
DEPLOY_NAME_PREFIX = 'st'
AVAILABILITY_ZONE_NAMES = [
    'us-west-2a',
    'us-west-2b',
    'us-west-2c'
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