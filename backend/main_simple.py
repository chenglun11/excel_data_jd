"""
简化版京东店铺数据管理API - 无需登录
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import os
from datetime import datetime
from data_processor import DataProcessor
from data_analyzer import DataAnalyzer

app = FastAPI(
    title="京东店铺数据管理API",
    description="京东店铺数据处理与分析管理后端API（简化版）",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic模型
class DataProcessRequest(BaseModel):
    selected_shops: Optional[List[str]] = None
    include_closed_orders: bool = False
    include_offline_orders: bool = False

# 初始化数据处理器
processor = DataProcessor()
analyzer = DataAnalyzer()

# API路由
@app.get("/")
async def root():
    return {"message": "京东店铺数据管理API（简化版）", "version": "1.0.0"}

@app.get("/data/files")
async def get_data_files():
    """获取数据文件列表"""
    dataset_path = "../dataset"
    if not os.path.exists(dataset_path):
        return {"files": []}

    files = []
    for file in os.listdir(dataset_path):
        if file.endswith(('.xlsx', '.xls')):
            file_path = os.path.join(dataset_path, file)
            file_size = os.path.getsize(file_path)
            files.append({
                "name": file,
                "size": file_size,
                "size_mb": round(file_size / 1024 / 1024, 2)
            })

    return {"files": files}

@app.get("/data/shops")
async def get_available_shops():
    """获取所有可用店铺列表"""
    try:
        shops = processor.get_available_shops()
        return {"shops": shops, "total": len(shops)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取店铺列表失败: {str(e)}")

@app.post("/data/process")
async def process_data(request: DataProcessRequest):
    """处理数据并返回结果"""
    try:
        filter_options = {
            'selected_shops': request.selected_shops,
            'include_closed_orders': request.include_closed_orders,
            'include_offline_orders': request.include_offline_orders
        }

        processed_df, analysis = processor.process_data(filter_options)

        if processed_df.empty:
            return {
                "success": False,
                "message": "没有找到符合条件的数据",
                "data": {},
                "analysis": {}
            }

        # 转换DataFrame为JSON格式
        data_records = processed_df.head(100).to_dict('records')  # 限制返回前100条

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

@app.get("/data/analysis/shops")
async def get_shop_analysis():
    """获取店铺分析数据"""
    try:
        shop_analysis = analyzer.get_shop_analysis()
        return shop_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"店铺分析失败: {str(e)}")

@app.get("/data/analysis/order-status")
async def get_order_status_analysis():
    """获取订单状态分析"""
    try:
        status_analysis = analyzer.get_order_status_analysis()
        return status_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"订单状态分析失败: {str(e)}")

@app.post("/data/export")
async def export_processed_data(request: DataProcessRequest):
    """导出处理后的数据"""
    try:
        filter_options = {
            'selected_shops': request.selected_shops,
            'include_closed_orders': request.include_closed_orders,
            'include_offline_orders': request.include_offline_orders
        }

        processed_df, analysis = processor.process_data(filter_options)

        if processed_df.empty:
            raise HTTPException(status_code=400, detail="没有数据可以导出")

        # 生成导出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"processed_data_{timestamp}.xlsx"

        success = processor.export_processed_data(filename)

        if success:
            return {
                "success": True,
                "message": "数据导出成功",
                "filename": filename,
                "records_count": len(processed_df)
            }
        else:
            raise HTTPException(status_code=500, detail="数据导出失败")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@app.get("/data/preview/{filename}")
async def preview_excel_file(filename: str):
    """预览Excel文件内容"""
    file_path = f"../dataset/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        # 读取Excel文件的前10行作为预览
        df = pd.read_excel(file_path, nrows=10)

        # 转换为JSON格式
        preview_data = {
            "columns": df.columns.tolist(),
            "data": df.to_dict('records'),
            "total_rows": len(df),
            "file_info": {
                "name": filename,
                "shape": df.shape
            }
        }

        return preview_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件错误: {str(e)}")

@app.get("/data/analyze/{filename}")
async def analyze_excel_file(filename: str):
    """分析Excel文件数据"""
    file_path = f"../dataset/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        df = pd.read_excel(file_path)

        analysis = {
            "basic_info": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": df.columns.tolist(),
                "memory_usage": df.memory_usage(deep=True).sum()
            },
            "data_types": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "numeric_summary": {}
        }

        # 数值列统计
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) > 0:
            analysis["numeric_summary"] = df[numeric_columns].describe().to_dict()

        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析文件错误: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)