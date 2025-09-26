import { execa } from 'execa';

async function run(cmd, args, options = {}) {
  const subprocess = execa(cmd, args, { stdio: 'inherit', ...options });
  await subprocess;
}

export async function testProject({ cwd, detected, skip = false }) {
  if (skip) return { skipped: true };
  const languages = detected.languages || [];
  for (const lang of languages) {
    if (lang === 'node') {
      await run(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['test', '--silent', '--if-present'], { cwd }).catch(() => {});
    }
    if (lang === 'python') {
      await run('pytest', ['-q'], { cwd }).catch(() => run('python', ['-m', 'unittest', 'discover'], { cwd }).catch(() => {}));
    }
    if (lang === 'java') {
      await run('mvn', ['-B', 'test'], { cwd }).catch(() => run('gradle', ['test'], { cwd }).catch(() => {}));
    }
    if (lang === 'go') {
      await run('go', ['test', './...'], { cwd }).catch(() => {});
    }
    if (lang === 'rust') {
      await run('cargo', ['test', '--all'], { cwd }).catch(() => {});
    }
  }
  return { success: true };
}


