#!/usr/bin/env python3

import subprocess
import yaml
import re
import os
from pathlib import Path

def extract_rules_for_standard_prometheus():
    """일반 Prometheus용 rules.yml 파일 생성"""
    
    output_dir = Path("prometheus-rules-standard")
    output_dir.mkdir(exist_ok=True)
    
    print("=== 일반 Prometheus용 Rules 추출 ===")
    
    # 모든 rule 파일 찾기
    rule_dir = Path("templates/prometheus/rules-1.14")
    rule_files = list(rule_dir.glob("*.yaml"))
    
    all_groups = []
    
    for rule_file in rule_files:
        print(f"🔄 처리 중: {rule_file.name}")
        
        try:
            # Helm template 렌더링
            cmd = [
                "helm", "template", ".", 
                "--values", "values-dev.yaml",
                "--show-only", str(rule_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"  ⚠️  렌더링 실패: {rule_file.name}")
                continue
                
            # YAML 파싱
            try:
                yaml_content = yaml.safe_load(result.stdout)
                
                if yaml_content and 'spec' in yaml_content and 'groups' in yaml_content['spec']:
                    groups = yaml_content['spec']['groups']
                    
                    # 각 그룹 처리
                    for group in groups:
                        if 'rules' in group:
                            processed_group = process_rules_group(group)
                            if processed_group and processed_group.get('rules'):
                                all_groups.append(processed_group)
                                print(f"  ✅ 그룹 추가: {group.get('name', 'unknown')}")
                
            except yaml.YAMLError as e:
                print(f"  ❌ YAML 파싱 실패: {rule_file.name}: {e}")
                
        except Exception as e:
            print(f"  ❌ 처리 실패: {rule_file.name}: {e}")
    
    # 최종 rules.yml 생성
    if all_groups:
        rules_content = {'groups': all_groups}
        
        # 일반 Prometheus용 파일 저장
        output_file = output_dir / "rules.yml"
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(rules_content, f, default_flow_style=False, allow_unicode=True)
        
        print(f"\n✅ 일반 Prometheus용 rules.yml 생성: {output_file}")
        print(f"📊 총 {len(all_groups)}개 그룹, {sum(len(g.get('rules', [])) for g in all_groups)}개 규칙")
        
        # 사용법 안내 파일 생성
        create_usage_guide(output_dir)
    else:
        print("❌ 추출할 규칙이 없습니다.")

def process_rules_group(group):
    """규칙 그룹을 일반 Prometheus용으로 변환"""
    
    processed_group = {
        'name': group.get('name', 'unknown'),
        'rules': []
    }
    
    if 'interval' in group:
        processed_group['interval'] = group['interval']
    
    for rule in group.get('rules', []):
        processed_rule = process_single_rule(rule)
        if processed_rule:
            processed_group['rules'].append(processed_rule)
    
    return processed_group

def process_single_rule(rule):
    """개별 규칙을 일반 Prometheus용으로 변환"""
    
    if 'expr' not in rule:
        return None
        
    expr = rule['expr']
    
    # 클러스터 라벨 제거 (선택적)
    # 방법 1: 클러스터 조건 완전 제거
    expr = re.sub(r',\s*cluster\s*=~?\s*"[^"]*"', '', expr)
    expr = re.sub(r'cluster\s*=~?\s*"[^"]*",\s*', '', expr)
    expr = re.sub(r'\{\s*cluster\s*=~?\s*"[^"]*"\s*\}', '{}', expr)
    
    # BY 절에서 cluster 제거
    expr = re.sub(r'BY\s*\(\s*cluster,\s*', 'BY (', expr)
    expr = re.sub(r'BY\s*\([^)]*cluster,\s*([^)]*)\)', r'BY (\1)', expr)
    expr = re.sub(r'BY\s*\([^)]*,\s*cluster\s*\)', lambda m: m.group(0).replace(', cluster', ''), expr)
    
    # group_left, group_right에서 cluster 제거
    expr = re.sub(r'group_left\([^)]*cluster[^)]*\)', 'group_left()', expr)
    expr = re.sub(r'group_right\([^)]*cluster[^)]*\)', 'group_right()', expr)
    
    # 빈 BY() 절 정리
    expr = re.sub(r'BY\s*\(\s*\)', '', expr)
    
    processed_rule = {
        'expr': expr.strip()
    }
    
    # 다른 필드들 복사
    for key in ['alert', 'record', 'for', 'keep_firing_for', 'labels', 'annotations']:
        if key in rule:
            processed_rule[key] = rule[key]
    
    return processed_rule

def create_usage_guide(output_dir):
    """사용법 안내 파일 생성"""
    
    guide_content = """# Prometheus Rules 사용법

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
"""
    
    guide_file = output_dir / "README.md"
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)

if __name__ == "__main__":
    extract_rules_for_standard_prometheus()