# Azure部署指南

## 方法1：使用Azure CLI部署

1. **安装Azure CLI**
   - 从[官方网站](https://docs.microsoft.com/zh-cn/cli/azure/install-azure-cli)下载并安装Azure CLI

2. **登录Azure**
   ```bash
   az login
   ```

3. **创建资源组（如果没有）**
   ```bash
   az group create --name xiaohongshu-rg --location eastasia
   ```

4. **创建App Service计划**
   ```bash
   az appservice plan create --name xiaohongshu-plan --resource-group xiaohongshu-rg --sku B1 --is-linux
   ```

5. **创建Web应用**
   ```bash
   az webapp create --resource-group xiaohongshu-rg --plan xiaohongshu-plan --name xiaohongshu-analyzer --runtime "PYTHON|3.10"
   ```

6. **配置应用设置**
   ```bash
   az webapp config appsettings set --resource-group xiaohongshu-rg --name xiaohongshu-analyzer --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true
   ```

7. **部署代码**
   ```bash
   az webapp up --resource-group xiaohongshu-rg --name xiaohongshu-analyzer --html
   ```

## 方法2：使用VS Code Azure扩展部署

1. **安装VS Code Azure扩展**
   - 打开VS Code
   - 进入扩展面板（Ctrl+Shift+X）
   - 搜索并安装"Azure App Service"扩展

2. **登录Azure**
   - 点击VS Code侧边栏的Azure图标
   - 点击"Sign in to Azure..."并完成登录

3. **部署应用**
   - 右键点击项目文件夹
   - 选择"Deploy to Web App..."
   - 选择你的订阅和之前创建的Web应用
   - 等待部署完成

## 方法3：通过Azure门户部署

1. **打开Azure门户**
   - 访问[Azure门户](https://portal.azure.com)

2. **导航到你的Web应用**
   - 搜索并打开之前创建的Web应用

3. **设置部署中心**
   - 在左侧菜单中选择"部署中心"
   - 选择"本地Git"作为源代码
   - 点击"保存"

4. **获取部署凭据**
   - 在部署中心页面获取Git URL
   - 设置或记下你的部署用户名和密码

5. **从本地Git部署**
   ```bash
   git init
   git add .
   git commit -m "初始部署"
   git remote add azure [你的Git URL]
   git push azure main
   ```

## 部署后配置

1. **检查应用日志**
   - 在Azure门户中，导航到Web应用 > 监视 > 日志流
   - 查看任何潜在的启动问题

2. **设置自定义域（可选）**
   - 在Azure门户中，导航到Web应用 > 自定义域
   - 按照说明添加你的域名

3. **配置SSL证书（可选）**
   - 导航到Web应用 > TLS/SSL设置
   - 创建或导入SSL证书并绑定到你的自定义域 