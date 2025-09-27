// github-checker.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('check-repo-form');
    const resultDiv = document.getElementById('result');
    const historyDiv = document.getElementById('history');
    
    let checkHistory = JSON.parse(localStorage.getItem('githubCheckHistory')) || [];
    
    // Проверяем существование элементов перед добавлением обработчиков
    const historyBtn = document.getElementById('history-btn');
    const profileBtn = document.getElementById('profile-btn');
    
    if (profileBtn) {
        profileBtn.addEventListener('click', function() {
            window.location.href = 'profile.html';
        });
    }
    
    if (historyBtn) {
        historyBtn.addEventListener('click', function() {
            const isVisible = historyDiv.style.display !== 'none';
            historyDiv.style.display = isVisible ? 'none' : 'block';
            resultDiv.style.display = isVisible ? 'block' : 'none';
            
            if (!isVisible) {
                displayHistory();
            }
        });
    }
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form submitted!');
        
        const url = document.getElementById('repo-url').value;
        console.log('URL:', url);
        
        const resultDiv = document.getElementById('result');
        const statusBadge = document.getElementById('repo-status');
        const repoInfo = document.getElementById('repo-info');
        
        resultDiv.style.display = 'block';
        historyDiv.style.display = 'none';
        
        // Показываем загрузку
        statusBadge.textContent = 'Проверка...';
        statusBadge.className = 'status-badge';
        repoInfo.innerHTML = '<p>Загружаем информацию о репозитории...</p>';
        
        console.log('Starting analysis...');
        
        try {
            const repoData = await checkGitHubRepo(url);
            
            // Сохраняем в историю
            const checkItem = {
                url: url,
                status: repoData.status,
                timestamp: new Date().toISOString(),
                repoName: repoData.repo_info?.name || url.split('/').slice(-2).join('/')
            };
            
            checkHistory.unshift(checkItem);
            if (checkHistory.length > 10) checkHistory = checkHistory.slice(0, 10);
            localStorage.setItem('githubCheckHistory', JSON.stringify(checkHistory));
            
            // Обновляем UI
            if (repoData.status === 'private') {
                statusBadge.textContent = '🔒 Приватный';
                statusBadge.className = 'status-badge private';
                repoInfo.innerHTML = `
                    <h4>${repoData.repo_info?.name || 'Репозиторий'}</h4>
                    <p><strong>Статус:</strong> Приватный репозиторий</p>
                    <p><strong>Доступ:</strong> Только для авторизованных пользователей</p>
                    <p class="error">⚠️ ${repoData.message}</p>
                `;
            } else if (repoData.status === 'success') {
                statusBadge.textContent = '✅ Анализ завершен';
                statusBadge.className = 'status-badge open';
                
                let analysisHtml = '';
                if (repoData.ai_analysis) {
                    const analysis = repoData.ai_analysis;
                    
                    if (analysis.recommendations && analysis.recommendations.length > 0) {
                        analysisHtml += `
                            <h5>Рекомендации по развертыванию:</h5>
                            <ul>
                                ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        `;
                    }
                    
                    if (analysis.files_to_add && analysis.files_to_add.length > 0) {
                        analysisHtml += `
                            <h5>Рекомендуемые файлы для добавления:</h5>
                            <ul>
                                ${analysis.files_to_add.map(file => `
                                    <li>
                                        <strong>${file.name}</strong> - ${file.description}
                                        <pre><code>${file.content}</code></pre>
                                    </li>
                                `).join('')}
                            </ul>
                        `;
                    }
                    
                    if (analysis.deployment_plan && analysis.deployment_plan.length > 0) {
                        analysisHtml += `
                            <h5>План развертывания:</h5>
                            <ol>
                                ${analysis.deployment_plan.map(step => `<li>${step}</li>`).join('')}
                            </ol>
                        `;
                    }
                    
                    if (analysis.tech_stack_analysis) {
                        analysisHtml += `
                            <h5>Анализ технологического стека:</h5>
                            <p>${analysis.tech_stack_analysis}</p>
                        `;
                    }
                }
                
                repoInfo.innerHTML = `
                    <h4>${repoData.repo_info?.name || 'Репозиторий'}</h4>
                    <p><strong>Статус:</strong> ${repoData.message}</p>
                    <p><strong>Описание:</strong> ${repoData.repo_info?.description || 'Нет описания'}</p>
                    <p><strong>Язык:</strong> ${repoData.repo_info?.language || 'Не указан'}</p>
                    <p><strong>Звезды:</strong> ${repoData.repo_info?.stargazers_count || 0}</p>
                    <p><strong>Обнаруженные технологии:</strong> ${repoData.detected_info?.languages?.join(', ') || 'Не определены'}</p>
                    <p class="success">✅ Репозиторий проанализирован системой Amazing Automata.</p>
                    
                    <div class="download-section">
                        <h5>📦 Скачать конфигурацию для Amazing Automata</h5>
                        <p>Получите готовую конфигурацию для автоматизации CI/CD:</p>
                        <button class="btn download-btn" onclick="downloadAmazingAutomataConfig('${url}', ${JSON.stringify(repoData).replace(/"/g, '&quot;')})">
                            ⬇️ Скачать automata.yml
                        </button>
                    </div>
                    
                    ${analysisHtml}
                `;
            } else {
                statusBadge.textContent = '❌ Ошибка';
                statusBadge.className = 'status-badge error';
                repoInfo.innerHTML = `
                    <h4>Ошибка анализа</h4>
                    <p class="error">${repoData.message}</p>
                `;
            }
            
        } catch (error) {
            statusBadge.textContent = '❌ Ошибка';
            statusBadge.className = 'status-badge error';
            repoInfo.innerHTML = `
                <p class="error">Ошибка при проверке репозитория:</p>
                <p>${error.message}</p>
                <p>Проверьте правильность ссылки и попробуйте снова.</p>
            `;
        }
    });
    
    function displayHistory() {
        const historyList = document.getElementById('history-list');
        historyList.innerHTML = '';
        
        if (checkHistory.length === 0) {
            historyList.innerHTML = '<p>История проверок пуста</p>';
            return;
        }
        
        checkHistory.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <strong>${item.repoName}</strong>
                <span class="check-status ${item.status}">${item.status === 'open' ? '🔓 Открытый' : '🔒 Закрытый'}</span>
                <br>
                <small>${new Date(item.timestamp).toLocaleString()}</small>
            `;
            historyList.appendChild(historyItem);
        });
    }
    
    async function checkGitHubRepo(url) {
        // Используем наш API для анализа
        try {
            console.log('Making API request to /analyze');
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ github_url: url })
            });
            
            console.log('Response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('API response:', data);
                return data;
            } else {
                const error = await response.json();
                console.error('API error:', error);
                throw new Error(error.detail || 'Ошибка при запросе к API');
            }
            
        } catch (error) {
            console.error('API request failed:', error);
            // Fallback: прямая проверка через GitHub API
            return await checkGitHubRepoDirect(url);
        }
    }
    
    async function checkGitHubRepoDirect(url) {
        // Извлекаем username и repo name из URL
        const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)/);
        if (!match) {
            throw new Error('Неверный формат GitHub ссылки');
        }
        
        const [, username, repo] = match;
        const apiUrl = `https://api.github.com/repos/${username}/${repo}`;
        
        try {
            const response = await fetch(apiUrl);
            
            if (response.status === 404) {
                throw new Error('Репозиторий не найден');
            }
            
            if (response.status === 403) {
                // Если достигнут лимит API, используем fallback проверку
                return await checkRepoViaPage(url);
            }
            
            const data = await response.json();
            
            if (response.status !== 200) {
                throw new Error(data.message || 'Ошибка при запросе к GitHub API');
            }
            
            return {
                status: data.private ? 'private' : 'success',
                message: data.private ? 'Приватный репозиторий' : 'Репозиторий доступен',
                repo_info: {
                    name: data.full_name,
                    description: data.description,
                    language: data.language,
                    stargazers_count: data.stargazers_count,
                    html_url: data.html_url
                },
                detected_info: {
                    languages: [data.language].filter(Boolean)
                }
            };
            
        } catch (error) {
            if (error.message.includes('Failed to fetch')) {
                // Fallback: проверка через открытие страницы
                return await checkRepoViaPage(url);
            }
            throw error;
        }
    }
    
    async function checkRepoViaPage(url) {
        // Простая проверка доступности страницы
        try {
            const response = await fetch(url);
            if (response.status === 404) {
                return { isPrivate: true };
            }
            return { isPrivate: false };
        } catch (error) {
            throw new Error('Не удалось проверить репозиторий');
        }
    }
});

