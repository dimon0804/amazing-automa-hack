import os
import asyncio
import subprocess
import tempfile
import shutil
import json
import re
from pathlib import Path
from typing import Dict, Any, AsyncGenerator
import paramiko
import threading
import time


class DeployService:
    def __init__(self, automata_path: Path):
        self.automata_path = automata_path
        self.active_deployments = {}
        
    async def test_server_connection(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Тестирует SSH подключение к серверу"""
        try:
            # Создаем SSH клиент
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Подключаемся к серверу
            ssh.connect(
                hostname=server_config['ip'],
                port=server_config['port'],
                username=server_config['user'],
                password=server_config['password'],
                timeout=10
            )
            
            # Тестируем команду
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
    
    async def deploy_repository(self, server_config: Dict[str, Any], repo_info: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Развертывает репозиторий на удаленном сервере"""
        deployment_id = f"{repo_info['name']}_{int(time.time())}"
        self.active_deployments[deployment_id] = {
            'status': 'running',
            'started_at': time.time()
        }
        
        try:
            yield f"🚀 Начинаем развертывание {repo_info['name']} на сервере {server_config['ip']}"
            
            # 1. Клонируем репозиторий локально для анализа
            yield "📥 Клонируем репозиторий для анализа..."
            temp_dir = await self._clone_repository(repo_info)
            
            # 2. Анализируем проект
            yield "🔍 Анализируем технологический стек..."
            detected_info = await self._analyze_project(temp_dir)
            yield f"✅ Обнаружены технологии: {', '.join(detected_info.get('languages', []))}"
            
            # 3. Генерируем конфигурацию
            yield "⚙️ Генерируем конфигурацию automata.yml..."
            await self._generate_config(temp_dir, detected_info, repo_info['name'])
            
            # 4. Создаем архив для передачи
            yield "📦 Создаем архив проекта..."
            archive_path = await self._create_archive(temp_dir, repo_info['name'])
            
            # 5. Подключаемся к серверу
            yield f"🔌 Подключаемся к серверу {server_config['ip']}..."
            ssh = await self._connect_to_server(server_config)
            
            # 6. Передаем файлы на сервер
            yield "📤 Передаем файлы на сервер..."
            remote_path = f"{server_config['deployPath']}/{repo_info['name']}"
            await self._upload_to_server(ssh, archive_path, remote_path)
            
            # 7. Устанавливаем зависимости на сервере
            yield "🔧 Устанавливаем зависимости на сервере..."
            await self._install_dependencies(ssh, remote_path, detected_info)
            
            # 8. Запускаем развертывание через Amazing Automata
            yield "🚀 Запускаем автоматическое развертывание..."
            await self._run_automata_deploy(ssh, remote_path, repo_info['name'])
            
            # 9. Проверяем статус приложения
            yield "🔍 Проверяем статус развернутого приложения..."
            app_status = await self._check_application_status(ssh, repo_info['name'])
            
            ssh.close()
            
            # Очистка
            shutil.rmtree(temp_dir, ignore_errors=True)
            os.remove(archive_path)
            
            yield "✅ Развертывание завершено успешно!"
            yield f"🌐 Приложение доступно по адресу: {app_status.get('url', 'http://server-ip:port')}"
            
            self.active_deployments[deployment_id]['status'] = 'completed'
            
        except Exception as e:
            yield f"❌ Ошибка развертывания: {str(e)}"
            self.active_deployments[deployment_id]['status'] = 'failed'
            raise
    
    async def _clone_repository(self, repo_info: Dict[str, Any]) -> Path:
        """Клонирует репозиторий во временную директорию"""
        temp_dir = Path(tempfile.mkdtemp())
        
        branch = repo_info.get('branch', 'main')
        clone_url = repo_info['url']
        
        try:
            result = subprocess.run([
                'git', 'clone', '--depth', '1', '--branch', branch, 
                clone_url, str(temp_dir)
            ], capture_output=True, text=True, check=True, timeout=60)
            
            return temp_dir
        except subprocess.CalledProcessError as e:
            raise Exception(f"Ошибка клонирования репозитория: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("Таймаут при клонировании репозитория")
    
    async def _analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Анализирует проект для определения технологий"""
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.automata_path) + os.pathsep + env.get('PYTHONPATH', '')
            
            result = subprocess.run([
                "python", "-m", "automata_cli.cli", "run", 
                "--cwd", str(project_path), "--stage", "detect"
            ], capture_output=True, text=True, check=True, env=env, cwd=self.automata_path)
            
            return json.loads(result.stdout)
        except Exception as e:
            raise Exception(f"Ошибка анализа проекта: {str(e)}")
    
    async def _generate_config(self, project_path: Path, detected_info: Dict[str, Any], project_name: str):
        """Генерирует automata.yml конфигурацию"""
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.automata_path) + os.pathsep + env.get('PYTHONPATH', '')
            
            subprocess.run([
                "python", "-m", "automata_cli.cli", "generate", 
                "--cwd", str(project_path), "--force"
            ], capture_output=True, text=True, check=True, env=env, cwd=self.automata_path)
            
        except Exception as e:
            raise Exception(f"Ошибка генерации конфигурации: {str(e)}")
    
    async def _create_archive(self, project_path: Path, project_name: str) -> str:
        """Создает архив проекта"""
        archive_path = tempfile.mktemp(suffix='.tar.gz')
        
        try:
            subprocess.run([
                'tar', '-czf', archive_path, '-C', str(project_path.parent), project_path.name
            ], check=True, capture_output=True)
            
            return archive_path
        except Exception as e:
            raise Exception(f"Ошибка создания архива: {str(e)}")
    
    async def _connect_to_server(self, server_config: Dict[str, Any]) -> paramiko.SSHClient:
        """Устанавливает SSH подключение к серверу"""
        try:
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
        except Exception as e:
            raise Exception(f"Ошибка подключения к серверу: {str(e)}")
    
    async def _upload_to_server(self, ssh: paramiko.SSHClient, archive_path: str, remote_path: str):
        """Загружает архив на сервер и распаковывает"""
        try:
            # Создаем SFTP соединение
            sftp = ssh.open_sftp()
            
            # Создаем директорию на сервере
            stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_path}')
            stdout.channel.recv_exit_status()
            
            # Загружаем архив
            remote_archive = f"{remote_path}/project.tar.gz"
            sftp.put(archive_path, remote_archive)
            
            # Распаковываем архив
            stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && tar -xzf project.tar.gz --strip-components=1')
            stdout.channel.recv_exit_status()
            
            # Удаляем архив
            stdin, stdout, stderr = ssh.exec_command(f'rm {remote_archive}')
            stdout.channel.recv_exit_status()
            
            sftp.close()
            
        except Exception as e:
            raise Exception(f"Ошибка загрузки файлов на сервер: {str(e)}")
    
    async def _install_dependencies(self, ssh: paramiko.SSHClient, remote_path: str, detected_info: Dict[str, Any]):
        """Устанавливает зависимости на сервере"""
        try:
            languages = detected_info.get('languages', [])
            
            # Устанавливаем Docker если его нет
            stdin, stdout, stderr = ssh.exec_command('which docker || (curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh)')
            stdout.channel.recv_exit_status()
            
            # Устанавливаем Python зависимости
            if 'python' in languages:
                stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && python3 -m pip install --upgrade pip')
                stdout.channel.recv_exit_status()
                
                stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && pip3 install -r requirements.txt')
                stdout.channel.recv_exit_status()
            
            # Устанавливаем Node.js зависимости
            if 'node' in languages:
                stdin, stdout, stderr = ssh.exec_command('which node || (curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs)')
                stdout.channel.recv_exit_status()
                
                stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && npm install')
                stdout.channel.recv_exit_status()
            
            # Устанавливаем Java зависимости
            if 'java' in languages:
                stdin, stdout, stderr = ssh.exec_command('which java || sudo apt-get update && sudo apt-get install -y openjdk-17-jdk')
                stdout.channel.recv_exit_status()
                
                stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && chmod +x gradlew && ./gradlew build -x test')
                stdout.channel.recv_exit_status()
                
        except Exception as e:
            raise Exception(f"Ошибка установки зависимостей: {str(e)}")
    
    async def _run_automata_deploy(self, ssh: paramiko.SSHClient, remote_path: str, project_name: str):
        """Запускает развертывание через Amazing Automata на сервере"""
        try:
            # Копируем automata_cli на сервер
            sftp = ssh.open_sftp()
            
            # Создаем директорию для automata_cli
            stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_path}/automata_cli')
            stdout.channel.recv_exit_status()
            
            # Копируем основные файлы automata_cli
            automata_files = [
                'automata_cli/__init__.py',
                'automata_cli/cli.py',
                'automata_cli/pipeline.py',
                'automata_cli/detectors.py',
                'automata_cli/utils/config.py',
                'automata_cli/generators/config_generator.py',
                'automata_cli/runners/builders.py',
                'automata_cli/runners/tests.py',
                'automata_cli/runners/deploy.py'
            ]
            
            for file_path in automata_files:
                if (self.automata_path / file_path).exists():
                    remote_file = f"{remote_path}/{file_path}"
                    sftp.put(str(self.automata_path / file_path), remote_file)
            
            sftp.close()
            
            # Запускаем развертывание
            stdin, stdout, stderr = ssh.exec_command(f'cd {remote_path} && PYTHONPATH={remote_path} python3 -m automata_cli.cli run --cwd . --stage all')
            
            # Читаем вывод
            while True:
                line = stdout.readline()
                if not line:
                    break
                # Здесь можно добавить логирование вывода
            
            stdout.channel.recv_exit_status()
            
        except Exception as e:
            raise Exception(f"Ошибка запуска развертывания: {str(e)}")
    
    async def _check_application_status(self, ssh: paramiko.SSHClient, project_name: str) -> Dict[str, Any]:
        """Проверяет статус развернутого приложения"""
        try:
            # Проверяем запущенные Docker контейнеры
            stdin, stdout, stderr = ssh.exec_command(f'docker ps --filter "name={project_name}-app" --format "{{{{.Names}}}}:{{{{.Status}}}}"')
            container_info = stdout.read().decode().strip()
            
            if container_info:
                # Извлекаем порт из Docker контейнера
                stdin, stdout, stderr = ssh.exec_command(f'docker port {project_name}-app')
                port_info = stdout.read().decode().strip()
                
                return {
                    'status': 'running',
                    'container': container_info,
                    'ports': port_info,
                    'url': f'http://server-ip:8000'  # Базовый URL
                }
            else:
                return {
                    'status': 'not_running',
                    'message': 'Контейнер не запущен'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def stop_deployment(self, deployment_id: str = None):
        """Останавливает активное развертывание"""
        if deployment_id and deployment_id in self.active_deployments:
            self.active_deployments[deployment_id]['status'] = 'stopped'
        else:
            # Останавливаем все активные развертывания
            for dep_id in self.active_deployments:
                if self.active_deployments[dep_id]['status'] == 'running':
                    self.active_deployments[dep_id]['status'] = 'stopped'
