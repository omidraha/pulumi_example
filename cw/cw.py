import json

import pulumi
from pulumi import log
import pulumi_aws
from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.core.v1 import ServiceAccount
from pulumi_kubernetes.core.v1.outputs import PodTemplateSpec, Container, PodSpec, EnvVar, EnvVarSource, \
    ConfigMapKeySelector, ResourceRequirements, VolumeMount, Volume, HostPathVolumeSource, ObjectFieldSelector, \
    Toleration, ConfigMapVolumeSource
from pulumi_kubernetes.meta.v1.outputs import LabelSelector, ObjectMeta
from pulumi_kubernetes.rbac.v1 import ClusterRole
from pulumi_kubernetes.rbac.v1 import ClusterRoleBinding
from pulumi_kubernetes.core.v1 import ConfigMap
from pulumi_kubernetes.apps.v1 import DaemonSet

from base.const import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DEP_MODE, REGION

"""
    @see:
        https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-setup-logs-FluentBit.html
        https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-setup-EKS-quickstart.html
        https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-prerequisites.html
        https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/fluent-bit/fluent-bit.yaml
"""
# fluent-bit.conf
fluent_bit_conf = """
[SERVICE]
    Flush             5
    Grace             30
    Log_Level         info
    Daemon            off
    Parsers_File          parsers.conf
    HTTP_Server           ${HTTP_SERVER}
    HTTP_Listen           0.0.0.0
    HTTP_Port         ${HTTP_PORT}
    storage.path          /var/fluent-bit/state/flb-storage/
    storage.sync          normal
    storage.checksum      off
    storage.backlog.mem_limit 5M
@INCLUDE application-log.conf
@INCLUDE dataplane-log.conf
@INCLUDE host-log.conf
"""
# application-log.conf
application_log_conf = """
[INPUT]
    Name        tail
    Tag         application.*
    Exclude_Path    /var/log/containers/cloudwatch-agent*, /var/log/containers/fluent-bit*, /var/log/containers/aws-node*, /var/log/containers/kube-proxy*
    Path        /var/log/containers/*.log
    multiline.parser    docker, cri
    DB          /var/fluent-bit/state/flb_container.db
    Mem_Buf_Limit       50MB
    Skip_Long_Lines     On
    Refresh_Interval    10
    Rotate_Wait     30
    storage.type    filesystem
    Read_from_Head      ${READ_FROM_HEAD}
[INPUT]
    Name        tail
    Tag         application.*
    Path        /var/log/containers/cloudwatch-agent*
    multiline.parser    docker, cri
    DB          /var/fluent-bit/state/flb_cwagent.db
    Mem_Buf_Limit       5MB
    Skip_Long_Lines     On
    Refresh_Interval    10
    Read_from_Head      ${READ_FROM_HEAD}
[FILTER]
    Name        kubernetes
    Match           application.*
    Kube_URL        https://kubernetes.default.svc:443
    Kube_Tag_Prefix     application.var.log.containers.
    Merge_Log       On
    Merge_Log_Key       log_processed
    K8S-Logging.Parser  On
    K8S-Logging.Exclude Off
    Labels          Off
    Annotations     Off
    Use_Kubelet     On
    Kubelet_Port    10250
    Buffer_Size     0
[OUTPUT]
    Name        cloudwatch_logs
    Match           application.*
    region          ${AWS_REGION}
    log_group_name      /${CLUSTER_NAME}/application
    log_stream_prefix   log-
    auto_create_group   true
    extra_user_agent    container-insights
"""

