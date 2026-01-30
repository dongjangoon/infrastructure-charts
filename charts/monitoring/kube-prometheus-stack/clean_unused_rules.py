#!/usr/bin/env python3

import yaml
from pathlib import Path

def clean_unused_rules():
    """매핑되지 않은 job을 사용하는 규칙들 제거"""
    
    # 유지할 job들 (매핑된 것들)
    allowed_jobs = {
        'kubernetes-service-endpoints',
        'kubernetes-nodes-cadvisor', 
        'kubernetes-apiservers'
    }
    
    input_file = Path("prometheus-rules-standard/rules-updated.yml")
    output_file = Path("prometheus-rules-standard/rules-clean.yml")
    
    print("🧹 사용하지 않는 규칙들 제거 중...")
    print("=" * 50)
    
    # YAML 파일 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        rules_data = yaml.safe_load(f)
    
    cleaned_groups = []
    removed_stats = {'groups': 0, 'rules': 0}
    
    for group in rules_data.get('groups', []):
        cleaned_rules = []
        group_name = group.get('name', 'unknown')
        
        for rule in group.get('rules', []):
            expr = rule.get('expr', '')
            
            # job="..." 패턴이 있는지 확인
            has_job_filter = 'job="' in expr
            
            if has_job_filter:
                # 허용된 job인지 확인
                has_allowed_job = any(f'job="{job}"' in expr for job in allowed_jobs)
                
                if has_allowed_job:
                    cleaned_rules.append(rule)
                else:
                    removed_stats['rules'] += 1
                    print(f"  ❌ 제거: {group_name} - {rule.get('alert', rule.get('record', 'unknown'))}")
            else:
                # job 필터가 없는 규칙은 유지
                cleaned_rules.append(rule)
        
        # 규칙이 남아있는 그룹만 유지
        if cleaned_rules:
            group['rules'] = cleaned_rules
            cleaned_groups.append(group)
            print(f"  ✅ 유지: {group_name} ({len(cleaned_rules)}개 규칙)")
        else:
            removed_stats['groups'] += 1
            print(f"  🗑️  그룹 제거: {group_name} (모든 규칙 제거됨)")
    
    # 정리된 데이터 저장
    cleaned_data = {'groups': cleaned_groups}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(cleaned_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"\n📁 정리된 파일: {output_file}")
    print(f"📊 정리 결과:")
    print(f"   • 제거된 그룹: {removed_stats['groups']}개")
    print(f"   • 제거된 규칙: {removed_stats['rules']}개") 
    print(f"   • 남은 그룹: {len(cleaned_groups)}개")
    
    # 남은 규칙 수 계산
    total_remaining_rules = sum(len(group.get('rules', [])) for group in cleaned_groups)
    print(f"   • 남은 규칙: {total_remaining_rules}개")
    
    # 유지된 job들 확인
    check_remaining_jobs_in_clean_file(output_file)

def check_remaining_jobs_in_clean_file(file_path):
    """정리된 파일에서 남은 job들 확인"""
    
    import re
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    job_patterns = re.findall(r'job="([^"]+)"', content)
    remaining_jobs = {}
    
    for job in job_patterns:
        if job not in remaining_jobs:
            remaining_jobs[job] = 0
        remaining_jobs[job] += 1
    
    print(f"\n✅ 정리된 파일의 job 분포:")
    for job, count in sorted(remaining_jobs.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {job:<35} ({count}회)")

if __name__ == "__main__":
    clean_unused_rules()