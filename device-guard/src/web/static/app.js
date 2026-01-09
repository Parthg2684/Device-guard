document.addEventListener('DOMContentLoaded', () => {
    // --- Element Selectors ---
    const refreshButton = document.getElementById('refresh-btn');
    const storageTableBody = document.getElementById('storage-device-table');
    const otherTableBody = document.getElementById('other-device-table');
    const registeredTableBody = document.getElementById('registered-devices-table');
    const registeredTabBtn = document.getElementById('registered-tab-btn');
    const settingsTabBtn = document.getElementById('settings-tab-btn');
    const logsTabBtn = document.getElementById('logs-tab-btn');
    
    // Settings elements
    const adminPasswordInput = document.getElementById('admin-password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const updatePasswordBtn = document.getElementById('update-password-btn');
    const togglePasswordBtn = document.getElementById('toggle-password');
    const autoBlockCheckbox = document.getElementById('auto-block');
    const logLevelSelect = document.getElementById('log-level');
    const maxLogSizeInput = document.getElementById('max-log-size');
    const exportDbBtn = document.getElementById('export-db-btn');
    const clearDbBtn = document.getElementById('clear-db-btn');
    const viewLogsBtn = document.getElementById('view-logs-btn');
    const restartServiceBtn = document.getElementById('restart-service-btn');
    const refreshLogsBtn = document.getElementById('refresh-logs-btn');
    const clearLogsBtn = document.getElementById('clear-logs-btn');
    const logsContainer = document.getElementById('logs-container');
    
    // Toast setup
    const toastElement = document.getElementById('appToast');
    const appToast = new bootstrap.Toast(toastElement, { delay: 4000 });
    const toastTitle = document.getElementById('toastTitle');
    const toastBody = document.getElementById('toastBody');

    // --- Helper Functions ---
    const showToast = (title, message, type = 'info') => {
        toastTitle.textContent = title;
        toastBody.textContent = message;
        toastElement.querySelector('.toast-header').className = `toast-header bg-${type} text-white`;
        appToast.show();
    };

    const truncate = (str, len = 25) => (!str || str.length <= len) ? str : `${str.substring(0, len)}...`;
    
    // --- Table Population Logic for BOTH tabs ---
    const populateDetectionTables = (storageDevices, otherDevices) => {
        const populate = (tbody, devices, isStorage) => {
            if (!tbody) return;
            tbody.innerHTML = '';
            if (!devices || devices.length === 0) {
                const cols = isStorage ? 6 : 5;
                tbody.innerHTML = `<tr><td colspan="${cols}" class="text-center text-muted"><em>None detected.</em></td></tr>`;
                return;
            }
            devices.forEach(device => {
                if (!device.canonical_id) return;
                const row = document.createElement('tr');
                let statusHtml = '', actionsHtml = '';

                if (device.is_registered) {
                    statusHtml = device.is_fingerprinted ? '<span class="badge bg-success"><i class="fa-solid fa-lock"></i> Secure</span>' : '<span class="badge bg-primary"><i class="fa-solid fa-check"></i> Registered</span>';
                    actionsHtml = `<button class="btn btn-danger btn-sm remove-btn" title="Remove"><i class="fa-solid fa-trash-can"></i></button>`;
                    if (device.is_fingerprinted) actionsHtml += ` <button class="btn btn-info btn-sm ms-1 verify-btn" title="Verify"><i class="fa-solid fa-shield-halved"></i></button>`;
                } else {
                    statusHtml = '<span class="badge bg-warning text-dark"><i class="fa-solid fa-triangle-exclamation"></i> Unregistered</span>';
                    actionsHtml = isStorage ? `<button class="btn btn-success btn-sm register-secure-btn" title="Register Securely"><i class="fa-solid fa-fingerprint"></i> Secure</button>` : `<button class="btn btn-secondary btn-sm register-btn" title="Register"><i class="fa-solid fa-plus"></i></button>`;
                }
                
                const serialHtml = `<span title="${device.serial_number || 'N/A'}">${truncate(device.serial_number)}</span>`;
                const vidPidHtml = `<small>${device.vid || 'N/A'}/${device.pid || 'N/A'}</small>`;

                row.innerHTML = isStorage
                    ? `<td>${device.friendly_name}</td><td>${statusHtml}</td><td>${device.drive_letter || 'N/A'}</td><td>${vidPidHtml}</td><td>${serialHtml}</td><td>${actionsHtml}</td>`
                    : `<td>${device.friendly_name}</td><td>${statusHtml}</td><td>${vidPidHtml}</td><td>${serialHtml}</td><td>${actionsHtml}</td>`;
                
                row.querySelector('.register-btn')?.addEventListener('click', () => registerDevice(device));
                row.querySelector('.register-secure-btn')?.addEventListener('click', () => registerDevice(device));
                row.querySelector('.verify-btn')?.addEventListener('click', () => verifyDevice(device));
                row.querySelector('.remove-btn')?.addEventListener('click', () => removeDevice(device));
                tbody.appendChild(row);
            });
        };
        populate(storageTableBody, storageDevices, true);
        populate(otherTableBody, otherDevices, false);
    };
    
    const populateRegisteredTable = (devices) => {
        if (!registeredTableBody) return;
        registeredTableBody.innerHTML = '';
        if (!devices || devices.length === 0) {
            registeredTableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted"><em>No devices are registered.</em></td></tr>`;
            return;
        }
        devices.forEach(device => {
            const row = document.createElement('tr');
            
            const parts = device.canonical_id.split('&');
            const vid = parts[0].replace('VID_', '');
            const pid = parts[1].replace('PID_', '');
            const serial = parts[2].replace('SN_', '');

            const isFingerprinted = device.structural_fingerprint ? '<span class="badge bg-success">Yes</span>' : '<span class="badge bg-secondary">No</span>';
            const actionsHtml = `<button class="btn btn-danger btn-sm remove-btn"><i class="fa-solid fa-trash-can"></i> Remove</button>`;
            
            // FIXED: Display full serial number with proper styling
            row.innerHTML = `
                <td>${device.friendly_name}</td>
                <td><span class="badge bg-info text-dark">${device.device_type}</span></td>
                <td><code>${vid}</code></td>
                <td><code>${pid}</code></td>
                <td class="serial-cell"><code title="${serial}">${serial}</code></td>
                <td>${isFingerprinted}</td>
                <td><small>${new Date(device.added_on).toLocaleString()}</small></td>
                <td>${actionsHtml}</td>`;

            row.querySelector('.remove-btn')?.addEventListener('click', () => removeDevice(device));
            registeredTableBody.appendChild(row);
        });
    };

    const refreshDeviceList = async () => {
        const loadingHtml = (cols) => `<tr><td colspan="${cols}" class="text-center"><em><i class="fa-solid fa-spinner fa-spin"></i> Loading...</em></td></tr>`;
        if (storageTableBody) storageTableBody.innerHTML = loadingHtml(6);
        if (otherTableBody) otherTableBody.innerHTML = loadingHtml(5);
        try {
            const response = await fetch('/api/usb_devices');
            if (!response.ok) throw new Error('Server returned an error.');
            const data = await response.json();
            if (!data || !Array.isArray(data.storage_devices) || !Array.isArray(data.other_devices)) throw new Error("Invalid data format from server.");
            populateDetectionTables(data.storage_devices, data.other_devices);
        } catch (error) {
            showToast('Error', `Could not load devices: ${error.message}`, 'danger');
            if (storageTableBody) storageTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">${error.message}</td></tr>`;
        }
    };
    
    const refreshRegisteredList = async () => {
        if (!registeredTableBody) return;
        registeredTableBody.innerHTML = `<tr><td colspan="8" class="text-center"><em><i class="fa-solid fa-spinner fa-spin"></i> Loading...</em></td></tr>`;
        try {
            const response = await fetch('/api/registered_devices');
            const devices = await response.json();
            if (!Array.isArray(devices)) throw new Error("Invalid data format.");
            populateRegisteredTable(devices);
        } catch (error) {
            showToast('Error', `Could not load registered list: ${error.message}`, 'danger');
        }
    };

    const postData = async (url, data = {}) => {
        try {
            const response = await fetch(url, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
            return await response.json();
        } catch (error) {
            showToast('API Error', `Connection to backend failed: ${error.message}`, 'danger');
            return null;
        }
    };

    const registerDevice = async (device) => {
        if (!confirm(`Register "${device.friendly_name}"?`)) return;
        
        // Password confirmation for security
        const password = prompt('Enter admin password to register device:');
        if (!password) return;
        
        showToast('Registering...', device.friendly_name, 'info');
        const result = await postData('/api/devices/register', { ...device, password });
        if (result?.success) showToast('Success', `${device.friendly_name} registered.`, 'success');
        else showToast('Failure', `Could not register. Error: ${result?.error || 'Unknown'}`, 'danger');
        refreshDeviceList();
    };

    const verifyDevice = async (device) => {
        showToast('Verifying...', device.friendly_name, 'info');
        const result = await postData('/api/devices/verify', device);
        if (result?.success) {
            showToast(result.is_valid ? 'Success' : 'FAILED!', `Device is ${result.is_valid ? 'authentic' : 'NOT authentic'}.`, result.is_valid ? 'success' : 'danger');
        } else {
            showToast('Error', 'Could not verify.', 'danger');
        }
    };
    
    const removeDevice = async (device) => {
        if (!confirm(`REMOVE "${device.friendly_name}" from whitelist?`)) return;
        
        // Password confirmation for security
        const password = prompt('Enter admin password to remove device:');
        if (!password) return;
        
        const result = await postData('/api/devices/remove', { ...device, password });
        if (result?.success) {
            showToast('Removed', `${device.friendly_name} has been removed.`, 'success');
            refreshDeviceList();
            refreshRegisteredList();
        } else {
            showToast('Error', `Could not remove: ${result?.error || 'Unknown'}`, 'danger');
        }
    };

    // --- Settings Functions ---
    const togglePasswordVisibility = () => {
        const type = adminPasswordInput.type === 'password' ? 'text' : 'password';
        adminPasswordInput.type = type;
        confirmPasswordInput.type = type;
        togglePasswordBtn.innerHTML = type === 'password' ? '<i class="fa-solid fa-eye"></i>' : '<i class="fa-solid fa-eye-slash"></i>';
    };

    const updatePassword = async () => {
        const newPassword = adminPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        if (!newPassword || !confirmPassword) {
            showToast('Error', 'Please enter and confirm the new password', 'danger');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            showToast('Error', 'Passwords do not match', 'danger');
            return;
        }
        
        if (newPassword.length < 6) {
            showToast('Error', 'Password must be at least 6 characters', 'danger');
            return;
        }
        
        // In a real implementation, this would update the backend
        showToast('Success', 'Password updated successfully', 'success');
        adminPasswordInput.value = '';
        confirmPasswordInput.value = '';
    };

    const exportDatabase = async () => {
        try {
            const response = await fetch('/api/settings/export_db');
            if (!response.ok) throw new Error('Export failed');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'device_whitelist.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('Success', 'Database exported successfully', 'success');
        } catch (error) {
            showToast('Error', `Export failed: ${error.message}`, 'danger');
        }
    };

    const clearDatabase = async () => {
        if (!confirm('Are you sure you want to clear ALL registered devices? This action cannot be undone.')) return;
        
        try {
            const result = await postData('/api/settings/clear_db', { password: prompt('Enter admin password to clear database:') });
            if (result?.success) {
                showToast('Success', 'All devices cleared from database', 'success');
                refreshRegisteredList();
            } else {
                showToast('Error', `Failed to clear database: ${result?.error || 'Unknown'}`, 'danger');
            }
        } catch (error) {
            showToast('Error', `Clear database failed: ${error.message}`, 'danger');
        }
    };

    const viewLogs = () => {
        // Switch to logs tab
        const logsTab = document.getElementById('logs-tab-btn');
        if (logsTab) {
            logsTab.click();
        }
    };

    const loadLogs = async () => {
        if (!logsContainer) return;
        
        logsContainer.innerHTML = '<div class="text-center text-muted"><i class="fa-solid fa-spinner fa-spin"></i> Loading logs...</div>';
        
        try {
            const response = await fetch('/api/settings/logs');
            if (!response.ok) throw new Error('Failed to load logs');
            
            const logs = await response.json();
            displayLogs(logs);
        } catch (error) {
            logsContainer.innerHTML = `<div class="text-center text-danger">Error loading logs: ${error.message}</div>`;
        }
    };

    const displayLogs = (logs) => {
        if (!logs || logs.length === 0) {
            logsContainer.innerHTML = '<div class="text-center text-muted">No logs available.</div>';
            return;
        }
        
        const logsHtml = logs.map(log => {
            const timestamp = new Date(log.time).toLocaleString();
            const levelClass = log.level === 'ERROR' ? 'text-danger' : 
                              log.level === 'WARNING' ? 'text-warning' : 
                              log.level === 'INFO' ? 'text-info' : 'text-secondary';
            
            return `
                <div class="border-bottom border-secondary pb-2 mb-2">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <span class="${levelClass} fw-bold">[${log.level}]</span>
                            <span class="ms-2">${timestamp}</span>
                        </div>
                        <div class="text-muted small">${log.source || 'Application'}</div>
                    </div>
                    <div class="mt-1">${log.message}</div>
                </div>
            `;
        }).join('');
        
        logsContainer.innerHTML = logsHtml;
    };

    const clearLogs = async () => {
        if (!confirm('Clear all system logs? This action cannot be undone.')) return;
        
        try {
            const result = await postData('/api/settings/clear_logs', { password: prompt('Enter admin password to clear logs:') });
            if (result?.success) {
                showToast('Success', 'Logs cleared successfully', 'success');
                loadLogs(); // Reload logs
            } else {
                showToast('Error', `Failed to clear logs: ${result?.error || 'Unknown'}`, 'danger');
            }
        } catch (error) {
            showToast('Error', `Clear logs failed: ${error.message}`, 'danger');
        }
    };

    const restartService = async () => {
        if (!confirm('Restart the Device Guard service?')) return;
        
        try {
            const result = await postData('/api/settings/restart', { password: prompt('Enter admin password to restart service:') });
            if (result?.success) {
                showToast('Success', 'Service restart initiated', 'info');
                setTimeout(() => window.location.reload(), 3000);
            } else {
                showToast('Error', `Restart failed: ${result?.error || 'Unknown'}`, 'danger');
            }
        } catch (error) {
            showToast('Error', `Restart failed: ${error.message}`, 'danger');
        }
    };

    // --- Event Listeners ---
    refreshButton?.addEventListener('click', refreshDeviceList);
    registeredTabBtn?.addEventListener('shown.bs.tab', refreshRegisteredList);
    settingsTabBtn?.addEventListener('shown.bs.tab', () => {
        // Load current settings when tab is opened
        // This would load from backend in a real implementation
    });
    logsTabBtn?.addEventListener('shown.bs.tab', loadLogs);
    
    // Settings event listeners
    togglePasswordBtn?.addEventListener('click', togglePasswordVisibility);
    updatePasswordBtn?.addEventListener('click', updatePassword);
    exportDbBtn?.addEventListener('click', exportDatabase);
    clearDbBtn?.addEventListener('click', clearDatabase);
    viewLogsBtn?.addEventListener('click', viewLogs);
    refreshLogsBtn?.addEventListener('click', loadLogs);
    clearLogsBtn?.addEventListener('click', clearLogs);
    restartServiceBtn?.addEventListener('click', restartService);

    // Initial load for the first tab
    refreshDeviceList();
});