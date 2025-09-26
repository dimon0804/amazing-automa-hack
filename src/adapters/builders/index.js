import { execa } from 'execa';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

async function run(cmd, args, options = {}) {
  const subprocess = execa(cmd, args, { stdio: 'inherit', ...options });
  await subprocess;
}

async function buildNode({ cwd }) {
  const hasPkgLock = existsSync(join(cwd, 'package-lock.json'));
  const hasPnpm = existsSync(join(cwd, 'pnpm-lock.yaml'));
  const hasYarn = existsSync(join(cwd, 'yarn.lock'));
  if (hasPnpm) await run('pnpm', ['install', '--frozen-lockfile'], { cwd }).catch(() => run('npm', ['ci'], { cwd }));
  else if (hasYarn) await run('yarn', ['install', '--frozen-lockfile'], { cwd }).catch(() => run('npm', ['ci'], { cwd }));
  else if (hasPkgLock) await run('npm', ['ci'], { cwd }).catch(() => run('npm', ['install'], { cwd }));
  else await run('npm', ['install'], { cwd }).catch(() => {});
  await run(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'build', '--if-present'], { cwd }).catch(() => {});
}

async function buildPython({ cwd }) {
  // Prefer uv/pip-tools/poetry if present
  const hasUv = existsSync(join(cwd, 'uv.lock'));
  const hasPoetry = existsSync(join(cwd, 'poetry.lock')) || existsSync(join(cwd, 'pyproject.toml'));
  if (hasUv) await run('uv', ['sync'], { cwd }).catch(() => {});
  else if (hasPoetry) await run('poetry', ['install', '--no-root'], { cwd }).catch(() => run('pip', ['install', '-r', 'requirements.txt'], { cwd }));
  else if (existsSync(join(cwd, 'requirements.txt'))) await run('pip', ['install', '-r', 'requirements.txt'], { cwd }).catch(() => {});
}

async function buildJava({ cwd }) {
  if (existsSync(join(cwd, 'mvnw'))) await run(process.platform === 'win32' ? 'mvnw.cmd' : './mvnw', ['-B', 'package', '-DskipTests'], { cwd }).catch(() => {});
  else if (existsSync(join(cwd, 'pom.xml'))) await run('mvn', ['-B', 'package', '-DskipTests'], { cwd }).catch(() => {});
  else if (existsSync(join(cwd, 'gradlew'))) await run(process.platform === 'win32' ? 'gradlew.bat' : './gradlew', ['build', '-x', 'test'], { cwd }).catch(() => {});
  else if (existsSync(join(cwd, 'build.gradle')) || existsSync(join(cwd, 'build.gradle.kts'))) await run('gradle', ['build', '-x', 'test'], { cwd }).catch(() => {});
}

async function buildGo({ cwd }) {
  await run('go', ['build', './...'], { cwd }).catch(() => {});
}

async function buildRust({ cwd }) {
  await run('cargo', ['build', '--release'], { cwd }).catch(() => {});
}

export async function buildProject({ cwd, cfg, detected, skip = false }) {
  if (skip) return { skipped: true };
  const languages = detected.languages || [];
  for (const lang of languages) {
    if (lang === 'node') await buildNode({ cwd });
    if (lang === 'python') await buildPython({ cwd });
    if (lang === 'java') await buildJava({ cwd });
    if (lang === 'go') await buildGo({ cwd });
    if (lang === 'rust') await buildRust({ cwd });
  }
  return { success: true };
}


