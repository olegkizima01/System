// Global state
let systemData = {
    windsurf: { configs: [] },
    vscode: { configs: [] },
    history: []
};

// Initialize - removed duplicate, handled at bottom of file

// Clock
function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('uk-UA', { hour12: false });
    const dateString = now.toLocaleDateString('uk-UA');
    document.getElementById('clock').textContent = `${dateString} ${timeString}`;
}

// Load System Status
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        document.getElementById('hostname').textContent = data.hostname;
        
        // Windsurf status
        const windsurfStatus = data.windsurf.installed ? 
            '<span style="color: var(--success)">✅ Installed</span>' : 
            '<span style="color: var(--danger)">❌ Not installed</span>';
        document.getElementById('windsurf-status').innerHTML = windsurfStatus;
        document.getElementById('windsurf-profiles').textContent = data.windsurf.configs;
        
        // VS Code status
        const vscodeStatus = data.vscode.installed ? 
            '<span style="color: var(--success)">✅ Installed</span>' : 
            '<span style="color: var(--danger)">❌ Not installed</span>';
        document.getElementById('vscode-status').innerHTML = vscodeStatus;
        document.getElementById('vscode-profiles').textContent = data.vscode.configs;
        
    } catch (error) {
        console.error('Error loading status:', error);
        addTerminalLine('Error loading system status', 'error');
    }
}

// Load Configs
async function loadConfigs(system) {
    try {
        const response = await fetch(`/api/configs/${system}`);
        const data = await response.json();
        systemData[system].configs = data.configs;
        updateConfigsList(system);
    } catch (error) {
        console.error(`Error loading ${system} configs:`, error);
    }
}

// Update Configs List
function updateConfigsList(system) {
    const container = document.getElementById(`${system}-configs`);
    const configs = systemData[system].configs;
    
    if (configs.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); padding: 20px; text-align: center;">No profiles found</div>';
        return;
    }
    
    container.innerHTML = configs.map(config => `
        <div class="profile-item">
            <div class="profile-info">
                <div class="profile-name">${config.name}</div>
                <div class="profile-meta">
                    Hostname: ${config.hostname} | Created: ${config.created}
                </div>
            </div>
            <div class="profile-actions">
                <button class="btn btn-success btn-small" onclick="restoreConfig('${system}', '${config.name}')">
                    Restore
                </button>
            </div>
        </div>
    `).join('');
}

// Run Cleanup
async function runCleanup(system) {
    const confirmMsg = `Are you sure you want to run full cleanup for ${system.toUpperCase()}?\n\nThis will:\n- Delete all ${system} files\n- Clear Keychain\n- Replace all IDs\n- Change hostname`;
    
    if (!confirm(confirmMsg)) return;
    
    addTerminalLine(`Starting ${system} cleanup...`, 'warning');
    
    try {
        const response = await fetch(`/api/cleanup/${system}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            addTerminalLine(`✅ ${system} cleanup completed successfully!`, 'success');
            addToHistory(`${system} cleanup completed`, 'success');
            setTimeout(() => {
                loadSystemStatus();
                loadConfigs(system);
            }, 2000);
        } else {
            addTerminalLine(`❌ Cleanup failed: ${data.error}`, 'error');
            addToHistory(`${system} cleanup failed`, 'error');
        }
    } catch (error) {
        addTerminalLine(`❌ Error: ${error.message}`, 'error');
    }
}

// Restore Config
async function restoreConfig(system, configName) {
    if (!confirm(`Restore configuration "${configName}" for ${system}?`)) return;
    
    addTerminalLine(`Restoring ${system} config: ${configName}...`);
    
    try {
        const response = await fetch(`/api/restore/${system}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: configName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addTerminalLine(`✅ Configuration restored successfully!`, 'success');
            addToHistory(`Restored ${system} config: ${configName}`, 'success');
            loadSystemStatus();
        } else {
            addTerminalLine(`❌ Restore failed: ${data.error}`, 'error');
        }
    } catch (error) {
        addTerminalLine(`❌ Error: ${error.message}`, 'error');
    }
}

