// profile.js
document.addEventListener('DOMContentLoaded', function() {
    // Загрузка данных пользователя (в реальном приложении - с сервера)
    const userData = JSON.parse(localStorage.getItem('userData')) || {
        name: 'Агаппина',
        email: 'agappina@example.com',
        checksCount: 12,
        openRepos: 8,
        privateRepos: 4
    };
    
    // Обновление UI
    document.getElementById('user-name').textContent = userData.name;
    document.getElementById('user-email').textContent = userData.email;
    document.getElementById('checks-count').textContent = userData.checksCount;
    document.getElementById('open-repos').textContent = userData.openRepos;
    document.getElementById('private-repos').textContent = userData.privateRepos;
    
    // Обработка настроек
    const settings = document.querySelectorAll('.setting-item input');
    settings.forEach(setting => {
        setting.addEventListener('change', function() {
            // Сохранение настроек
            const settingsData = {
                notifications: document.querySelectorAll('.setting-item input')[0].checked,
                saveHistory: document.querySelectorAll('.setting-item input')[1].checked,
                darkTheme: document.querySelectorAll('.setting-item input')[2].checked
            };
            localStorage.setItem('userSettings', JSON.stringify(settingsData));
        });
    });
});