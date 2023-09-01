from base.cluster import create_cluster
from base.provider import create_provider
from base.vpc import create_eip, create_vpc
from cw.cw import create_fb_cw_ns, create_fb_cw_cm, create_fb_cw_iam, create_fb_cw_role, create_fb_cw_ds


def up():
    eip = create_eip()
    vpc = create_vpc(eip)
    cluster = create_cluster(vpc)
    oidc_url = cluster.core.oidc_provider.url
    oidc_arn = cluster.core.oidc_provider.arn
    provider = create_provider(cluster)
    ns = create_fb_cw_ns(provider)
    create_fb_cw_cm()
    sa = create_fb_cw_iam()
    create_fb_cw_role(ns, oidc_url, oidc_arn, sa)
    create_fb_cw_ds()
