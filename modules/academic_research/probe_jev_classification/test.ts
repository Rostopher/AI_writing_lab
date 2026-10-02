/**
 * probe: 通过 Vercel AI Gateway 调用 TypeSafe Jev，测试三布尔问题的论文类型判断。
 *
 * 只调用 typesafe-ai/jev，不调用任何其他模型。
 *
 * API key 来源：项目根目录 .env 的 JEV_API_KEY（映射到 AI_GATEWAY_API_KEY）。
 */
import 'dotenv/config';
import { experimental_evaluate as evaluate } from 'ai';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import dotenv from 'dotenv';

// .env 在项目根目录（probe 目录上三层）
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..', '..', '..');
dotenv.config({ path: path.join(repoRoot, '.env') });

// Vercel AI Gateway SDK 读 AI_GATEWAY_API_KEY；本仓库用 JEV_API_KEY 命名
if (!process.env.AI_GATEWAY_API_KEY && process.env.JEV_API_KEY) {
  process.env.AI_GATEWAY_API_KEY = process.env.JEV_API_KEY;
}
if (!process.env.AI_GATEWAY_API_KEY) {
  throw new Error('缺少 AI_GATEWAY_API_KEY / JEV_API_KEY，请在 .env 配置');
}

const JEV_MODEL = 'typesafe-ai/jev';

async function main() {
  const state = `
    This economics paper uses administrative data and a policy reform.
    The authors estimate treatment effects using difference-in-differences.
    The paper does not construct or estimate a structural economic model.
    It does not develop a new formal theoretical model.
  `;

  const result = await evaluate({
    model: JEV_MODEL,
    state,
    questions: {
      empirical: {
        type: 'boolean',
        instructions:
          'Does this paper conduct substantive empirical analysis using data?',
      },
      structural: {
        type: 'boolean',
        instructions:
          'Does this paper estimate an explicit structural economic model using data?',
      },
      theory: {
        type: 'boolean',
        instructions:
          'Does this paper develop a substantive original formal theoretical model as a major contribution?',
      },
    },
  });

  console.log('=== Jev answers ===');
  console.dir(result.answers, { depth: null });
}

main().catch((err) => {
  console.error('调用失败：', err);
  process.exit(1);
});
