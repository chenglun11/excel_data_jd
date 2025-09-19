# 故障排除指南

## 上传失败："load failed" 错误

### 🚨 **最常见问题：CORS 跨域错误**

#### 1. CORS 配置问题 ⭐️⭐️⭐️
**现象**:
- 上传时提示 "load failed"
- 浏览器控制台显示 CORS 错误
- 前端能访问，但上传失败

**解决方案**:

##### A. 后端 FastAPI 配置 (推荐)
在后端代码中添加 CORS 中间件：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

##### B. 开发环境临时解决方案
1. **Chrome 插件**: 安装 "CORS Unblock" 或 "CORS Toggle" 插件
2. **Chrome 启动参数**:
   ```bash
   chrome --disable-web-security --user-data-dir=/tmp/chrome_dev
   ```
3. **代理设置**: 在 `next.config.ts` 中配置代理

##### C. 生产环境解决方案
- 将前端和后端部署到同一域名下
- 使用 Nginx 反向代理
- 配置服务器正确的 CORS 头部

#### 2. 服务器未启动或地址错误
**现象**: 上传时提示 "load failed" 或 "网络连接失败"

**解决方案**:
- 检查后端服务器是否已启动
- 确认 API 地址是否正确（默认: http://localhost:6532）
- 在设置页面使用"CORS检测"功能验证

#### 3. 网络超时
**现象**: 大文件上传时失败

**解决方案**:
- 在设置页面增加超时时间（默认 30 秒）
- 建议设置为 60000 毫秒（1分钟）或更长
- 检查文件大小是否超过限制（默认 50MB）

#### 4. 认证问题
**现象**: 上传时提示认证失败

**解决方案**:
- 确保已正确登录
- 检查 token 是否有效
- 重新登录后再试

#### 4. 文件格式或大小问题
**现象**: 特定文件上传失败

**解决方案**:
- 确保文件格式为 .xlsx 或 .xls
- 检查文件大小不超过 50MB
- 确保文件没有损坏

#### 5. 认证问题
**现象**: 上传时提示认证失败

**解决方案**:
- 确保已正确登录
- 检查 token 是否有效
- 重新登录后再试

### 调试步骤：

1. **检查当前配置**:
   - 打开浏览器开发者工具（F12）
   - 进入设置页面
   - 点击"测试连接"按钮
   - 查看控制台输出的配置信息

2. **检查网络请求**:
   - 在开发者工具的 Network 标签页
   - 尝试上传文件
   - 查看失败的请求详情

3. **修改配置**:
   - 在设置页面调整 API 地址
   - 增加超时时间
   - 重新测试连接

### 常用配置：

#### 开发环境
- API 地址: `http://localhost:6532`
- 超时时间: `60000` (60秒)
- 包含凭据: `启用`

#### 生产环境
- API 地址: `http://apis.lchnan.cn`
- 超时时间: `30000` (30秒)
- 包含凭据: `启用`

### 如果问题仍然存在：

1. 检查后端服务器日志
2. 确认网络连接稳定
3. 尝试使用其他浏览器
4. 清除浏览器缓存和 localStorage
5. 联系技术支持