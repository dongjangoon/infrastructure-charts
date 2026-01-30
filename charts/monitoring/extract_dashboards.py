#!/usr/bin/env python3

import subprocess
import yaml
import json
import os
from pathlib import Path

def extract_dashboards():
    """Extract Grafana dashboard JSONs from kube-prometheus-stack"""
    
    # Create output directory
    output_dir = Path("dashboards-json")
    output_dir.mkdir(exist_ok=True)
    
    # Find all dashboard YAML files
    dashboard_dir = Path("templates/grafana/dashboards-1.14")
    dashboard_files = list(dashboard_dir.glob("*.yaml"))
    
    print(f"Found {len(dashboard_files)} dashboard files")
    
    for yaml_file in dashboard_files:
        dashboard_name = yaml_file.stem
        print(f"Processing: {dashboard_name}")
        
        try:
            # Run helm template command
            cmd = [
                "helm", "template", ".", 
                "--values", "values-dev.yaml",
                "--show-only", str(yaml_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"  ERROR: Helm template failed for {dashboard_name}")
                print(f"  {result.stderr}")
                continue
                
            # Parse YAML output
            try:
                yaml_content = yaml.safe_load(result.stdout)
                
                # Extract JSON from data section
                if yaml_content and 'data' in yaml_content:
                    for key, value in yaml_content['data'].items():
                        if key.endswith('.json'):
                            # Parse and validate JSON
                            try:
                                json_data = json.loads(value)
                                
                                # Save to file
                                output_file = output_dir / f"{dashboard_name}.json"
                                with open(output_file, 'w', encoding='utf-8') as f:
                                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                                
                                print(f"  ✓ Extracted: {output_file}")
                                break
                            except json.JSONDecodeError as e:
                                print(f"  ERROR: Invalid JSON in {dashboard_name}: {e}")
                else:
                    print(f"  WARNING: No data section found in {dashboard_name}")
                    
            except yaml.YAMLError as e:
                print(f"  ERROR: Failed to parse YAML for {dashboard_name}: {e}")
                
        except subprocess.SubprocessError as e:
            print(f"  ERROR: Failed to run helm template for {dashboard_name}: {e}")

if __name__ == "__main__":
    extract_dashboards()
    print("\nDashboard extraction completed!")