import glob
from pulumi import log
from base.const import DEPLOY_NAME_PREFIX, SSH_KEY_PATH
from pulumi_aws import ec2


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
