import { loadConfig } from './utils/config.js';
import { detectProject } from './detectors/index.js';
import { buildProject } from './adapters/builders/index.js';
import { testProject } from './adapters/builders/test.js';
import { deployProject } from './adapters/deployers/index.js';

export async function runPipeline({ cwd, configPath, stage = 'all' }) {
  const cfg = await loadConfig(configPath);
  const detected = await detectProject({ cwd, cfg });

  if (stage === 'detect') {
    console.log(JSON.stringify(detected, null, 2));
    return;
  }

  const buildResult = stage === 'detect' ? null : await buildProject({ cwd, cfg, detected, skip: stage !== 'all' && stage !== 'build' ? true : false });
  
  if (stage === 'build') return;

  await testProject({ cwd, cfg, detected, skip: stage !== 'all' && stage !== 'test' ? true : false });

  if (stage === 'test') return;

  await deployProject({ cwd, cfg, detected, skip: stage !== 'all' && stage !== 'deploy' ? true : false });
}


