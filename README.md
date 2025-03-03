# PicFast

## 项目概述

PicFast 是一款高效、快速的图片缓存服务，旨在为开发者和企业提供高性能的图片存储与缓存解决方案。通过优化图片加载速度、降低服务器负担和提升用户体验，PicFast
成为现代应用和网站不可或缺的工具。

### 主要功能

1. 高速缓存与加载
   PicFast 采用先进的缓存算法，确保图片数据能够快速加载，减少用户等待时间。
   支持多种缓存策略（如内存缓存、磁盘缓存），根据图片使用频率自动优化存储位置。
2. 智能压缩与优化

+ 自动对上传的图片进行无损压缩，减少文件大小而不影响视觉质量。
+ 支持多种图片格式（如 JPEG、PNG、WebP），并根据浏览器支持情况动态选择最优格式，进一步提升加载速度。

3. 分布式缓存架构

+ 基于分布式系统设计，支持大规模图片缓存和高并发访问。
+ 支持多节点部署，自动负载均衡，确保服务的高可用性和稳定性。

## 本地开发环境要求

* Python 3.10+
* FastAPI 0.112.1+

## 安装与使用

1. 克隆仓库:
   ```
   git clone https://github.com/tao-xiaoxin/PicFast.git
   ```

2. 进入项目目录:
   ```
   cd PicFast
   ```
3. 设置环境以及依赖:
   ```
   cp .env.example .env
   python -m venv venv 
   source ./venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. 启动项目:
   ```
   uvicorn main:app --reload --host 0.0.0.0 --port 8099
   ```
5. 访问应用：
    - API文档：http://localhost:8099/api/v1/docs

## 项目结构

```
PicFast/
├── apps/                 # 应用模块目录
├── core/                 # 核心配置和功能
├── deploy                # 部署相关配置
├── middleware/           # 中间件
├── utils/               # 工具函数
├── __pycache__/
├── .env                 # 环境变量配置
├── .env.example         # 环境变量示例
├── .gitignore          # Git忽略文件
├── LICENSE             # 开源协议
├── main.py             # 主程序入口
└── requirements.txt     # 依赖包列表
```

## 在Typora 中使用

+ 请参考[`Typora` 使用指南](docs/typora/README.md)

## 开发指南

### 添加新功能

1. 在apps 中创建对应的应用目录，创建对应的文件，如schemas, services, crud, models等文件。
2. 更新 `core/router.py` 以包含新的API端点。

### 代码风格

- 遵循 PEP 8 编码规范
- 使用 Black 进行代码格式化
- 使用 isort 对导入进行排序

## 部署

1. 确保已正确设置所有环境变量。
2. 使用 `gunicorn` 和 `deploy/gunicorn.conf.py` 配置文件启动应用，执行如下命令启动：

```
chmod +x start.sh
./start_app.sh 8099
```

3. 最后使用 Nginx 作为反向代理并配置域名。

## 版本控制

我们使用 [SemVer](http://semver.org/)
进行版本控制。查看 [tags on this repository](https://github.com/tao-xiaoxin/PicFast/-/tags) 以获取所有可用版本。

## 致谢

* 感谢所有为这个项目做出贡献的团队成员。
* 特别感谢 [FastAPI](https://fastapi.tiangolo.com/) 的支持。