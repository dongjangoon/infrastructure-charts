# Prometheus Rules 사용법

## 📁 파일 설명
- `rules.yml`: 일반 Prometheus용 변환된 규칙들

## 🔧 적용 방법

### 1. Prometheus 설정 파일에 추가
```yaml
# prometheus.yml
rule_files:
  - "rules.yml"
```

### 2. Docker Compose 사용 시
```yaml
version: '3'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./rules.yml:/etc/prometheus/rules.yml
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
```

### 3. Kubernetes ConfigMap 사용 시
```bash
kubectl create configmap prometheus-rules --from-file=rules.yml
```

## ⚠️  주의사항

1. **메트릭 이름 확인**: 
   - `container_*` 메트릭은 cAdvisor 필요
   - `kube_*` 메트릭은 kube-state-metrics 필요

2. **Job 이름 확인**:
   - `job="kubelet"` → 실제 kubelet job 이름으로 변경
   - `job="node-exporter"` → 실제 node-exporter job 이름으로 변경

3. **라벨 확인**:
   - 클러스터 라벨이 제거되었으므로 필요시 수동 추가

## 🛠️ 커스터마이징

필요에 따라 다음을 수정하세요:
- Job 이름들
- 임계값들 
- 라벨 셀렉터들
- 알림 수신자 설정
