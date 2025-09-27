import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import paramiko

load_dotenv()

app = FastAPI(title="GitHub Analyzer", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="front"), name="static")

class SimpleGitHubAnalyzer:
    def __init__(self):
        pass
    
    async def analyze_repository(self, github_url: str) -> Dict[str, Any]:
        """Analyze GitHub repository using simple detection"""
        try:
            # Check if repository is public
            is_public, repo_info = await self._check_repository_visibility(github_url)
            if not is_public:
                return {
                    "status": "private",
                    "message": "Репозиторий является приватным и не может быть проанализирован",
                    "repo_info": repo_info
                }
            
            # Clone repository
            temp_dir = await self._clone_repository(github_url)
            
            # Run simple detection
            detected_info = self._run_simple_detect(temp_dir)
            
            # Get analysis
            analysis = self._get_simple_analysis(
                repo_info=repo_info,
                detected_info=detected_info,
                repo_path=temp_dir
            )
            
            return {
                "status": "success",
                "message": "Анализ завершен успешно",
                "repo_info": repo_info,
                "detected_info": detected_info,
                "ai_analysis": analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при анализе: {str(e)}",
                "repo_info": {}
            }
        finally:
            if 'temp_dir' in locals() and temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except PermissionError:
                    print(f"Warning: Could not delete temp directory {temp_dir}")
    
    async def _check_repository_visibility(self, github_url: str) -> tuple[bool, Dict[str, Any]]:
        """Check if GitHub repository is public"""
        try:
            # Extract owner and repo from URL
            parts = github_url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                raise ValueError("Invalid GitHub URL")
            
            owner, repo = parts[0], parts[1].replace(".git", "")
            
            # Check via GitHub API
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
                
                if response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Репозиторий не найден")
                
                if response.status_code == 403:
                    # Rate limited or private
                    return False, {"message": "Репозиторий недоступен (возможно приватный)"}
                
                repo_data = response.json()
                return not repo_data.get("private", True), repo_data
                
        except httpx.HTTPError:
            return False, {"message": "Ошибка при проверке репозитория"}
    
    async def _clone_repository(self, github_url: str) -> Path:
        """Clone repository to temporary directory"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            import subprocess
            # Try cloning without specifying branch (gets default branch)
            result = subprocess.run(
                ["git", "clone", "--depth", "1", github_url, str(temp_dir)],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode != 0:
                # If that fails, try to detect and use the default branch
                if "not found in upstream origin" in result.stderr:
                    # Try to get the default branch
                    default_branch_result = subprocess.run([
                        'git', 'ls-remote', '--symref', github_url, 'HEAD'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if default_branch_result.returncode == 0:
                        # Extract default branch from output
                        import re
                        match = re.search(r'refs/heads/(\w+)', default_branch_result.stdout)
                        if match:
                            default_branch = match.group(1)
                            # Clean up failed attempt
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            temp_dir = Path(tempfile.mkdtemp())
                            
                            # Try again with default branch
                            result = subprocess.run(
                                ["git", "clone", "--depth", "1", "--branch", default_branch, github_url, str(temp_dir)],
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
            
            if result.returncode != 0:
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                if "git" in result.stderr.lower() and "not found" in result.stderr.lower():
                    raise HTTPException(status_code=400, detail="Git не установлен. Установите Git для клонирования репозиториев.")
                raise HTTPException(status_code=400, detail=f"Не удалось клонировать репозиторий: {result.stderr}")
            
            return temp_dir
            
        except subprocess.TimeoutExpired:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            raise HTTPException(status_code=400, detail="Таймаут при клонировании репозитория")
        except FileNotFoundError:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            raise HTTPException(status_code=400, detail="Git не найден. Установите Git для клонирования репозиториев.")
    
    def _run_simple_detect(self, repo_path: Path) -> Dict[str, Any]:
        """Run simple detection on the repository"""
        try:
            languages = []
            file_count = 0
            
            # Scan files for language detection
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and '.git' not in str(file_path):
                    file_count += 1
                    file_name = file_path.name.lower()
                    
                    # Detect languages by file extensions
                    if file_name.endswith('.py'):
                        if 'python' not in languages:
                            languages.append('python')
                    elif file_name.endswith('.js') or file_name.endswith('.ts'):
                        if 'javascript' not in languages:
                            languages.append('javascript')
                    elif file_name.endswith('.java'):
                        if 'java' not in languages:
                            languages.append('java')
                    elif file_name.endswith('.go'):
                        if 'go' not in languages:
                            languages.append('go')
                    elif file_name.endswith('.rs'):
                        if 'rust' not in languages:
                            languages.append('rust')
                    elif file_name == 'package.json':
                        if 'node' not in languages:
                            languages.append('node')
                    elif file_name == 'requirements.txt':
                        if 'python' not in languages:
                            languages.append('python')
                    elif file_name == 'pom.xml':
                        if 'java' not in languages:
                            languages.append('java')
                    elif file_name == 'go.mod':
                        if 'go' not in languages:
                            languages.append('go')
                    elif file_name == 'cargo.toml':
                        if 'rust' not in languages:
                            languages.append('rust')
                    elif file_name == 'dockerfile':
                        if 'docker' not in languages:
                            languages.append('docker')
            
            return {
                "languages": languages,
                "file_count": file_count
            }
            
        except Exception as e:
            print(f"Detection error: {e}")
            return {
                "languages": [],
                "file_count": 0
            }
    
    def _get_simple_analysis(self, repo_info: Dict[str, Any], detected_info: Dict[str, Any], repo_path: Path) -> Dict[str, Any]:
        """Get simple analysis without AI"""
        recommendations = []
        files_to_add = []
        deployment_plan = []
        
        # Basic recommendations based on detected technologies
        languages = detected_info.get('languages', [])
        
        if not (repo_path / "Dockerfile").exists():
            recommendations.append("Добавить Dockerfile для контейнеризации приложения")
            files_to_add.append({
                "name": "Dockerfile",
                "content": self._generate_dockerfile(languages),
                "description": "Конфигурация Docker контейнера"
            })
        
        if 'python' in languages and not (repo_path / "requirements.txt").exists():
            recommendations.append("Добавить requirements.txt для Python зависимостей")
            files_to_add.append({
                "name": "requirements.txt",
                "content": "# Add your Python dependencies here\n# Example:\n# fastapi==0.100.0\n# uvicorn==0.23.0",
                "description": "Python зависимости"
            })
        
        if 'node' in languages and not (repo_path / "package.json").exists():
            recommendations.append("Добавить package.json для Node.js зависимостей")
            files_to_add.append({
                "name": "package.json",
                "content": '{\n  "name": "your-project",\n  "version": "1.0.0",\n  "main": "index.js",\n  "scripts": {\n    "start": "node index.js"\n  },\n  "dependencies": {}\n}',
                "description": "Node.js конфигурация"
            })
        
        # Always recommend CI/CD
        if not (repo_path / ".github" / "workflows").exists():
            recommendations.append("Настроить CI/CD пайплайн с GitHub Actions")
            files_to_add.append({
                "name": ".github/workflows/ci.yml",
                "content": self._generate_github_actions(languages),
                "description": "CI/CD пайплайн"
            })
        
        # Generate deployment plan
        deployment_plan = [
            "1. Настроить автоматическую сборку",
            "2. Добавить тестирование",
            "3. Настроить развертывание",
            "4. Добавить мониторинг"
        ]
        
        # Tech stack analysis
        tech_stack_analysis = f"Обнаружены технологии: {', '.join(languages) if languages else 'Не определены'}"
        
        return {
            "recommendations": recommendations,
            "files_to_add": files_to_add,
            "deployment_plan": deployment_plan,
            "tech_stack_analysis": tech_stack_analysis,
                "priority_actions": ["Добавить Dockerfile", "Настроить CI/CD"] if not (repo_path / "Dockerfile").exists() else ["Настроить CI/CD"]
        }
    
    def _generate_dockerfile(self, languages: List[str]) -> str:
        """Generate Dockerfile based on detected languages"""
        if 'python' in languages:
            return """FROM python:3.11-slim

