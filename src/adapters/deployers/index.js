import { execa } from 'execa';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

async function run(cmd, args, options = {}) {
  const subprocess = execa(cmd, args, { stdio: 'inherit', ...options });
  await subprocess;
}

async function deployDocker({ cwd, cfg }) {
  const docker = cfg?.deploy?.docker;
  if (!docker) return;
  const image = docker.image || 'app:auto';
  const file = docker.file || (existsSync(join(cwd, 'Dockerfile')) ? 'Dockerfile' : null);
  if (!file) return;
  await run('docker', ['build', '-f', file, '-t', image, '.'], { cwd });
  if (docker.push) await run('docker', ['push', image], { cwd });
}

async function deploySSH({ cwd, cfg }) {
  const ssh = cfg?.deploy?.ssh;
  if (!ssh) return;
  // Minimal rsync/ssh flow
  const host = ssh.host;
  const user = ssh.user || 'root';
  const path = ssh.path || '/opt/app';
  if (!host) return;
  // zip & ship
  await run('powershell', [
    '-NoProfile',
    '-Command',
    `Compress-Archive -Path * -DestinationPath automata.zip -Force`
  ], { cwd }).catch(() => {});
  await run('scp', ['-o', 'StrictHostKeyChecking=no', 'automata.zip', `${user}@${host}:${path}/`], { cwd }).catch(() => {});
  await run('ssh', [`${user}@${host}`, `cd ${path} && unzip -o automata.zip && ${ssh.restart || 'echo "deployed"'}`]).catch(() => {});
}

export async function deployProject({ cwd, cfg, detected, skip = false }) {
  if (skip) return { skipped: true };
  await deployDocker({ cwd, cfg });
  await deploySSH({ cwd, cfg });
  return { success: true };
}