// Show Configs Modal
function showConfigs(system) {
    const modal = document.getElementById('profiles-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.textContent = `${system.toUpperCase()} Profiles`;
    
    const configs = systemData[system].configs;
    
    if (configs.length === 0) {
        modalBody.innerHTML = '<p style="text-align: center; padding: 40px; color: var(--text-muted);">No profiles found</p>';
    } else {
        modalBody.innerHTML = configs.map(config => `
            <div class="profile-item">
                <div class="profile-info">
                    <div class="profile-name">${config.name}</div>
                    <div class="profile-meta">
                        Hostname: ${config.hostname}<br>
                        Created: ${config.created}<br>
                        Description: ${config.description || 'N/A'}
                    </div>
                </div>
                <div class="profile-actions">
                    <button class="btn btn-success btn-small" onclick="restoreConfig('${system}', '${config.name}'); closeModal();">
                        Restore
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    modal.classList.add('active');
}

// Close Modal
function closeModal() {
    document.getElementById('profiles-modal').classList.remove('active');
}

// Check Status
function checkStatus(system) {
    addTerminalLine(`Checking ${system} status...`);
    loadSystemStatus();
    loadConfigs(system);
    addTerminalLine(`✅ Status updated`, 'success');
}

// Add Terminal Line
function addTerminalLine(text, type = 'normal') {
    const terminal = document.getElementById('terminal');
    const line = document.createElement('div');
    line.className = 'terminal-line';
    
    const time = new Date().toLocaleTimeString('uk-UA', { hour12: false });
    
    let className = 'terminal-text';
    if (type === 'error') className = 'terminal-error';
    if (type === 'warning') className = 'terminal-warning';
    if (type === 'success') className = 'terminal-text';
    
    line.innerHTML = `
        <span class="terminal-prompt">[${time}]</span>
        <span class="${className}">${text}</span>
    `;
    
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
    
    // Keep only last 50 lines
    while (terminal.children.length > 50) {
        terminal.removeChild(terminal.firstChild);
    }
}

// Load History
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        systemData.history = data.history;
        updateHistoryList();
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Update History List
function updateHistoryList() {
    const container = document.getElementById('history');
    const history = systemData.history;
    
    if (history.length === 0) {
        container.innerHTML = `
            <div class="history-item">
                <span class="history-time">${new Date().toLocaleString('uk-UA')}</span>
                <span class="history-text">System initialized. No changes yet.</span>
            </div>
        `;
        return;
    }
    
    container.innerHTML = history.map(item => `
        <div class="history-item">
            <span class="history-time">${item.timestamp}</span>
            <span class="history-text">${item.message}</span>
        </div>
    `).join('');
}

// Add to History
function addToHistory(message, type = 'info') {
    const historyItem = {
        timestamp: new Date().toLocaleString('uk-UA'),
        message: message,
        type: type
    };
    
    systemData.history.unshift(historyItem);
    
    // Keep only last 20 items
    if (systemData.history.length > 20) {
        systemData.history = systemData.history.slice(0, 20);
    }
    
    updateHistoryList();
}

// Close modal on outside click
document.getElementById('profiles-modal').addEventListener('click', (e) => {
    if (e.target.id === 'profiles-modal') {
        closeModal();
    }
});

// Stealth Functions
async function loadStealthStatus() {
    try {
        const response = await fetch('/api/stealth/status');
        const data = await response.json();
        
        // Update monitor status
        const monitorStatus = document.getElementById('stealth-monitor-status');
        if (data.stealth_monitor) {
            monitorStatus.innerHTML = '<span style="color: var(--success)">✅ Active</span>';
            document.getElementById('monitor-btn-text').textContent = 'Stop Monitor';
        } else {
            monitorStatus.innerHTML = '<span style="color: var(--danger)">❌ Inactive</span>';
            document.getElementById('monitor-btn-text').textContent = 'Start Monitor';
        }
        
        // Update fingerprint status
        const fingerprintStatus = document.getElementById('fingerprint-status');
        fingerprintStatus.innerHTML = `
            <div style="font-size: 0.8em;">
                <div>Host: ${data.hostname}</div>
                <div>MAC: ${data.mac_address}</div>
                <div>UUID: ${data.hardware_uuid}</div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading stealth status:', error);
    }
}

async function runStealthCleanup() {
    const confirmMsg = 'Are you sure you want to run STEALTH CLEANUP?\n\nThis will:\n- Change ALL hardware fingerprints\n- Randomize network identifiers\n- Clear system logs\n- Spoof browser fingerprints\n- Enable behavioral obfuscation';
    
    if (!confirm(confirmMsg)) return;
    
    addTerminalLine('🕵️ Starting STEALTH CLEANUP...', 'warning');
    
    try {
        const response = await fetch('/api/stealth/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            addTerminalLine('✅ STEALTH CLEANUP completed successfully!', 'success');
            addToHistory('Stealth cleanup completed', 'success');
            setTimeout(() => {
                loadSystemStatus();
                loadStealthStatus();
            }, 2000);
        } else {
            addTerminalLine(`❌ Stealth cleanup failed: ${data.error}`, 'error');
            addToHistory('Stealth cleanup failed', 'error');
        }
    } catch (error) {
        addTerminalLine(`❌ Error: ${error.message}`, 'error');
    }
}

async function runHardwareSpoof() {
    const confirmMsg = 'Run HARDWARE SPOOFING?\n\nThis will:\n- Change Hardware UUID\n- Spoof CPU fingerprint\n- Randomize memory layout\n- Modify graphics fingerprint';
    
    if (!confirm(confirmMsg)) return;
    
    addTerminalLine('🔧 Starting Hardware Spoofing...', 'warning');
    
    try {
        const response = await fetch('/api/hardware/spoof', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            addTerminalLine('✅ Hardware spoofing completed!', 'success');
            addToHistory('Hardware spoofing completed', 'success');
            loadStealthStatus();
        } else {
            addTerminalLine(`❌ Hardware spoofing failed: ${data.error}`, 'error');
        }
    } catch (error) {
        addTerminalLine(`❌ Error: ${error.message}`, 'error');
    }
}

async function toggleStealthMonitor() {
    const isActive = document.getElementById('monitor-btn-text').textContent === 'Stop Monitor';
    const action = isActive ? 'stop' : 'start';
    
    addTerminalLine(`${action === 'start' ? '▶️' : '⏹️'} ${action === 'start' ? 'Starting' : 'Stopping'} stealth monitor...`);
    
    try {
        const response = await fetch('/api/stealth/monitor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addTerminalLine(`✅ Stealth monitor ${action}ed successfully!`, 'success');
            loadStealthStatus();
        } else {
            addTerminalLine(`❌ Failed to ${action} stealth monitor: ${data.error}`, 'error');
        }
    } catch (error) {
        addTerminalLine(`❌ Error: ${error.message}`, 'error');
    }
}

// Update stealth status functions
function updateStealthStatus(system, status) {
    const element = document.getElementById(`${system}-stealth-status`);
    if (element) {
        element.textContent = status;
        element.className = 'status-value ' + (status === 'ACTIVE' ? 'status-success' : 'status-inactive');
    }
}

function updateGlobalStealthStatus(status) {
    const element = document.getElementById('global-stealth-status');
    if (element) {
        element.textContent = status;
        element.className = 'status-value ' + (status === 'ACTIVE' ? 'status-success' : 'status-inactive');
    }
}

function updateHardwareStatus(status) {
    const element = document.getElementById('hardware-status');
    if (element) {
        element.textContent = status;
        element.className = 'status-value ' + (status === 'APPLIED' ? 'status-success' : 'status-inactive');
    }
}

function updateMonitorStatus(status) {
    const element = document.getElementById('monitor-status');
    if (element) {
        element.textContent = status;
        element.className = 'status-value ' + (status === 'RUNNING' ? 'status-success' : 'status-inactive');
    }
}

function updateSSHStatus(status) {
    const element = document.getElementById('ssh-status');
    if (element) {
        element.textContent = status;
        element.className = 'status-value ' + (status === 'ROTATED' ? 'status-success' : 'status-inactive');
    }
}

function updateProcessCount(system, count) {
    const element = document.getElementById(`${system}-processes`);
    if (element) {
        element.textContent = count;
        element.className = 'monitor-value ' + (count > 0 ? 'status-warning' : 'status-success');
    }
}

function updateNetworkStatus(status) {
    const element = document.getElementById('network-status');
    if (element) {
        element.textContent = status;
        element.className = 'monitor-value ' + (status === 'NORMAL' ? 'status-success' : 'status-warning');
    }
}

function updateFingerprintStatus(status) {
    const element = document.getElementById('fingerprint-status');
    if (element) {
        element.textContent = status;
        element.className = 'monitor-value ' + (status === 'SPOOFED' ? 'status-success' : 'status-inactive');
    }
}

// Individual stealth system functions
function runStealthCleanup(system) {
    const systemName = system.toUpperCase();
    addTerminalLine(`🕵️ Starting ${systemName} stealth cleanup...`);
    
    fetch(`/api/stealth/cleanup/${system}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addTerminalLine(`✅ ${systemName} stealth cleanup completed successfully`);
            updateStealthStatus(system, 'ACTIVE');
        } else {
            addTerminalLine(`❌ ${systemName} stealth cleanup failed: ` + data.message);
        }
    })
    .catch(error => {
        addTerminalLine(`❌ Error during ${systemName} stealth cleanup: ` + error);
    });
}

function runHardwareSpoof(system) {
    const systemName = system.toUpperCase();
    addTerminalLine(`🎭 Starting ${systemName} hardware spoofing...`);
    
    fetch(`/api/stealth/hardware-spoof/${system}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addTerminalLine(`✅ ${systemName} hardware spoofing completed successfully`);
            updateHardwareStatus('APPLIED');
        } else {
            addTerminalLine(`❌ ${systemName} hardware spoofing failed: ` + data.message);
        }
    })
    .catch(error => {
        addTerminalLine(`❌ Error during ${systemName} hardware spoofing: ` + error);
    });
}