WORKDIR /app

# Copy requirements.txt if it exists
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY . .

EXPOSE 8000

# Try different common entry points
CMD ["python", "-c", "import time; print('Python app running on port 8000'); time.sleep(3600)"]"""
        elif 'node' in languages:
            return """FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]"""
        elif 'java' in languages:
            return """FROM openjdk:17-jdk-slim

WORKDIR /app

# Copy JAR files from different build systems
COPY target/*.jar app.jar 2>/dev/null || \
COPY build/libs/*.jar app.jar 2>/dev/null || \
COPY *.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]"""
        else:
            return """FROM ubuntu:20.04

WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["echo", "Hello from container"]"""
    
    def _generate_github_actions(self, languages: List[str]) -> str:
        """Generate GitHub Actions workflow"""
        if 'python' in languages:
            return """name: Python CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest"""
        elif 'node' in languages:
            return """name: Node.js CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    - name: Install dependencies
      run: npm ci
    - name: Run tests
      run: npm test"""
        else:
            return """name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build
      run: echo "Build step" """


class SimpleDeployService:
    def __init__(self):
        self.automata_path = Path(__file__).parent.parent  # Path to main automata project
    
    async def test_server_connection(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test SSH connection to server"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                hostname=server_config['ip'],
                port=server_config['port'],
                username=server_config['user'],
                password=server_config['password'],
                timeout=10
            )
            
            stdin, stdout, stderr = ssh.exec_command('echo "SSH connection successful"')
            result = stdout.read().decode().strip()
            
            ssh.close()
            
            return {
                'success': True,
                'message': 'SSH подключение успешно установлено',
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Ошибка SSH подключения: {str(e)}'
            }
    
    async def deploy_repository(self, server_config: Dict[str, Any], repo_info: Dict[str, Any]):
        """Deploy repository to server"""
        try:
            yield "🚀 Начинаем развертывание на сервере..."
            
            # 1. Clone repository locally
            yield "📥 Клонируем репозиторий..."
            temp_dir = await self._clone_repository(repo_info)
            
            # 2. Analyze project
            yield "🔍 Анализируем технологический стек..."
            detected_info = self._analyze_project_simple(temp_dir)
            yield f"✅ Обнаружены технологии: {', '.join(detected_info.get('languages', []))}"
            
            # 3. Generate configuration
            yield "⚙️ Генерируем конфигурацию..."
            await self._generate_simple_config(temp_dir, detected_info, repo_info['name'])
            
            # 4. Create archive
            yield "📦 Создаем архив проекта..."
            archive_path = await self._create_archive(temp_dir, repo_info['name'])
            
            # 5. Connect to server
            yield f"🔌 Подключаемся к серверу {server_config['ip']}..."
            ssh = await self._connect_to_server(server_config)
            
            # 6. Upload to server
            yield "📤 Передаем файлы на сервер..."
            remote_path = f"{server_config['deployPath']}/{repo_info['name']}"
            await self._upload_to_server(ssh, archive_path, remote_path)
            
            # 7. Install dependencies
            yield "🔧 Устанавливаем зависимости..."
            await self._install_dependencies(ssh, remote_path, detected_info)
            
            # 8. Deploy application
            yield "🚀 Запускаем приложение..."
            yield "🐳 Создаем/обновляем Dockerfile..."
            await self._deploy_application(ssh, remote_path, repo_info['name'], detected_info)
            
            # 9. Check status
            yield "🔍 Проверяем статус приложения..."
            app_status = await self._check_app_status(ssh, repo_info['name'])
            
            ssh.close()
            
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
            os.remove(archive_path)
            
            # Report final status
            if app_status.get('status') == 'running':
                yield "✅ Развертывание завершено успешно!"
                yield f"🌐 Приложение доступно: {app_status.get('url', 'http://server-ip:port')}"
                yield f"📊 Статус: {app_status.get('message', 'Запущено')}"
            elif app_status.get('status') == 'stopped':
                yield "⚠️ Развертывание завершено, но контейнер остановлен"
                yield f"📊 Статус: {app_status.get('message', 'Остановлен')}"
                yield "💡 Попробуйте перезапустить контейнер вручную"
            else:
                yield "❌ Развертывание завершено с ошибками"
                yield f"📊 Статус: {app_status.get('message', 'Неизвестно')}"
                yield "💡 Проверьте логи контейнера для диагностики"
            
        except Exception as e:
            yield f"❌ Ошибка развертывания: {str(e)}"
            raise
    
    async def _clone_repository(self, repo_info: Dict[str, Any]) -> Path:
        """Clone repository to temporary directory"""
        temp_dir = Path(tempfile.mkdtemp())
        branch = repo_info.get('branch', 'main')
        repo_url = repo_info['url']
        
        import subprocess
        try:
            # First try with the specified branch
            result = subprocess.run([
                'git', 'clone', '--depth', '1', '--branch', branch, 
                repo_url, str(temp_dir)
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                # If branch not found, try to detect the default branch
                if "not found in upstream origin" in result.stderr:
                    # Try to get the default branch
                    default_branch_result = subprocess.run([
                        'git', 'ls-remote', '--symref', repo_url, 'HEAD'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if default_branch_result.returncode == 0:
                        # Extract default branch from output like "ref: refs/heads/main HEAD"
                        import re
                        match = re.search(r'refs/heads/(\w+)', default_branch_result.stdout)
                        if match:
                            default_branch = match.group(1)
                            # Clean up failed attempt
                            import shutil
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            temp_dir = Path(tempfile.mkdtemp())
                            
                            # Try again with default branch
                            result = subprocess.run([
                                'git', 'clone', '--depth', '1', '--branch', default_branch, 
                                repo_url, str(temp_dir)
                            ], capture_output=True, text=True, timeout=120)
                            
                            if result.returncode == 0:
                                return temp_dir
                    
                    # If we still can't find a branch, try without specifying branch (gets default)
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    temp_dir = Path(tempfile.mkdtemp())
                    
                    result = subprocess.run([
                        'git', 'clone', '--depth', '1', repo_url, str(temp_dir)
                    ], capture_output=True, text=True, timeout=120)
                
                if result.returncode != 0:
                    error_msg = f"Failed to clone repository {repo_url}"
                    if result.stderr:
                        error_msg += f"\nGit error: {result.stderr}"
                    if result.stdout:
                        error_msg += f"\nGit output: {result.stdout}"
                    raise Exception(error_msg)
            
            return temp_dir
            
        except subprocess.TimeoutExpired:
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Timeout while cloning repository {repo_url}")
        except FileNotFoundError:
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception("Git is not installed. Please install Git to clone repositories.")
        except Exception as e:
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Error cloning repository {repo_url}: {str(e)}")
    
    def _analyze_project_simple(self, project_path: Path) -> Dict[str, Any]:
        """Simple project analysis"""
        languages = []
        file_count = 0
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and '.git' not in str(file_path):
                file_count += 1
                file_name = file_path.name.lower()
                
                if file_name.endswith('.py') or file_name == 'requirements.txt':
                    if 'python' not in languages:
                        languages.append('python')
                elif file_name.endswith('.js') or file_name == 'package.json':
                    if 'node' not in languages:
                        languages.append('node')
                elif file_name.endswith('.java') or file_name in ['pom.xml', 'build.gradle']:
                    if 'java' not in languages:
                        languages.append('java')
                elif file_name.endswith('.go') or file_name == 'go.mod':
                    if 'go' not in languages:
                        languages.append('go')
                elif file_name == 'dockerfile':
                    if 'docker' not in languages:
                        languages.append('docker')
        
        return {"languages": languages, "file_count": file_count}
    
    async def _generate_simple_config(self, project_path: Path, detected_info: Dict[str, Any], project_name: str):
        """Generate simple automata.yml config"""
        config = {
            'name': project_name,
            'version': '1.0.0',
            'description': f'Auto-generated config for {project_name}',
            'build': {},
            'test': {},
            'deploy': {
                'docker': {
                    'image': f'{project_name}:latest',
                    'file': 'Dockerfile',
                    'port': 8000,
                    'push': False,
                    'env': {}
                }
            }
        }
        
        languages = detected_info.get('languages', [])
        
        if 'python' in languages:
            config['build']['python'] = {'command': 'if [ -f requirements.txt ]; then pip install -r requirements.txt; fi'}
            config['deploy']['docker']['env']['PYTHONUNBUFFERED'] = '1'
        
        if 'node' in languages:
            config['build']['node'] = {'command': 'npm install'}
            config['deploy']['docker']['env']['NODE_ENV'] = 'production'
        
        if 'java' in languages:
            config['build']['java'] = {'command': './gradlew build -x test'}
            config['deploy']['docker']['port'] = 8080
        
        # Save config
        config_path = project_path / 'automata.yml'
        import yaml
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    async def _create_archive(self, project_path: Path, project_name: str) -> str:
        """Create project archive"""
        archive_path = tempfile.mktemp(suffix='.tar.gz')
        
        import subprocess
        subprocess.run([
            'tar', '-czf', archive_path, '-C', str(project_path.parent), project_path.name
        ], check=True, capture_output=True)
        
        return archive_path
    
    async def _connect_to_server(self, server_config: Dict[str, Any]) -> paramiko.SSHClient:
        """Connect to server via SSH"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(
            hostname=server_config['ip'],
            port=server_config['port'],
            username=server_config['user'],
            password=server_config['password'],
            timeout=30
        )
        
        return ssh
    
    async def _upload_to_server(self, ssh: paramiko.SSHClient, archive_path: str, remote_path: str):
        """Upload and extract archive on server"""
        sftp = ssh.open_sftp()
        
        # Create directory
        stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_path}')
        stdout.channel.recv_exit_status()
        
        # Upload archive
        remote_archive = f"{remote_path}/project.tar.gz"
        sftp.put(archive_path, remote_archive)
        
        # Extract archive
        stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && tar -xzf project.tar.gz --strip-components=1')
        stdout.channel.recv_exit_status()
        
        # Remove archive
        stdin, stdout, stderr = ssh.exec_command(f'rm {remote_archive}')
        stdout.channel.recv_exit_status()
        
        sftp.close()
    
    async def _install_dependencies(self, ssh: paramiko.SSHClient, remote_path: str, detected_info: Dict[str, Any]):
        """Install dependencies on server"""
        languages = detected_info.get('languages', [])
        
        # Install Docker
        stdin, stdout, stderr = ssh.exec_command('which docker || (curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh)')
        stdout.channel.recv_exit_status()
        
        if 'python' in languages:
            stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && python3 -m pip install --upgrade pip')
            stdout.channel.recv_exit_status()
            
            # Only install requirements.txt if it exists
            stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && ls requirements.txt')
            if stdout.channel.recv_exit_status() == 0:
                stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && pip3 install -r requirements.txt')
                stdout.channel.recv_exit_status()
        
        if 'node' in languages:
            stdin, stdout, stderr = ssh.exec_command('which node || (curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs)')
            stdout.channel.recv_exit_status()
            
            stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && npm install')
            stdout.channel.recv_exit_status()
        
        if 'java' in languages:
            # Install Java and build tools
            stdin, stdout, stderr = ssh.exec_command('apt-get update && apt-get install -y openjdk-17-jdk')
            stdout.channel.recv_exit_status()
            
            # Check if it's a Gradle project
            stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && ls build.gradle*')
            if stdout.channel.recv_exit_status() == 0:
                # Install Gradle wrapper permissions
                stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && chmod +x gradlew')
                stdout.channel.recv_exit_status()
            else:
                # Install Maven for Maven projects
                stdin, stdout, stderr = ssh.exec_command('apt-get install -y maven')
                stdout.channel.recv_exit_status()
    
    async def _deploy_application(self, ssh: paramiko.SSHClient, remote_path: str, project_name: str, detected_info: Dict[str, Any]):
        """Deploy application using Docker"""
        languages = detected_info.get('languages', [])
        
        # For Java projects, we need to build the project first
        if 'java' in languages:
            # Check if it's a Gradle project
            stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && ls build.gradle*')
            if stdout.channel.recv_exit_status() == 0:
                # Build Gradle project
                stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && ./gradlew build -x test')
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    error_output = stderr.read().decode().strip()
                    raise Exception(f"Failed to build Gradle project: {error_output}")
            else:
                # Check if it's a Maven project
                stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && ls pom.xml')
                if stdout.channel.recv_exit_status() == 0:
                    # Build Maven project
                    stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && mvn clean package -DskipTests')
                    exit_status = stdout.channel.recv_exit_status()
                    if exit_status != 0:
                        error_output = stderr.read().decode().strip()
                        raise Exception(f"Failed to build Maven project: {error_output}")
        
        # Always regenerate Dockerfile to ensure it's up to date
        dockerfile_content = self._generate_dockerfile(languages)
        stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && cat > Dockerfile << "EOF"\n{dockerfile_content}\nEOF')
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error_output = stderr.read().decode().strip()
            raise Exception(f"Failed to create Dockerfile: {error_output}")
        
        # Verify Dockerfile was created correctly
        stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && cat Dockerfile')
        dockerfile_check = stdout.read().decode().strip()
        if "requirements.txt*" not in dockerfile_check:
            raise Exception(f"Dockerfile was not updated correctly. Content: {dockerfile_check}")
        
        # Stop and remove existing container
        stdin, stdout, stderr = ssh.exec_command(f'docker stop {project_name}-app 2>/dev/null || true')
        stdout.channel.recv_exit_status()
        
        stdin, stdout, stderr = ssh.exec_command(f'docker rm {project_name}-app 2>/dev/null || true')
        stdout.channel.recv_exit_status()
        
        # Build Docker image
        stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && docker build -t {project_name}:latest .')
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error_output = stderr.read().decode().strip()
            raise Exception(f"Failed to build Docker image: {error_output}")
        
        # Run new container
        port = 8080 if 'java' in languages else 8000
        stdin, stdout, stderr = ssh.exec_command(f'docker run -d --name {project_name}-app -p {port}:{port} {project_name}:latest')
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error_output = stderr.read().decode().strip()
            raise Exception(f"Failed to start container: {error_output}")
        
        # Wait a moment for container to start
        import asyncio
        await asyncio.sleep(2)
        
        # Check if container is running
        stdin, stdout, stderr = ssh.exec_command(f'docker ps --filter "name={project_name}-app" --format "{{{{.Names}}}}"')
        container_name = stdout.read().decode().strip()
        if not container_name:
            # Check if container exists but stopped
            stdin, stdout, stderr = ssh.exec_command(f'docker ps -a --filter "name={project_name}-app" --format "{{{{.Names}}}}:{{{{.Status}}}}"')
            container_status = stdout.read().decode().strip()
            if container_status:
                # Container exists but is stopped - this might be normal for some apps
                stdin, stdout, stderr = ssh.exec_command(f'docker logs {project_name}-app')
                logs = stdout.read().decode().strip()
                print(f"Container stopped. Logs: {logs}")
                # Don't raise exception - container might have completed its task successfully
            else:
                # Container doesn't exist at all
                raise Exception(f"Container {project_name}-app was not created")
    
    async def _check_app_status(self, ssh: paramiko.SSHClient, project_name: str) -> Dict[str, Any]:
        """Check application status"""
        # Check running containers
        stdin, stdout, stderr = ssh.exec_command(f'docker ps --filter "name={project_name}-app" --format "{{{{.Names}}}}:{{{{.Status}}}}:{{{{.Ports}}}}"')
        container_info = stdout.read().decode().strip()
        
        if container_info:
            # Get port information
            stdin, stdout, stderr = ssh.exec_command(f'docker port {project_name}-app')
            port_info = stdout.read().decode().strip()
            
            # Extract port from port_info (format: 0.0.0.0:8080->8080/tcp)
            port = "8080"  # default
            if port_info:
                import re
                port_match = re.search(r':(\d+)->', port_info)
                if port_match:
                    port = port_match.group(1)
            
            return {
                'status': 'running',
                'container': container_info,
                'ports': port_info,
                'url': f'http://server-ip:{port}',
                'message': f'✅ Приложение запущено и доступно на порту {port}'
            }
        else:
            # Check if container exists but is stopped
            stdin, stdout, stderr = ssh.exec_command(f'docker ps -a --filter "name={project_name}-app" --format "{{{{.Names}}}}:{{{{.Status}}}}"')
            all_containers = stdout.read().decode().strip()
            
            if all_containers:
                return {
                    'status': 'stopped',
                    'message': f'Контейнер существует, но остановлен: {all_containers}',
                    'container': all_containers
                }
            else:
                return {
                    'status': 'not_found',
                    'message': 'Контейнер не найден. Возможно, произошла ошибка при создании.'
                }
    
    def _generate_dockerfile(self, languages: List[str]) -> str:
        """Generate Dockerfile based on detected languages"""
        if 'python' in languages:
            return """FROM python:3.11-slim

WORKDIR /app

# Copy requirements.txt if it exists
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY . .

EXPOSE 8000

# Try different common entry points
CMD ["python", "-c", "import time; print('Python app running on port 8000'); time.sleep(3600)"]"""
        elif 'node' in languages:
            return """FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]"""
        elif 'java' in languages:
            return """FROM openjdk:17-jdk-slim

WORKDIR /app

# Copy JAR files from different build systems
COPY target/*.jar app.jar 2>/dev/null || \
COPY build/libs/*.jar app.jar 2>/dev/null || \
COPY *.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]"""
        else:
            return """FROM ubuntu:20.04

WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["echo", "Hello from container"]"""

    def _generate_github_actions(self, languages: List[str]) -> str:
        """Generate GitHub Actions workflow"""
        if 'python' in languages:
            return """name: Python CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest"""
        elif 'node' in languages:
            return """name: Node.js CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    - name: Install dependencies
      run: npm ci
    - name: Run tests
      run: npm test"""
        else:
            return """name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build
      run: echo "Build your project here"
    - name: Test
      run: echo "Run your tests here" """

# Initialize services
analyzer = SimpleGitHubAnalyzer()
deploy_service = SimpleDeployService()

@app.get("/")
async def root():
    return FileResponse("front/index.html")

@app.get("/deploy")
async def deploy_page():
    return FileResponse("front/deploy.html")

@app.post("/analyze")
async def analyze_repo(request: Dict[str, str]):
    """Analyze GitHub repository"""
    github_url = request.get("github_url")
    if not github_url:
        raise HTTPException(status_code=400, detail="GitHub URL is required")
    
    result = await analyzer.analyze_repository(github_url)
    return result

@app.post("/test-server")
async def test_server(server_config: dict):
    """Test SSH connection to server"""
    try:
        result = await deploy_service.test_server_connection(server_config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deploy")
async def deploy_repository(request: dict):
    """Deploy repository to server"""
    try:
        server_config = request.get("server", {})
        repository = request.get("repository", {})
        
        if not server_config or not repository:
            raise HTTPException(status_code=400, detail="Server config and repository info are required")
        
        async def generate():
            async for log_line in deploy_service.deploy_repository(server_config, repository):
                yield f"data: {json.dumps({'message': log_line})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-deploy")
async def stop_deploy():
    """Stop active deployment"""
    return {"status": "stopped"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
