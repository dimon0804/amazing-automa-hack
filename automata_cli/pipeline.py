from pathlib import Path
from .utils.config import load_config
from .detectors import detect_project
from .runners.builders import build_project
from .runners.tests import test_project
from .runners.deploy import deploy_project
from .generators.config_generator import auto_generate_config


def run_pipeline(*, cwd: Path, config_path: Path, stage: str = 'all') -> None:
    # Сначала обнаруживаем языки
    detected = detect_project(cwd)
    
    # Автоматически генерируем конфиг если его нет
    if not config_path.exists():
        print("No config found, auto-generating...")
        auto_generate_config(cwd, detected, force=True)
        config_path = cwd / 'automata.yml'
    
    cfg = load_config(config_path)

    if stage == 'detect':
        import json
        print(json.dumps(detected, indent=2))
        return

    skip_build = stage not in ('all', 'build')
    skip_test = stage not in ('all', 'test')
    skip_deploy = stage not in ('all', 'deploy')

    build_project(cwd, cfg, detected, skip=skip_build)
    if stage == 'build':
        return

    test_project(cwd, cfg, detected, skip=skip_test)
    if stage == 'test':
        return

    deploy_project(cwd, cfg, detected, skip=skip_deploy)


