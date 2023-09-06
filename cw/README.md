
This contains examples of using Pulumi to manage fluent-bit and cloudwatch resources.


### Confirm metadata appended to pod or other Kubernetes objects


    $ kubectl auth can-i list pods --as=system:serviceaccount:amazon-cloudwatch:fluent-bit
    yes

* https://docs.fluentbit.io/manual/pipeline/filters/kubernetes#optional-feature-using-kubelet-to-get-metadata
