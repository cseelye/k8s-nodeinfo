# k8s-nodeinfo
Introspect k8s worker nodes and create a CR with hardware info.

This is a quick demonstration of how to use the python kubernetes-client to write an extremely simple controller that publishes information in a CR.

## How To Run
Apply the CRD, deploy the controller, and then view the resulting CR(s).
```
kubectl apply -f nodeinfo_crd.yaml
kubectl apply -f deploy.yaml
kubectl describe nodeinfo -n nodeinfo
```
