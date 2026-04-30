# AGENTS.md

## 项目环境
- 本项目代码需 `conda activate SpecLabOS` 激活环境后运行

## 浏览器调试
- 需要通过浏览器查看页面结构、交互、控制台、网络请求时，优先使用 `playwright-cli`技能

- 需要显式打开可见浏览器窗口时，使用有头模式：
  ```powershell
  playwright-cli open http://127.0.0.1:5173 --headed
  ```