// Global stealth functions
function runGlobalStealthCleanup() {
    addTerminalLine('🌐 Starting global stealth cleanup...');
    
    fetch('/api/stealth/global-cleanup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addTerminalLine('✅ Global stealth cleanup completed successfully');
            updateGlobalStealthStatus('ACTIVE');
        } else {
            addTerminalLine('❌ Global stealth cleanup failed: ' + data.message);
        }
    })
    .catch(error => {
        addTerminalLine('❌ Error during global stealth cleanup: ' + error);
    });
}

function runGlobalHardwareSpoof() {
    addTerminalLine('🎭 Starting global hardware spoofing...');
    
    fetch('/api/stealth/global-hardware-spoof', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addTerminalLine('✅ Global hardware spoofing completed successfully');
            updateHardwareStatus('APPLIED');
        } else {
            addTerminalLine('❌ Global hardware spoofing failed: ' + data.message);
        }
    })
    .catch(error => {
        addTerminalLine('❌ Error during global hardware spoofing: ' + error);
    });
}

function rotateSSHKeys() {
    addTerminalLine('🔑 Starting SSH key rotation...');
    
    fetch('/api/stealth/ssh-rotation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addTerminalLine('✅ SSH keys rotated successfully');
            updateSSHStatus('ROTATED');
        } else {
            addTerminalLine('❌ SSH rotation failed: ' + data.message);
        }
    })
    .catch(error => {
        addTerminalLine('❌ Error during SSH rotation: ' + error);
    });
}

