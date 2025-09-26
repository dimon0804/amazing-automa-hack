import argparse
from pathlib import Path
from .pipeline import run_pipeline
from .generators.config_generator import auto_generate_config, generate_automata_yml


def main() -> None:
    parser = argparse.ArgumentParser(prog='automata', description='Automata CI/CD (Python)')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_run = sub.add_parser('run', help='Run pipeline: detect -> build -> test -> deploy')
    p_run.add_argument('--cwd', type=str, default='.', help='Project directory')
    p_run.add_argument('--config', type=str, default='automata.yml', help='Config path')
    p_run.add_argument('--stage', type=str, choices=['all', 'detect', 'build', 'test', 'deploy'], default='all')

    p_generate = sub.add_parser('generate', help='Generate automata.yml config')
    p_generate.add_argument('--cwd', type=str, default='.', help='Project directory')
    p_generate.add_argument('--force', action='store_true', help='Force overwrite existing config')

    args = parser.parse_args()

    if args.cmd == 'run':
        cwd = Path(args.cwd).resolve()
        config_path = (cwd / args.config).resolve()
        run_pipeline(cwd=cwd, config_path=config_path, stage=args.stage)
    
    elif args.cmd == 'generate':
        cwd = Path(args.cwd).resolve()
        from .detectors import detect_project
        detected = detect_project(cwd)
        auto_generate_config(cwd, detected, force=args.force)


if __name__ == '__main__':
    main()


