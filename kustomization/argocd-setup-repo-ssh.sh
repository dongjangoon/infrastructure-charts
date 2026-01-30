#!/bin/bash
# ArgoCD에 SSH 키로 Private GitHub 리포지토리 등록

echo "SSH 키로 GitHub 리포지토리를 ArgoCD에 등록합니다..."
echo ""
echo "사전 준비:"
echo "  1. SSH 키 생성: ssh-keygen -t ed25519 -C 'argocd@k3d'"
echo "  2. GitHub에 Deploy Key 등록: Settings > Deploy keys > Add deploy key"
echo "     (공개키: ~/.ssh/id_ed25519.pub 내용 복사)"
echo ""

# SSH 개인키 경로 (수정 필요)
SSH_PRIVATE_KEY_PATH="$HOME/.ssh/id_rsa"

if [ ! -f "$SSH_PRIVATE_KEY_PATH" ]; then
    echo "ERROR: SSH 개인키를 찾을 수 없습니다: $SSH_PRIVATE_KEY_PATH"
    exit 1
fi

kubectl create secret generic github-repo-secret \
  --from-file=sshPrivateKey=$SSH_PRIVATE_KEY_PATH \
  --namespace argocd \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl label secret github-repo-secret \
  argocd.argoproj.io/secret-type=repository \
  --namespace argocd

kubectl annotate secret github-repo-secret \
  managed-by=argocd.argoproj.io \
  --namespace argocd

kubectl patch secret github-repo-secret \
  --namespace argocd \
  --type merge \
  -p '{"stringData":{"type":"git","url":"git@github.com:dongjangoon/infrastructure-charts.git"}}'

echo ""
echo "✓ 리포지토리 인증 정보가 등록되었습니다!"
echo ""
echo "Application을 다시 동기화하세요:"
echo "  kubectl patch application app-of-apps -n argocd --type merge -p '{\"metadata\":{\"annotations\":{\"argocd.argoproj.io/refresh\":\"normal\"}}}'"
