from pulumi_kubernetes.core.v1 import Pod
import pulumi_kubernetes


def create_pod(namespace, pvc):
    """
    :param namespace:
    :param pvc:
    :return:
    """
    pod = Pod("volume_test_pod",
              metadata={
                  "name": "volume-test",
                  "namespace": namespace.metadata.name,
              },
              spec={
                  "restartPolicy": "Always",
                  "containers": [pulumi_kubernetes.core.v1.ContainerArgs(
                      name="volume-test",
                      image="nginx:stable-alpine",
                      image_pull_policy="IfNotPresent",
                      liveness_probe=pulumi_kubernetes.core.v1.ProbeArgs(
                          exec_=pulumi_kubernetes.core.v1.ExecActionArgs(
                              command=["ls", "/data/lost+found"],
                          ),
                          initial_delay_seconds=5,
                          period_seconds=5
                      ),
                      volume_mounts=[
                          pulumi_kubernetes.core.v1.VolumeMountArgs(
                              name="vol",
                              mount_path="/data"
                          )],
                      ports=[
                          pulumi_kubernetes.core.v1.ContainerPortArgs(
                              container_port=80
                          )
                      ]
                  )],
                  "volumes": [
                      pulumi_kubernetes.core.v1.VolumeArgs(
                          name="vol",
                          persistent_volume_claim=pulumi_kubernetes.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                              claim_name=pvc.metadata.name),
                      )
                  ]
              }
              )
    return pod
