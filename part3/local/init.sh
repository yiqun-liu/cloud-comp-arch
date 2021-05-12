~/apps/kind create cluster --name local --config cluster.yaml
kubectl cluster-info --context kind-local
kubectl label nodes local-worker cca-project-nodetype=node-a-2core
kubectl label nodes local-worker2 cca-project-nodetype=node-b-4core
kubectl label nodes local-worker3 cca-project-nodetype=node-c-8core

# operate on the cluster

# delete cluster
# ~/apps/kind delete cluster --name test
