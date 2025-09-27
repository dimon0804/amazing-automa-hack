// github-checker.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('check-repo-form');
    const resultDiv = document.getElementById('result');
    const historyDiv = document.getElementById('history');
    const historyBtn = document.getElementById('history-btn');
    const profileBtn = document.getElementById('profile-btn');
    
    let checkHistory = JSON.parse(localStorage.getItem('githubCheckHistory')) || [];
    
    // Переход на страницу профиля
    profileBtn.addEventListener('click', function() {
        window.location.href = 'profile.html';
    });
    
    // Переключение истории
    historyBtn.addEventListener('click', function() {
        const isVisible = historyDiv.style.display !== 'none';
        historyDiv.style.display = isVisible ? 'none' : 'block';
        resultDiv.style.display = isVisible ? 'block' : 'none';
        
        if (!isVisible) {
            displayHistory();
        }
    });
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const url = document.getElementById('repo-url').value;
        const resultDiv = document.getElementById('result');
        const statusBadge = document.getElementById('repo-status');
        const repoInfo = document.getElementById('repo-info');
        
        resultDiv.style.display = 'block';
        historyDiv.style.display = 'none';
        
        // Показываем загрузку
        statusBadge.textContent = 'Проверка...';
        statusBadge.className = 'status-badge';
        repoInfo.innerHTML = '<p>Загружаем информацию о репозитории...</p>';
        
        try {
            const repoData = await checkGitHubRepo(url);
            
            // Сохраняем в историю
            const checkItem = {
                url: url,
                status: repoData.isPrivate ? 'private' : 'open',
                timestamp: new Date().toISOString(),
                repoName: repoData.full_name || url
            };
            
            checkHistory.unshift(checkItem);
            if (checkHistory.length > 10) checkHistory = checkHistory.slice(0, 10);
            localStorage.setItem('githubCheckHistory', JSON.stringify(checkHistory));
            
            // Обновляем UI
            if (repoData.isPrivate) {
                statusBadge.textContent = '🔒 Закрытый';
                statusBadge.className = 'status-badge private';
                repoInfo.innerHTML = `
                    <h4>${repoData.full_name || 'Репозиторий'}</h4>
                    <p><strong>Статус:</strong> Закрытый репозиторий</p>
                    <p><strong>Доступ:</strong> Только для авторизованных пользователей</p>
                    <p class="error">⚠️ Этот репозиторий является приватным и не может быть использован без разрешения.</p>
                `;
            } else {
                statusBadge.textContent = '🔓 Открытый';
                statusBadge.className = 'status-badge open';
                repoInfo.innerHTML = `
                    <h4>${repoData.full_name || 'Репозиторий'}</h4>
                    <p><strong>Статус:</strong> Открытый репозиторий</p>
                    <p><strong>Описание:</strong> ${repoData.description || 'Нет описания'}</p>
                    <p><strong>Язык:</strong> ${repoData.language || 'Не указан'}</p>
                    <p><strong>Звезды:</strong> ${repoData.stargazers_count || 0}</p>
                    <p><strong>Последнее обновление:</strong> ${new Date(repoData.updated_at).toLocaleDateString()}</p>
                    <p class="success">✅ Этот репозиторий можно безопасно использовать в проектах.</p>
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
                full_name: data.full_name,
                description: data.description,
                language: data.language,
                stargazers_count: data.stargazers_count,
                updated_at: data.updated_at,
                isPrivate: data.private
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