#!/bin/bash

# Harbor 서버 정보 - 실제 환경에 맞게 변경
HARBOR_HOST="${HARBOR_HOST_IP}:30003"
CERT_DIR="/etc/docker/certs.d/${HARBOR_HOST}"

# 1. Harbor에서 인증서 다운로드
echo "Downloading Harbor certificate..."
echo | openssl s_client -connect ${HARBOR_HOST} -servername ${HARBOR_HOST} 2>/dev/null | \
  openssl x509 -outform PEM > harbor-ca.crt

if [ ! -s harbor-ca.crt ]; then
    echo "Failed to download certificate. Trying alternative method..."
    curl -k https://${HARBOR_HOST}/api/v2.0/systeminfo/getcert -o harbor-ca.crt
fi

# 인증서 확인
echo "Certificate info:"
openssl x509 -in harbor-ca.crt -text -noout | grep -E "Subject:|Issuer:|Not After"

# 2. 노드 IP 주소 직접 지정 (kubectl get nodes -o wide 결과에서 확인)
MASTER_IP="${MASTER_NODE_IP}"
WORKER1_IP="${WORKER1_NODE_IP}"
WORKER2_GPU_IP="${WORKER2_GPU_NODE_IP}"

# 노드 리스트
declare -A NODES
NODES["worker1"]="${WORKER1_IP}"
NODES["worker2-gpu"]="${WORKER2_GPU_IP}"

# SSH KEY
SSH_KEY="~/.ssh/${SSH_KEY_NAME}"

# 3. 각 노드에 인증서 설정
for node_name in "${!NODES[@]}"; do
  NODE_IP="${NODES[$node_name]}"
  echo "Configuring node: $node_name ($NODE_IP)"

  if [[ "$NODE_IP" == *"XXX"* ]]; then
    echo "Skipping $node_name - IP not configured"
    continue
  fi

  echo "Copying certificate to $node_name..."
  scp -i ${SSH_KEY} -o StrictHostKeyChecking=no harbor-ca.crt ubuntu@${NODE_IP}:/tmp/

  ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ubuntu@${NODE_IP} << ENDSSH
    sudo mkdir -p /etc/docker/certs.d/${HARBOR_HOST}
    sudo cp /tmp/harbor-ca.crt /etc/docker/certs.d/${HARBOR_HOST}/ca.crt
    sudo cp /tmp/harbor-ca.crt /usr/local/share/ca-certificates/harbor-ca.crt
    sudo update-ca-certificates
    sudo mkdir -p /etc/containerd/certs.d/${HARBOR_HOST}
    sudo tee /etc/containerd/certs.d/${HARBOR_HOST}/hosts.toml << EOF
server = "https://${HARBOR_HOST}"

[host."https://${HARBOR_HOST}"]
  ca = "/etc/containerd/certs.d/${HARBOR_HOST}/ca.crt"
  skip_verify = false
EOF
    sudo cp /tmp/harbor-ca.crt /etc/containerd/certs.d/${HARBOR_HOST}/ca.crt
    sudo systemctl restart containerd
    sudo systemctl restart kubelet
    echo "Configuration completed on \$(hostname)"
ENDSSH

  echo "Node $node_name configured successfully"
done

echo "Harbor certificate setup completed!"

# 4. 테스트를 위한 임시 Pod 생성
echo "Creating test pod to verify image pull..."
kubectl run test-harbor-pull --image=${HARBOR_HOST}/monitoring/spring:latest \
  --dry-run=client -o yaml | kubectl apply -f -

sleep 10
kubectl describe pod test-harbor-pull | grep -E "Events:|Pulling|Pulled|Failed"
kubectl delete pod test-harbor-pull --ignore-not-found=true
