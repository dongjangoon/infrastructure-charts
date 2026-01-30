#!/usr/bin/env python3

import json
import glob
import re
import os
from pathlib import Path

def make_dashboards_portable():
    """환경 독립적인 대시보드로 변환"""
    
    input_dir = Path("dashboards-json")
    output_dir = Path("dashboards-portable")
    output_dir.mkdir(exist_ok=True)
    
    print("=== 환경 독립적 대시보드 생성 ===")
    
    for json_file in input_dir.glob("*.json"):
        if os.path.getsize(json_file) == 0:
            print(f"⚠️  빈 파일 건너뜀: {json_file.name}")
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                dashboard = json.load(f)
            
            print(f"🔄 처리 중: {json_file.name}")
            
            # 1. 데이터소스를 기본값으로 변경
            dashboard_str = json.dumps(dashboard)
            
            # 2. 클러스터 필터 제거 (선택적)
            # cluster=~"$cluster" -> 제거 또는 .*로 변경
            dashboard_str = re.sub(r',\s*cluster=~"\$cluster"', '', dashboard_str)
            dashboard_str = re.sub(r'cluster=~"\$cluster",\s*', '', dashboard_str)
            dashboard_str = re.sub(r'\{cluster=~"\$cluster"\}', '{}', dashboard_str)
            
            # 3. 템플릿 변수에서 클러스터 숨기기 설정
            dashboard = json.loads(dashboard_str)
            
            if 'templating' in dashboard and 'list' in dashboard['templating']:
                for var in dashboard['templating']['list']:
                    if var.get('name') == 'cluster':
                        # 클러스터 변수를 숨기고 전체 선택하도록 설정
                        var['hide'] = 2  # 완전히 숨김
                        var['current'] = {
                            "selected": True,
                            "text": ["All"],
                            "value": ["$__all"]
                        }
                        var['allValue'] = ".*"
                        var['includeAll'] = True
                        break
            
            # 4. 데이터소스 변수 기본값 설정
            if 'templating' in dashboard and 'list' in dashboard['templating']:
                for var in dashboard['templating']['list']:
                    if var.get('name') == 'datasource':
                        var['current'] = {
                            "selected": False,
                            "text": "default",
                            "value": "default"
                        }
                        break
            
            # 5. 저장
            output_file = output_dir / json_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(dashboard, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 변환 완료: {output_file}")
            
        except Exception as e:
            print(f"❌ 오류 {json_file.name}: {e}")

def create_cluster_specific_version():
    """클러스터별 맞춤 버전도 생성"""
    
    input_dir = Path("dashboards-json") 
    output_dir = Path("dashboards-cluster-agnostic")
    output_dir.mkdir(exist_ok=True)
    
    print("\n=== 클러스터 무관 버전 생성 ===")
    
    for json_file in input_dir.glob("*.json"):
        if os.path.getsize(json_file) == 0:
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                dashboard = json.load(f)
            
            dashboard_str = json.dumps(dashboard)
            
            # 모든 클러스터 참조 제거
            dashboard_str = re.sub(r',\s*cluster=~"\$cluster"', '', dashboard_str)
            dashboard_str = re.sub(r'cluster=~"\$cluster",\s*', '', dashboard_str)
            dashboard_str = re.sub(r',\s*cluster="\$cluster"', '', dashboard_str)
            dashboard_str = re.sub(r'cluster="\$cluster",\s*', '', dashboard_str)
            dashboard_str = re.sub(r'\{cluster=~"\$cluster"\}', '{}', dashboard_str)
            dashboard_str = re.sub(r'\{cluster="\$cluster"\}', '{}', dashboard_str)
            
            # {{cluster}} 레이블도 제거
            dashboard_str = re.sub(r'\{\{cluster\}\}:?', '', dashboard_str)
            dashboard_str = re.sub(r':?\{\{cluster\}\}', '', dashboard_str)
            
            dashboard = json.loads(dashboard_str)
            
            # 클러스터 관련 템플릿 변수 제거
            if 'templating' in dashboard and 'list' in dashboard['templating']:
                dashboard['templating']['list'] = [
                    var for var in dashboard['templating']['list'] 
                    if var.get('name') != 'cluster'
                ]
            
            output_file = output_dir / json_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(dashboard, f, indent=2, ensure_ascii=False)
                
            print(f"✅ 클러스터 무관 버전: {output_file}")
            
        except Exception as e:
            print(f"❌ 오류 {json_file.name}: {e}")

if __name__ == "__main__":
    make_dashboards_portable()
    create_cluster_specific_version()
    
    print(f"\n📁 결과:")
    print(f"  • dashboards-portable/     : 범용적 사용 (클러스터 변수 숨김)")
    print(f"  • dashboards-cluster-agnostic/ : 클러스터 무관 (클러스터 참조 완전 제거)")
    print(f"\n💡 사용법:")
    print(f"  1. Grafana에 임포트")
    print(f"  2. 데이터소스를 사용 중인 Prometheus로 변경")
    print(f"  3. 바로 사용 가능!")