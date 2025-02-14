# AiTools

AI工具集应用系统 - 一个集成了多种AI功能的FastAPI和Gradio应用

## 项目概述

AiTools 是一个强大的AI工具集，集成了文本处理、图像处理和音频处理等多种AI功能。本项目使用FastAPI作为后端框架，Gradio提供交互式界面，采用伪三层架构设计，旨在提供一个灵活、可扩展的AI应用开发平台。

### 主要功能

- 文本处理：
    - 对话语音识别：将语音转换为文本，支持AI音频处理。
    - PDF内容提取：从PDF文档中提取和处理文本内容，适用于NLP任务。
    - 文本生成语音：将文本转换为自然语音输出，使用ChatTTS技术。

- 图像处理：
    - 黑白转彩色：将黑白图像转换为彩色图像。
    - 文字生成图片：基于文本描述生成相应的图像。
    - 图片描述生成：分析图片内容，生成文字描述或标题。

- 音频/视频处理：
    - 文字生成视频：将文本内容转换为视频形式。
    - 对话音频生成：基于文本生成对话形式的音频。

- 多模态处理：
    - 多个功能涉及多模态技术，如文字转图像、图像转文字描述等，体现了系统处理不同类型数据的能力。

- AI应用集成：
    - 系统集成了多种AI应用场景，包括AI音频、AI办公、AI图像和AI视频等领域。

- 高级技术应用：
    - 使用了如Qwen-VL-Chat-Finetuned-De等先进的AI模型，以提供高质量的图像生成和处理功能。

## 本地开发环境要求

* Python 3.10+
* FastAPI 0.112.1+

## 安装与使用

1. 克隆仓库:
   ```
   git clone http://gitlab.gwm.cn/rddg/ai/ai-tool.git
   ```

2. 进入项目目录:
   ```
   cd ai-tool
   ```

3. 首次设置项目：
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

4. 配置环境变量：
    - 复制 `.env.example` 到 `.env`
    - 根据您的需求编辑 `.env` 文件

5. 启动集成服务器：
   ```bash
   ./scripts/deploy.sh
   ```

6. 访问应用：
    - API文档：http://localhost:8099/docs

## 项目结构

本项目采用伪三层架构，目录结构如下：

```
aitools/
│
├── app/                      # 主应用目录
│   ├── api/                  # API 相关代码
│   │   ├── v1/               # API 版本 1
│   │   │   ├── endpoints/    # API 端点
│   │   │   │   ├── __init__.py
│   │   │   │   ├── text_processing.py    # 文本处理 API
│   │   │   │   ├── image_processing.py   # 图像处理 API
│   │   │   │   └── audio_processing.py   # 音频处理 API
│   │   │   └── router.py     # API v1 子路由
│   │   └── __init__.py
│   ├── core/                 # 核心配置和功能
│   │   ├── __init__.py
│   │   ├── conf.py           # 主配置文件
│   │   ├── path_conf.py      # 路径配置
│   │   ├── registrar.py      # 路由注册器
│   │   └── router.py         # 总路由
│   ├── schemas/              # Pydantic 模型（用于数据验证）
│   │   ├── __init__.py
│   │   ├── text_schema.py
│   │   ├── image_schema.py
│   │   └── audio_schemas.py
│   ├── services/             # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── text_service/
│   │   ├── image_service/
│   │   └── audio_service/
│   │       └── speech_recognition.py
│   ├── crud/                 # 数据库操作层
│   │   ├── __init__.py
│   │   ├── text_crud.py
│   │   ├── image_crud.py
│   │   └── audio_crud.py
│   ├── models/               # 数据库模型
│   │   ├── __init__.py
│   │   └── base_models.py
│   ├── db/                   # 数据库连接和会话
│   │   ├── __init__.py
│   │   └── database.py
│   ├── utils/                # 通用工具函数
│   │   ├── __init__.py
│   │   ├── audio_utils.py
│   │   ├── exception.py        # 异常处理
│   │   ├── file_decrypt.py
│   │   ├── file_validators.py  # 文件验证工具
│   │   ├── log.py
│   │   ├── response.py         # 全局响应对象
│   │   ├── schema.py 
│   │   ├── serializers.py     # 序列化工具
│   │   ├── text_formatting.py # 文本格式化工具
│   │   └── timezone.py         # 时间工具
│   ├── middleware/           # 中间件目录
│   │   ├── __init__.py
│   │   └── access_middleware.py # 记录访问日志的中间件
│   └── main.py               # 应用入口点
│
├── ai_models/                # AI 模型文件
│   ├── __init__.py
│   ├── text_models/          # 文本处理模型
│   │   └── README.md         # 模型使用说明
│   ├── image_models/         # 图像处理模型
│   │   └── README.md
│   └── audio_models/         # 音频处理模型
│       └── README.md
│
├── media/                    # 媒体文件存储目录
│   ├── uploads/              # 用户上传的原始文件
│   │   ├── audio/
│   │   └── video/
│   └── processed/            # 处理后的文件
│       ├── audio/
│       └── video/
│
├── tests/                    # 测试目录
│   ├── __init__.py
│   ├── api/                  # API 测试
│   │   └── test_endpoints.py
│   ├── services/             # 服务层测试
│   │   ├── test_text_service.py
│   │   ├── test_image_service.py
│   │   └── test_audio_service.py
│   └── crud/                 # CRUD 操作测试
│       ├── test_text_crud.py
│       ├── test_image_crud.py
│       └── test_audio_crud.py
│
├── scripts/                  # 脚本文件
│   ├── setup.sh              # 环境设置脚本
│   └── start_server.sh       # 启动服务器脚本
│
├── deployment/               # 部署相关配置
│   └── gunicorn.conf.py
│
├── logs/                     # 日志文件目录
│   ├── access.log            # 访问日志
│   └── error.log             # 错误日志
│
├── local_packages/           # 本地包目录
│   └── README.md             # 本地包使用说明
│
├── static/                   # 静态文件目录
│   ├── css/                  # CSS 文件
│   ├── js/                   # JavaScript 文件
│   └── images/               # 图片文件
│
├── templates/                # HTML 模板目录
│
├── .env.example              # 环境变量示例文件
├── .env                      # 实际环境变量文件（不提交到版本控制）
├── .gitignore                # Git 忽略文件
├── requirements.txt          # 项目依赖列表
└── README.md                 # 项目说明文档
```