# dataplane-log.conf
dataplane_log_conf = """
[INPUT]
    Name        systemd
    Tag         dataplane.systemd.*
    Systemd_Filter      _SYSTEMD_UNIT=docker.service
    Systemd_Filter      _SYSTEMD_UNIT=containerd.service
    Systemd_Filter      _SYSTEMD_UNIT=kubelet.service
    DB          /var/fluent-bit/state/systemd.db
    Path        /var/log/journal
    Read_From_Tail      ${READ_FROM_TAIL}
[INPUT]
    Name        tail
    Tag         dataplane.tail.*
    Path        /var/log/containers/aws-node*, /var/log/containers/kube-proxy*
    multiline.parser    docker, cri
    DB          /var/fluent-bit/state/flb_dataplane_tail.db
    Mem_Buf_Limit       50MB
    Skip_Long_Lines     On
    Refresh_Interval    10
    Rotate_Wait     30
    storage.type    filesystem
    Read_from_Head      ${READ_FROM_HEAD}
[FILTER]
    Name        modify
    Match           dataplane.systemd.*
    Rename          _HOSTNAME           hostname
    Rename          _SYSTEMD_UNIT           systemd_unit
    Rename          MESSAGE             message
    Remove_regex    ^((?!hostname|systemd_unit|message).)*$
[FILTER]
    Name        aws
    Match           dataplane.*
    imds_version    v1
[OUTPUT]
    Name        cloudwatch_logs
    Match           dataplane.*
    region          ${AWS_REGION}
    log_group_name      /${CLUSTER_NAME}/dataplane
    log_stream_prefix   log-
    auto_create_group   true
    extra_user_agent    container-insights
"""
# host-log.conf
host_log_conf = """
[INPUT]
    Name        tail
    Tag         host.dmesg
    Path        /var/log/dmesg
    Key         message
    DB          /var/fluent-bit/state/flb_dmesg.db
    Mem_Buf_Limit       5MB
    Skip_Long_Lines     On
    Refresh_Interval    10
    Read_from_Head      ${READ_FROM_HEAD}
[INPUT]
    Name        tail
    Tag         host.messages
    Path        /var/log/messages
    Parser          syslog
    DB          /var/fluent-bit/state/flb_messages.db
    Mem_Buf_Limit       5MB
    Skip_Long_Lines     On
    Refresh_Interval    10
    Read_from_Head      ${READ_FROM_HEAD}
[INPUT]
    Name        tail
    Tag         host.secure
    Path        /var/log/secure
    Parser          syslog
    DB          /var/fluent-bit/state/flb_secure.db
    Mem_Buf_Limit       5MB
    Skip_Long_Lines     On
    Refresh_Interval    10
    Read_from_Head      ${READ_FROM_HEAD}
[FILTER]
    Name        aws
    Match           host.*
    imds_version    v1
[OUTPUT]
    Name        cloudwatch_logs
    Match           host.*
    region          ${AWS_REGION}
    log_group_name      /${CLUSTER_NAME}/host
    log_stream_prefix   log-
    auto_create_group   true
    extra_user_agent    container-insights
"""
# parsers.conf
parsers_conf = r"""
[PARSER]
    Name        syslog
    Format          regex
    Regex           ^(?<time>[^ ]* {1,2}[^ ]* [^ ]*) (?<host>[^ ]*) (?<ident>[a-zA-Z0-9_\/\.\-]*)(?:\[(?<pid>[0-9]+)\])?(?:[^\:]*\:)? *(?<message>.*)$
    Time_Key        time
    Time_Format     %b %d %H:%M:%S
[PARSER]
    Name        container_firstline
    Format          regex
    Regex           (?<log>(?<="log":")\S(?!\.).*?)(?<!\\)".*(?<stream>(?<="stream":").*?)".*(?<time>\d{4}-\d{1,2}-\d{1,2}T\d{2}:\d{2}:\d{2}\.\w*).*(?=})
    Time_Key        time
    Time_Format     %Y-%m-%dT%H:%M:%S.%LZ
[PARSER]
    Name        cwagent_firstline
    Format          regex
    Regex           (?<log>(?<="log":")\d{4}[\/-]\d{1,2}[\/-]\d{1,2}[ T]\d{2}:\d{2}:\d{2}(?!\.).*?)(?<!\\)".*(?<stream>(?<="stream":").*?)".*(?<time>\d{4}-\d{1,2}-\d{1,2}T\d{2}:\d{2}:\d{2}\.\w*).*(?=})
    Time_Key        time
    Time_Format     %Y-%m-%dT%H:%M:%S.%LZ
"""

FLUENT_BIT_HTTP_PORT = '2020'
FLUENT_BIT_READ_FROM_HEAD = 'Off'
FLUENT_BIT_READ_FROM_TAIL = 'On'
FLUENT_BIT_HTTP_SERVER = 'On'

