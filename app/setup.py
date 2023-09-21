from pulumi import log

from app.app import create_app


def app_setup():
    """
    """
    log.info('[app.app_setup]')
    create_app()