async function toggleStealthMonitor() {
    const button = document.getElementById('monitor-btn-text');
    const isRunning = button.textContent === 'STOP MONITOR';
    
    addTerminalLine(isRunning ? '⏹️ Stopping stealth monitor...' : '▶️ Starting stealth monitor...');
    
    fetch('/api/stealth/monitor', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: isRunning ? 'stop' : 'start' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const newStatus = isRunning ? 'STOPPED' : 'RUNNING';
            const newButtonText = isRunning ? 'START MONITOR' : 'STOP MONITOR';
            
            addTerminalLine(`✅ Stealth monitor ${newStatus.toLowerCase()} successfully`);
            updateMonitorStatus(newStatus);
            button.textContent = newButtonText;
        } else {
            addTerminalLine(`❌ Failed to ${isRunning ? 'stop' : 'start'} stealth monitor: ` + data.message);
        }
    })
    .catch(error => {
        addTerminalLine(`❌ Error ${isRunning ? 'stopping' : 'starting'} stealth monitor: ` + error);
    });
}

// One-click complete processes
async function runFullWindsurfProcess() {
    const confirmMsg = '🚀 ЗАПУСТИТИ ПОВНИЙ ПРОЦЕС WINDSURF?\n\n' +
        'Це виконає:\n' +
        '✅ Deep Cleanup (видалення всіх файлів)\n' +
        '✅ Advanced Cleanup (браузери + системні списки)\n' +
        '✅ Identifier Cleanup (Machine ID + Device ID)\n' +
        '✅ Keychain Cleanup (всі токени)\n' +
        '✅ Browser IndexedDB (Chrome, Safari, Firefox)\n' +
        '✅ Hostname Rotation (750+ варіантів)\n' +
        '✅ MAC Address Spoof\n' +
        '✅ Network Reset (DNS, ARP, DHCP)\n' +
        '✅ Auto-Restore (через 5 годин)\n\n' +
        '⚠️ ВАЖЛИВО: Після завершення потрібно перезавантажити систему!';
    
    if (!confirm(confirmMsg)) return;
    
    const statusElement = document.getElementById('windsurf-mega-status');
    const progressElement = document.getElementById('windsurf-progress');
    
    statusElement.textContent = '⏳ ЗАПУСК...';
    statusElement.className = 'mega-button-status running';
    progressElement.style.display = 'block';
    progressElement.innerHTML = '';
    
    addTerminalLine('🚀 Запуск ПОВНОГО процесу Windsurf...', 'warning');
    addTerminalLine('⏳ Це може зайняти 5-10 хвилин...', 'warning');
    
    try {
        const response = await fetch('/api/cleanup/windsurf/full', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        // Відображення кроків
        if (data.steps) {
            data.steps.forEach(step => {
                const stepClass = step.status === 'success' ? 'success' : 
                                 step.status === 'failed' ? 'failed' : 
                                 step.status === 'running' ? 'running' : '';
                
                const stepIcon = step.status === 'success' ? '✅' : 
                                step.status === 'failed' ? '❌' : 
                                step.status === 'running' ? '⏳' : '⏭️';
                
                progressElement.innerHTML += `
                    <div class="progress-step ${stepClass}">
                        ${stepIcon} ${step.step}: ${step.status.toUpperCase()}
                    </div>
                `;
                
                addTerminalLine(`${stepIcon} ${step.step}: ${step.status}`, 
                              step.status === 'success' ? 'success' : 
                              step.status === 'failed' ? 'error' : 'normal');
            });
        }
        
        if (data.success) {
            statusElement.textContent = '✅ ЗАВЕРШЕНО!';
            statusElement.className = 'mega-button-status success';
            addTerminalLine('🎉 WINDSURF ПОВНИЙ ПРОЦЕС ЗАВЕРШЕНО!', 'success');
            addTerminalLine('⚠️ ПЕРЕЗАВАНТАЖТЕ СИСТЕМУ для повного ефекту!', 'warning');
            
            setTimeout(() => {
                loadSystemStatus();
                loadConfigs('windsurf');
            }, 2000);
        } else {
            throw new Error(data.message || 'Process failed');
        }
    } catch (error) {
        statusElement.textContent = '❌ ПОМИЛКА';
        statusElement.className = 'mega-button-status error';
        addTerminalLine(`❌ Помилка: ${error.message}`, 'error');
    }
}

async function runFullVSCodeProcess() {
    const confirmMsg = '🚀 ЗАПУСТИТИ ПОВНИЙ ПРОЦЕС VS CODE?\n\n' +
        'Це виконає:\n' +
        '✅ Deep Cleanup (видалення всіх файлів)\n' +
        '✅ Identifier Cleanup (Machine ID + Device ID)\n' +
        '✅ Keychain Cleanup (GitHub, Microsoft токени)\n' +
        '✅ Browser Data Cleanup (всі браузери)\n' +
        '✅ Extensions Cleanup (всі розширення)\n' +
        '✅ Hostname Rotation (750+ варіантів)\n' +
        '✅ Network Reset (DNS, ARP, DHCP)\n' +
        '✅ System Lists Cleanup (macOS)\n' +
        '✅ Auto-Restore (через 5 годин)\n\n' +
        '⚠️ ВАЖЛИВО: Після завершення потрібно перезавантажити систему!';
    
    if (!confirm(confirmMsg)) return;
    
    const statusElement = document.getElementById('vscode-mega-status');
    const progressElement = document.getElementById('vscode-progress');
    
    statusElement.textContent = '⏳ ЗАПУСК...';
    statusElement.className = 'mega-button-status running';
    progressElement.style.display = 'block';
    progressElement.innerHTML = '';
    
    addTerminalLine('🚀 Запуск ПОВНОГО процесу VS Code...', 'warning');
    addTerminalLine('⏳ Це може зайняти 5-10 хвилин...', 'warning');
    
    try {
        const response = await fetch('/api/cleanup/vscode/full', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        // Відображення кроків
        if (data.steps) {
            data.steps.forEach(step => {
                const stepClass = step.status === 'success' ? 'success' : 
                                 step.status === 'failed' ? 'failed' : 
                                 step.status === 'running' ? 'running' : '';
                
                const stepIcon = step.status === 'success' ? '✅' : 
                                step.status === 'failed' ? '❌' : 
                                step.status === 'running' ? '⏳' : '⏭️';
                
                progressElement.innerHTML += `
                    <div class="progress-step ${stepClass}">
                        ${stepIcon} ${step.step}: ${step.status.toUpperCase()}
                    </div>
                `;
                
                addTerminalLine(`${stepIcon} ${step.step}: ${step.status}`, 
                              step.status === 'success' ? 'success' : 
                              step.status === 'failed' ? 'error' : 'normal');
            });
        }
        
        if (data.success) {
            statusElement.textContent = '✅ ЗАВЕРШЕНО!';
            statusElement.className = 'mega-button-status success';
            addTerminalLine('🎉 VS CODE ПОВНИЙ ПРОЦЕС ЗАВЕРШЕНО!', 'success');
            addTerminalLine('⚠️ ПЕРЕЗАВАНТАЖТЕ СИСТЕМУ для повного ефекту!', 'warning');
            
            setTimeout(() => {
                loadSystemStatus();
                loadConfigs('vscode');
            }, 2000);
        } else {
            throw new Error(data.message || 'Process failed');
        }
    } catch (error) {
        statusElement.textContent = '❌ ПОМИЛКА';
        statusElement.className = 'mega-button-status error';
        addTerminalLine(`❌ Помилка: ${error.message}`, 'error');
    }
}

// Real-time monitoring
function startRealTimeMonitoring() {
    setInterval(() => {
        // Check process counts
        fetch('/api/monitor/processes')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateProcessCount('windsurf', data.windsurf || 0);
                    updateProcessCount('vscode', data.vscode || 0);
                }
            })
            .catch(error => console.error('Monitor error:', error));
        
        // Check network status
        fetch('/api/monitor/network')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateNetworkStatus(data.status || 'NORMAL');
                }
            })
            .catch(error => console.error('Network monitor error:', error));
        
        // Check fingerprint status
        fetch('/api/monitor/fingerprint')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateFingerprintStatus(data.status || 'ORIGINAL');
                }
            })
            .catch(error => console.error('Fingerprint monitor error:', error));
    }, 5000); // Update every 5 seconds
}

// Initial terminal message
addTerminalLine('🚀 Deep Cleanup System initialized', 'success');
addTerminalLine('🕵️ Stealth mode ready...', 'success');

// Start real-time monitoring when page loads
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
    loadSystemStatus();
    setInterval(loadSystemStatus, 5000);
    loadConfigs('windsurf');
    loadConfigs('vscode');
    loadHistory();
    loadStealthStatus();
    setInterval(loadStealthStatus, 10000);
    startRealTimeMonitoring();
});
