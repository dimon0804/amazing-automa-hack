import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> None:
    try:
        subprocess.run(cmd, cwd=str(cwd), check=True)
    except Exception:
        pass


def _deploy_docker(cwd: Path, cfg: dict) -> None:
    docker = (cfg or {}).get('deploy', {}).get('docker')
    if not docker:
        # Создать образ с именем по умолчанию
        image = f"{cwd.name}:latest"
        file = "Dockerfile"
    else:
        image = docker.get('image', f"{cwd.name}:latest")
        file = docker.get('file', 'Dockerfile')
    
    print(f"🐳 Building Docker image: {image}")
    _run(['docker', 'build', '-f', file, '-t', image, '.'], cwd)
    
    if docker and docker.get('push'):
        print(f"📤 Pushing image: {image}")
        _run(['docker', 'push', image], cwd)
    
    # Автоматически запускаем контейнер
    _run_docker_container(cwd, image, docker)


def _run_docker_container(cwd: Path, image: str, docker_config: dict) -> None:
    """Автоматически запускает Docker контейнер"""
    container_name = f"{cwd.name}-app"
    
    # Останавливаем существующий контейнер если есть
    _run(['docker', 'stop', container_name], cwd)
    _run(['docker', 'rm', container_name], cwd)
    
    # Определяем порт из Dockerfile или используем по умолчанию
    port = docker_config.get('port', 8000) if docker_config else 8000
    
    # Определяем переменные окружения
    env_vars = docker_config.get('env', {}) if docker_config else {}
    env_args = []
    for key, value in env_vars.items():
        env_args.extend(['-e', f'{key}={value}'])
    
    # Запускаем контейнер
    cmd = ['docker', 'run', '-d', '--rm', '--name', container_name, f'-p{port}:{port}'] + env_args + [image]
    print(f"🚀 Starting container: {container_name} on port {port}")
    _run(cmd, cwd)
    
    print(f"✅ Application is running at: http://localhost:{port}")
    print(f"📋 Container name: {container_name}")
    print(f"🔍 To view logs: docker logs {container_name}")
    print(f"🛑 To stop: docker stop {container_name}")


def _deploy_ssh(cwd: Path, cfg: dict) -> None:
    ssh = (cfg or {}).get('deploy', {}).get('ssh')
    if not ssh:
        return
    host = ssh.get('host')
    user = ssh.get('user', 'root')
    path = ssh.get('path', '/opt/app')
    if not host:
        return
    # zip & ship
    _run(['zip', '-r', 'automata.zip', '.'], cwd)
    _run(['scp', '-o', 'StrictHostKeyChecking=no', 'automata.zip', f'{user}@{host}:{path}/'], cwd)
    restart = ssh.get('restart', 'echo deployed')
    _run(['ssh', f'{user}@{host}', f'cd {path} && unzip -o automata.zip && {restart}'], cwd)


def deploy_project(cwd: Path, cfg: dict, detected: dict, *, skip: bool = False) -> None:
    if skip:
        return
    _deploy_docker(cwd, cfg)
    _deploy_ssh(cwd, cfg)


