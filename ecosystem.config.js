module.exports = {
  apps: [
    {
      name: 'speclab-backend',
      cwd: './backend',
      script: '/home/fangyikai/miniconda3/envs/speclab/bin/uvicorn',
      args: 'main:app --host 0.0.0.0 --port 20081',
      interpreter: 'none',
      env: {
        PYTHONPATH: '.'
      }
    }
  ]
};
