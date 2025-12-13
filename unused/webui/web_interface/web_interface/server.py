#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import subprocess
from datetime import datetime
from urllib.parse import parse_qs, urlparse

PORT = 9999  # Змінено з 8888 на 9999 для уникнення конфліктів

# Отримати абсолютний шлях до директорії скрипта
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, 'templates')
STATIC_DIR = os.path.join(SCRIPT_DIR, 'static')

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            template_path = os.path.join(TEMPLATES_DIR, 'index.html')
            try:
                with open(template_path, 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Template not found: {template_path}")
        elif self.path == '/api/status':
            self.send_json_response(self.get_system_status())
        elif self.path == '/api/configs/windsurf':
            self.send_json_response(self.get_configs('windsurf'))
        elif self.path == '/api/configs/vscode':
            self.send_json_response(self.get_configs('vscode'))
        elif self.path.startswith('/static/'):
            super().do_GET()
        else:
            self.send_error(404)
    
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            if self.path == '/api/cleanup/windsurf':
                result = self.run_cleanup('windsurf')
                self.send_json_response(result)
            elif self.path == '/api/cleanup/vscode':
                result = self.run_cleanup('vscode')
                self.send_json_response(result)
            elif self.path == '/api/check/windsurf':
                result = self.run_check('windsurf')
                self.send_json_response(result)
            elif self.path == '/api/check/vscode':
                result = self.run_check('vscode')
                self.send_json_response(result)
            elif self.path == '/api/full-cycle':
                result = self.run_full_cycle()
                self.send_json_response(result)
            else:
                self.send_error(404)
        except json.JSONDecodeError as e:
            self.send_json_response({'success': False, 'error': f'Invalid JSON: {str(e)}'})
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_system_status(self):
        hostname = subprocess.getoutput("scutil --get HostName 2>/dev/null || echo 'Not set'")
        
        # Більш гнучка перевірка Windsurf
        windsurf_installed = (
            os.path.exists('/Applications/Windsurf.app') or
            os.path.exists('/Applications/windsurf.app') or
            subprocess.getoutput("which windsurf 2>/dev/null") != "" or
            subprocess.getoutput("find /Applications -name '*indsurf*' -type d 2>/dev/null") != ""
        )
        
        # Більш гнучка перевірка VS Code
        vscode_installed = (
            os.path.exists('/Applications/Visual Studio Code.app') or
            os.path.exists('/Applications/Code.app') or
            subprocess.getoutput("which code 2>/dev/null") != "" or
            subprocess.getoutput("find /Applications -name '*Visual Studio Code*' -type d 2>/dev/null") != ""
        )
        
        # Використовувати абсолютні шляхи для конфігів
        parent_dir = os.path.dirname(SCRIPT_DIR)
        windsurf_configs_dir = os.path.join(parent_dir, 'configs')
        vscode_configs_dir = os.path.join(parent_dir, 'configs_vscode')
        
        windsurf_configs = 0
        vscode_configs = 0
        
        if os.path.exists(windsurf_configs_dir):
            try:
                windsurf_configs = len([f for f in os.listdir(windsurf_configs_dir) 
                                       if os.path.isdir(os.path.join(windsurf_configs_dir, f))])
            except Exception as e:
                print(f"Error counting windsurf configs: {e}")
        
        if os.path.exists(vscode_configs_dir):
            try:
                vscode_configs = len([f for f in os.listdir(vscode_configs_dir) 
                                     if os.path.isdir(os.path.join(vscode_configs_dir, f))])
            except Exception as e:
                print(f"Error counting vscode configs: {e}")
        
        return {
            'hostname': hostname,
            'windsurf': {'installed': windsurf_installed, 'configs': windsurf_configs},
            'vscode': {'installed': vscode_installed, 'configs': vscode_configs},
            'timestamp': datetime.now().isoformat()
        }
    
    def get_configs(self, system):
        # Використовувати абсолютні шляхи
        parent_dir = os.path.dirname(SCRIPT_DIR)
        configs_dir = os.path.join(parent_dir, 'configs' if system == 'windsurf' else 'configs_vscode')
        configs = []
        
        if os.path.exists(configs_dir):
            try:
                for config_name in os.listdir(configs_dir):
                    config_path = os.path.join(configs_dir, config_name)
                    if os.path.isdir(config_path):
                        metadata_file = os.path.join(config_path, 'metadata.json')
                        if os.path.exists(metadata_file):
                            try:
                                with open(metadata_file, 'r') as f:
                                    metadata = json.load(f)
                                    configs.append(metadata)
                            except (json.JSONDecodeError, IOError) as e:
                                print(f"Error reading {metadata_file}: {e}")
            except Exception as e:
                print(f"Error listing configs: {e}")
        
        return {'configs': configs}
    
    def run_cleanup(self, system):
        """Запустити повний cleanup скрипт з усім потенціалом"""
        parent_dir = os.path.dirname(SCRIPT_DIR)
        
        if system == 'windsurf':
            script_path = os.path.join(parent_dir, 'deep_windsurf_cleanup.sh')
        else:
            script_path = os.path.join(parent_dir, 'deep_vscode_cleanup.sh')
        
        if not os.path.exists(script_path):
            return {
                'success': False,
                'error': f'Script not found: {script_path}',
                'system': system
            }
        
        try:
            # Запустити скрипт з усім його потенціалом
            # - Валідація hostname
            # - Перевірка конфліктів IDE
            # - Розширене Keychain очищення
            # - Очищення state.vscdb (API ключі)
            # - Browser IndexedDB очищення
            # - Резервування конфігурацій
            # - Автовідновлення через 5 годин
            
            process = subprocess.Popen(
                ['bash', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=parent_dir
            )
            
            # Отримати вивід
            stdout, stderr = process.communicate(timeout=600)  # 10 хвилин timeout
            
            success = process.returncode == 0
            
            return {
                'success': success,
                'system': system,
                'returncode': process.returncode,
                'output': stdout,
                'error': stderr if stderr else None,
                'message': f'Cleanup for {system} completed' if success else f'Cleanup for {system} failed'
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                'success': False,
                'system': system,
                'error': 'Cleanup timeout (10 minutes exceeded)',
                'message': 'Cleanup took too long'
            }
        except Exception as e:
            return {
                'success': False,
                'system': system,
                'error': str(e),
                'message': f'Error running cleanup: {str(e)}'
            }
    
    def run_check(self, system):
        """Запустити перевірку якості cleanup"""
        parent_dir = os.path.dirname(SCRIPT_DIR)
        
        # Запустити check_identifier_cleanup.sh
        script_path = os.path.join(parent_dir, 'check_identifier_cleanup.sh')
        
        if not os.path.exists(script_path):
            return {
                'success': False,
                'error': f'Check script not found: {script_path}',
                'system': system
            }
        
        try:
            process = subprocess.Popen(
                ['bash', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=parent_dir
            )
            
            stdout, stderr = process.communicate(timeout=120)  # 2 хвилини
            
            success = process.returncode == 0
            
            return {
                'success': success,
                'system': system,
                'returncode': process.returncode,
                'output': stdout,
                'error': stderr if stderr else None,
                'message': 'Check completed' if success else 'Check found issues'
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                'success': False,
                'system': system,
                'error': 'Check timeout',
                'message': 'Check took too long'
            }
        except Exception as e:
            return {
                'success': False,
                'system': system,
                'error': str(e),
                'message': f'Error running check: {str(e)}'
            }

    def run_full_cycle(self):
        """Запустити повний цикл: cleanup → email → windsurf"""
        parent_dir = os.path.dirname(SCRIPT_DIR)
        
        script_path = os.path.join(parent_dir, 'windsurf_full_cycle.py')
        
        if not os.path.exists(script_path):
            return {
                'success': False,
                'error': f'Full cycle script not found: {script_path}'
            }
        
        try:
            process = subprocess.Popen(
                ['python3', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=parent_dir
            )
            
            stdout, stderr = process.communicate(timeout=1800)  # 30 хвилин
            
            success = process.returncode == 0
            
            return {
                'success': success,
                'returncode': process.returncode,
                'output': stdout,
                'error': stderr if stderr else None,
                'message': 'Full cycle completed' if success else 'Full cycle failed'
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                'success': False,
                'error': 'Full cycle timeout (30 minutes exceeded)',
                'message': 'Full cycle took too long'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Error running full cycle: {str(e)}'
            }

if __name__ == '__main__':
    # НЕ змінювати поточну директорію - використовувати абсолютні шляхи
    print(f"📂 Script directory: {SCRIPT_DIR}")
    print(f"📂 Templates directory: {TEMPLATES_DIR}")
    print(f"📂 Static directory: {STATIC_DIR}")
    
    # Перевірити чи існують необхідні директорії
    if not os.path.exists(TEMPLATES_DIR):
        print(f"⚠️  Templates directory not found: {TEMPLATES_DIR}")
        print(f"📂 Creating templates directory...")
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
    
    if not os.path.exists(STATIC_DIR):
        print(f"⚠️  Static directory not found: {STATIC_DIR}")
        print(f"📂 Creating static directory...")
        os.makedirs(STATIC_DIR, exist_ok=True)
    
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"🌐 Server running at http://localhost:{PORT}")
        print(f"✅ Press Ctrl+C to stop")
        httpd.serve_forever()
