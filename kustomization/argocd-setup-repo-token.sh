#!/bin/bash
# ArgoCD에 GitHub Personal Access Token으로 리포지토리 등록

echo "GitHub Personal Access Token으로 리포지토리를 등록합니다..."
echo ""
echo "사전 준비:"
echo "  1. GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)"
echo "  2. Generate new token (classic)"
echo "  3. 권한: repo (Full control of private repositories) 선택"
echo "  4. 생성된 토큰 복사"
echo ""

read -p "GitHub Personal Access Token을 입력하세요: " GITHUB_TOKEN

if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: 토큰이 입력되지 않았습니다."
    exit 1
fi

kubectl create secret generic github-repo-secret \
  --from-literal=username=dongjangoon \
  --from-literal=password=$GITHUB_TOKEN \
  --namespace argocd \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl label secret github-repo-secret \
  argocd.argoproj.io/secret-type=repository \
  --namespace argocd

kubectl patch secret github-repo-secret \
  --namespace argocd \
  --type merge \
  -p '{"stringData":{"type":"git","url":"https://github.com/dongjangoon/infrastructure-charts.git"}}'

echo ""
echo "✓ 리포지토리 인증 정보가 등록되었습니다!"
echo ""
echo "Application을 다시 동기화하세요:"
echo "  kubectl patch application app-of-apps -n argocd --type merge -p '{\"metadata\":{\"annotations\":{\"argocd.argoproj.io/refresh\":\"normal\"}}}'"
