import pulumi_aws
from pulumi import log


def create_db(
        sg,
        sng,
        db_res_name,
        db_name,
        db_password,
        instance_class,
        is_public,
):
    """
    :param sg: security group
    :param sng: subnet group
    :param db_name: DB name
    :param db_res_name: DB res name
    :param db_password: DB password
    :param instance_class: db instance type
    :param is_public: is db public
    :param availability_zone: db availability zone
    :return:
    """
    log.info('[base.rds.create_db]')
    db = pulumi_aws.rds.Instance(
        db_res_name,
        allocated_storage=20,
        db_name=db_name,
        username="postgres",
        password=db_password,
        engine="postgres",
        engine_version="12.17",
        instance_class=instance_class,
        parameter_group_name="default.postgres12",
        skip_final_snapshot=True,
        vpc_security_group_ids=[sg.id],
        db_subnet_group_name=sng.name,
        multi_az=False,
        # @note: Enable automated backup
        backup_retention_period=7,
        backup_window="07:00-07:30",
        publicly_accessible=is_public,
    )
    return db
