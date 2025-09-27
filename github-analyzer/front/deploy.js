// deploy.js - Логика развертывания на сервере
let currentTab = 'server-tab';
let serverConfig = {};
let repoInfo = {};
let deployInProgress = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Deploy page loaded!');
    
    // Инициализация форм
    initServerForm();
    initRepoForm();
    initDeployControls();
    
    // Обработка выбора ветки
    const branchSelect = document.getElementById('deploy-branch');
    const customBranch = document.getElementById('custom-branch');
    
    branchSelect.addEventListener('change', function() {
        if (this.value === 'custom') {
            customBranch.style.display = 'block';
            customBranch.required = true;
        } else {
            customBranch.style.display = 'none';
            customBranch.required = false;
        }
    });
});

// Навигация по табам
function showTab(tabName) {
    // Скрыть все табы
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Показать выбранный таб
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
    
    currentTab = tabName;
    updateNavigation();
}

function nextTab() {
    const tabs = ['server-tab', 'repo-tab', 'deploy-tab'];
    const currentIndex = tabs.indexOf(currentTab);
    if (currentIndex < tabs.length - 1) {
        showTab(tabs[currentIndex + 1]);
    }
}

function previousTab() {
    const tabs = ['server-tab', 'repo-tab', 'deploy-tab'];
    const currentIndex = tabs.indexOf(currentTab);
    if (currentIndex > 0) {
        showTab(tabs[currentIndex - 1]);
    }
}

function updateNavigation() {
    const prevBtn = document.getElementById('prev-tab-btn');
    const nextBtn = document.getElementById('next-tab-btn');
    const tabs = ['server-tab', 'repo-tab', 'deploy-tab'];
    const currentIndex = tabs.indexOf(currentTab);
    
    prevBtn.style.display = currentIndex > 0 ? 'block' : 'none';
    nextBtn.style.display = currentIndex < tabs.length - 1 ? 'block' : 'none';
    
    // Обновляем текст кнопки "Далее"
    if (currentTab === 'server-tab' && !serverConfig.connected) {
        nextBtn.disabled = true;
        nextBtn.textContent = 'Сначала подключитесь к серверу';
    } else if (currentTab === 'repo-tab' && !repoInfo.analyzed) {
        nextBtn.disabled = true;
        nextBtn.textContent = 'Сначала проанализируйте репозиторий';
    } else {
        nextBtn.disabled = false;
        nextBtn.textContent = 'Далее →';
    }
}

// Инициализация формы сервера
function initServerForm() {
    const form = document.getElementById('server-config-form');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            await testServerConnection();
        });
    }
}

// Инициализация формы репозитория
function initRepoForm() {
    const form = document.getElementById('repo-select-form');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            await analyzeRepository();
        });
    }
}

// Инициализация контролов развертывания
function initDeployControls() {
    const startBtn = document.getElementById('start-deploy-btn');
    const stopBtn = document.getElementById('stop-deploy-btn');
    
    if (startBtn) {
        startBtn.addEventListener('click', startDeployment);
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', stopDeployment);
    }
}

// Тестирование подключения к серверу
async function testServerConnection() {
    const statusDiv = document.getElementById('server-status');
    const statusBadge = document.getElementById('server-status-badge');
    const statusInfo = document.getElementById('server-status-info');
    
    // Получаем данные формы
    const formData = new FormData(document.getElementById('server-config-form'));
    serverConfig = {
        ip: formData.get('server-ip'),
        port: parseInt(formData.get('server-port')),
        user: formData.get('server-user'),
        password: formData.get('server-password'),
        deployPath: formData.get('deploy-path')
    };
    
    statusDiv.style.display = 'block';
    statusBadge.textContent = 'Проверка подключения...';
    statusBadge.className = 'status-badge';
    statusInfo.innerHTML = '<p>Проверяем SSH подключение к серверу...</p>';
    
    try {
        const response = await fetch('/test-server', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(serverConfig)
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusBadge.textContent = '✅ Подключено';
            statusBadge.className = 'status-badge success';
            statusInfo.innerHTML = `
                <p><strong>Сервер:</strong> ${serverConfig.ip}:${serverConfig.port}</p>
                <p><strong>Пользователь:</strong> ${serverConfig.user}</p>
                <p><strong>Путь развертывания:</strong> ${serverConfig.deployPath}</p>
                <p class="success">SSH подключение успешно установлено!</p>
            `;
            serverConfig.connected = true;
        } else {
            statusBadge.textContent = '❌ Ошибка подключения';
            statusBadge.className = 'status-badge error';
            statusInfo.innerHTML = `
                <p class="error">Ошибка подключения к серверу:</p>
                <p>${result.error}</p>
                <p>Проверьте IP адрес, порт, логин и пароль.</p>
            `;
            serverConfig.connected = false;
        }
    } catch (error) {
        statusBadge.textContent = '❌ Ошибка';
        statusBadge.className = 'status-badge error';
        statusInfo.innerHTML = `
            <p class="error">Ошибка при проверке подключения:</p>
            <p>${error.message}</p>
        `;
        serverConfig.connected = false;
    }
    
    updateNavigation();
}

