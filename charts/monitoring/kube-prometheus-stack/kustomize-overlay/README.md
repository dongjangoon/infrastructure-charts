# Prometheus Rules Kustomize Overlay

이 디렉토리는 추출된 Prometheus rules를 기존 Prometheus 설정에 추가하는 Kustomize overlay입니다.

## 📁 구조
```
kustomize-overlay/
├── kustomization.yaml              # 메인 Kustomize 설정
├── prometheus-config-patch.yaml    # Prometheus 설정 패치
├── prometheus-deployment-patch.yaml # Deployment 볼륨 마운트 패치
└── README.md                      # 이 파일
```

## 🔧 사용법

### 1. 환경에 맞게 수정
```bash
# 실제 환경에 맞게 수정하세요
vim kustomization.yaml  # base 경로 수정
vim prometheus-config-patch.yaml  # configmap 이름 확인
vim prometheus-deployment-patch.yaml  # deployment 이름 확인
```

### 2. 배포 미리보기
```bash
kustomize build kustomize-overlay/
```

### 3. 실제 배포
```bash
kubectl apply -k kustomize-overlay/
```

## ⚙️ 주요 수정 포인트

### kustomization.yaml
- `resources`: 실제 base prometheus 경로로 수정
- `namespace`: 프로메테우스가 설치된 네임스페이스

### prometheus-config-patch.yaml
- `metadata.name`: 실제 prometheus config ConfigMap 이름
- `rule_files`: 기존 rule_files에 추가 경로 포함

### prometheus-deployment-patch.yaml
- `metadata.name`: 실제 prometheus Deployment/StatefulSet 이름
- `containers[].name`: 실제 prometheus 컨테이너 이름

## 🎯 동작 원리

1. **ConfigMap 생성**: `rules-clean.yml`을 기반으로 `prometheus-additional-rules` ConfigMap 생성
2. **설정 패치**: 기존 `prometheus.yml`에 추가 rule_files 경로 추가
3. **볼륨 마운트**: Prometheus Pod에 추가 ConfigMap 마운트
4. **자동 로드**: Prometheus가 새로운 rules 파일 자동 감지 및 로드

## 📋 확인 방법

```bash
# ConfigMap 확인
kubectl get configmap prometheus-additional-rules -n monitoring

# Rules 로드 확인
kubectl logs deployment/prometheus -n monitoring

# Prometheus UI에서 확인
# Status → Rules 에서 추가된 규칙들 확인
```

## 🚨 주의사항

1. **네임스페이스**: Prometheus와 동일한 네임스페이스 사용
2. **권한**: Prometheus ServiceAccount에 ConfigMap 읽기 권한 필요
3. **재시작**: 설정 변경 후 Prometheus Pod 재시작 필요할 수 있음
4. **백업**: 기존 설정 백업 후 적용 권장