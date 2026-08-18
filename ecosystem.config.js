/**
 * SpecLabOS PM2 启动配置。
 * cwd 改为基于 __dirname 的绝对路径，避免从其他目录启动时相对路径失效。
 */

// ── 实验室公共配置注入（读取共享密钥；文件缺失时返回空对象，本地开发不受影响）──
const COMMON_ENV = (() => {
  try {
    const out = {};
    for (const line of require("fs")
      .readFileSync("/home/fangyikai/lab-common.env", "utf-8")
      .split(/\r?\n/)) {
      if (line.trim().startsWith("#")) continue;
      const idx = line.indexOf("=");
      if (idx > 0) out[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
    }
    return out;
  } catch {
    return {};
  }
})();

module.exports = {
  apps: [
    {
      name: 'speclab-backend',
      cwd: __dirname + '/backend',
      script: '/polymer/conda/envs/SpecLabOS/bin/uvicorn',
      args: 'main:app --host 0.0.0.0 --port 8010',
      interpreter: 'none',
      env: {
        ...COMMON_ENV,
        PYTHONPATH: '.'
      }
    }
  ]
}
