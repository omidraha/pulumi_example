
Usage:

Clone the project:

    git clone https://github.com/omidraha/pulumi_example/

Generate certificates files including `ca.crt`, `ca.key`, `issuer.crt` and `issuer.key`:

    cd pulumi_example/linkerd
    step certificate create root.linkerd.cluster.local ca.crt ca.key --profile root-ca --no-password --insecure
    step certificate create identity.linkerd.cluster.local issuer.crt issuer.key --profile intermediate-ca --not-after 8760h --no-password --insecure --ca ca.crt --ca-key ca.key

Install the requirements: 

    python -r requirements.txt

Deploy:

    pulumi up 
