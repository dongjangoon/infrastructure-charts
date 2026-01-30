# Infrastructure Charts

이 레포지토리는 Kubernetes 환경에서 로그 수집 및 모니터링 인프라를 구축하기 위한 Helm 차트와 Kustomization 설정을 포함합니다.

## 📋 목차

- [개요](#개요)
- [구성 요소](#구성-요소)
- [설치 방법](#설치-방법)
- [로그 수집 설정](#로그-수집-설정)
- [OpenSearch 클러스터 확장](#opensearch-클러스터-확장)
- [인덱스 및 스냅샷 관리](#인덱스-및-스냅샷-관리)
- [모니터링](#모니터링)
- [트러블슈팅](#트러블슈팅)

## 🎯 개요

이 인프라는 다음과 같은 구성으로 Kubernetes 로그 수집 및 검색 환경을 제공합니다:

- **Fluent Bit**: Kubernetes 클러스터의 모든 컨테이너 로그 수집
- **OpenSearch**: 로그 저장 및 검색 엔진
- **OpenSearch Dashboards**: 로그 시각화 및 검색 UI
- **Prometheus**: 메트릭 수집 및 모니터링

## 🏗️ 구성 요소

### Helm Charts (`charts/monitoring/`)

```
charts/monitoring/
├── opensearch/
│   ├── values.yaml              # 단일 노드 기본 설정
│   ├── values-single.yaml       # 단일 노드 상세 설정
│   └── values-cluster.yaml      # 3노드 클러스터 설정
└── opensearch-dashboards/
    └── values.yaml
```

### Kustomization (`kustomization/fluent-bit/`)

```
kustomization/fluent-bit/
├── base/
│   ├── configmap.yaml           # 기본 Fluent Bit 설정
│   ├── daemonset.yaml           # Fluent Bit DaemonSet
│   ├── rbac.yaml                # 권한 설정
│   └── kustomization.yaml
└── overlays/
    └── k3d-alloy-kafka-dev/
        ├── patches/
        │   └── cluster-config.yaml  # 클러스터별 설정
        └── kustomization.yaml
```

## 🚀 설치 방법

### 1. 네임스페이스 생성

```bash
kubectl create namespace logging
```

### 2. OpenSearch 및 OpenSearch Dashboards 설치

```bash
# OpenSearch 설치 (단일 노드)
helm install opensearch charts/monitoring/opensearch -n logging -f charts/monitoring/opensearch/values.yaml

# OpenSearch Dashboards 설치
helm install opensearch-dashboards charts/monitoring/opensearch-dashboards -n logging
```

### 3. Fluent Bit 설치

```bash
# Kustomization을 사용한 Fluent Bit 배포
kubectl apply -k kustomization/fluent-bit/overlays/k3d-alloy-kafka-dev
```

## 📊 로그 수집 설정

### Fluent Bit 구성

Fluent Bit는 다음과 같이 구성됩니다:

#### 입력 (INPUT)
- **Path**: `/var/log/containers/*.log`
- **Parser**: CRI (Container Runtime Interface)
- **Tag**: `kube.*`

#### 필터 (FILTER)
- **클러스터 메타데이터 추가**: `cluster_name` 필드 추가
- **환경 감지**: Lua 스크립트로 애플리케이션 환경 추출
- **멀티라인 처리**: Java 스택 트레이스 등 멀티라인 로그 병합

#### 출력 (OUTPUT)
- **대상**: OpenSearch 클러스터
- **인덱스**: `{cluster_name}-logs` 형식
- **호스트**: `opensearch-cluster-master:9200`

### 클러스터별 설정 커스터마이징

새로운 클러스터를 위한 설정을 추가하려면:

1. `kustomization/fluent-bit/overlays/` 아래에 새 폴더 생성
2. `patches/cluster-config.yaml`에서 클러스터명과 OpenSearch 연결 정보 수정
3. `kustomization.yaml`에서 패치 경로 설정

```yaml
# patches/cluster-config.yaml 예시
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [FILTER]
        Name modify
        Match kube.*
        Add cluster_name your-cluster-name
    
    [OUTPUT]
        Name opensearch
        Host your-opensearch-host
        Index your-cluster-name-logs
```


## 🔄 OpenSearch 클러스터 확장

### 프로덕션 환경에서 3노드 클러스터 구성

리소스가 충분한 환경에서는 고가용성을 위해 3노드 클러스터를 구성할 수 있습니다:

```bash
# 3노드 클러스터로 업그레이드
helm upgrade opensearch charts/monitoring/opensearch -n logging -f charts/monitoring/opensearch/values-cluster.yaml
```

#### 주요 차이점:

| 설정 | 단일 노드 | 3노드 클러스터 |
|------|-----------|----------------|
| `singleNode` | `true` | `false` |
| `replicas` | `1` | `3` |
| `discovery.seed_hosts` | 없음 | `opensearch-cluster-master-headless` |
| `cluster.initial_master_nodes` | 없음 | `master-0,master-1,master-2` |
| `sysctlInit.enabled` | `false` | `true` |

### 리소스 요구사항

#### 단일 노드
- **CPU**: 1000m
- **Memory**: 2Gi
- **Java Heap**: 1G

#### 3노드 클러스터 (각 노드)
- **CPU**: 500m
- **Memory**: 1Gi  
- **Java Heap**: 512m

## 💾 인덱스 및 스냅샷 관리

### 인덱스 템플릿 설정 (선언적 관리)

#### 자동 인덱스 템플릿 생성

OpenSearch values.yaml에 인덱스 템플릿 설정이 포함되어 있어 샤드 및 레플리카를 선언적으로 관리할 수 있습니다:

```yaml
# values.yaml 또는 values-cluster.yaml
indexTemplate:
  enabled: true
  name: "logs-template"
  patterns: ["*-logs*", "*-log-*"]
  shards: 3
  replicas: 1
  refreshInterval: "5s"
  codec: "best_compression"
  priority: 100
```

#### 작동 방식

1. **Helm Hook**: OpenSearch 설치/업그레이드 시 자동으로 인덱스 템플릿 생성
2. **자동 적용**: 패턴에 맞는 새 인덱스는 자동으로 설정된 샤드/레플리카 적용
3. **기존 인덱스**: 영향 없음 (이미 생성된 인덱스는 변경되지 않음)

#### 수동 인덱스 템플릿 생성 (옵션)

```bash
# 독립적인 Job으로 인덱스 템플릿 생성
kubectl apply -f templates/opensearch-index-template.yaml

# 또는 직접 API 호출
curl -X PUT "localhost:9200/_index_template/logs-template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["*-logs*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1
    }
  }
}'
```

#### 인덱스 템플릿 확인

```bash
# 템플릿 목록 확인
curl -s "http://localhost:9200/_index_template"

# 특정 템플릿 확인
curl -s "http://localhost:9200/_index_template/logs-template"
```

### 스냅샷 리포지토리 설정

데이터 백업을 위한 스냅샷 리포지토리를 구성합니다:

```bash
# 스냅샷 리포지토리 생성
curl -X PUT "localhost:9200/_snapshot/backup-repo" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/opensearch/snapshots"
  }
}
'

# 스냅샷 생성
curl -X PUT "localhost:9200/_snapshot/backup-repo/snapshot-$(date +%Y%m%d)" -H 'Content-Type: application/json' -d'
{
  "indices": "*-logs*",
  "ignore_unavailable": true,
  "include_global_state": false
}
'
```

## 📈 모니터링

### Prometheus 메트릭

OpenSearch와 Fluent Bit 모두 Prometheus 메트릭을 제공합니다:

#### OpenSearch 메트릭
- **엔드포인트**: `http://opensearch-cluster-master:9200/_prometheus/metrics`
- **ServiceMonitor**: 자동으로 생성됨

#### Fluent Bit 메트릭
- **엔드포인트**: `http://fluent-bit-pod:2020/api/v1/metrics/prometheus`
- **포트**: 2020

### 대시보드 접근

```bash
# OpenSearch Dashboards 포트 포워딩
kubectl port-forward -n logging svc/opensearch-dashboards 5601:5601

# 브라우저에서 http://localhost:5601 접근
```

### 헬스 체크

```bash
# 클러스터 상태 확인
kubectl port-forward -n logging svc/opensearch-cluster-master 9200:9200
curl -s "http://localhost:9200/_cluster/health?pretty"

# 노드 목록 확인
curl -s "http://localhost:9200/_cat/nodes?v"

# 인덱스 목록 확인  
curl -s "http://localhost:9200/_cat/indices?v"
```

## 🔧 트러블슈팅

### 일반적인 문제들

#### 1. Fluent Bit 로그 수집 안됨

**증상**: OpenSearch에 로그가 수집되지 않음

**해결방법**:
```bash
# Fluent Bit 로그 확인
kubectl logs -n logging daemonset/fluent-bit

# 설정 확인
kubectl get configmap -n logging fluent-bit-config -o yaml

# 연결 테스트
kubectl exec -n logging $(kubectl get pods -n logging -l app.kubernetes.io/name=fluentbit -o jsonpath='{.items[0].metadata.name}') -- curl -I http://opensearch-cluster-master:9200
```

#### 1-1. 다른 클러스터 배포 시 공통 에러

**증상**: 새 클러스터에 Fluent Bit 배포 시 에러 발생

**일반적인 원인과 해결책**:

```bash
# 1. 네임스페이스 생성 확인
kubectl create namespace logging

# 2. 클러스터별 overlay 설정 확인
ls -la kustomization/fluent-bit/overlays/

# 3. OpenSearch 호스트명 확인
# patches/cluster-config.yaml에서 Host 설정이 올바른지 확인
Host opensearch-cluster-master  # 같은 클러스터 내
# 또는
Host external-opensearch.domain.com  # 외부 클러스터

# 4. 권한 문제 해결
kubectl apply -f kustomization/fluent-bit/base/rbac.yaml

# 5. 설정 적용 확인
kubectl get configmap -n logging fluent-bit-config
kubectl get daemonset -n logging fluent-bit

# 6. 파드 상태 확인
kubectl get pods -n logging -l app.kubernetes.io/name=fluentbit
kubectl describe pods -n logging -l app.kubernetes.io/name=fluentbit
```

**새 클러스터용 overlay 생성**:
```bash
# 1. 새 overlay 디렉토리 생성
mkdir -p kustomization/fluent-bit/overlays/new-cluster-name

# 2. kustomization.yaml 복사 및 수정
cp kustomization/fluent-bit/overlays/k3d-alloy-kafka-dev/kustomization.yaml \
   kustomization/fluent-bit/overlays/new-cluster-name/

# 3. patches 디렉토리 및 설정 복사
cp -r kustomization/fluent-bit/overlays/k3d-alloy-kafka-dev/patches \
      kustomization/fluent-bit/overlays/new-cluster-name/

# 4. cluster-config.yaml에서 클러스터명과 OpenSearch 호스트 수정
# - cluster_name: new-cluster-name
# - Host: your-opensearch-host
# - Index: new-cluster-name-logs
```

#### 2. OpenSearch 부트스트랩 실패

**증상**: `max virtual memory areas vm.max_map_count [65530] is too low`

**해결방법**:
```bash
# values-cluster.yaml에서 sysctlInit 활성화
sysctlInit:
  enabled: true
```

#### 3. 클러스터 노드 간 연결 실패

**증상**: 노드들이 계속 클러스터에서 제거됨

**해결방법**:
- 리소스 부족: CPU/Memory 요구사항 확인
- 네트워크 정책: 9300 포트 통신 확인
- 단일 노드로 되돌리기: `values.yaml` 사용

#### 4. 메모리 부족으로 파드 스케줄링 실패

**증상**: `Insufficient memory`

**해결방법**:
```bash
# 리소스 요구사항 감소
resources:
  requests:
    memory: "1Gi"
  limits:
    memory: "1Gi"

# Java 힙 크기 조정
opensearchJavaOpts: "-Xmx512m -Xms512m"
```

### 로그 분석

#### Fluent Bit 로그 레벨 변경
```yaml
[SERVICE]
    Log_Level debug  # info -> debug로 변경
```

#### OpenSearch 로그 확인
```bash
kubectl logs -n logging opensearch-cluster-master-0 --tail=50
```

## 📝 참고사항

### 프로덕션 배포 체크리스트

- [ ] 충분한 리소스 확보 (CPU 6+ cores, Memory 16+ GB)
- [ ] 영구 볼륨 백업 전략 수립
- [ ] 스냅샷 자동화 스크립트 설정
- [ ] 모니터링 및 알림 구성
- [ ] 로그 보존 정책 설정
- [ ] 보안 설정 검토 (현재는 보안 비활성화 상태)

### 보안 고려사항

현재 설정은 개발/테스트 환경용으로 보안이 비활성화되어 있습니다:

```yaml
# 프로덕션에서는 보안 활성화 권장
securityConfig:
  enabled: true  # false -> true로 변경

config:
  opensearch.yml: |
    plugins.security.disabled: false  # true -> false로 변경
```

---

**Last Updated**: 2025-09-27  
**Version**: 1.0.0