### 架构说明

| 工作流程 | Java           | AiTools |
|------|----------------|---------|
| 视图   | Controller     | api     |
| 数据传输 | DTO            | schemas |
| 业务逻辑 | Service + Impl | service |
| 数据访问 | DAO / Mapper   | crud    |
| 模型   | Model / Entity | model   |

## AI 模型文件

本项目使用的AI模型文件不包含在Git仓库中。请按照以下步骤获取必要的模型文件：

1. 克隆项目后，导航到 `ai_models` 目录。
2. 在每个子目录（text_models, image_models, audio_models）中，您会找到一个 README.md 文件。
3. 按照每个 README.md 文件中的指示下载和放置相应的模型文件。

注意：确保您有权限访问和使用这些模型文件。如果您在获取模型文件时遇到任何问题，请联系项目管理员。

## 开发指南

### 添加新功能

1. 在相应的目录（api, schemas, services, crud, models）中创建新文件。
2. 更新 `app/api/v1/router.py` 以包含新的API端点。

### 环境安装
通过命令行参数来指定是否为开发版本。接受一个新的命令行参数 `-d` 来指示开发版本。

使用方法：

- 对于开发模式：`./setup.sh -d`
- 对于生产模式：`./setup.sh`
- 如需将当前项目的 `local_packages` 复制到 `/gwm-tmp/local_package` 可以添加 `-c` 选项
- 如果需要强制重新创建虚拟环境，可以添加 `-f` 选项：`./setup.sh -f` 或 `./setup.sh -d -f`

### gwm-tmp 下的目录说明
```
gwm-tmp
├── ai_models
│   ├── __init__.py
│   ├── text_models/          # 文本处理模型
│   │   └── README.md         # 模型使用说明
│   ├── image_models/         # 图像处理模型
│   │   └── README.md
│   └── audio_models/         # 音频处理模型
│       └── README.md
├── ai-tool                   # 线上运行服务
├── aitool                    # 开发版测试版
├── ai_tools                  # webui 开发版
├── aitools                   # 开发版测试版
├── experiments               # 实验性研究脚本项目
└── local_package             # 线上版本地依赖包
```

### 代码风格

- 遵循 PEP 8 编码规范
- 使用 Black 进行代码格式化
- 使用 isort 对导入进行排序

## 部署

1. 确保已正确设置所有环境变量。
2. 使用 `gunicorn` 和 `deployment/gunicorn.conf.py` 配置文件启动应用。
3. 考虑使用 Nginx 作为反向代理。

```bash
# 启动生产环境，使用默认配置
./deploy.sh -o

# 启动测试环境，使用自定义设备和环境类型
./deploy.sh -t --device1 cuda:1 --device2 cuda:2 --env-type test

# 启动开发环境，使用生产环境类型
./deploy.sh -d --env-type pro

# 启动线上
DEVICE1=cuda:0 DEVICE2=cuda:1 DEVICE3=cuda:3 ENVIRONMENT=pro gunicorn -b "0.0.0.0:8087" -c ./deployment/gunicorn_conf.py -D "app.main:app"
DEVICE1=cuda:2 DEVICE2=cuda:3 DEVICE3=cuda:3 ENVIRONMENT=pro gunicorn -b "0.0.0.0:8086" -c ./deployment/gunicorn_conf.py -D "app.main:app"
DEVICE1=cuda:4 DEVICE2=cuda:5 DEVICE3=cuda:3 ENVIRONMENT=pro gunicorn -b "0.0.0.0:8085" -c ./deployment/gunicorn_conf.py -D "app.main:app"

# 启动测试 
DEVICE1=cuda:3 DEVICE2=cuda:3 DEVICE3=cuda:3 ENVIRONMENT=test gunicorn -b "0.0.0.0:8098" -c ./deployment/gunicorn_conf.py -D "app.main:app"

# 关闭端口
fuser -k 8088/tcp
fuser -k 8087/tcp
fuser -k 8086/tcp
fuser -k 8085/tcp
fuser -k 8084/tcp
fuser -k 8098/tcp
```
## 故障排除

- 如果遇到依赖问题，请检查 `requirements.txt` 文件并重新运行 `pip install -r requirements.txt`。
- 对于数据库连接问题，请验证 `.env` 文件中的数据库配置。
- 日志文件位于 `logs/` 目录，可以查看以获取更多错误信息。

## 版本控制

我们使用 [SemVer](http://semver.org/)
进行版本控制。查看 [tags on this repository](https://gitlab.gwm.cn/rddg/ai/ai-tool/-/tags) 以获取所有可用版本。

## 作者

* **开发团队名称** - *初始工作* - [团队链接](https://gitlab.gwm.cn/rddg)

查看 [contributors](https://gitlab.gwm.cn/rddg/ai/ai-tool/-/project_members) 列表以了解谁参与了这个项目。

## 致谢

* 感谢所有为这个项目做出贡献的团队成员。
* 特别感谢 [FastAPI](https://fastapi.tiangolo.com/) 的支持。