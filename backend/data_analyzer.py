"""
京东店铺数据分析器
用于分析Excel文件结构并提供数据预览
"""
import pandas as pd
import os
from typing import Dict, List, Any, Optional

class DataAnalyzer:
    def __init__(self, dataset_path: str = "../dataset"):
        self.dataset_path = dataset_path
        self.product_file = None
        self.order_file = None
        self.bill_file = None
        self._identify_files()

    def _identify_files(self):
        """识别数据集中的文件类型"""
        if not os.path.exists(self.dataset_path):
            return

        for file in os.listdir(self.dataset_path):
            if file.endswith(('.xlsx', '.xls')):
                if '产品信息' in file:
                    self.product_file = os.path.join(self.dataset_path, file)
                elif '订单' in file:
                    self.order_file = os.path.join(self.dataset_path, file)
                elif '账单' in file:
                    self.bill_file = os.path.join(self.dataset_path, file)

    def get_file_info(self) -> Dict[str, Any]:
        """获取所有文件的基本信息"""
        info = {
            "product_file": self.product_file,
            "order_file": self.order_file,
            "bill_file": self.bill_file,
            "files_analysis": {}
        }

        for file_type, file_path in [
            ("product", self.product_file),
            ("order", self.order_file),
            ("bill", self.bill_file)
        ]:
            if file_path and os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path, nrows=0)  # 只读取列名
                    info["files_analysis"][file_type] = {
                        "file_name": os.path.basename(file_path),
                        "columns": df.columns.tolist(),
                        "column_count": len(df.columns)
                    }
                except Exception as e:
                    info["files_analysis"][file_type] = {
                        "error": str(e)
                    }

        return info

    def preview_data(self, file_type: str, nrows: int = 10) -> Dict[str, Any]:
        """预览指定类型文件的数据"""
        file_map = {
            "product": self.product_file,
            "order": self.order_file,
            "bill": self.bill_file
        }

        file_path = file_map.get(file_type)
        if not file_path or not os.path.exists(file_path):
            return {"error": f"文件 {file_type} 不存在"}

        try:
            df = pd.read_excel(file_path, nrows=nrows)
            return {
                "columns": df.columns.tolist(),
                "data": df.to_dict('records'),
                "shape": df.shape,
                "dtypes": df.dtypes.astype(str).to_dict()
            }
        except Exception as e:
            return {"error": str(e)}

    def analyze_product_columns(self) -> Dict[str, Any]:
        """分析产品信息表的列结构，查找商品编号列"""
        if not self.product_file:
            return {"error": "产品信息表文件不存在"}

        try:
            df = pd.read_excel(self.product_file, nrows=100)  # 读取前100行进行分析

            # 查找可能的商品编号列
            potential_sku_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(keyword in col_str for keyword in ['商品编号', 'sku', '编号', '货号', '商品id']):
                    potential_sku_columns.append(col)

            # 分析数据类型和唯一值
            analysis = {
                "total_columns": len(df.columns),
                "all_columns": df.columns.tolist(),
                "potential_sku_columns": potential_sku_columns,
                "column_analysis": {}
            }

            for col in df.columns:
                analysis["column_analysis"][col] = {
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "unique_count": int(df[col].nunique()),
                    "sample_values": df[col].dropna().head(3).tolist()
                }

            return analysis
        except Exception as e:
            return {"error": str(e)}

    def analyze_order_columns(self) -> Dict[str, Any]:
        """分析订单表的列结构，查找关键字段"""
        if not self.order_file:
            return {"error": "订单文件不存在"}

        try:
            df = pd.read_excel(self.order_file, nrows=100)

            # 查找关键列
            key_columns = {
                "sku_columns": [],
                "amount_columns": [],
                "status_columns": [],
                "shop_columns": []
            }

            for col in df.columns:
                col_str = str(col).lower()
                if any(keyword in col_str for keyword in ['商品编号', 'sku', '编号', '货号']):
                    key_columns["sku_columns"].append(col)
                elif any(keyword in col_str for keyword in ['买家实付', '实付', '金额', '价格', '付款']):
                    key_columns["amount_columns"].append(col)
                elif any(keyword in col_str for keyword in ['状态', '订单状态', 'status']):
                    key_columns["status_columns"].append(col)
                elif any(keyword in col_str for keyword in ['店铺', 'shop', '商店']):
                    key_columns["shop_columns"].append(col)

            analysis = {
                "total_columns": len(df.columns),
                "all_columns": df.columns.tolist(),
                "key_columns": key_columns,
                "column_analysis": {}
            }

            for col in df.columns:
                analysis["column_analysis"][col] = {
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "unique_count": int(df[col].nunique()),
                    "sample_values": df[col].dropna().head(3).tolist()
                }

            return analysis
        except Exception as e:
            return {"error": str(e)}

    def get_order_status_analysis(self) -> Dict[str, Any]:
        """分析订单状态分布"""
        if not self.order_file:
            return {"error": "订单文件不存在"}

        try:
            df = pd.read_excel(self.order_file)

            # 查找状态列
            status_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(keyword in col_str for keyword in ['状态', 'status']):
                    status_columns.append(col)

            status_analysis = {}
            for col in status_columns:
                status_counts = df[col].value_counts().to_dict()
                status_analysis[col] = {
                    "unique_statuses": list(status_counts.keys()),
                    "status_counts": status_counts,
                    "total_records": len(df)
                }

            return {
                "status_columns": status_columns,
                "status_analysis": status_analysis,
                "total_orders": len(df)
            }
        except Exception as e:
            return {"error": str(e)}

    def get_shop_analysis(self) -> Dict[str, Any]:
        """分析店铺分布"""
        if not self.order_file:
            return {"error": "订单文件不存在"}

        try:
            df = pd.read_excel(self.order_file)

            # 查找店铺列
            shop_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(keyword in col_str for keyword in ['店铺', 'shop', '商店']):
                    shop_columns.append(col)

            shop_analysis = {}
            for col in shop_columns:
                shop_counts = df[col].value_counts().to_dict()
                shop_analysis[col] = {
                    "unique_shops": list(shop_counts.keys()),
                    "shop_counts": shop_counts,
                    "total_shops": df[col].nunique()
                }

            return {
                "shop_columns": shop_columns,
                "shop_analysis": shop_analysis,
                "total_orders": len(df)
            }
        except Exception as e:
            return {"error": str(e)}

# 测试代码
if __name__ == "__main__":
    analyzer = DataAnalyzer()
    print("=== 文件信息 ===")
    print(analyzer.get_file_info())

    print("\n=== 产品列分析 ===")
    print(analyzer.analyze_product_columns())

    print("\n=== 订单列分析 ===")
    print(analyzer.analyze_order_columns())

    print("\n=== 订单状态分析 ===")
    print(analyzer.get_order_status_analysis())

    print("\n=== 店铺分析 ===")
    print(analyzer.get_shop_analysis())