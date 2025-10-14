class QBControllerApp {
    constructor() {
        this.currentView = 'dashboard';
        this.init();
    }

    async init() {
        await this.loadConfig();
        this.setupEventListeners();
        this.startStatusUpdates();
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config/');
            this.config = await response.json();
            this.renderConfigForms();
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    }

    setupEventListeners() {
        // 导航菜单
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchView(e.target.dataset.view);
            });
        });

        // Lucky设备表单
        document.getElementById('add-lucky-device').addEventListener('click', () => {
            this.showLuckyDeviceForm();
        });

        // qBittorrent实例表单
        document.getElementById('add-qbit-instance').addEventListener('click', () => {
            this.showQbitInstanceForm();
        });

        // 保存控制器设置
        document.getElementById('save-controller-settings').addEventListener('click', () => {
            this.saveControllerSettings();
        });
    }

    switchView(viewName) {
        this.currentView = viewName;
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(`${viewName}-view`).classList.add('active');

        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-view="${viewName}"]`).classList.add('active');
    }

    renderConfigForms() {
        this.renderLuckyDevices();
        this.renderQbitInstances();
        this.renderControllerSettings();
    }

    renderLuckyDevices() {
        const container = document.getElementById('lucky-devices-list');
        container.innerHTML = '';

        this.config.lucky_devices.forEach((device, index) => {
            const deviceElement = this.createLuckyDeviceElement(device, index);
            container.appendChild(deviceElement);
        });
    }

    createLuckyDeviceElement(device, index) {
        const div = document.createElement('div');
        div.className = 'device-item card mb-2';
        div.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${device.name}</h5>
                <p class="card-text">
                    <small class="text-muted">API: ${device.api_url}</small><br>
                    <small class="text-muted">权重: ${device.weight}</small>
                </p>
                <button class="btn btn-sm btn-warning edit-device" data-index="${index}">编辑</button>
                <button class="btn btn-sm btn-danger delete-device" data-index="${index}">删除</button>
                <button class="btn btn-sm btn-info test-device" data-index="${index}">测试连接</button>
            </div>
        `;

        div.querySelector('.edit-device').addEventListener('click', () => this.editLuckyDevice(index));
        div.querySelector('.delete-device').addEventListener('click', () => this.deleteLuckyDevice(index));
        div.querySelector('.test-device').addEventListener('click', () => this.testLuckyDevice(device));

        return div;
    }

    showLuckyDeviceForm(device = null) {
        // 显示Lucky设备表单模态框
        const modal = new bootstrap.Modal(document.getElementById('luckyDeviceModal'));
        const form = document.getElementById('lucky-device-form');
        
        if (device) {
            // 编辑模式
            form.dataset.editIndex = device.index;
            document.getElementById('device-name').value = device.name;
            document.getElementById('device-api-url').value = device.api_url;
            document.getElementById('device-weight').value = device.weight;
            document.getElementById('device-enabled').checked = device.enabled;
            document.getElementById('device-description').value = device.description || '';
        } else {
            // 添加模式
            form.reset();
            delete form.dataset.editIndex;
        }
        
        modal.show();
    }

    async saveLuckyDevice(formData) {
        try {
            const url = '/api/config/lucky-devices';
            const method = formData.editIndex !== undefined ? 'PUT' : 'POST';
            const finalUrl = formData.editIndex !== undefined 
                ? `${url}/${formData.editIndex}` 
                : url;

            const response = await fetch(finalUrl, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: formData.name,
                    api_url: formData.api_url,
                    weight: parseFloat(formData.weight),
                    enabled: formData.enabled === 'true',
                    description: formData.description
                })
            });

            if (response.ok) {
                await this.loadConfig();
                this.showAlert('设备保存成功', 'success');
                return true;
            } else {
                throw new Error('保存失败');
            }
        } catch (error) {
            this.showAlert('设备保存失败: ' + error.message, 'danger');
            return false;
        }
    }

    async testLuckyDevice(device) {
        try {
            const response = await fetch('/api/lucky/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ api_url: device.api_url })
            });

            const result = await response.json();
            if (result.success) {
                this.showAlert('连接测试成功', 'success');
            } else {
                this.showAlert('连接测试失败: ' + result.message, 'danger');
            }
        } catch (error) {
            this.showAlert('测试请求失败: ' + error.message, 'danger');
        }
    }

    // 类似的实现qBittorrent实例管理...
    // 控制器设置管理...
    // 状态监控显示...

    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.getElementById('alerts-container');
        container.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    async startStatusUpdates() {
        // 定期更新状态信息
        setInterval(async () => {
            await this.updateStatus();
        }, 2000);
    }

    async updateStatus() {
        try {
            const [luckyStatus, qbitStatus, controllerState] = await Promise.all([
                fetch('/api/lucky/status').then(r => r.json()),
                fetch('/api/qbit/status').then(r => r.json()),
                fetch('/api/qbit/controller-state').then(r => r.json())
            ]);

            this.renderStatus(luckyStatus, qbitStatus, controllerState);
        } catch (error) {
            console.error('状态更新失败:', error);
        }
    }

    renderStatus(luckyStatus, qbitStatus, controllerState) {
        // 渲染状态到界面
        this.renderLuckyStatus(luckyStatus);
        this.renderQbitStatus(qbitStatus);
        this.renderControllerState(controllerState);
    }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new QBControllerApp();
});