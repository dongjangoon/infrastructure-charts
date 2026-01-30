helm upgrade --install prometheus-central prometheus-community/kube-prometheus-stack -f values-cluster2-central.yaml -n monitoring --create-namespace