// Функция скачивания конфигурации Amazing Automata
function downloadAmazingAutomataConfig(githubUrl, repoData) {
    try {
        // Извлекаем имя репозитория из URL
        const repoName = githubUrl.split('/').slice(-1)[0].replace('.git', '');
        
        // Генерируем конфигурацию automata.yml
        const config = generateAmazingAutomataConfig(repoData, repoName);
        
        // Создаем blob и скачиваем файл
        const blob = new Blob([config], { type: 'text/yaml' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'automata.yml';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        // Показываем инструкцию
        showUsageInstructions(repoName);
        
    } catch (error) {
        console.error('Error downloading config:', error);
        alert('Ошибка при скачивании конфигурации: ' + error.message);
    }
}

// Генерация конфигурации automata.yml
function generateAmazingAutomataConfig(repoData, repoName) {
    const languages = repoData.detected_info?.languages || [];
    const hasPython = languages.includes('python');
    const hasNode = languages.includes('node') || languages.includes('javascript');
    const hasJava = languages.includes('java');
    const hasGo = languages.includes('go');
    const hasRust = languages.includes('rust');
    
    let config = `name: ${repoName}
version: 1.0.0
description: Auto-generated config for ${repoName}
build:
`;

    if (hasPython) {
        config += `  python:
    command: pip install -r requirements.txt
    output: dist/
`;
    }
    
    if (hasNode) {
        config += `  node:
    command: npm ci && npm run build
    output: dist/
`;
    }
    
    if (hasJava) {
        config += `  java:
    command: mvn clean package -DskipTests
    output: target/*.jar
`;
    }
    
    if (hasGo) {
        config += `  go:
    command: go build -o bin/app .
    output: bin/
`;
    }
    
    if (hasRust) {
        config += `  rust:
    command: cargo build --release
    output: target/release/
`;

    config += `
test:
`;

    if (hasPython) {
        config += `  python:
    command: pytest -v
    coverage: true
`;
    }
    
    if (hasNode) {
        config += `  node:
    command: npm test
    coverage: true
`;
    }
    
    if (hasJava) {
        config += `  java:
    command: mvn test
    coverage: true
`;
    }

    config += `
deploy:
  docker:
    image: ${repoName}:latest
    file: Dockerfile
    port: 8000
    push: false
    env:
`;

    if (hasNode) {
        config += `      NODE_ENV: production
      PORT: "8000"
`;
    }
    
    if (hasPython) {
        config += `      PYTHONUNBUFFERED: "1"
      PORT: "8000"
`;
    }

    config += `
  ssh:
    host: localhost
    user: root
    path: /opt/${repoName}
    restart: systemctl restart ${repoName}
`;

    return config;
}

// Показ инструкций по использованию
function showUsageInstructions(repoName) {
    const instructions = `
🎉 Конфигурация automata.yml скачана!

📋 Как использовать:

1. Поместите файл automata.yml в корень вашего проекта
2. Убедитесь что установлен Amazing Automata
3. Запустите автоматизацию:

   python -m automata_cli.cli run --cwd . --config automata.yml --stage all

4. Или по этапам:
   python -m automata_cli.cli run --cwd . --stage detect    # Детекция
   python -m automata_cli.cli run --cwd . --stage build     # Сборка  
   python -m automata_cli.cli run --cwd . --stage test      # Тестирование
   python -m automata_cli.cli run --cwd . --stage deploy    # Развертывание

✨ Amazing Automata автоматически:
   - Обнаружит технологии в проекте
   - Соберет приложение
   - Запустит тесты
   - Создаст Docker образ
   - Развернет приложение

🚀 Готово к автоматизации!`;

    // Создаем модальное окно с инструкциями
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: white;
        padding: 30px;
        border-radius: 10px;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    `;
    
    modalContent.innerHTML = `
        <h3>🎉 Конфигурация скачана!</h3>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap;">${instructions}</pre>
        <button onclick="this.parentElement.parentElement.remove()" style="
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 15px;
        ">Понятно!</button>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Закрытие по клику вне модального окна
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}