env = [
    EnvVar(
        name="AWS_REGION",
        value_from=EnvVarSource(
            config_map_key_ref=ConfigMapKeySelector(
                name="fluent-bit-cluster-info",
                key="logs.region"
            )
        )
    ),
    EnvVar(
        name="CLUSTER_NAME",
        value_from=EnvVarSource(
            config_map_key_ref=ConfigMapKeySelector(
                name="fluent-bit-cluster-info",
                key="cluster.name"
            )
        )
    ),
    EnvVar(
        name="HTTP_SERVER",
        value_from=EnvVarSource(
            config_map_key_ref=ConfigMapKeySelector(
                name="fluent-bit-cluster-info",
                key="http.server"
            )
        )
    ),
    EnvVar(
        name="HTTP_PORT",
        value_from=EnvVarSource(
            config_map_key_ref=ConfigMapKeySelector(
                name="fluent-bit-cluster-info",
                key="http.port"
            )
        )
    ),
    EnvVar(
        name="READ_FROM_HEAD",
        value_from=EnvVarSource(
            config_map_key_ref=ConfigMapKeySelector(
                name="fluent-bit-cluster-info",
                key="read.head"
            )
        )
    ),
    EnvVar(
        name="READ_FROM_TAIL",
        value_from=EnvVarSource(
            config_map_key_ref=ConfigMapKeySelector(
                name="fluent-bit-cluster-info",
                key="read.tail"
            )
        )
    ),
    EnvVar(
        name="HOST_NAME",
        value_from=EnvVarSource(
            field_ref=ObjectFieldSelector(field_path="spec.nodeName")
        )
    ),
    EnvVar(
        name="HOSTNAME",
        value_from=EnvVarSource(
            field_ref=ObjectFieldSelector(api_version="v1", field_path="metadata.name")
        )
    ),
    EnvVar(
        name="CI_VERSION",
        value="k8s/1.3.16"
    ),
    EnvVar(
        name="AWS_ACCESS_KEY_ID",
        value=AWS_ACCESS_KEY_ID
    ),
    EnvVar(
        name="AWS_SECRET_ACCESS_KEY",
        value=AWS_SECRET_ACCESS_KEY
    ),
]

tolerations = [
    Toleration(
        key="node-role.kubernetes.io/master",
        operator="Exists",
        effect="NoSchedule"),
    Toleration(
        operator="Exists",
        effect="NoExecute"),
    Toleration(
        operator="Exists",
        effect="NoSchedule")
]

volumes = [
    Volume(
        name="fluentbitstate",
        host_path=HostPathVolumeSource(
            path="/var/fluent-bit/state",
        )
    ),
    Volume(
        name="varlog",
        host_path=HostPathVolumeSource(
            path="/var/log")
    ),
    Volume(
        name="varlibdockercontainers",
        host_path=HostPathVolumeSource(
            path="/var/lib/docker/containers")),
    Volume(
        name="fluent-bit-config",
        config_map=ConfigMapVolumeSource(
            name="fluent-bit-config")
    ),
    Volume(
        name="runlogjournal",
        host_path=HostPathVolumeSource(
            path="/run/log/journal")
    ),
    Volume(
        name="dmesg",
        host_path=HostPathVolumeSource(
            path="/var/log/dmesg")
    ),
]


def iam_role_func(args):
    """
    :param args:
    :return:
    """
    oidc_url, oidc_arn, namespace, service_account_name = args
    cond = f"system:serviceaccount:{namespace}:{service_account_name}"
    ret = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": oidc_arn
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            f"{oidc_url}:aud": "sts.amazonaws.com",
                            f"{oidc_url}:sub": cond
                        },
                    }
                }
            ]
        }
    )
    return ret


def create_fb_cw_ns(provider):
    """
    Create fluent bit for CloudWatch
    :return:
    """
    log.info('[base.cw.create_fb_cw_ns]')
    ns = Namespace(
        'amazon-cloudwatch',
        metadata={
            'name': 'amazon-cloudwatch',
        },
        opts=pulumi.ResourceOptions(
            provider=provider,
            parent=provider,
        )
    )
    return ns


def create_fb_cw_cm():
    log.info('[base.cw.create_fb_cw_cm]')
    cm_cluster = ConfigMap(
        'fluent_bit_cluster_info',
        metadata={
            'name': 'fluent-bit-cluster-info',
            'namespace': 'amazon-cloudwatch',
        },
        data={
            "cluster.name": DEP_MODE,
            "http.server": FLUENT_BIT_HTTP_SERVER,
            "http.port": FLUENT_BIT_HTTP_PORT,
            "read.head": FLUENT_BIT_READ_FROM_HEAD,
            "read.tail": FLUENT_BIT_READ_FROM_TAIL,
            "logs.region": REGION,
        },
    )
    cm = ConfigMap(
        'fluent_bit_config',
        metadata={
            'name': 'fluent-bit-config',
            'namespace': 'amazon-cloudwatch',
            'labels': {
                'k8s-app': 'fluent-bit',
            },
        },
        data={
            "fluent-bit.conf": fluent_bit_conf,
            "application-log.conf": application_log_conf,
            "dataplane-log.conf": dataplane_log_conf,
            "host-log.conf": host_log_conf,
            "parsers.conf": parsers_conf,
        },
    )
    return cm_cluster, cm


