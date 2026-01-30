# K6를 사용한 쿠버네티스 HPA 및 Cluster AutoScaling 테스트

이 프로젝트는 폐쇄망 쿠버네티스 멀티 클러스터 환경에서 HPA(Horizontal Pod Autoscaler)와 Cluster AutoScaling 테스트를 위한 k6 부하 테스트 도구 및 설정을 제공합니다.

## 📋 목차

- [사전 요구사항](#사전-요구사항)
- [폐쇄망 k6 설치](#폐쇄망-k6-설치)
- [테스트 환경 구성](#테스트-환경-구성)
- [부하 테스트 실행](#부하-테스트-실행)
- [모니터링 및 검증](#모니터링-및-검증)
- [파일 구성](#파일-구성)

## 🔧 사전 요구사항

### 클러스터 환경
- Kubernetes 클러스터 (멀티 클러스터 환경)
- Metrics Server 설치 및 동작
- Cluster Autoscaler 구성
- HPA 기능 활성화

### 필요한 권한
```bash
# HPA 및 Pod 스케일링 확인 권한
kubectl auth can-i get hpa
kubectl auth can-i get pods
kubectl auth can-i get nodes
```

## 📦 폐쇄망 k6 설치

### 1. 인터넷 연결 환경에서 바이너리 다운로드

k6 GitHub Releases 페이지에서 플랫폼에 맞는 바이너리를 다운로드합니다:

**다운로드 링크**: https://github.com/grafana/k6/releases

#### Linux (x64)
```bash
# 최신 버전 확인 후 다운로드 (예: v0.47.0)
wget https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz
```

#### Linux (ARM64)
```bash
wget https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-arm64.tar.gz
```

#### Windows
```bash
# Windows 환경용
curl -L https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-windows-amd64.zip -o k6-windows.zip
```

### 2. 폐쇄망 환경으로 파일 전송

- USB, 외장하드 등 물리적 매체를 통해 다운로드한 바이너리 파일을 폐쇄망으로 전송
- 또는 승인된 파일 전송 시스템 사용

### 3. 폐쇄망에서 k6 설치

#### Linux/macOS
```bash
# 압축 해제
tar -xzf k6-v0.47.0-linux-amd64.tar.gz

# 실행 권한 부여
chmod +x k6

# PATH에 추가 (예: /usr/local/bin)
sudo mv k6 /usr/local/bin/

# 설치 확인
k6 version
```

#### Windows
```bash
# ZIP 압축 해제
unzip k6-v0.47.0-windows-amd64.zip

# 환경변수 PATH에 추가하거나 직접 실행
./k6.exe version
```

### 4. 설치 검증

```bash
# k6 버전 확인
k6 version

# 도움말 확인
k6 --help
```

## 🚀 테스트 환경 구성

### 1. 테스트 애플리케이션 배포

```bash
# 테스트용 Nginx 애플리케이션 배포
kubectl apply -f test-app-deployment.yaml

# 배포 확인
kubectl get pods -l app=test-app
kubectl get svc test-app-service
```

### 2. HPA 설정

```bash
# HPA 구성 적용
kubectl apply -f test-app-hpa.yaml

# HPA 상태 확인
kubectl get hpa test-app-hpa
kubectl describe hpa test-app-hpa
```

### 3. Metrics Server 확인

```bash
# Metrics Server 동작 확인
kubectl get pods -n kube-system | grep metrics-server
kubectl top nodes
kubectl top pods -n default
```

## 🏃 부하 테스트 실행

### 1. 기본 부하 테스트

```bash
# 간단한 부하 테스트 실행
k6 run simple-load-test.js

# 실시간 결과 확인
k6 run --out cloud simple-load-test.js
```

### 2. HPA 테스트 (권장)

```bash
# HPA 동작 확인용 부하 테스트
k6 run load-test.js

# 백그라운드 실행
nohup k6 run load-test.js > load-test.log 2>&1 &
```

### 3. Cluster AutoScaling 테스트

```bash
# 높은 부하로 노드 스케일링 유발
k6 run stress-test.js

# 리소스 사용량이 높은 테스트
k6 run --vus 200 --duration 15m stress-test.js
```

### 4. 테스트 옵션 사용자 정의

```bash
# 사용자 수와 지속 시간 직접 설정
k6 run --vus 50 --duration 10m load-test.js

# 결과를 JSON으로 출력
k6 run --out json=results.json load-test.js
```

## 📊 모니터링 및 검증

### 1. HPA 모니터링

```bash
# HPA 상태 실시간 모니터링
kubectl get hpa test-app-hpa -w

# Pod 스케일링 실시간 확인
kubectl get pods -l app=test-app -w

# HPA 이벤트 확인
kubectl describe hpa test-app-hpa
```

### 2. 리소스 사용량 확인

```bash
# Pod CPU/메모리 사용량
kubectl top pods -l app=test-app

# 노드 리소스 사용량
kubectl top nodes

# 상세한 Pod 리소스 정보
kubectl describe pods -l app=test-app
```

### 3. Cluster AutoScaling 확인

```bash
# 노드 수 변화 모니터링
kubectl get nodes -w

# Cluster Autoscaler 로그 확인
kubectl logs -n kube-system deployment/cluster-autoscaler

# Node 스케일링 이벤트
kubectl get events --sort-by='.lastTimestamp' | grep node
```

### 4. 테스트 결과 분석

```bash
# k6 테스트 요약 결과 확인
cat load-test-summary.json

# 테스트 로그 확인
tail -f load-test.log
```

## 📁 파일 구성

```
k6/
├── README.md                    # 이 파일
├── test-app-deployment.yaml     # 테스트용 애플리케이션 배포 설정
├── test-app-hpa.yaml           # HPA 설정
├── load-test.js                # 메인 부하 테스트 스크립트
├── simple-load-test.js         # 간단한 부하 테스트
└── stress-test.js              # 스트레스 테스트 (노드 스케일링용)
```

### 각 파일 설명

#### `test-app-deployment.yaml`
- 테스트용 Nginx 애플리케이션 Deployment 및 Service
- CPU/메모리 리소스 제한 설정으로 HPA 동작 보장

#### `test-app-hpa.yaml`
- HPA 설정 (CPU 50%, 메모리 70% 임계값)
- 1~10개 Pod 자동 스케일링
- 스케일업/다운 정책 포함

#### `load-test.js`
- 종합적인 부하 테스트 스크립트
- 단계별 부하 증가 시나리오
- 상세한 메트릭 및 결과 요약 제공

#### `simple-load-test.js`
- 기본적인 부하 테스트
- HPA 동작 확인용 최소 설정

#### `stress-test.js`
- 고부하 테스트로 노드 오토스케일링 유발
- 클러스터 자원 한계 테스트용

## 🔍 테스트 시나리오 예시

### 시나리오 1: HPA 기본 동작 확인
1. `kubectl apply -f test-app-deployment.yaml`
2. `kubectl apply -f test-app-hpa.yaml`
3. `k6 run simple-load-test.js`
4. `kubectl get hpa -w`로 스케일링 확인

### 시나리오 2: 단계적 부하 증가 테스트
1. `k6 run load-test.js`
2. 별도 터미널에서 `kubectl get pods -l app=test-app -w`
3. CPU 사용률에 따른 Pod 증가 관찰

### 시나리오 3: 노드 오토스케일링 테스트
1. `k6 run stress-test.js`
2. `kubectl get nodes -w`로 노드 증가 확인
3. 클러스터 오토스케일러 로그 모니터링

## ⚠️ 주의사항

1. **리소스 모니터링**: 테스트 실행 중 클러스터 리소스를 지속적으로 모니터링
2. **테스트 환경**: 운영 환경이 아닌 개발/테스트 환경에서 실행 권장
3. **정리**: 테스트 완료 후 불필요한 리소스 정리
   ```bash
   kubectl delete -f test-app-hpa.yaml
   kubectl delete -f test-app-deployment.yaml
   ```
4. **네트워크**: 폐쇄망에서 k6가 Service DNS를 해석할 수 있도록 네트워크 설정 확인

## 🚨 문제 해결

### HPA가 동작하지 않는 경우
- Metrics Server 동작 상태 확인
- Pod에 리소스 requests 설정 확인
- HPA 대상 메트릭 수집 가능 여부 확인

### k6 테스트가 실패하는 경우
- Service DNS 이름 해석 가능 여부 확인
- Pod가 정상적으로 실행 중인지 확인
- 네트워크 정책 및 방화벽 설정 확인

### 노드 오토스케일링이 발생하지 않는 경우
- Cluster Autoscaler 설정 및 동작 상태 확인
- 노드 그룹의 최대 크기 설정 확인
- 리소스 요청량이 기존 노드 용량을 초과하는지 확인