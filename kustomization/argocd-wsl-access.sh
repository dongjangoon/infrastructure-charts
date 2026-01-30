#!/bin/bash
# WSL 환경에서 ArgoCD UI 접근을 위한 포트포워딩 스크립트

echo "ArgoCD UI 접근을 위한 포트포워딩 시작..."
echo ""
echo "접속 방법:"
echo "  Windows 브라우저: http://localhost:8080"
echo "  WSL: http://${WSL_IP}:8080"
echo ""
echo "초기 비밀번호 확인:"
echo "  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"
echo ""
echo "포트포워딩 중... (Ctrl+C로 종료)"
echo ""

kubectl port-forward svc/argocd-server -n argocd 8080:80 --address 0.0.0.0
