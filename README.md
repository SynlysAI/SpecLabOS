# SpecLabOS

SpecLabOS 用于统一管理实验设备、工作流编排与任务运行。

## 本地运行

1. 创建并激活环境

```powershell
conda create -n SpecLabOS python=3.12 -y
conda activate SpecLabOS
```

2. 安装后端依赖

```powershell
cd E:\xx_project\SpecLabOS\backend
pip install -r requirements.txt
```

3. 启动后端服务

```powershell
cd E:\xx_project\SpecLabOS\backend
uvicorn main:app --reload
```

4. 安装并启动前端

```powershell
cd E:\xx_project\SpecLabOS\frontend
npm install
npm run dev
```

## 基础验证

后端测试：

```powershell
cd E:\xx_project\SpecLabOS\backend
pytest -v
```

前端构建：

```powershell
cd E:\xx_project\SpecLabOS\frontend
npm run build
```
