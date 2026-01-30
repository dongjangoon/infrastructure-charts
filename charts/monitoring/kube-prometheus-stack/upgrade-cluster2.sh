helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack -f values-cluster2.yaml -n monitoring --create-namespace
