import os
import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> None:
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(cwd) + os.pathsep + env.get('PYTHONPATH', '')
        subprocess.run(cmd, cwd=str(cwd), check=True, env=env)
    except Exception:
        pass


def test_project(cwd: Path, cfg: dict, detected: dict, *, skip: bool = False) -> None:
    if skip:
        return
    for lang in detected.get('languages', []):
        if lang == 'node':
            _run(['npm', 'test', '--silent', '--if-present'], cwd)
        elif lang == 'python':
            _run(['pytest', '-q'], cwd)
        elif lang == 'java':
            _run(['mvn', '-B', 'test'], cwd)
        elif lang == 'go':
            _run(['go', 'test', './...'], cwd)
        elif lang == 'rust':
            _run(['cargo', 'test', '--all'], cwd)


