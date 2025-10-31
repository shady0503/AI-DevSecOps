import json
import os
from pathlib import Path
from typing import Dict, List, Any

class SecurityReportParser:
    def __init__(self, brut_dir: str, parsed_dir: str):
        self.brut_dir = brut_dir
        self.parsed_dir = parsed_dir
        self.deduplicated_vulns = {}  # Key: (vuln_id, affected_component)
    
    def crawl_reports(self) -> List[tuple]:
        """Recursively find all .json report files"""
        files = []
        for root, dirs, filenames in os.walk(self.brut_dir):
            for filename in filenames:
                if filename.endswith('.json'):
                    file_path = os.path.join(root, filename)
                    report_type = self.detect_report_format(file_path)
                    pipeline_run = Path(root).name
                    if pipeline_run.isdigit():
                        files.append((file_path, report_type, int(pipeline_run)))  
        return files

    def detect_report_format(self, file_path: str) -> str:
        """Detect format from JSON structure"""
        if file_path.__contains__('container-scan'):
            return 'trivy'
        elif file_path.__contains__('sast-reports'):
            return 'semgrep'
        elif file_path.__contains__('iac-scan'):
            return 'checkov'
        elif file_path.__contains__('cve-reports'):
            return 'grype'
        elif file_path.__contains__('dast-reports'):
            return 'owasp-zap'

    def parse_report(self, file_path: str, report_type: str, run_id: int) -> List[Dict]:
        """Parse specific report format"""
        if report_type == 'trivy':
            return self.parse_trivy(file_path, run_id)
        elif report_type == 'grype':
            return self.parse_grype(file_path, run_id)
        elif report_type == 'checkov':
            return self.parse_checkov(file_path, run_id)
        elif report_type == 'semgrep':
            return self.parse_semgrep(file_path, run_id)
        elif report_type == 'owasp-zap':
            return self.parse_owasp_zap(file_path, run_id)
        return []

    def deduplicate_and_merge(self, vulns: List[Dict], run_id: int):
        """Merge vulnerabilities, deduplicating by vuln_id only and collecting affected components"""
        for vuln in vulns:
            key = vuln['vuln_id']
            if key in self.deduplicated_vulns:
                existing = self.deduplicated_vulns[key]
                # Merge affected components
                if vuln['affected_component'] not in existing['affected_components']:
                    existing['affected_components'].append(vuln['affected_component'])
                # Update metadata if more complete
                for field in ['cvss_score', 'fixed_version', 'description', 'cwe']:
                    if not existing.get(field) and vuln.get(field):
                        existing[field] = vuln[field]
                # Update pipeline runs and occurrences
                if run_id not in existing['pipeline_runs']:
                    existing['pipeline_runs'].append(run_id)
                existing['occurrences'] += vuln.get('occurrences', 1)
            else:
                # Initialize new entry
                vuln['affected_components'] = [vuln.pop('affected_component')]
                vuln['pipeline_runs'] = [run_id]
                vuln['occurrences'] = vuln.get('occurrences', 1)
                self.deduplicated_vulns[key] = vuln

    def parse_trivy(self, file_path: str, run_id: int) -> List[Dict]:
        """Parse Trivy container scan report"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        vulns = []
        for result in data.get('Results', []):
            for vuln in result.get('Vulnerabilities', []):
                cvss_score = vuln.get('CVSS', {}).get('nvd', {}).get('V3Score')
            
                new_vuln = {
                    "vuln_id": vuln.get('VulnerabilityID'),
                    "type": "vulnerability",
                    "title": vuln.get('Title'),
                    "affected_component": vuln.get('PkgName'),
                    "affected_version": vuln.get('InstalledVersion'),
                    "severity": vuln.get('Severity', 'UNKNOWN'),
                    "description": vuln.get('Description'),
                    "cvss_score": cvss_score,
                    "fixed_version": vuln.get('FixedVersion'),
                    "source": "trivy",
                }
                vulns.append(new_vuln)
        none_count = sum(1 for v in vulns if v.get('vuln_id') is None)
        if none_count > 0:
            print(f"Warning: {none_count} vulnerabilities found without IDs.")
        return vulns

    def parse_grype(self, file_path: str, run_id: int) -> List[Dict]:
        """Parse Grype SCA report"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        

        vulns = []
        for match in data.get('matches', []):
            vuln_data = match.get('vulnerability', {})
            artifact = match.get('artifact', {})
            
            cvss_data = vuln_data.get('cvss', [])
            cvss_score = cvss_data[0].get('metrics', {}).get('baseScore') if cvss_data else None
            
            cwe_list = vuln_data.get('cwes', [])
            cwe = cwe_list[0].get('cwe') if cwe_list else None
            
            fix_versions = vuln_data.get('fix', {}).get('versions', [])
            fixed_version = fix_versions[0] if fix_versions else None
            
            new_vuln = {
                "vuln_id": vuln_data.get('id'),
                "type": "dependency",
                "title": vuln_data.get('description', '').split('\n')[0],
                "affected_component": artifact.get('name'),
                "affected_version": artifact.get('version'),
                "severity": vuln_data.get('severity', 'UNKNOWN'),
                "description": vuln_data.get('description'),
                "cvss_score": cvss_score,
                "cwe": cwe,
                "fixed_version": fixed_version,
                "source": "grype",
            }
            vulns.append(new_vuln)
        none_count = sum(1 for v in vulns if v.get('vuln_id') is None)
        if none_count > 0:
            print(f"Warning: {none_count} vulnerabilities found without IDs.")
        return vulns

    def parse_checkov(self, file_path: str, run_id: int) -> List[Dict]:
        """Parse Checkov IaC scan report"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        vulns = []
        
        for result in data.get('results', {}).get('failed_checks', []):
            severity = result.get('check_result', {}).get('result', 'UNKNOWN')
            severity_map = {'passed': 'LOW', 'failed': 'HIGH'}
            
            new_vuln = {
                "vuln_id": result.get('check_id'),
                "type": "iac_violation",
                "title": result.get('check_name'),
                "affected_component": result.get('resource'),
                "affected_file": result.get('file_path'),
                "severity": severity_map.get(severity, 'MEDIUM'),
                "description": result.get('description'),
                "cvss_score": None,
                "cwe": None,
                "fixed_version": None,
                "source": "checkov",
            }
            vulns.append(new_vuln)
        none_count = sum(1 for v in vulns if v.get('vuln_id') is None)
        if none_count > 0:
            print(f"Warning: {none_count} vulnerabilities found without IDs.")
        return vulns

    def parse_semgrep(self, file_path: str, run_id: int) -> List[Dict]:
        """Parse Semgrep SAST report"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        vulns = []
        
        for result in data.get('results', []):
            severity = result.get('extra', {}).get('severity', 'INFO').upper()
            severity_map = {'INFO': 'LOW', 'WARNING': 'MEDIUM', 'ERROR': 'HIGH'}
            
            new_vuln = {
                "vuln_id": result.get('check_id'),
                "type": "sast_finding",
                "title": result.get('check_id'),
                "affected_component": result.get('path'),
                "affected_line": result.get('start', {}).get('line'),
                "severity": severity_map.get(severity, 'MEDIUM'),
                "description": result.get('extra', {}).get('message', ''),
                "cvss_score": None,
                "cwe": None,
                "fixed_version": None,
                "source": "semgrep",
            }
            vulns.append(new_vuln)
        none_count = sum(1 for v in vulns if v.get('vuln_id') is None)
        if none_count > 0:
            print(f"Warning: {none_count} vulnerabilities found without IDs.")
        
        return vulns
    def parse_owasp_zap(self, file_path: str, run_id: int) -> List[Dict]:
        """Parse OWASP ZAP DAST report"""
        try:
             with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

        vulns = []
    
        for site in data.get('site', []):
            for alert in site.get('alerts', []):
                new_vuln = {
                    "vuln_id": alert.get('pluginid'),
                    "type": "dast_finding",
                    "title": alert.get('name'),
                    "affected_component": site.get('name'),
                    "affected_url": alert.get('url'),
                    "severity": alert.get('riskcode').upper() if alert.get('riskcode') else 'MEDIUM',
                    "description": alert.get('desc'),
                    "cvss_score": None,
                    "cwe": alert.get('cwe'),
                    "fixed_version": None,
                    "source": "owasp-zap",
                }
                vulns.append(new_vuln)
    
        none_count = sum(1 for v in vulns if v.get('vuln_id') is None)
        if none_count > 0:
            print(f"Warning: {none_count} vulnerabilities found without IDs in {file_path}")
            vulns = [v for v in vulns if v.get('vuln_id') is not None]
        return vulns
    def run(self):
        """Main orchestration"""
        files = self.crawl_reports()
        for file_path, report_type, pipeline_run in files:
            vulns = self.parse_report(file_path, report_type, pipeline_run)
            vulns = [v for v in vulns if v.get('vuln_id') is not None]
            self.deduplicate_and_merge(vulns, pipeline_run)
        self.save_parsed_reports()
    
    def save_parsed_reports(self):
        """Save deduplicated vulnerabilities to JSON"""
        output_path = os.path.join(self.parsed_dir, 'deduplicated_vulnerabilities.json')
        os.makedirs(self.parsed_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(list(self.deduplicated_vulns.values()), f, indent=2)

if __name__ == "__main__":
    parser = SecurityReportParser(
        brut_dir=r"C:\Users\achra\Desktop\report\brut",
        parsed_dir=r"C:\Users\achra\Desktop\report\parsed"
    )
    parser.run()
    print(len(parser.deduplicated_vulns), "deduplicated vulnerabilities found.")
