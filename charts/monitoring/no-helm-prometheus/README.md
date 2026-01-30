# Multi-Cluster Prometheus Federation Monitoring Stack

이 구성은 Kustomize를 사용하여 멀티 클러스터 Prometheus Federation 모니터링 스택을 배포합니다. kube-prometheus-stack 헬름 차트 없이 순수 매니페스트로 구성되어 **어느 환경에서나 재사용 가능**합니다.

## 🏗️ Architecture

```
Central Cluster:
├── Prometheus (Federation Master) + LoadBalancer
├── Grafana 12.1.0 + 기본 대시보드들
├── Node Exporter
└── Kube-state-metrics

Remote Clusters:
├── Prometheus (Federation Slave) + LoadBalancer  
├── Node Exporter
└── Kube-state-metrics
```

## 📁 Directory Structure

```
no-helm-prometheus/
├── base/                           # 공통 매니페스트
│   ├── namespace.yaml
│   ├── prometheus/
│   ├── node-exporter/
│   └── kube-state-metrics/
├── overlays/
│   ├── central/                    # 중앙 클러스터 (Federation Master)
│   │   ├── grafana/               # Grafana + 대시보드
│   │   │   ├── configmap.yaml     # Datasource 설정
│   │   │   ├── dashboards-configmap.yaml
│   │   │   ├── kubernetes-overview-dashboard.yaml
│   │   │   ├── node-exporter-dashboard.yaml
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   ├── prometheus-federation-config.yaml
│   │   └── kustomization.yaml
│   └── remote/                     # 원격 클러스터 (Federation Slave)
│       ├── prometheus-remote-config.yaml
│       └── kustomization.yaml
└── README.md
```

## 🚀 배포 방법

### 1. Central Cluster (Federation Master)
```bash
kubectl config use-context <central-cluster-context>
kubectl apply -k overlays/central
```

### 2. Remote Cluster (Federation Slave)
```bash
kubectl config use-context <remote-cluster-context>
kubectl apply -k overlays/remote
```

## 🌐 접속 정보

### Direct LoadBalancer Access
- **Prometheus (Central)**: `http://<central-lb-ip>:9090`
- **Prometheus (Remote)**: `http://<remote-lb-ip>:9090`
- **Grafana**: `http://<central-lb-ip>:3000`

### Port-forward Access (for development)
```bash
# Prometheus
kubectl port-forward -n monitoring svc/central-prometheus-service 9090:9090

# Grafana
kubectl port-forward -n monitoring svc/central-grafana 3000:3000
```

## 📊 기본 대시보드

Grafana에는 다음 대시보드가 자동으로 프로비저닝됩니다:

1. **Kubernetes Overview**
   - 클러스터 전체 리소스 현황
   - CPU/Memory 사용량
   - Pod/Node/Service 카운트

2. **Node Exporter Full**
   - 노드별 상세 메트릭
   - CPU, Memory, Network, Disk I/O

## 🔄 Federation 설정

Central Prometheus가 Remote Prometheus에서 다음 메트릭들을 수집:

```yaml
params:
  'match[]':
    - '{job=~"kubernetes-.*"}'
    - '{job=~"node-exporter"}'
    - '{job=~"kube-state-metrics"}'
    - 'up'
    - 'prometheus_build_info'
```

## 🔧 환경별 커스터마이징

### 1. 클러스터 이름 변경
`overlays/central/prometheus-federation-config.yaml`에서:
```yaml
external_labels:
  cluster: 'your-cluster-name'
```

### 2. Federation 타겟 추가
Remote Prometheus의 LoadBalancer IP를 Central 설정에 추가:
```yaml
static_configs:
- targets:
  - '<remote-lb-ip>:9090'
```

### 3. 대시보드 추가
새로운 대시보드를 추가하려면:
1. `overlays/central/grafana/`에 새 ConfigMap 생성
2. `overlays/central/grafana/deployment.yaml`의 volumeMounts에 추가
3. `overlays/central/kustomization.yaml`의 resources에 추가

## ✅ 다중 환경 재사용 가능

이 구성은 다음과 같이 **어느 환경에서나 재사용 가능**합니다:

### 환경별 오버레이 생성
```bash
# 새로운 환경을 위한 오버레이 생성
cp -r overlays/central overlays/production
cp -r overlays/remote overlays/staging

# 환경별 설정 수정
vi overlays/production/prometheus-federation-config.yaml
vi overlays/staging/prometheus-remote-config.yaml
```

### 다른 쿠버네티스 배포판 지원
- k3s, k8s, EKS, GKE, AKS 등 모든 환경
- LoadBalancer 타입이 지원되지 않는 환경에서는 NodePort로 변경
- Ingress Controller 사용 시 Ingress 리소스 추가

### GitOps 친화적
- ArgoCD, Flux 등 GitOps 도구와 완벽 호환
- Kustomize 네이티브 지원

## 🔍 트러블슈팅

### Federation 연결 확인
```bash
# Central Prometheus 타겟 상태 확인
curl http://<central-lb-ip>:9090/api/v1/targets

# Federation endpoint 테스트
curl "http://<remote-lb-ip>:9090/federate?match[]={job=~\"kubernetes-.*\"}"
```

### Grafana Datasource 확인
1. Grafana 로그인: admin/admin
2. Configuration > Data sources > prometheus
3. Test 버튼으로 연결 확인

## 📈 모니터링 범위

### Metrics 수집 대상:
- **Kubernetes API Server**: 클러스터 상태
- **Node Metrics**: CPU, Memory, Network, Disk
- **Pod Metrics**: 컨테이너 리소스 사용량  
- **Service Metrics**: 서비스 상태
- **Kube-state-metrics**: 쿠버네티스 오브젝트 상태

### Multi-cluster 가시성:
- 중앙화된 메트릭 수집
- 클러스터별 레이블링
- 통합 대시보드 제공