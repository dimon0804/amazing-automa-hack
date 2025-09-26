import fs from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { extname } from 'node:path';
import YAML from 'yaml';
import TOML from '@iarna/toml';

export async function loadConfig(configPath) {
  if (!existsSync(configPath)) return {};
  const content = await fs.readFile(configPath, 'utf8');
  const ext = extname(configPath).toLowerCase();
  if (ext === '.yml' || ext === '.yaml') return YAML.parse(content) || {};
  if (ext === '.toml') return TOML.parse(content) || {};
  if (ext === '.json') return JSON.parse(content || '{}');
  return {};
}


