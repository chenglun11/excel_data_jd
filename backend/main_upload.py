"""
文件上传版京东店铺数据管理API
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
from datetime import datetime
import tempfile
from upload_processor import UploadProcessor

app = FastAPI(
    title="京东店铺数据管理API",
    description="支持文件上传的京东店铺数据处理与分析API",
    version="2.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
UPLOAD_DIR = "uploads"
EXPORT_DIR = "exports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# Pydantic模型
class DataProcessRequest(BaseModel):
    selected_shops: Optional[List[str]] = None
    include_closed_orders: bool = False
    include_offline_orders: bool = False

# 全局处理器实例
current_processor = None

@app.get("/")
async def root():
    return {"message": "京东店铺数据管理API（文件上传版）", "version": "2.0.0"}

@app.post("/upload/files")
async def upload_files(
    product_file: UploadFile = File(..., description="产品信息表Excel文件"),
    order_file: UploadFile = File(..., description="订单信息表Excel文件")
):
    """上传产品和订单Excel文件"""
    global current_processor

    try:
        # 验证文件类型
        if not product_file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="产品文件必须是Excel格式")

        if not order_file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="订单文件必须是Excel格式")

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        product_filename = f"product_{timestamp}_{product_file.filename}"
        order_filename = f"order_{timestamp}_{order_file.filename}"

        # 保存文件
        product_path = os.path.join(UPLOAD_DIR, product_filename)
        order_path = os.path.join(UPLOAD_DIR, order_filename)

        with open(product_path, "wb") as buffer:
            shutil.copyfileobj(product_file.file, buffer)

        with open(order_path, "wb") as buffer:
            shutil.copyfileobj(order_file.file, buffer)

        # 初始化处理器并加载数据
        current_processor = UploadProcessor()
        success = current_processor.load_from_files(product_path, order_path)

        if not success:
            raise HTTPException(status_code=500, detail="文件加载失败")

        # 分析文件结构
        analysis = current_processor.analyze_uploaded_files(product_path, order_path)

        return {
            "success": True,
            "message": "文件上传成功",
            "files": {
                "product_file": product_filename,
                "order_file": order_filename
            },
            "analysis": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.get("/data/shops")
async def get_available_shops():
    """获取所有可用店铺列表"""
    global current_processor

    if current_processor is None:
        raise HTTPException(status_code=400, detail="请先上传文件")

    try:
        shops = current_processor.get_available_shops()
        return {"shops": shops, "total": len(shops)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取店铺列表失败: {str(e)}")

@app.post("/data/process")
async def process_data(request: DataProcessRequest):
    """处理上传的数据"""
    global current_processor

    if current_processor is None:
        raise HTTPException(status_code=400, detail="请先上传文件")

    try:
        filter_options = {
            'selected_shops': request.selected_shops,
            'include_closed_orders': request.include_closed_orders,
            'include_offline_orders': request.include_offline_orders
        }

        processed_df, analysis = current_processor.process_data(filter_options)

        if processed_df.empty:
            return {
                "success": False,
                "message": "没有找到符合条件的数据",
                "data": {},
                "analysis": {}
            }

        # 转换DataFrame为JSON格式，限制返回条数
        data_records = processed_df.head(100).fillna(0).to_dict('records')

        # 清理数据中的NaN值
        for record in data_records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        return {
            "success": True,
            "message": f"数据处理完成，共处理 {len(processed_df)} 条记录",
            "data": {
                "records": data_records,
                "total_records": len(processed_df),
                "columns": processed_df.columns.tolist()
            },
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据处理失败: {str(e)}")

@app.post("/data/export")
async def export_processed_data(request: DataProcessRequest):
    """导出处理后的数据"""
    global current_processor

    if current_processor is None:
        raise HTTPException(status_code=400, detail="请先上传文件")

    try:
        filter_options = {
            'selected_shops': request.selected_shops,
            'include_closed_orders': request.include_closed_orders,
            'include_offline_orders': request.include_offline_orders
        }

        processed_df, analysis = current_processor.process_data(filter_options)

        if processed_df.empty:
            raise HTTPException(status_code=400, detail="没有数据可以导出")

        # 生成导出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"processed_data_{timestamp}.xlsx"
        filepath = os.path.join(EXPORT_DIR, filename)

        success = current_processor.export_processed_data(filepath)

        if success:
            return {
                "success": True,
                "message": "数据导出成功",
                "filename": filename,
                "records_count": len(processed_df),
                "download_url": f"/download/{filename}"
            }
        else:
            raise HTTPException(status_code=500, detail="数据导出失败")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """下载导出的文件"""
    filepath = os.path.join(EXPORT_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.get("/files/list")
async def list_uploaded_files():
    """列出已上传的文件"""
    try:
        files = []
        if os.path.exists(UPLOAD_DIR):
            for file in os.listdir(UPLOAD_DIR):
                if file.endswith(('.xlsx', '.xls')):
                    filepath = os.path.join(UPLOAD_DIR, file)
                    file_size = os.path.getsize(filepath)
                    files.append({
                        "name": file,
                        "size": file_size,
                        "size_mb": round(file_size / 1024 / 1024, 2),
                        "upload_time": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                    })

        return {"files": files, "total": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@app.delete("/files/clear")
async def clear_uploaded_files():
    """清理上传的文件"""
    global current_processor

    try:
        # 清理上传文件
        if os.path.exists(UPLOAD_DIR):
            for file in os.listdir(UPLOAD_DIR):
                filepath = os.path.join(UPLOAD_DIR, file)
                os.remove(filepath)

        # 清理导出文件
        if os.path.exists(EXPORT_DIR):
            for file in os.listdir(EXPORT_DIR):
                filepath = os.path.join(EXPORT_DIR, file)
                os.remove(filepath)

        # 重置处理器
        current_processor = None

        return {"success": True, "message": "文件清理完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件清理失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import pandas as pd  # 添加pandas导入
    uvicorn.run(app, host="0.0.0.0", port=8000)