def create_fb_cw_iam():
    log.info('[base.cw.create_fb_cw_iam]')
    sa = ServiceAccount(
        'fluent_bit',
        metadata={
            'name': 'fluent-bit',
            'namespace': 'amazon-cloudwatch',
        },
    )
    cr = ClusterRole(
        'fluent_bit_role',
        rules=[
            {
                'nonResourceURLs': ['/metrics'],
                'verbs': ['get'],
            },
            {
                'apiGroups': [''],
                'resources': ['namespaces', 'pods', 'pods/logs', 'nodes', 'nodes/proxy'],
                'verbs': ['get', 'list', 'watch'],
            },
        ],
    )
    crb = ClusterRoleBinding(
        'fluent_bit_role_binding',
        metadata={
            'name': 'fluent-bit-role-binding',
        },
        role_ref={
            'api_group': 'rbac.authorization.k8s.io',
            'kind': 'ClusterRole',
            'name': 'fluent-bit-role',
        },
        subjects=[
            {
                'kind': 'ServiceAccount',
                'name': sa.metadata['name'],
                'namespace': sa.metadata['namespace'],
            },
        ],
    )
    return sa


def create_fb_cw_ds():
    log.info('[base.cw.create_fb_cw_ds]')
    ds = DaemonSet(
        "fluent-bit",
        metadata={
            'name': 'fluent-bit',
            'namespace': 'amazon-cloudwatch',
            'labels': {
                'k8s-app': 'fluent-bit',
                'version': 'v1',
                'kubernetes.io/cluster-service': "true",
            },
        },
        spec={
            "selector": LabelSelector(match_labels={
                "k8s-app": "fluent-bit",
            }),
            "template": PodTemplateSpec(
                metadata=ObjectMeta(
                    labels={
                        "k8s-app": "fluent-bit",
                        "version": "v1",
                        "kubernetes.io/cluster-service": "true",
                    }
                ),
                spec=PodSpec(
                    containers=[
                        Container(
                            name="fluent-bit",
                            image="public.ecr.aws/aws-observability/aws-for-fluent-bit:latest",
                            image_pull_policy="Always",
                            env=env,
                            resources=ResourceRequirements(
                                limits={"memory": "200Mi"},
                                requests={"cpu": "500m", "memory": "100Mi"},
                            ),
                            volume_mounts=[
                                VolumeMount(
                                    name="fluentbitstate",
                                    mount_path="/var/fluent-bit/state",
                                ),
                                VolumeMount(
                                    name="varlog",
                                    mount_path="/var/log",
                                    read_only=True,
                                ),
                                VolumeMount(
                                    name="varlibdockercontainers",
                                    mount_path="/var/lib/docker/containers",
                                    read_only=True,
                                ),
                                VolumeMount(
                                    name="fluent-bit-config",
                                    mount_path="/fluent-bit/etc/",
                                ),
                                VolumeMount(
                                    name="runlogjournal",
                                    mount_path="/run/log/journal",
                                    read_only=True,
                                ),
                                VolumeMount(
                                    name="dmesg",
                                    mount_path="/var/log/dmesg",
                                    read_only=True,
                                ),
                            ],
                        )
                    ],
                    volumes=volumes,
                    tolerations=tolerations,
                    termination_grace_period_seconds=10,
                    host_network=True,
                    dns_policy="ClusterFirstWithHostNet",
                    service_account_name="fluent-bit"
                )
            )
        },
    )


def create_fb_cw_role(
        namespace,
        oidc_url,
        oidc_arn,
        service_account
):
    log.info('[base.cw.create_fb_cw_role]')
    r = pulumi_aws.iam.Role(
        "fluent-bit-cloud-watch-r",
        assume_role_policy=pulumi.Output.all(
            oidc_url,
            oidc_arn,
            namespace.metadata.name,
            service_account.metadata.name
        ).apply(
            func=iam_role_func
        ),
    )
    pa = pulumi_aws.iam.RolePolicyAttachment(
        "fluent-bit-cloud-watch-r-policy-attachment",
        role=r.name,
        policy_arn="arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
    )
