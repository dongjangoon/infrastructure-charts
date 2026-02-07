# Claude.md — LLM Tracing 인프라 (k3s + Istio Gateway API + Grafana Tempo + OTel Collector)

## Project Overview

WSL2 환경에서 k3s로 Kubernetes 클러스터를 구성하고, **Istio 서비스 메시 + Kubernetes Gateway API** 기반으로 모든 외부 트래픽을 라우팅한다.

- 라우팅: **Gateway → HTTPRoute / GRPCRoute** 패턴 (Ingress 사용 금지)
- 트레이싱: **App (OTel SDK) → OTel Collector → Grafana Tempo → Grafana UI**
- 메트릭: **kube-prometheus-stack** (Prometheus + Grafana + Alertmanager + dcgm-exporter)
- 서비스 메시: Istio 자동 mTLS
- GPU 서빙: vLLM (NVIDIA GPU)

## 아키텍처

```
WSL2 Host IP → Istio Gateway (LoadBalancer) → Services

Namespaces:
├── istio-system: Gateway, Istiod
├── monitoring: kube-prometheus-stack, dcgm-exporter
├── tracing: OTel Collector, Tempo
├── langfuse: Langfuse (PostgreSQL, ClickHouse, Redis, MinIO)
├── litellm: LiteLLM Proxy
└── llm: vLLM

라우팅 (via Istio Gateway):
  grafana.local     → Grafana (monitoring)
  prometheus.local  → Prometheus (monitoring)
  tempo.local       → Tempo (tracing)
  langfuse.local    → Langfuse (langfuse)
  litellm.local     → LiteLLM (litellm)
  :4317             → OTel Collector gRPC (tracing)
  :4318             → OTel Collector HTTP (tracing)
```

## 시스템 요구사항

| 항목 | 최소 | 권장 |
|---|---|---|
| RAM | 12GB | 16GB+ |
| Disk | 30GB | 50GB+ |
| GPU | NVIDIA 8GB+ VRAM | NVIDIA 16GB+ VRAM |
| CUDA | 12.x+ | 최신 |

## Phase 0: 사전 요구사항

### 필수 도구 설치 확인
```bash
docker --version && kubectl version --client && helm version && istioctl version --remote=false
nvidia-smi  # GPU 확인
```

### k3s 설치 (sudo 필요)
```bash
# k3s 설치 (traefik 비활성화 - Istio Gateway 사용)
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=traefik" sh -

# kubeconfig 설정
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config

# NVIDIA Container Toolkit 설정 (GPU 사용 시)
sudo nvidia-ctk runtime configure --runtime=containerd
sudo systemctl restart k3s
```

### GPU 확인
```bash
kubectl get nodes -o json | jq '.items[].status.capacity' | grep nvidia
# "nvidia.com/gpu": "1" 확인
```

## Phase 1: 네임스페이스 생성

```bash
kubectl create namespace istio-system
kubectl create namespace monitoring
kubectl create namespace tracing
kubectl create namespace llm
```

> langfuse, litellm 네임스페이스는 별도 Helm 차트에서 생성됨

## Phase 2: Istio 설치

```bash
# Helm repos
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

# Gateway API CRD (experimental for GRPCRoute)
kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/experimental-install.yaml

# Istio 설치
helm upgrade --install istio-base istio/base -n istio-system --wait
helm upgrade --install istiod istio/istiod -n istio-system -f infra/helm-values/istiod-values.yaml --wait

# Sidecar injection
kubectl label namespace tracing monitoring llm istio-injection=enabled --overwrite
```

Values 파일: `infra/helm-values/istiod-values.yaml`

## Phase 3: Gateway 및 Routes

```bash
kubectl apply -f infra/istio/gateway.yaml
kubectl apply -f infra/istio/reference-grants.yaml
kubectl apply -f infra/istio/routes/
kubectl apply -f infra/istio/telemetry.yaml
```

파일 위치:
- `infra/istio/gateway.yaml` - Main Gateway (ports 80, 4317, 4318)
- `infra/istio/reference-grants.yaml` - Cross-namespace grants (monitoring, tracing, langfuse, litellm, llm)
- `infra/istio/routes/` - HTTPRoute 정의

## Phase 4: kube-prometheus-stack

```bash
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring -f infra/helm-values/kube-prometheus-stack-values.yaml --wait --timeout 10m
```

Values 파일: `infra/helm-values/kube-prometheus-stack-values.yaml`

### dcgm-exporter (GPU 메트릭)
```bash
# dcgm-exporter는 별도 설치 또는 기존 것 유지
kubectl apply -f infra/manifests/dcgm-exporter/
```

