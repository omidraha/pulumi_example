import pulumi_aws
import json
from pulumi import log

from const import DEPLOY_NAME_PREFIX


def create_eks_cluster_role():
    """
    Create the EKS Cluster Role
    :return:
    """
    log.info('[base.iam.create_eks_cluster_role]')
    eks_cluster_role = pulumi_aws.iam.Role(
        f"eks-cluster-role{DEPLOY_NAME_PREFIX}",
        name='EKS-Cluster-Role',
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "",
                "Effect": "Allow",
                "Principal": {
                    "Service": "eks.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
            }]
        })
    )
    return eks_cluster_role


def create_eks_cluster_role_policy_attachment(eks_cluster_role):
    """
    Attach the AmazonEKSClusterPolicy to the EKS Cluster Role
    :param eks_cluster_role:
    :return:
    """
    log.info('[base.iam.create_eks_cluster_role_policy_attachment]')
    eks_cluster_role_policy_attachment = pulumi_aws.iam.RolePolicyAttachment(
        f"eks-cluster-role-policy{DEPLOY_NAME_PREFIX}",
        role=eks_cluster_role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
    )
    return eks_cluster_role_policy_attachment


def create_eks_worker_role():
    """
    Create the EKS Worker Role
    """
    log.info('[base.iam.create_eks_worker_role]')
    eks_worker_role = pulumi_aws.iam.Role(
        f"eks-worker-role{DEPLOY_NAME_PREFIX}",
        name='EKS-Worker-Role',
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "",
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
            }]
        })
    )
    return eks_worker_role


def create_worker_role_policy_attachment_node(eks_worker_role):
    """
    Attach the AmazonEKSWorkerNodePolicy to the EKS Worker Role
    :param eks_worker_role:
    :return:
    """
    log.info('[base.iam.create_worker_role_policy_attachment_node]')
    worker_role_policy_attachment = pulumi_aws.iam.RolePolicyAttachment(
        f"eks-worker-role-policy-amazon-eks-worker-node-policy{DEPLOY_NAME_PREFIX}",
        role=eks_worker_role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
    )
    return worker_role_policy_attachment


def create_worker_role_policy_attachment_cni(eks_worker_role):
    """
    Attach the AmazonEKS_CNI_Policy to the EKS Worker Role
    :param eks_worker_role:
    :return:
    """
    log.info('[base.iam.create_worker_role_policy_attachment_cni]')
    worker_role_policy_attachment = pulumi_aws.iam.RolePolicyAttachment(
        f"eks-worker-role-policy-amazon-eks-cni-policy{DEPLOY_NAME_PREFIX}",
        role=eks_worker_role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
    )
    return worker_role_policy_attachment


def create_worker_role_policy_attachment_ec2(eks_worker_role):
    """
    Attach the AmazonEC2ContainerRegistryReadOnly to the EKS Worker Role
    :param eks_worker_role:
    :return:
    """
    log.info('[base.iam.create_worker_role_policy_attachment_ec2]')
    worker_role_policy_attachment = pulumi_aws.iam.RolePolicyAttachment(
        f"eks-worker-role-policy-amazon-ec2-container-registry-readonly{DEPLOY_NAME_PREFIX}",
        role=eks_worker_role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
    )
    return worker_role_policy_attachment


def create_cluster_iam():
    log.info('[base.iam.create_cluster_iam]')
    eks_cluster_role = create_eks_cluster_role()
    create_eks_cluster_role_policy_attachment(eks_cluster_role)
    eks_worker_role = create_eks_worker_role()
    create_worker_role_policy_attachment_node(eks_worker_role)
    create_worker_role_policy_attachment_cni(eks_worker_role)
    create_worker_role_policy_attachment_ec2(eks_worker_role)
    return eks_worker_role
