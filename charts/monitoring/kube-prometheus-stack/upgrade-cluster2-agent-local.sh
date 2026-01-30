helm upgrade --install prometheus-agent prometheus-community/kube-prometheus-stack -f values-cluster2-agent-local.yaml -n monitoring-agent --create-namespace
