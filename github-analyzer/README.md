# 🌟 GitHub Repository Analyzer

> **Умная система анализа GitHub репозиториев с автоматической генерацией CI/CD конфигураций**

![GitHub Analyzer](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Что это такое?

**GitHub Repository Analyzer** — это веб-приложение, которое автоматически анализирует публичные GitHub репозитории и предоставляет:

- 🔍 **Детекцию технологий** (Python, Node.js, Java, Go, Rust, Docker)
- 📊 **Анализ структуры проекта** 
- 💡 **Умные рекомендации** по CI/CD и развертыванию
- 📦 **Автоматическую генерацию конфигураций** для Amazing Automata
- 🎯 **Готовые файлы** для автоматизации (Dockerfile, GitHub Actions, etc.)

## 🏗️ Структура проекта

```
github-analyzer/
├── 📁 front/                    # Фронтенд (HTML, CSS, JS)
│   ├── index.html              # Главная страница
│   ├── github-checker.js       # Логика анализа
│   └── styleses.css            # Стили
├── 📄 simple_app.py            # Основное приложение (FastAPI)
├── 📄 simple_requirements.txt  # Зависимости
├── 📄 Dockerfile              # Контейнеризация
└── 📄 README.md               # Документация
```

## ⚡ Быстрый старт

### 1. Установка

```bash
# Клонируйте репозиторий
git clone <your-repo-url>
cd github-analyzer

# Установите зависимости
pip install -r simple_requirements.txt
```

### 2. Запуск

```bash
# Запустите приложение
python simple_app.py
```

### 3. Использование

1. Откройте браузер: **http://localhost:8000**
2. Введите ссылку на GitHub репозиторий
3. Нажмите **"🔍 Проверить"**
4. Получите детальный анализ и рекомендации
5. Скачайте готовую конфигурацию для Amazing Automata

## 🎯 Возможности

### ✨ Анализ репозиториев
- **Проверка публичности** репозитория
- **Детекция технологий** по файлам и расширениям
- **Анализ структуры** проекта
- **Подсчет файлов** и метрик

### 🛠️ Генерация конфигураций
- **Dockerfile** для контейнеризации
- **GitHub Actions** для CI/CD
- **requirements.txt** для Python проектов
- **package.json** для Node.js проектов
- **automata.yml** для Amazing Automata

### 🎨 Умные рекомендации
- **План развертывания** по шагам
- **Приоритетные действия** для улучшения
- **Анализ технологического стека**
- **Советы по безопасности** и мониторингу

## 🔧 API Endpoints

### `POST /analyze`
Анализирует GitHub репозиторий

**Запрос:**
```json
{
  "github_url": "https://github.com/fastapi/fastapi"
}
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Анализ завершен успешно",
  "repo_info": {
    "name": "fastapi/fastapi",
    "description": "FastAPI framework...",
    "language": "Python",
    "stargazers_count": 89848
  },
  "detected_info": {
    "languages": ["python", "javascript"],
    "file_count": 2487
  },
  "ai_analysis": {
    "recommendations": ["Добавить Dockerfile..."],
    "files_to_add": [...],
    "deployment_plan": [...],
    "tech_stack_analysis": "Обнаружены технологии: python, javascript"
  }
}
```

### `GET /health`
Проверка состояния сервиса

## 🐳 Docker запуск

```bash
# Сборка образа
docker build -t github-analyzer .

# Запуск контейнера
docker run -p 8000:8000 github-analyzer
```

## 🎨 Интерфейс

- **Современный дизайн** с адаптивной версткой
- **Интуитивно понятный** интерфейс
- **Реальное время** анализа
- **Детальные результаты** с рекомендациями
- **Кнопка скачивания** конфигурации

## 🔗 Интеграция с Amazing Automata

После анализа репозитория вы можете:

1. **Скачать готовую конфигурацию** `automata.yml`
2. **Использовать в Amazing Automata:**
   ```bash
   python -m automata_cli.cli run --cwd your-project --config automata.yml --stage all
   ```

## 📋 Примеры анализа

### Python проект (FastAPI)
- ✅ Обнаружены: Python, JavaScript
- 📁 Файлов: 2,487
- 💡 Рекомендации: Dockerfile, CI/CD, тестирование

### Node.js проект (React)
- ✅ Обнаружены: JavaScript, TypeScript
- 📁 Файлов: 1,200+
- 💡 Рекомендации: package.json, Docker, GitHub Actions

## 🚀 Roadmap

- [ ] Поддержка приватных репозиториев (с токеном)
- [ ] Интеграция с ChatGPT/OpenAI для умного анализа
- [ ] Экспорт в различные форматы (JSON, YAML)
- [ ] История анализов
- [ ] Пользовательские аккаунты
- [ ] API для интеграции с внешними системами

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Создайте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) - за отличный веб-фреймворк
- [Amazing Automata](https://github.com/your-repo/amazing-automata) - за систему автоматизации CI/CD
- [GitHub API](https://docs.github.com/en/rest) - за предоставление данных о репозиториях

---

**Сделано с ❤️ для автоматизации DevOps процессов**