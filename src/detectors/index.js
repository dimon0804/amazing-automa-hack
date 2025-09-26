import fg from 'fast-glob';
import { existsSync } from 'node:fs';

export async function detectProject({ cwd, cfg }) {
  const files = await fg(['**/*'], { cwd, dot: true, onlyFiles: true, ignore: ['**/node_modules/**', '**/.git/**'] });
  const has = (name) => files.some(f => f.toLowerCase().endsWith(name.toLowerCase()));

  const languages = [];

  if (has('package.json')) languages.push('node');
  if (has('requirements.txt') || has('pyproject.toml')) languages.push('python');
  if (has('pom.xml') || has('build.gradle') || has('build.gradle.kts')) languages.push('java');
  if (has('go.mod')) languages.push('go');
  if (has('Cargo.toml')) languages.push('rust');
  if (has('Dockerfile')) languages.push('docker');

  return { languages, files };
}


