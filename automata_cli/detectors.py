from pathlib import Path


def detect_project(cwd: Path) -> dict:
    files = [p for p in cwd.rglob('*') if p.is_file() and '.git' not in p.parts and 'node_modules' not in p.parts]
    names = [p.name.lower() for p in files]

    languages = []
    if 'package.json' in names:
        languages.append('node')
    if 'requirements.txt' in names or 'pyproject.toml' in names:
        languages.append('python')
    if 'pom.xml' in names or 'build.gradle' in names or 'build.gradle.kts' in names:
        languages.append('java')
    if 'go.mod' in names:
        languages.append('go')
    if 'cargo.toml' in names:
        languages.append('rust')
    if 'dockerfile' in names:
        languages.append('docker')

    return {
        'languages': languages,
        'file_count': len(files),
    }