## Phase 5: Tempo + OTel Collector

```bash
helm upgrade --install tempo grafana/tempo -n tracing -f infra/helm-values/tempo-values.yaml --wait
helm upgrade --install otel-collector open-telemetry/opentelemetry-collector \
  -n tracing -f infra/helm-values/otel-collector-values.yaml --wait
```

## Phase 6: vLLM 배포

```bash
kubectl apply -f infra/manifests/vllm/
kubectl -n llm wait --for=condition=Ready pod -l app=vllm --timeout=600s
```

매니페스트: `infra/manifests/vllm/`
- `pvc.yaml` - 모델 캐시 PVC (50Gi)
- `deployment.yaml` - vLLM Deployment + Service (Qwen2.5-3B-Instruct)

## Phase 7: 검증

```bash
# Gateway 상태 확인
kubectl -n istio-system get gateway,pods,svc

# Gateway External IP 확인
GATEWAY_IP=$(kubectl -n istio-system get svc main-gateway-istio -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo $GATEWAY_IP

# 서비스 접속 테스트
curl -H "Host: grafana.local" http://$GATEWAY_IP/
curl -H "Host: prometheus.local" http://$GATEWAY_IP/
curl -H "Host: langfuse.local" http://$GATEWAY_IP/
curl -H "Host: litellm.local" http://$GATEWAY_IP/
```

| 서비스 | URL | 인증 |
|---|---|---|
| Grafana | http://grafana.local | admin/admin |
| Prometheus | http://prometheus.local | - |
| Langfuse | http://langfuse.local | 가입 후 로그인 |
| LiteLLM | http://litellm.local | Bearer token |

## 디렉토리 구조

```
infra/
├── istio/
│   ├── gateway.yaml
│   ├── reference-grants.yaml
│   ├── telemetry.yaml
│   └── routes/
│       ├── grafana-route.yaml
│       ├── prometheus-route.yaml
│       ├── tempo-route.yaml
│       ├── otel-http-route.yaml
│       ├── otel-grpc-route.yaml
│       ├── langfuse-route.yaml
│       └── litellm-route.yaml
├── helm-values/
│   ├── istiod-values.yaml
│   ├── kube-prometheus-stack-values.yaml
│   ├── tempo-values.yaml
│   └── otel-collector-values.yaml
├── manifests/
│   └── vllm/
│       ├── pvc.yaml
│       └── deployment.yaml
└── kind/
    └── cluster-config.yaml  # kind 사용 시 참고
```

## 트러블슈팅

### Istio Gateway
| 증상 | 해결 |
|---|---|
| Gateway pod 미생성 | `kubectl get gatewayclass` 확인, CRD 재설치 |
| 404 응답 | Host 헤더 확인, hosts 파일 점검 |
| gRPC 연결 실패 | Service `appProtocol: grpc` 확인 |

### k3s + GPU
| 증상 | 해결 |
|---|---|
| GPU 미인식 | `nvidia-ctk runtime configure --runtime=containerd` 후 k3s 재시작 |
| Device Plugin 미동작 | `kubectl -n kube-system logs -l name=nvidia-device-plugin-ds` |
| vLLM OOM | `--gpu-memory-utilization` 감소 (0.5~0.9) |
| vLLM Pending | 메모리 부족 - requests.memory 줄이기 또는 다른 Pod 정리 |

### 디버깅
```bash
istioctl proxy-status
kubectl -n tracing logs -f deploy/otel-collector-opentelemetry-collector
kubectl -n llm logs -f deploy/vllm
kubectl -n llm exec -it deploy/vllm -- nvidia-smi
kubectl top nodes  # 리소스 사용량 확인
```

## 금지사항

- `kind: Ingress` 사용 금지 (Gateway API 사용)
- Istio VirtualService/DestinationRule 사용 금지
- Gateway API CRD 설치 전 istiod 설치 금지
- node-exporter에 sidecar injection 금지
- vLLM `--gpu-memory-utilization` 1.0 사용 금지 (OOM 위험)
- Secret에 API 키 하드코딩 후 Git commit 금지
- vLLM을 Docker로 직접 실행 금지 (반드시 Kubernetes에서 배포)

## hosts 파일 설정

Windows (`C:\Windows\System32\drivers\etc\hosts`):
```
<GATEWAY_IP>  grafana.local prometheus.local tempo.local langfuse.local litellm.local
```

> GATEWAY_IP는 `kubectl -n istio-system get svc main-gateway-istio -o jsonpath='{.status.loadBalancer.ingress[0].ip}'`로 확인

## 앱 환경변수

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://<GATEWAY_IP>:4317"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
export OTEL_SERVICE_NAME="my-app"
```
