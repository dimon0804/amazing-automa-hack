// Исправленная версия GitHub Checker
document.addEventListener('DOMContentLoaded', function() {
    console.log('GitHub Checker loaded!');
    
    const form = document.getElementById('check-repo-form');
    const resultDiv = document.getElementById('result');
    const historyDiv = document.getElementById('history');
    
    let checkHistory = JSON.parse(localStorage.getItem('githubCheckHistory')) || [];
    
    console.log('Form found:', form);
    console.log('Result div found:', resultDiv);
    
    if (!form) {
        console.error('Form not found!');
        return;
    }
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form submitted!');
        
        const url = document.getElementById('repo-url').value;
        console.log('URL:', url);
        
        if (!url) {
            console.error('No URL provided');
            return;
        }
        
        const statusBadge = document.getElementById('repo-status');
        const repoInfo = document.getElementById('repo-info');
        
        if (!resultDiv || !statusBadge || !repoInfo) {
            console.error('Required elements not found');
            return;
        }
        
        resultDiv.style.display = 'block';
        historyDiv.style.display = 'none';
        
        // Показываем загрузку
        statusBadge.textContent = 'Проверка...';
        statusBadge.className = 'status-badge';
        repoInfo.innerHTML = '<p>Загружаем информацию о репозитории...</p>';
        
        console.log('Starting analysis...');
        
        try {
            const repoData = await checkGitHubRepo(url);
            console.log('Analysis complete:', repoData);
            
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
            updateUI(repoData, statusBadge, repoInfo, url);
            
        } catch (error) {
            console.error('Analysis error:', error);
            statusBadge.textContent = '❌ Ошибка';
            statusBadge.className = 'status-badge error';
            repoInfo.innerHTML = `
                <p class="error">Ошибка при проверке репозитория:</p>
                <p>${error.message}</p>
                <p>Проверьте правильность ссылки и попробуйте снова.</p>
            `;
        }
    });
    
    function updateUI(repoData, statusBadge, repoInfo, url) {
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
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h4 style="margin: 0;">${repoData.repo_info?.name || 'Репозиторий'}</h4>
                    <button onclick="resetForm()" style="
                        background: linear-gradient(135deg, #4ade80, #22c55e);
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 12px;
                        font-weight: 600;
                        box-shadow: 0 4px 15px rgba(74, 222, 128, 0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='translateY(0)'">
                        🔄 Новый анализ
                    </button>
                </div>
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
    }
    
    async function checkGitHubRepo(url) {
        console.log('Making API request to /analyze');
        try {
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
            throw error;
        }
    }
});

// Функция скачивания конфигурации Amazing Automata
function downloadAmazingAutomataConfig(githubUrl, repoData) {
    try {
        console.log('Downloading config for:', githubUrl);
        
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
    }

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
        background: linear-gradient(135deg, #1a1a1a, #0d0d0d);
        padding: 30px;
        border-radius: 16px;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.8);
        border: 1px solid rgba(93, 211, 255, 0.2);
        color: #e6f7ff;
    `;
    
    modalContent.innerHTML = `
        <h3 style="color: #ffffff; margin-bottom: 20px; text-align: center;">🎉 Конфигурация скачана!</h3>
        <pre style="background: #0a0a0a; color: #e6f7ff; padding: 20px; border-radius: 12px; overflow-x: auto; white-space: pre-wrap; border: 1px solid rgba(93, 211, 255, 0.2); font-family: 'Fira Code', monospace; line-height: 1.6;">${instructions}</pre>
        <button onclick="this.parentElement.parentElement.remove()" style="
            background: linear-gradient(135deg, #5dd3ff, #00bfff);
            color: #001a33;
            border: none;
            padding: 12px 24px;
            border-radius: 12px;
            cursor: pointer;
            margin-top: 20px;
            font-weight: 700;
            font-size: 16px;
            box-shadow: 0 6px 20px rgba(93, 211, 255, 0.4);
            transition: all 0.3s ease;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(93, 211, 255, 0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 20px rgba(93, 211, 255, 0.4)'">Понятно!</button>
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
    
    // Функция сброса формы для нового анализа
    window.resetForm = function() {
        const resultDiv = document.getElementById('result');
        const repoUrl = document.getElementById('repo-url');
        
        // Очищаем поле ввода
        repoUrl.value = '';
        
        // Скрываем результат
        resultDiv.style.display = 'none';
        
        // Фокусируемся на поле ввода
        repoUrl.focus();
        
        console.log('Form reset for new analysis');
    }
