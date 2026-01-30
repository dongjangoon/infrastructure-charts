# ArgoCD GitOps 구성 가이드

## 1. ArgoCD 설치

### k3d 로컬 환경에 설치
```bash
# ArgoCD 설치
kubectl apply -k argocd/overlays/k3d-central

# ArgoCD 설치 확인
kubectl get pods -n argocd

# 초기 admin 비밀번호 확인
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

### 프로덕션 환경에 설치
```bash
kubectl apply -k argocd/overlays/production
```

## 2. ArgoCD UI 접근

### k3d 로컬 환경
NodePort로 노출되어 있습니다:
```bash
# http://localhost:30080 또는 https://localhost:30443
# k3d 클러스터 생성 시 포트 매핑 필요:
# k3d cluster create mycluster -p "30080:30080@server:0" -p "30443:30443@server:0"
```

또는 포트포워딩:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# https://localhost:8080
```

### 로그인
- Username: `admin`
- Password: 위에서 확인한 초기 비밀번호

## 3. GitOps 구성 방법

### 방법 1: 개별 Application 배포
각 애플리케이션을 개별적으로 배포합니다.

```bash
# Monitoring 애플리케이션 배포
kubectl apply -f applications/monitoring-app.yaml

# Fluent-bit 애플리케이션 배포
kubectl apply -f applications/fluent-bit-app.yaml
```

### 방법 2: App of Apps 패턴 (권장)
하나의 Application이 모든 하위 Application을 관리합니다.

```bash
# App of Apps 배포 (모든 애플리케이션 자동 관리)
kubectl apply -f applications/app-of-apps.yaml
```

## 4. 동작 방식

1. **자동 동기화**: Git 리포지토리의 변경사항이 자동으로 클러스터에 반영됩니다
2. **Self-Heal**: 클러스터에서 수동으로 변경한 내용은 자동으로 Git 상태로 복구됩니다
3. **Prune**: Git에서 삭제된 리소스는 클러스터에서도 자동으로 삭제됩니다

## 5. Application 설정 커스터마이징

각 환경별로 다른 overlay를 사용하려면 Application의 `source.path`를 수정하세요:

```yaml
# 예: Production 환경용 monitoring
spec:
  source:
    path: kustomization/monitoring/overlays/production
```

## 6. 디렉토리 구조

```
kustomization/
├── argocd/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   └── namespace.yaml
│   └── overlays/
│       ├── k3d-central/
│       │   └── kustomization.yaml
│       └── production/
│           └── kustomization.yaml
├── applications/
│   ├── kustomization.yaml
│   ├── app-of-apps.yaml
│   ├── monitoring-app.yaml
│   └── fluent-bit-app.yaml
├── monitoring/
│   ├── base/
│   └── overlays/
│       ├── k3d-central/
│       └── production/
└── fluent-bit/
    ├── base/
    └── overlays/
        └── k3d-central/
```

## 7. ArgoCD CLI 사용 (선택사항)

```bash
# ArgoCD CLI 설치
brew install argocd  # macOS
# 또는
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd

# ArgoCD 로그인
argocd login localhost:30080 --insecure

# 애플리케이션 목록 확인
argocd app list

# 애플리케이션 동기화
argocd app sync monitoring

# 애플리케이션 상태 확인
argocd app get monitoring
```

## 8. 트러블슈팅

### Application이 동기화되지 않을 때
```bash
# Application 상태 확인
kubectl describe application monitoring -n argocd

# ArgoCD 서버 로그 확인
kubectl logs -n argocd deployment/argocd-server

# Application 수동 동기화
kubectl patch application monitoring -n argocd --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"HEAD"}}}'
```

### Git 리포지토리 인증 문제
Private 리포지토리의 경우 SSH 키 또는 토큰이 필요합니다:
```bash
# UI: Settings > Repositories > Connect Repo
# 또는 CLI:
argocd repo add https://github.com/dongjangoon/infrastructure-charts.git --username <username> --password <token>
```

## 9. 보안 권장사항

1. **초기 비밀번호 변경**
```bash
argocd account update-password
```

2. **RBAC 설정**: 필요한 경우 사용자별 권한 설정
3. **Private 리포지토리 사용**: 프로덕션에서는 private 리포지토리 권장
4. **TLS 활성화**: 프로덕션에서는 insecure 모드 비활성화

## 10. 다음 단계

- ArgoCD Notifications 설정 (Slack, Email 등)
- ArgoCD Image Updater 설정 (자동 이미지 태그 업데이트)
- ApplicationSet 사용 (여러 환경 자동 관리)
- Webhook 설정 (Git push 시 즉시 동기화)
