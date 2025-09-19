# 无认证模式设置指南

## 🔓 跳过登录，直接使用功能

如果你暂时不想实现登录功能，可以配置后端支持无认证访问。

### 后端配置 (FastAPI)

#### 1. 移除认证依赖 (推荐临时方案)

在你的 FastAPI 路由中，临时移除或注释掉认证检查：

```python
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
# from your_auth_module import get_current_user  # 注释掉

app = FastAPI()

# 原来需要认证的路由
@app.get("/data/shops")
async def get_shops():
    # current_user: User = Depends(get_current_user)  # 注释掉这行
    # 直接返回店铺列表
    return {"shops": ["店铺1", "店铺2", "店铺3"]}

@app.post("/data/process")
async def process_data(request: ProcessRequest):
    # current_user: User = Depends(get_current_user)  # 注释掉这行
    # 直接处理数据
    return {"success": True, "message": "处理完成"}

@app.post("/data/export")
async def export_data(request: ExportRequest):
    # current_user: User = Depends(get_current_user)  # 注释掉这行
    # 直接导出数据
    return {"success": True, "filename": "export.xlsx"}

@app.post("/upload/files")
async def upload_files(
    product_file: UploadFile = File(...),
    order_file: UploadFile = File(...)
):
    # current_user: User = Depends(get_current_user)  # 注释掉这行
    # 直接处理文件上传
    return {
        "success": True,
        "files": {
            "product_file": product_file.filename,
            "order_file": order_file.filename
        }
    }
```

#### 2. 条件认证 (灵活方案)

如果你想保留认证功能但允许绕过：

```python
from fastapi import FastAPI, Depends, HTTPException
from typing import Optional

# 可选认证依赖
def get_optional_user() -> Optional[User]:
    try:
        # 尝试获取用户，失败时返回 None
        return get_current_user()
    except:
        return None

@app.get("/data/shops")
async def get_shops(current_user: Optional[User] = Depends(get_optional_user)):
    # 可以访问，不管是否登录
    return {"shops": ["店铺1", "店铺2", "店铺3"]}

@app.post("/data/process")
async def process_data(
    request: ProcessRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    # 记录用户信息（如果有的话）
    if current_user:
        print(f"用户 {current_user.username} 正在处理数据")
    else:
        print("匿名用户正在处理数据")

    return {"success": True, "message": "处理完成"}
```

#### 3. 环境变量控制 (生产就绪方案)

```python
import os
from fastapi import FastAPI, Depends

# 从环境变量读取是否需要认证
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() == "true"

def get_user_if_required():
    if REQUIRE_AUTH:
        return Depends(get_current_user)
    else:
        return Depends(lambda: None)  # 返回空用户

@app.get("/data/shops")
async def get_shops(current_user = get_user_if_required()):
    return {"shops": ["店铺1", "店铺2", "店铺3"]}
```

然后在 `.env` 文件中设置：
```env
REQUIRE_AUTH=false  # 开发环境
# REQUIRE_AUTH=true  # 生产环境
```

### 测试配置

修改后端后，使用前端的测试功能验证：

1. 打开设置页面 (`/settings`)
2. 点击 **"🔓 测试无认证模式"** 按钮
3. 查看控制台输出，确认所有端点都返回成功

### 前端已经完成的修改

前端代码已经修改为无认证模式：

- ✅ 移除了 token 检查
- ✅ 使用无认证的 API 请求
- ✅ 文件上传不需要登录
- ✅ 数据处理不需要登录
- ✅ 数据导出不需要登录

### 注意事项

1. **开发环境**：无认证模式适合快速开发和测试
2. **生产环境**：建议启用认证保护数据安全
3. **数据安全**：无认证模式下任何人都能访问和处理数据
4. **日志记录**：建议记录操作日志，即使没有用户信息

### 恢复认证

如果后续想恢复认证功能：

1. 在后端恢复 `Depends(get_current_user)`
2. 前端取消注释登录相关代码
3. 测试登录流程是否正常