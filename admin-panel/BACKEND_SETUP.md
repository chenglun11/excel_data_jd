# 后端开发环境配置指南

## 🚨 上传失败的后端配置问题

### 问题：前端 `load failed` 错误

如果前端显示 "load failed" 错误，通常是后端配置问题。在开发环境中，需要在后端代码中写死一些配置。

### 解决方案

#### 1. FastAPI CORS 配置 (必须)

在后端主文件中添加：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 开发环境 CORS 配置 - 写死配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js 开发服务器
        "http://127.0.0.1:3000",  # 备用地址
        "http://localhost:3001",  # 备用端口
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

#### 2. 文件上传大小限制

```python
from fastapi import FastAPI, UploadFile, File

# 增加文件大小限制
app.add_middleware(
    LimitUploadSizeMiddleware,
    max_upload_size=50_000_000  # 50MB
)

# 或在路由中设置
@app.post("/upload/files")
async def upload_files(
    product_file: UploadFile = File(..., max_size=50_000_000),
    order_file: UploadFile = File(..., max_size=50_000_000)
):
    pass
```

#### 3. 开发环境完整示例

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="JD Store Management API")

# 开发环境判断
is_development = os.getenv("ENVIRONMENT", "development") == "development"

if is_development:
    # 开发环境：宽松的 CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发时允许所有来源
        allow_credentials=False,  # 使用 * 时必须设为 False
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 生产环境：严格的 CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://your-domain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

@app.get("/")
async def root():
    return {"message": "JD Store Management API", "status": "running"}

@app.post("/upload/files")
async def upload_files(
    product_file: UploadFile = File(...),
    order_file: UploadFile = File(...)
):
    # 检查文件类型
    allowed_types = ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     "application/vnd.ms-excel"]

    if product_file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="产品文件格式不支持")

    if order_file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="订单文件格式不支持")

    # 处理文件上传逻辑
    return {
        "success": True,
        "message": "文件上传成功",
        "files": {
            "product_file": product_file.filename,
            "order_file": order_file.filename
        }
    }
```

### 常见问题排查

#### 1. 检查后端是否启动
```bash
curl http://localhost:6532/
# 应该返回 JSON 响应
```

#### 2. 检查 CORS 头部
```bash
curl -X OPTIONS http://localhost:6532/upload/files \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v
# 检查响应中是否包含 Access-Control-Allow-* 头部
```

#### 3. 检查文件上传端点
```bash
curl -X POST http://localhost:6532/upload/files \
  -F "product_file=@test.xlsx" \
  -F "order_file=@test.xlsx" \
  -v
```

### 环境变量配置

创建 `.env` 文件：

```env
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
MAX_UPLOAD_SIZE=52428800
```

然后在代码中使用：

```python
from dotenv import load_dotenv
import os

load_dotenv()

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 测试步骤

1. 启动后端服务
2. 在前端设置页面点击"运行完整调试"
3. 查看浏览器控制台输出
4. 根据错误信息调整后端配置
5. 重新测试文件上传功能