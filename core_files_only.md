# 最小核心文件版本

如果遇到上传问题，可以先上传这些最小核心文件：

## 立即上传的文件（6个）

1. **config.py** (1.8KB) - 配置管理
2. **pyproject.toml** (242字节) - 项目依赖
3. **deploy_requirements.txt** (69字节) - 部署依赖
4. **fly.toml** (567字节) - Fly.io配置
5. **README.md** (2KB) - 项目说明
6. **.env.example** (199字节) - 环境变量示例

## 后续分批添加

**第二批:**
- bot.py (分块上传或用Git)
- database.py
- order_processor.py

**第三批:**
- Dockerfile
- .gitignore
- FLY_DEPLOYMENT_GUIDE.md

这样可以先建立基本的项目结构，然后逐步完善。