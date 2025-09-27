import yaml
from pathlib import Path
from typing import Dict, List, Optional


def generate_automata_yml(cwd: Path, detected: Dict, project_name: Optional[str] = None) -> Dict:
    """Генерирует automata.yml на основе обнаруженных языков и структуры проекта"""
    
    if not project_name:
        project_name = cwd.name.lower().replace(' ', '-').replace('_', '-')
    
    config = {
        'name': project_name,
        'version': '1.0.0',
        'description': f'Auto-generated config for {project_name}',
        'build': {},
        'test': {},
        'deploy': {}
    }
    
    # Настройки сборки на основе языков
    languages = detected.get('languages', [])
    
    if 'python' in languages:
        config['build']['python'] = {
            'command': 'pip install -r requirements.txt',
            'output': 'dist/'
        }
    
    if 'node' in languages:
        config['build']['node'] = {
            'command': 'npm ci && npm run build',
            'output': 'dist/'
        }
    
    if 'java' in languages:
        config['build']['java'] = {
            'command': 'mvn clean package -DskipTests',
            'output': 'target/*.jar'
        }
    
    if 'go' in languages:
        config['build']['go'] = {
            'command': 'go build -o bin/app .',
            'output': 'bin/'
        }
    
    if 'rust' in languages:
        config['build']['rust'] = {
            'command': 'cargo build --release',
            'output': 'target/release/'
        }
    
    # Настройки тестирования
    if 'python' in languages:
        config['test']['python'] = {
            'command': 'pytest -v',
            'coverage': True
        }
    
    if 'node' in languages:
        config['test']['node'] = {
            'command': 'npm test',
            'coverage': True
        }
    
    if 'java' in languages:
        config['test']['java'] = {
            'command': 'mvn test',
            'coverage': True
        }
    
    # Настройки деплоя
    if 'docker' in languages:
        config['deploy']['docker'] = {
            'image': f'{project_name}:latest',
            'file': 'Dockerfile',
            'port': 8000,
            'push': False,
            'env': {}
        }
    else:
        # Если нет Dockerfile, создадим базовый
        config['deploy']['docker'] = {
            'image': f'{project_name}:latest',
            'file': 'Dockerfile',
            'port': 8000,
            'push': False,
            'env': {}
        }
    
    # Добавляем специфичные переменные окружения для разных типов приложений
    if 'node' in languages:
        config['deploy']['docker']['env']['NODE_ENV'] = 'production'
        config['deploy']['docker']['env']['PORT'] = '8000'
    
    if 'python' in languages:
        config['deploy']['docker']['env']['PYTHONUNBUFFERED'] = '1'
        config['deploy']['docker']['env']['PORT'] = '8000'
    
    # SSH деплой (опционально)
    config['deploy']['ssh'] = {
        'host': 'localhost',
        'user': 'root',
        'path': f'/opt/{project_name}',
        'restart': f'systemctl restart {project_name}'
    }
    
    return config


def save_automata_yml(config: Dict, path: Path) -> None:
    """Сохраняет конфигурацию в файл automata.yml"""
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)


def generate_dockerfile(cwd: Path, detected: Dict) -> None:
    """Генерирует базовый Dockerfile если его нет"""
    dockerfile_path = cwd / 'Dockerfile'
    if dockerfile_path.exists():
        return
    
    languages = detected.get('languages', [])
    
    if 'python' in languages:
        dockerfile_content = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "hello"]"""
    elif 'node' in languages:
        dockerfile_content = """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 8000
CMD ["node", "index.js"]"""
    else:
        dockerfile_content = """FROM ubuntu:20.04
WORKDIR /app
COPY . .
EXPOSE 8000
CMD ["echo", "Hello from container"]"""
    
    with open(dockerfile_path, 'w', encoding='utf-8') as f:
        f.write(dockerfile_content)
    
    print(f"Generated Dockerfile for {cwd.name}")


def auto_generate_config(cwd: Path, detected: Dict, force: bool = False) -> bool:
    """Автоматически генерирует automata.yml если его нет"""
    config_path = cwd / 'automata.yml'
    
    if config_path.exists() and not force:
        print(f"Config already exists: {config_path}")
        return False
    
    print(f"Generating automata.yml for {cwd.name}...")
    
    try:
        config = generate_automata_yml(cwd, detected)
        save_automata_yml(config, config_path)
        
        # Генерируем Dockerfile если его нет
        generate_dockerfile(cwd, detected)
        
        print(f"Generated: {config_path}")
        return True
    except Exception as e:
        print(f"Error generating config: {e}")
        return False
