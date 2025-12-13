#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import subprocess
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from pathlib import Path

# Завантаження конфігурації з .env
def load_env():
    env_path = Path(__file__).parent.parent / '.env'
    env_example_path = Path(__file__).parent.parent / '.env.example'
    
    # Створити .env з .env.example якщо не існує
    if not env_path.exists() and env_example_path.exists():
        import shutil
        shutil.copy(env_example_path, env_path)
        print(f"⚙️  Створено .env з .env.example")
    
    # Завантажити змінні
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars

ENV_CONFIG = load_env()
PORT = int(ENV_CONFIG.get('WEB_PORT', 8888))

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('templates/index.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path == '/api/status':
            self.send_json_response(self.get_system_status())
        elif self.path == '/api/configs/windsurf':
            self.send_json_response(self.get_configs('windsurf'))
        elif self.path == '/api/configs/vscode':
            self.send_json_response(self.get_configs('vscode'))
        elif self.path == '/api/history':
            self.send_json_response(self.get_history())
        elif self.path == '/api/stealth/status':
            self.send_json_response(self.get_stealth_status())
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
            elif self.path == '/api/cleanup/windsurf/advanced':
                result = self.run_advanced_cleanup('windsurf')
                self.send_json_response(result)
            elif self.path == '/api/cleanup/windsurf/full':
                result = self.run_full_process('windsurf')
                self.send_json_response(result)
            elif self.path == '/api/cleanup/vscode':
                result = self.run_cleanup('vscode')
                self.send_json_response(result)
            elif self.path == '/api/cleanup/vscode/full':
                result = self.run_full_process('vscode')
                self.send_json_response(result)
            elif self.path == '/api/restore/windsurf':
                result = self.run_restore('windsurf', data.get('config', ''))
                self.send_json_response(result)
            elif self.path == '/api/restore/vscode':
                result = self.run_restore('vscode', data.get('config', ''))
                self.send_json_response(result)
            elif self.path.startswith('/api/stealth/cleanup/'):
                system = self.path.split('/')[-1]
                result = self.run_stealth_cleanup(system)
                self.send_json_response(result)
            elif self.path.startswith('/api/stealth/hardware-spoof/'):
                system = self.path.split('/')[-1]
                result = self.run_hardware_spoof(system)
                self.send_json_response(result)
            elif self.path == '/api/stealth/global-cleanup':
                result = self.run_global_stealth_cleanup()
                self.send_json_response(result)
            elif self.path == '/api/stealth/global-hardware-spoof':
                result = self.run_global_hardware_spoof()
                self.send_json_response(result)
            elif self.path == '/api/stealth/ssh-rotation':
                result = self.run_ssh_rotation()
                self.send_json_response(result)
            elif self.path == '/api/stealth/monitor':
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                result = self.toggle_stealth_monitor(data.get('action'))
                self.send_json_response(result)
            elif self.path == '/api/monitor/processes':
                result = self.get_process_counts()
                self.send_json_response(result)
            elif self.path == '/api/monitor/network':
                result = self.get_network_status()
                self.send_json_response(result)
            elif self.path == '/api/monitor/fingerprint':
                result = self.get_fingerprint_status()
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
        
        windsurf_configs = len([f for f in os.listdir('../configs') if os.path.isdir(f'../configs/{f}')]) if os.path.exists('../configs') else 0
        vscode_configs = len([f for f in os.listdir('../configs_vscode') if os.path.isdir(f'../configs_vscode/{f}')]) if os.path.exists('../configs_vscode') else 0
        
        return {
            'hostname': hostname,
            'windsurf': {
                'installed': windsurf_installed,
                'configs': windsurf_configs
            },
            'vscode': {
                'installed': vscode_installed,
                'configs': vscode_configs
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_configs(self, system):
        configs_dir = f'../configs' if system == 'windsurf' else f'../configs_vscode'
        configs = []
        
        if os.path.exists(configs_dir):
            for config_name in os.listdir(configs_dir):
                config_path = os.path.join(configs_dir, config_name)
                if os.path.isdir(config_path):
                    metadata_file = os.path.join(config_path, 'metadata.json')
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            configs.append(metadata)
        
        return {'configs': configs}
    
    def get_history(self):
        # Тут можна додати логіку для читання історії змін
        return {'history': []}
    
    def run_cleanup(self, system):
        try:
            script = '../deep_windsurf_cleanup.sh' if system == 'windsurf' else '../deep_vscode_cleanup.sh'
            # Додаємо timeout 300 секунд (5 хвилин) та змінні середовища
            env = os.environ.copy()
            env['SUDO_ASKPASS'] = '../sudo_helper.sh'
            
            result = subprocess.run([script], 
                                  capture_output=True, text=True, 
                                  cwd=os.path.dirname(__file__),
                                  timeout=300,
                                  env=env)
            return {'success': result.returncode == 0, 'message': result.stdout if result.returncode == 0 else result.stderr}
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Cleanup timed out after 5 minutes'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_advanced_cleanup(self, system):
        try:
            if system == 'windsurf':
                script = '../advanced_windsurf_cleanup.sh'
            else:
                return {'success': False, 'message': f'Advanced cleanup not available for: {system}'}
            
            env = os.environ.copy()
            env['SUDO_ASKPASS'] = '../sudo_helper.sh'
            
            result = subprocess.run([script], capture_output=True, text=True, 
                                  cwd=os.path.dirname(__file__), timeout=600, env=env)
            
            message = result.stdout if result.returncode == 0 else result.stderr
            if result.returncode == 0:
                message += "\n⚠️ ВАЖЛИВО: Перезавантажте macOS для повного ефекту!"
            
            return {'success': result.returncode == 0, 'message': message}
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Advanced cleanup timed out after 10 minutes'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_restore(self, system, config_name):
        # Логіка відновлення конфігурації
        return {'success': True, 'message': f'Restored {config_name}'}
    
    def get_stealth_status(self):
        # Перевірка статусу stealth процесів
        stealth_monitor_running = os.path.exists('/tmp/stealth_monitor.pid')
        
        # Перевірка fingerprints
        hostname = subprocess.getoutput("scutil --get HostName 2>/dev/null || echo 'Not set'")
        mac_address = subprocess.getoutput("ifconfig en0 2>/dev/null | awk '/ether/{print $2}' || echo 'Not found'")
        
        # Перевірка Hardware UUID
        hw_uuid = subprocess.getoutput("system_profiler SPHardwareDataType 2>/dev/null | grep 'Hardware UUID' | awk '{print $3}' || echo 'Not found'")
        
        return {
            'stealth_monitor': stealth_monitor_running,
            'hostname': hostname,
            'mac_address': mac_address,
            'hardware_uuid': hw_uuid[:8] + '...' + hw_uuid[-8:] if len(hw_uuid) > 16 else hw_uuid,
            'timestamp': datetime.now().isoformat()
        }
    
    def run_stealth_cleanup(self, system):
        try:
            if system == 'windsurf':
                script = '../stealth_cleanup.sh'
            elif system == 'vscode':
                script = '../vscode_stealth_cleanup.sh'
            else:
                return {'success': False, 'message': f'Unknown system: {system}'}
            
            env = os.environ.copy()
            env['SUDO_ASKPASS'] = '../sudo_helper.sh'
            
            result = subprocess.run([script], capture_output=True, text=True, 
                                  cwd=os.path.dirname(__file__), timeout=180, env=env)
            return {'success': result.returncode == 0, 'message': result.stdout if result.returncode == 0 else result.stderr}
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Stealth cleanup timed out after 3 minutes'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_hardware_spoof(self, system):
        try:
            env = os.environ.copy()
            env['SUDO_ASKPASS'] = '../sudo_helper.sh'
            
            result = subprocess.run(['../hardware_spoof.sh'], capture_output=True, text=True, 
                                  cwd=os.path.dirname(__file__), timeout=120, env=env)
            return {'success': result.returncode == 0, 'message': result.stdout if result.returncode == 0 else result.stderr}
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Hardware spoof timed out after 2 minutes'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_global_stealth_cleanup(self):
        try:
            # Run both stealth cleanups
            windsurf_result = subprocess.run(['../stealth_cleanup.sh'], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            vscode_result = subprocess.run(['../vscode_stealth_cleanup.sh'], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            success = windsurf_result.returncode == 0 and vscode_result.returncode == 0
            message = f"Windsurf: {windsurf_result.stdout if windsurf_result.returncode == 0 else windsurf_result.stderr}\nVS Code: {vscode_result.stdout if vscode_result.returncode == 0 else vscode_result.stderr}"
            return {'success': success, 'message': message}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_global_hardware_spoof(self):
        try:
            result = subprocess.run(['../hardware_spoof.sh'], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            return {'success': result.returncode == 0, 'message': result.stdout if result.returncode == 0 else result.stderr}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def run_ssh_rotation(self):
        try:
            result = subprocess.run(['../ssh_rotation.sh'], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            return {'success': result.returncode == 0, 'message': result.stdout if result.returncode == 0 else result.stderr}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def toggle_stealth_monitor(self, action):
        try:
            if action == 'start':
                result = subprocess.run(['../stealth_monitor.sh'], 
                                      capture_output=True, text=True, cwd=os.path.dirname(__file__))
            else:
                # Stop monitor by killing the process
                result = subprocess.run(['pkill', '-f', 'stealth_monitor.sh'], 
                                      capture_output=True, text=True)
            
            return {'success': result.returncode == 0, 'message': result.stdout if result.returncode == 0 else result.stderr}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_process_counts(self):
        try:
            # Count Windsurf processes
            windsurf_result = subprocess.run(['pgrep', '-c', '-f', 'Windsurf'], 
                                           capture_output=True, text=True)
            windsurf_count = int(windsurf_result.stdout.strip()) if windsurf_result.returncode == 0 else 0
            
            # Count VS Code processes
            vscode_result = subprocess.run(['pgrep', '-c', '-f', 'Visual Studio Code'], 
                                         capture_output=True, text=True)
            vscode_count = int(vscode_result.stdout.strip()) if vscode_result.returncode == 0 else 0
            
            return {'success': True, 'windsurf': windsurf_count, 'vscode': vscode_count}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_network_status(self):
        try:
            # Check network connectivity
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=5)
            status = 'NORMAL' if result.returncode == 0 else 'OFFLINE'
            return {'success': True, 'status': status}
        except Exception as e:
            return {'success': True, 'status': 'UNKNOWN'}
    
    def get_fingerprint_status(self):
        try:
            # Check if hardware spoofing is active by looking for modified system files
            result = subprocess.run(['ls', '/tmp/hardware_spoof_active'], 
                                  capture_output=True, text=True)
            status = 'SPOOFED' if result.returncode == 0 else 'ORIGINAL'
            return {'success': True, 'status': status}
        except Exception as e:
            return {'success': True, 'status': 'ORIGINAL'}
    
    def run_hardware_spoof(self):
        try:
            env = os.environ.copy()
            env.update(ENV_CONFIG)
            
            result = subprocess.run(['../hardware_spoof.sh'], capture_output=True, text=True, timeout=300, env=env)
            return {'success': result.returncode == 0, 'output': result.stdout, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_full_process(self, system):
        """Запускає повний процес: cleanup + advanced + stealth + monitor"""
        try:
            steps = []
            env = os.environ.copy()
            env['SUDO_ASKPASS'] = '../sudo_helper.sh'
            
            # Step 1: Deep Cleanup
            steps.append({'step': 'Deep Cleanup', 'status': 'running'})
            script = '../deep_windsurf_cleanup.sh' if system == 'windsurf' else '../deep_vscode_cleanup.sh'
            result1 = subprocess.run([script], capture_output=True, text=True, 
                                   cwd=os.path.dirname(__file__), timeout=900, env=env)
            steps[-1]['status'] = 'success' if result1.returncode == 0 else 'failed'
            steps[-1]['output'] = result1.stdout if result1.returncode == 0 else result1.stderr
            
            if result1.returncode != 0:
                return {'success': False, 'steps': steps, 'message': 'Deep cleanup failed'}
            
            # Step 2: Advanced Cleanup (тільки для Windsurf)
            if system == 'windsurf':
                steps.append({'step': 'Advanced Cleanup', 'status': 'running'})
                result2 = subprocess.run(['../advanced_windsurf_cleanup.sh'], 
                                       capture_output=True, text=True, 
                                       cwd=os.path.dirname(__file__), timeout=600, env=env)
                steps[-1]['status'] = 'success' if result2.returncode == 0 else 'failed'
                steps[-1]['output'] = result2.stdout if result2.returncode == 0 else result2.stderr
            
            # Step 3: Identifier Cleanup
            steps.append({'step': 'Identifier Cleanup', 'status': 'running'})
            id_script = '../windsurf_identifier_cleanup.sh' if system == 'windsurf' else '../vscode_identifier_cleanup.sh'
            if os.path.exists(os.path.join(os.path.dirname(__file__), id_script)):
                result3 = subprocess.run([id_script], capture_output=True, text=True, 
                                       cwd=os.path.dirname(__file__), timeout=180, env=env)
                steps[-1]['status'] = 'success' if result3.returncode == 0 else 'warning'
                steps[-1]['output'] = result3.stdout if result3.returncode == 0 else result3.stderr
            else:
                steps[-1]['status'] = 'skipped'
                steps[-1]['output'] = 'Script not found'
            
            # Step 4: Check Status
            steps.append({'step': 'Status Check', 'status': 'running'})
            check_script = '../check_windsurf_backup.sh' if system == 'windsurf' else '../check_vscode_backup.sh'
            if os.path.exists(os.path.join(os.path.dirname(__file__), check_script)):
                result4 = subprocess.run([check_script], capture_output=True, text=True, 
                                       cwd=os.path.dirname(__file__), timeout=60, env=env)
                steps[-1]['status'] = 'success'
                steps[-1]['output'] = result4.stdout
            else:
                steps[-1]['status'] = 'skipped'
            
            return {
                'success': True, 
                'steps': steps,
                'message': f'✅ Full {system.upper()} process completed!\n\n⚠️ ВАЖЛИВО: Перезавантажте систему для повного ефекту!'
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'steps': steps, 'message': 'Process timed out'}
        except Exception as e:
            return {'success': False, 'steps': steps, 'message': str(e)}

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Дозволити повторне використання адреси
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"🌐 Server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()
