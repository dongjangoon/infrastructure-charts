#!/usr/bin/env python3

import re
from pathlib import Path

def update_job_names():
    """Job 이름들을 다른 환경의 실제 job 이름으로 변경"""
    
    # Job 이름 매핑 테이블
    job_mapping = {
        'node-exporter': 'kubernetes-service-endpoints',
        'kube-state-metrics': 'kubernetes-service-endpoints', 
        'kubelet': 'kubernetes-nodes-cadvisor',
        'apiserver': 'kubernetes-apiservers',
        # 나머지는 일단 그대로 유지 (필요시 추가)
    }
    
    input_file = Path("prometheus-rules-standard/rules.yml")
    output_file = Path("prometheus-rules-standard/rules-updated.yml")
    
    print("🔄 Job 이름 업데이트 중...")
    print("=" * 50)
    
    # 파일 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 각 매핑에 대해 변경 수행
    changes_made = {}
    
    for old_job, new_job in job_mapping.items():
        # job="old_name" -> job="new_name" 패턴 변경
        pattern = f'job="{old_job}"'
        replacement = f'job="{new_job}"'
        
        old_content = content
        content = content.replace(pattern, replacement)
        
        # 변경 횟수 계산
        changes_count = old_content.count(pattern)
        if changes_count > 0:
            changes_made[old_job] = {'new_name': new_job, 'count': changes_count}
            print(f"✅ {old_job:25} → {new_job:30} ({changes_count}회 변경)")
    
    # 업데이트된 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n📁 업데이트된 파일: {output_file}")
    
    # 변경 요약
    if changes_made:
        print(f"\n📊 변경 요약:")
        total_changes = sum(info['count'] for info in changes_made.values())
        print(f"   총 {len(changes_made)}개 job, {total_changes}회 변경")
    else:
        print("\n⚠️  변경된 job이 없습니다.")
    
    # 남은 job들 확인
    check_remaining_jobs(content)

def check_remaining_jobs(content):
    """변경되지 않은 job들 확인"""
    
    print(f"\n🔍 남은 하드코딩된 job들:")
    print("-" * 40)
    
    # 모든 job 패턴 찾기
    job_patterns = re.findall(r'job="([^"]+)"', content)
    remaining_jobs = {}
    
    for job in job_patterns:
        if job not in remaining_jobs:
            remaining_jobs[job] = 0
        remaining_jobs[job] += 1
    
    # 빈도순으로 정렬해서 표시
    for job, count in sorted(remaining_jobs.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {job:<35} ({count}회)")
    
    if remaining_jobs:
        print(f"\n💡 필요시 이 job들도 추가로 매핑하세요:")
        print("   job_mapping에 추가 → 스크립트 재실행")

if __name__ == "__main__":
    update_job_names()