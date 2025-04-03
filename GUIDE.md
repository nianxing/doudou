# 小红书内容分析工具使用指南

本文档将指导您如何配置和使用小红书内容分析工具，特别是如何设置API代理服务来有效绕过小红书的反爬虫措施。

## 1. 配置API代理服务

### 1.1 选择API服务提供商

本工具支持多个API服务提供商，每个提供商都有不同的特点和价格。以下是一些建议：

| 提供商 | 免费试用 | 价格 | 特点 | 推荐程度 |
|-------|---------|------|------|---------|
| [ScrapingAPI](https://www.scrapingapi.com/) | 1,000次 | $29/月起 | 综合性能好，支持JS渲染 | ⭐⭐⭐⭐⭐ |
| [ScraperAPI](https://www.scraperapi.com/) | 1,000次 | $29/月起 | 价格合理，易于使用 | ⭐⭐⭐⭐ |
| [ZenRows](https://www.zenrows.com/) | 1,000次 | $49/月起 | 反爬虫能力强 | ⭐⭐⭐⭐⭐ |
| [ScrapeStack](https://scrapestack.com/) | 10,000次 | $29.99/月起 | 免费额度多 | ⭐⭐⭐ |
| [ScrapingDog](https://www.scrapingdog.com/) | 1,000次 | $20/月起 | 价格低 | ⭐⭐⭐ |

您可以选择一个或多个服务进行测试，看哪个最适合您的需求。

### 1.2 注册账号并获取API密钥

1. 访问您选择的API服务提供商网站
2. 注册一个账号
3. 在仪表盘或设置页面找到您的API密钥
4. 复制API密钥，稍后会用到

### 1.3 配置环境变量

1. 在项目根目录找到`.env.example`文件
2. 复制该文件并重命名为`.env`
3. 使用文本编辑器打开`.env`文件
4. 找到对应提供商的API密钥设置项，填入您的API密钥

例如，如果您使用ScrapingAPI，应该设置：

```
SCRAPINGAPI_KEY=your_actual_api_key_here
PREFERRED_API_PROXY=scrapingapi
```

如果您使用ZenRows，应该设置：

```
ZENROWS_API_KEY=your_actual_api_key_here
PREFERRED_API_PROXY=zenrows
```

### 1.4 测试API配置

在配置完成后，您可以运行测试脚本来验证API代理服务是否正常工作：

```bash
python test_api_proxy.py
```

此脚本会：
- 检查API密钥是否已正确配置
- 尝试抓取小红书的页面
- 尝试解析内容
- 尝试搜索关键词

如果测试成功，您会看到"测试全部通过!"的消息。

## 2. 使用小红书内容分析工具

### 2.1 启动应用

启动应用有两种方式：

**Windows**:
```bash
python app.py
```
或双击`start.bat`

**Linux/Mac**:
```bash
python app.py
```
或运行`./start.sh`

### 2.2 使用Web界面

1. 打开浏览器访问 http://localhost:8080
2. 在输入框中粘贴小红书帖子URL
3. 点击"分析"按钮
4. 等待系统处理（会按优先级依次尝试：API代理服务 > 浏览器自动化 > 基础抓取）
5. 查看分析结果

### 2.3 使用手动输入功能

如果自动抓取失败，您可以使用手动输入功能：

1. 点击"手动输入内容"按钮
2. 填写帖子标题
3. 填写帖子内容
4. 可选：添加图片URL（每行一个）
5. 点击"提交手动输入"按钮
6. 查看分析结果

## 3. 常见问题解决

### 3.1 API代理服务抓取失败

可能的原因：
- API密钥无效或已过期
- API服务账户余额不足
- API服务对特定网站有限制

解决方案：
1. 检查API密钥是否正确
2. 检查您的API服务账户余额
3. 尝试切换到其他API服务提供商
4. 在`.env`文件中设置`PREFERRED_API_PROXY`为其他提供商

### 3.2 所有抓取方法都失败

可能的原因：
- 帖子URL无效
- 帖子已被删除
- 帖子需要登录才能查看
- 网络连接问题

解决方案：
1. 确认URL是否正确
2. 在浏览器中手动打开URL，检查内容是否可见
3. 如果内容可见，使用手动输入功能
4. 检查网络连接

### 3.3 分析结果不准确

可能的原因：
- 内容过于简短
- 语言或格式过于特殊
- 关键词提取算法限制

解决方案：
1. 尝试使用更详细的手动输入
2. 优化原始内容，使其更具描述性
3. 根据您的需求手动调整关键词

## 4. 进阶使用

### 4.1 批量处理

如果您需要批量处理多个URL，可以编写简单的脚本：

```python
import api_proxy_tool as proxy

urls = [
    "https://www.xiaohongshu.com/discovery/item/xxxxxx",
    "https://www.xiaohongshu.com/discovery/item/yyyyyy",
    "https://www.xiaohongshu.com/discovery/item/zzzzzz"
]

results = []
for url in urls:
    print(f"处理: {url}")
    result = proxy.main(url)
    results.append(result)

# 保存结果
import json
with open("batch_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

### 4.2 自定义API代理服务

如果您有其他偏好的API代理服务，可以在`config.py`中添加：

```python
API_PROVIDERS = {
    # ... 现有配置 ...
    
    "your_provider": {
        "base_url": "https://api.your-provider.com/scrape",
        "params": {
            "api_key": API_KEYS["YOUR_PROVIDER_KEY"],
            "url": None,  # 在请求时填充
            "render_js": "true",
            "other_param": "value"
        }
    }
}
```

然后在`.env`文件中添加：

```
YOUR_PROVIDER_KEY=your_api_key_here
PREFERRED_API_PROXY=your_provider
```

## 5. API使用优化建议

为了优化API使用和成本，请考虑以下建议：

1. **缓存结果**：对于已经抓取过的URL，考虑缓存结果，避免重复请求
2. **使用免费额度**：许多API服务提供免费额度，充分利用这些额度进行测试
3. **选择合适的计划**：根据您的使用量选择最经济的计划
4. **监控用量**：定期检查API调用次数，避免意外超额
5. **退避策略**：在批量处理时，添加适当的延迟，避免API请求过于频繁

## 6. 法律和伦理考虑

使用网页抓取工具时，请注意以下事项：

1. 遵守网站的服务条款和robots.txt规则
2. 限制抓取频率，避免对目标网站造成负担
3. 仅将抓取的内容用于个人学习和研究
4. 尊重内容创作者的权益
5. 不要分发或商业化使用抓取的内容

---

如果您有任何问题或建议，请提交issue或联系维护者。祝您使用愉快！ 