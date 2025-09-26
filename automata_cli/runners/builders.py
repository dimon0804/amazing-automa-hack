import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> None:
    try:
        subprocess.run(cmd, cwd=str(cwd), check=True)
    except Exception:
        pass


def build_node(cwd: Path) -> None:
    _run(['npm', 'ci'], cwd)
    _run(['npm', 'install'], cwd)
    _run(['npm', 'run', 'build', '--if-present'], cwd)


def build_python(cwd: Path) -> None:
    if (cwd / 'requirements.txt').exists():
        _run(['pip', 'install', '-r', 'requirements.txt'], cwd)


def build_java(cwd: Path) -> None:
    if (cwd / 'pom.xml').exists():
        _run(['mvn', '-B', 'package', '-DskipTests'], cwd)
    else:
        _run(['gradle', 'build', '-x', 'test'], cwd)


def build_go(cwd: Path) -> None:
    _run(['go', 'build', './...'], cwd)


def build_rust(cwd: Path) -> None:
    _run(['cargo', 'build', '--release'], cwd)


def build_project(cwd: Path, cfg: dict, detected: dict, *, skip: bool = False) -> None:
    if skip:
        return
    for lang in detected.get('languages', []):
        if lang == 'node':
            build_node(cwd)
        elif lang == 'python':
            build_python(cwd)
        elif lang == 'java':
            build_java(cwd)
        elif lang == 'go':
            build_go(cwd)
        elif lang == 'rust':
            build_rust(cwd)