// Анализ репозитория
async function analyzeRepository() {
    const analysisDiv = document.getElementById('repo-analysis');
    const analysisBadge = document.getElementById('repo-analysis-badge');
    const analysisInfo = document.getElementById('repo-analysis-info');
    
    // Получаем данные формы
    const formData = new FormData(document.getElementById('repo-select-form'));
    const repoUrl = formData.get('repo-url');
    const projectName = formData.get('project-name') || extractProjectName(repoUrl);
    const branch = formData.get('deploy-branch') === 'custom' ? 
                  formData.get('custom-branch') : formData.get('deploy-branch');
    
    repoInfo = {
        url: repoUrl,
        name: projectName,
        branch: branch
    };
    
    analysisDiv.style.display = 'block';
    analysisBadge.textContent = 'Анализ...';
    analysisBadge.className = 'status-badge';
    analysisInfo.innerHTML = '<p>Анализируем репозиторий...</p>';
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ github_url: repoUrl })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            analysisBadge.textContent = '✅ Анализ завершен';
            analysisBadge.className = 'status-badge success';
            
            const detectedLanguages = result.detected_info?.languages?.join(', ') || 'Не определены';
            const fileCount = result.detected_info?.file_count || 0;
            
            analysisInfo.innerHTML = `
                <p><strong>Репозиторий:</strong> ${repoInfo.name}</p>
                <p><strong>Ветка:</strong> ${branch}</p>
                <p><strong>Языки программирования:</strong> ${detectedLanguages}</p>
                <p><strong>Количество файлов:</strong> ${fileCount}</p>
                <p><strong>Описание:</strong> ${result.repo_info?.description || 'Нет описания'}</p>
                <p class="success">Репозиторий готов к развертыванию!</p>
            `;
            
            repoInfo.analyzed = true;
            repoInfo.detectedInfo = result.detected_info;
            repoInfo.repoInfo = result.repo_info;
            
            // Показываем план развертывания
            showDeployPlan();
        } else {
            analysisBadge.textContent = '❌ Ошибка анализа';
            analysisBadge.className = 'status-badge error';
            analysisInfo.innerHTML = `
                <p class="error">Ошибка при анализе репозитория:</p>
                <p>${result.message}</p>
            `;
            repoInfo.analyzed = false;
        }
    } catch (error) {
        analysisBadge.textContent = '❌ Ошибка';
        analysisBadge.className = 'status-badge error';
        analysisInfo.innerHTML = `
            <p class="error">Ошибка при анализе репозитория:</p>
            <p>${error.message}</p>
        `;
        repoInfo.analyzed = false;
    }
    
    updateNavigation();
}

// Извлечение имени проекта из URL
function extractProjectName(url) {
    const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)/);
    return match ? match[2].replace('.git', '') : 'unknown-project';
}

