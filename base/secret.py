from typing import Optional

import pulumi
from pulumi import log
from pulumi_kubernetes.core.v1 import Secret


def create_secret(
        res_secret_name,
        data: Optional[dict],
        string_data,
        namespace,
):
    """
    @note: value of dict should be base64
    :param res_secret_name:
    :param namespace:
    :param data:
    :param string_data:
    :return:
    """
    log.info('[develop_sdk.secret.create_secret]')
    secret = Secret(
        res_secret_name,
        metadata={
            "namespace": namespace.metadata.name
        },
        type="Opaque",
        data=data,
        string_data=string_data,
        opts=pulumi.ResourceOptions(
            depends_on=[namespace],
        ),
    )
    return secret
