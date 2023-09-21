from pulumi import log


def read_file(path):
    """
    :param path:
    :return:
    """
    log.info(f'[devops_sdk.utils.read_file] path:{path}')
    with open(path) as fp:
        return fp.read()