// Показать план развертывания
function showDeployPlan() {
    const summaryDiv = document.getElementById('deploy-summary');
    const planDiv = document.getElementById('deploy-plan');
    const controlsDiv = document.getElementById('deploy-controls');
    
    const languages = repoInfo.detectedInfo?.languages || [];
    const hasDocker = languages.includes('docker');
    const hasPython = languages.includes('python');
    const hasNode = languages.includes('node');
    const hasJava = languages.includes('java');
    
    let buildSteps = [];
    let deploySteps = [];
    
    // Шаги сборки
    if (hasPython) buildSteps.push('📦 Установка Python зависимостей (pip install)');
    if (hasNode) buildSteps.push('📦 Установка Node.js зависимостей (npm install)');
    if (hasJava) buildSteps.push('📦 Сборка Java проекта (./gradlew build)');
    
    // Шаги развертывания
    deploySteps.push('🔍 Клонирование репозитория с GitHub');
    deploySteps.push('🔧 Автоматическая генерация automata.yml конфигурации');
    if (!hasDocker) deploySteps.push('🐳 Создание Dockerfile для контейнеризации');
    deploySteps.push('🏗️ Сборка проекта на сервере');
    deploySteps.push('🧪 Запуск тестов');
    deploySteps.push('🐳 Создание Docker образа');
    deploySteps.push('🚀 Запуск приложения в Docker контейнере');
    deploySteps.push('🌐 Настройка доступа к приложению');
    
    planDiv.innerHTML = `
        <div class="plan-section">
            <h5>📋 Информация о развертывании:</h5>
            <ul>
                <li><strong>Сервер:</strong> ${serverConfig.ip}:${serverConfig.port}</li>
                <li><strong>Путь:</strong> ${serverConfig.deployPath}/${repoInfo.name}</li>
                <li><strong>Репозиторий:</strong> ${repoInfo.url}</li>
                <li><strong>Ветка:</strong> ${repoInfo.branch}</li>
                <li><strong>Технологии:</strong> ${languages.join(', ')}</li>
            </ul>
        </div>
        
        <div class="plan-section">
            <h5>🏗️ Шаги сборки:</h5>
            <ol>
                ${buildSteps.map(step => `<li>${step}</li>`).join('')}
            </ol>
        </div>
        
        <div class="plan-section">
            <h5>🚀 Шаги развертывания:</h5>
            <ol>
                ${deploySteps.map(step => `<li>${step}</li>`).join('')}
            </ol>
        </div>
    `;
    
    summaryDiv.style.display = 'block';
    controlsDiv.style.display = 'block';
}

// Начать развертывание
async function startDeployment() {
    if (deployInProgress) return;
    
    deployInProgress = true;
    const startBtn = document.getElementById('start-deploy-btn');
    const stopBtn = document.getElementById('stop-deploy-btn');
    const logDiv = document.getElementById('deploy-log');
    const logContent = document.getElementById('log-content');
    
    startBtn.disabled = true;
    startBtn.textContent = '🚀 Развертывание...';
    stopBtn.style.display = 'block';
    logDiv.style.display = 'block';
    
    logContent.innerHTML = '<p>🚀 Начинаем развертывание...</p>';
    
    try {
        const deployData = {
            server: serverConfig,
            repository: repoInfo
        };
        
        const response = await fetch('/deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(deployData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Обработка стримингового ответа
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.trim()) {
                    logContent.innerHTML += `<p>${line}</p>`;
                    logContent.scrollTop = logContent.scrollHeight;
                }
            }
        }
        
        logContent.innerHTML += '<p class="success">✅ Развертывание завершено успешно!</p>';
        
    } catch (error) {
        logContent.innerHTML += `<p class="error">❌ Ошибка развертывания: ${error.message}</p>`;
    } finally {
        deployInProgress = false;
        startBtn.disabled = false;
        startBtn.textContent = '🔄 Повторить развертывание';
        stopBtn.style.display = 'none';
    }
}

// Остановить развертывание
async function stopDeployment() {
    if (!deployInProgress) return;
    
    try {
        await fetch('/stop-deploy', {
            method: 'POST'
        });
        
        deployInProgress = false;
        const startBtn = document.getElementById('start-deploy-btn');
        const stopBtn = document.getElementById('stop-deploy-btn');
        const logContent = document.getElementById('log-content');
        
        startBtn.disabled = false;
        startBtn.textContent = '🔄 Повторить развертывание';
        stopBtn.style.display = 'none';
        
        logContent.innerHTML += '<p class="warning">⏹️ Развертывание остановлено пользователем</p>';
    } catch (error) {
        console.error('Ошибка при остановке развертывания:', error);
    }
}
