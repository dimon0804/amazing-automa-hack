# Быстрый старт - Amazing Automata

## 1. Установка (2 минуты)

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd amazing-automata-hack

# Установите зависимости
pip install -r requirements.txt
```

## 2. Тестирование на примерах (5 минут)

### Пример 1: Простое Python приложение
```bash
cd examples/hello_py
python -m automata_cli.cli run --stage all
```

### Пример 2: FastAPI веб-приложение
```bash
cd examples/sample_api
python -m automata_cli.cli run --stage all
```

### Пример 3: Flask приложение
```bash
cd examples/desktop2proxy
python -m automata_cli.cli run --stage all
```

## 3. Использование на вашем проекте (3 минуты)

### Шаг 1: Подготовьте проект
Убедитесь, что в корне проекта есть:
- `requirements.txt` (Python) или `package.json` (Node.js) или другие файлы зависимостей
- Тесты (pytest, npm test, etc.)
- `Dockerfile` (опционально, для деплоя)

### Шаг 2: Создайте automata.yml
```yaml
deploy:
  docker:
    image: your-app:latest
    file: Dockerfile
    push: false
```

### Шаг 3: Запустите пайплайн
```bash
python -m automata_cli.cli run --cwd /path/to/your/project
```

## 4. Проверка результатов

После выполнения вы увидите:
- **Detect**: список найденных технологий
- **Build**: установленные зависимости
- **Test**: результаты тестов
- **Deploy**: собранный Docker-образ (если настроено)

## 5. Интеграция в CI/CD

### GitHub Actions
```yaml
- name: Run Automata
  run: python -m automata_cli.cli run --stage all
```

### GitLab CI
```yaml
script:
  - python -m automata_cli.cli run --stage all
```

## Готово!

Теперь у вас есть универсальный пайплайн, который автоматически:
- Определяет технологии в проекте
- Собирает зависимости
- Запускает тесты
- Создает Docker-образы

**Время настройки: ~10 минут вместо часов написания индивидуальных пайплайнов.**
