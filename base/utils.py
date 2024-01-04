import glob
from base.const import DEPLOY_NAME_PREFIX, SSH_KEY_PATH
from pulumi_aws import ec2
import pulumi_kubernetes
from pulumi import log, Output


def read_file(path):
    """
    :param path:
    :return:
    """
    log.info(f'[devops_sdk.utils.read_file] path:{path}')
    with open(path) as fp:
        return fp.read()


def get_public_keys():
    ssh_key_path = f'{SSH_KEY_PATH}*.pub'
    public_keys = []
    for index, path in enumerate(glob.glob(ssh_key_path)):
        with open(path) as fp:
            data = fp.read()
            key = ec2.KeyPair(
                f'key{DEPLOY_NAME_PREFIX}-{index}',
                public_key=data,
                tags={"Name": f'key{DEPLOY_NAME_PREFIX}'},
            )
            public_keys.append(key)
    return public_keys


def dict_to_k8n_env_var_args(env: dict = None):
    """
    :param env:
    :return:
    """
    log.info('[devops_sdk.utils.dict_to_k8n_env_var_args]')
    if not env:
        return None
    env_vars = list()
    for k, v in env.items():
        env_vars.append(
            pulumi_kubernetes.core.v1.EnvVarArgs(
                name=k,
                value=v.apply(lambda value: f'{value}')
                if isinstance(v, Output) else str(v),
            ),
        )
    return env_vars
