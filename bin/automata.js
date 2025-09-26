#!/usr/bin/env node
import { hideBin } from 'yargs/helpers';
import yargs from 'yargs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
import { runPipeline } from '../src/pipeline.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = resolve(__filename, '..');

async function main() {
  const argv = yargs(hideBin(process.argv))
    .scriptName('automata')
    .usage('Использование: $0 <cmd> [опции]')
    .command(
      'run',
      'Запустить универсальный пайплайн (detect -> build -> test -> deploy)',
      y =>
        y
          .option('cwd', {
            type: 'string',
            describe: 'Каталог проекта',
            default: process.cwd()
          })
          .option('config', {
            type: 'string',
            describe: 'Путь к automata.yml',
            default: 'automata.yml'
          })
          .option('stage', {
            type: 'string',
            choices: ['all', 'detect', 'build', 'test', 'deploy'],
            default: 'all'
          }),
      async args => {
        const cwd = resolve(String(args.cwd));
        const configPath = resolve(cwd, String(args.config));
        if (!existsSync(cwd)) {
          console.error(`Каталог не найден: ${cwd}`);
          process.exit(2);
        }
        await runPipeline({ cwd, configPath, stage: String(args.stage) });
      }
    )
    .demandCommand(1)
    .help()
    .strict()
    .parse();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});


