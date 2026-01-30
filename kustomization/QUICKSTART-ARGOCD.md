# ArgoCD GitOps 빠른 시작 가이드

## 1️⃣ ArgoCD 설치 (30초)

```bash
# k3d 로컬 환경
kubectl apply -k argocd/overlays/k3d-central

# 설치 완료 대기
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
```

## 2️⃣ 초기 비밀번호 확인

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

## 3️⃣ ArgoCD UI 접속

```bash
# 포트 포워딩
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 브라우저에서 접속: https://localhost:8080
# Username: admin
# Password: 위에서 확인한 비밀번호
```

## 4️⃣ GitOps 활성화 (App of Apps 패턴)

```bash
# 모든 애플리케이션을 한 번에 GitOps로 관리
kubectl apply -f applications/app-of-apps.yaml

# 배포 상태 확인
kubectl get applications -n argocd

# 세부 정보 확인
kubectl get application monitoring -n argocd -o yaml
```

## 🎉 완료!

이제 Git에 push하면 자동으로 클러스터에 반영됩니다!

```bash
# 예: monitoring 설정 변경
vim monitoring/overlays/k3d-central/kustomization.yaml
git add .
git commit -m "feat: update monitoring config"
git push

# ArgoCD가 자동으로 감지하고 배포 (최대 3분)
# 또는 즉시 동기화:
kubectl patch application monitoring -n argocd --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"normal"}}}'
```

## 📊 현재 관리 중인 애플리케이션

- **monitoring**: Prometheus, Grafana, Jaeger 등
- **fluent-bit**: 로그 수집

## 🔧 유용한 명령어

```bash
# 모든 Application 상태 확인
kubectl get app -n argocd

# 특정 Application 동기화 상태
kubectl get app monitoring -n argocd -o jsonpath='{.status.sync.status}'

# Application 강제 동기화
kubectl patch app monitoring -n argocd --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"HEAD"}}}'

# ArgoCD 로그 확인
kubectl logs -n argocd deployment/argocd-server -f
```

## 📚 더 자세한 내용

`README-ARGOCD.md` 참고
