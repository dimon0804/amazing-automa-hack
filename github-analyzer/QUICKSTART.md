# 🚀 Быстрый старт - GitHub Repository Analyzer

## ⚡ Запуск за 3 шага

### 1️⃣ Установка зависимостей
```bash
pip install -r simple_requirements.txt
```

### 2️⃣ Запуск приложения
```bash
python simple_app.py
```

### 3️⃣ Открыть в браузере
Перейдите по адресу: **http://localhost:8000**

---

## 🎯 Как использовать

1. **Введите ссылку** на GitHub репозиторий
2. **Нажмите "🔍 Проверить"**
3. **Получите анализ** с рекомендациями
4. **Скачайте конфигурацию** для Amazing Automata

---

## 📋 Примеры репозиториев для тестирования

### Python проекты:
- `https://github.com/fastapi/fastapi`
- `https://github.com/django/django`
- `https://github.com/pallets/flask`

### Node.js проекты:
- `https://github.com/facebook/react`
- `https://github.com/nodejs/node`
- `https://github.com/expressjs/express`

### Java проекты:
- `https://github.com/spring-projects/spring-boot`
- `https://github.com/apache/kafka`
- `https://github.com/eclipse-vertx/vert.x`

### Go проекты:
- `https://github.com/golang/go`
- `https://github.com/gin-gonic/gin`
- `https://github.com/kubernetes/kubernetes`

---

## 🔧 Что получаете после анализа

### ✅ Автоматически определяется:
- **Языки программирования** (Python, Node.js, Java, Go, Rust)
- **Количество файлов** в проекте
- **Структура проекта** и зависимости

### 📦 Генерируется конфигурация:
- **automata.yml** - для Amazing Automata
- **Dockerfile** - для контейнеризации
- **GitHub Actions** - для CI/CD
- **requirements.txt** - для Python проектов

### 💡 Рекомендации:
- **План развертывания** по шагам
- **Приоритетные действия** для улучшения
- **Анализ технологического стека**
- **Советы по безопасности**

---

## 🎉 После скачивания конфигурации

### Используйте в Amazing Automata:
```bash
# Полный пайплайн
python -m automata_cli.cli run --cwd . --config automata.yml --stage all

# По этапам
python -m automata_cli.cli run --cwd . --stage detect    # Детекция
python -m automata_cli.cli run --cwd . --stage build     # Сборка  
python -m automata_cli.cli run --cwd . --stage test      # Тестирование
python -m automata_cli.cli run --cwd . --stage deploy    # Развертывание
```

---

## 🐳 Docker запуск (опционально)

```bash
# Сборка образа
docker build -t github-analyzer .

# Запуск контейнера
docker run -p 8000:8000 github-analyzer
```

---

## 🛠️ Структура проекта

```
github-analyzer/
├── 📁 front/                    # Фронтенд
│   ├── index.html              # Главная страница
│   ├── github-checker.js       # Логика анализа
│   └── styleses.css            # Стили
├── 📄 simple_app.py            # Основное приложение
├── 📄 simple_requirements.txt  # Зависимости
├── 📄 Dockerfile              # Контейнеризация
├── 📄 README.md               # Подробная документация
└── 📄 QUICKSTART.md           # Эта инструкция
```

---

## 🎨 Возможности интерфейса

- **Современный дизайн** с анимациями
- **Адаптивная верстка** для всех устройств
- **Реальное время** анализа репозиториев
- **Красивые результаты** с рекомендациями
- **Кнопка скачивания** с инструкциями

---

## ⚠️ Требования

- **Python 3.8+**
- **Git** (для клонирования репозиториев)
- **Интернет** (для доступа к GitHub API)

---

## 🆘 Поддержка

Если что-то не работает:

1. **Проверьте Python версию:** `python --version`
2. **Установите Git:** [git-scm.com](https://git-scm.com/)
3. **Проверьте интернет соединение**
4. **Убедитесь что репозиторий публичный**

---

**🎉 Готово! Наслаждайтесь автоматизацией CI/CD!**
