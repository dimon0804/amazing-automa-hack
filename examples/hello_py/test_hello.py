from hello import greet


def test_greet() -> None:
    assert greet("World") == "Hello, World!"
 

def test_cli_execution() -> None:
    import sys
    import subprocess
    from pathlib import Path

    project_dir = Path(__file__).parent
    result = subprocess.run(
        [sys.executable, "hello.py", "Alice"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "Hello, Alice!"
