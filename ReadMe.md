# 小红书帖子分析与内容生成工具

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.2.3-purple.svg)](https://getbootstrap.com/)

一个用于分析小红书帖子并生成优化内容的高效工具，支持AI辅助分析、热门帖子爬取和图片、视频内容智能分析功能。

## 📑 目录

- [功能概述](#功能概述)
- [系统架构](#系统架构)
- [核心功能](#核心功能)
  - [基础功能](#基础功能)
  - [AI增强功能](#ai增强功能)
  - [热门帖子分析](#热门帖子分析)
  - [媒体内容分析](#媒体内容分析)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [安装步骤](#安装步骤)
  - [配置指南](#配置指南)
- [部署指南](#部署指南)
  - [本地部署](#本地部署)
  - [PythonAnywhere部署](#pythonanywhere部署)
  - [Azure部署](#azure部署)
- [使用说明](#使用说明)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 功能概述

该工具提供了一套全面的小红书帖子分析和内容优化解决方案：

- **内容抓取**：自动提取小红书帖子中的文字、图片和视频内容
- **关键词分析**：智能提取内容核心关键词，支持AI深度分析
- **热门帖子分析**：爬取同类关键词下的热门帖子，了解行业趋势
- **图片内容分析**：AI识别图片场景、物品、风格和品质
- **视频内容分析**：提取视频关键帧，分析视频内容和物品
- **内容优化**：生成SEO友好的标题和正文，提升内容质量
- **改进建议**：提供专业的内容、图片和视频改进建议
- **Web界面**：直观易用的用户界面，支持一键分析

## 系统架构

系统采用模块化设计，包含以下核心组件：

- **输入模块**：接收小红书帖子URL，支持Web界面和命令行输入
- **抓取模块**：使用requests和BeautifulSoup提取帖子内容，处理反爬机制
- **分析模块**：提取关键词，支持规则分析和AI深度分析
- **媒体分析模块**：分析图片和视频内容，提取关键信息
- **热门帖子模块**：抓取同类热门内容，多策略保障成功率
- **生成模块**：基于规则或AI生成优化内容和建议
- **输出模块**：格式化结果并展示，支持导出功能

![系统架构图](https://via.placeholder.com/800x400?text=System+Architecture)

## 核心功能

### 基础功能

1. **帖子内容抓取**
   - 自动提取标题、正文、图片URL和视频URL
   - 支持手动输入（当自动抓取失败时）
   - 处理小红书反爬机制，提高成功率

2. **关键词分析**
   - 产品类别识别
   - 品牌和型号提取
   - 特性关键词识别

3. **内容优化生成**
   - 基于模板的标题优化
   - 保留原文核心信息的正文改写
   - 自动添加热门标签和互动引导

4. **内容改进建议**
   - 图片数量优化建议
   - 文字长度调整建议
   - 视频内容添加建议
   - 发布时间和互动策略建议

### AI增强功能

该项目支持通过AI服务增强分析和内容生成能力：

1. **DeepSeek API集成**（优先）
   - 更精确的关键词提取
   - 深度内容结构分析
   - 高质量内容生成

2. **OpenAI API集成**（备选）
   - GPT模型驱动的内容理解
   - 自然语言优化生成
   - 个性化建议生成

3. **多层级架构**
   - 优先使用DeepSeek API
   - 备选OpenAI API
   - 最后回退到规则分析（无需API密钥）

与基础版相比，AI增强版提供：
- 更精确的关键词提取和主题识别
- 深度内容分析（主题、类别、风格、受众、情感）
- 更自然流畅的内容生成
- 针对性更强的改进建议

### 热门帖子分析

系统支持爬取同类热门帖子，帮助了解行业趋势：

1. **多策略爬取**
   - 直接网页爬取（搜索结果页面）
   - API接口爬取（小红书搜索API）
   - 模拟数据生成（当爬取受限时）

2. **智能排序和分析**
   - 基于点赞数排序
   - 提取热门标题模式和关键词
   - 识别热门内容特点

3. **参考价值**
   - 了解热门内容标题风格
   - 分析热门话题和表达方式
   - 指导内容创作方向

### 媒体内容分析

系统支持对帖子中的图片和视频进行深入分析：

1. **图片智能分析**
   - 主体内容和场景识别
   - 物品和产品识别
   - 视觉风格和色调分析
   - 图片质量和吸引力评分
   - 图片关键词提取

2. **视频内容分析**
   - 关键帧提取和分析
   - 视频主题识别
   - 视频中的物品识别
   - 视频质量和吸引力评分
   - 视频关键词提取

3. **媒体优化建议**
   - 图片质量提升建议
   - 图片风格一致性建议
   - 视频内容优化建议
   - 图片组合和数量建议

4. **关键词拓展**
   - 从图片和视频中提取额外关键词
   - 丰富内容关键词库
   - 增强内容关联性

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- pip 包管理器
- 互联网连接（用于API访问和内容爬取）

### 安装步骤

1. 克隆仓库（或下载源码）：
   ```bash
   git clone https://github.com/your-username/xiaohongshu-analyzer.git
   cd xiaohongshu-analyzer
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 运行应用：
   - Windows: 双击 `run_demo.bat`
   - Linux/Mac: 执行 `bash run_demo.sh`
   - 或直接运行：`python app.py`

4. 访问Web界面：
   在浏览器中打开 http://localhost:8080

### 配置指南

#### 基础配置

默认情况下，无需额外配置即可使用基础功能。

#### AI服务配置

要启用AI增强功能，请设置以下环境变量：

1. **DeepSeek API**（推荐）：
   ```bash
   # Windows
   set DEEPSEEK_API_KEY=your_deepseek_api_key

   # Linux/MacOS
   export DEEPSEEK_API_KEY=your_deepseek_api_key
   ```

2. **OpenAI API**（备选）：
   ```bash
   # Windows
   set OPENAI_API_KEY=your_openai_api_key

   # Linux/MacOS
   export OPENAI_API_KEY=your_openai_api_key
   ```

#### 媒体分析配置

媒体分析功能依赖于以下库：

- **Pillow**：图像处理库
- **OpenCV**：视频处理库
- **PyTube**：视频下载库（用于分析YouTube视频）

以上依赖项已包含在`requirements.txt`中。如果你遇到"未找到模块"错误，请确保已成功安装这些依赖：

```bash
pip install Pillow opencv-python-headless pytube
```

## 部署指南

### 本地部署

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行应用：
   ```bash
   python app.py
   ```

3. 访问：http://localhost:8080

### PythonAnywhere部署

1. 创建PythonAnywhere账户并登录

2. 上传项目文件

3. 创建虚拟环境并安装依赖：
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 xiaohongshu-tool
   pip install -r requirements.txt
   ```

4. 配置Web应用：
   - 添加新的Web应用
   - 选择Flask框架
   - 设置WSGI文件指向app.py
   - 设置工作目录为项目所在目录
   - 设置虚拟环境路径

5. 重新加载应用

详细部署说明请查看 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)。

### Azure部署

请参考 [Azure部署指南](DEPLOYMENT_GUIDE.md) 了解如何将项目部署到Microsoft Azure云平台。

## 使用说明

1. 输入小红书帖子URL（格式：https://www.xiaohongshu.com/discovery/item/...)
2. 点击"分析"按钮
3. 系统将自动分析帖子内容并提供结果：
   - 关键词分析
   - AI深度分析（如果启用）
   - 图片和视频内容分析（如果有媒体内容）
   - 优化标题和正文
   - 内容改进建议
   - 同类热门帖子

![使用演示](https://via.placeholder.com/800x500?text=Usage+Demo)

## 项目结构

```
xiaohongshu-analyzer/
├── app.py                  # Flask应用入口
├── xiaohongshu_tool.py     # 基础功能核心模块
├── xiaohongshu_ai_tool.py  # AI增强功能模块
├── media_analyzer.py       # 图片和视频分析模块
├── templates/              # HTML模板
│   └── index.html          # Web界面
├── run_demo.bat            # Windows启动脚本
├── run_demo.sh             # Linux/Mac启动脚本
├── requirements.txt        # 项目依赖
├── web.config              # Azure部署配置
├── DEPLOYMENT_GUIDE.md     # 部署指南
└── README.md               # 项目说明
```

## 技术栈

- **后端**：
  - Python 3.10
  - Flask 2.3.3
  - Requests
  - BeautifulSoup4
  - OpenAI API / DeepSeek API
  - Pillow (图像处理)
  - OpenCV (视频处理)
  - PyTube (视频下载)

- **前端**：
  - HTML5 / CSS3
  - Bootstrap 5.2.3
  - JavaScript ES6

- **部署**：
  - PythonAnywhere
  - Microsoft Azure
  - Docker (可选)

## 常见问题

**Q: 为什么无法抓取某些小红书帖子？**
A: 小红书有反爬机制，如遇抓取失败，系统会提示手动输入内容。您也可以尝试更换IP或添加Cookie信息。

**Q: 图片和视频分析功能为什么无法工作？**
A: 确保已安装所需的依赖包(Pillow, OpenCV, PyTube)，同时需要配置有效的AI API密钥(DeepSeek或OpenAI)来启用完整的媒体分析功能。

**Q: 为什么视频分析比较慢？**
A: 视频分析需要下载视频文件、提取关键帧并分析多个图像，这个过程可能需要较长时间，特别是对于大型视频文件。

**Q: 如何判断是否使用了AI增强功能？**
A: 界面标题栏会显示"AI增强版"标志，并且分析结果中会包含AI深度分析部分。

**Q: 热门帖子数据是实时的吗？**
A: 系统会尝试实时爬取，但如遇到反爬限制，会使用模拟数据进行兜底。

**Q: 如何提高内容抓取的成功率？**
A: 尝试添加有效的Cookie信息，或减少短时间内的请求频率。

## 贡献指南

欢迎对项目进行贡献！请按以下步骤：

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件。

---

**免责声明**：本工具仅供学习研究使用，请勿用于商业目的或违反小红书平台规定。使用过程中请遵守相关法律法规和平台政策。
