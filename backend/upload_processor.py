"""
京东店铺数据处理器
支持Excel文件上传和数据处理，包含重复数据检测和去重功能
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

class UploadProcessor:
    """
    京东店铺数据处理器

    主要功能：
    - 加载产品信息表和订单数据
    - 数据清理和去重
    - 产品信息与订单数据匹配
    - 成本利润计算
    - 数据分析和统计
    - 处理结果导出

    Attributes:
        product_df: 产品信息DataFrame
        order_df: 订单数据DataFrame
        processed_data: 处理后的数据DataFrame
        dedup_stats: 去重统计信息
    """

    def __init__(self):
        """初始化处理器"""
        self.product_df = None
        self.order_df = None
        self.processed_data = None
        self.dedup_stats = {}

    def load_from_files(self, product_file_path: str, order_file_path: str) -> bool:
        """
        从Excel文件加载产品和订单数据

        Args:
            product_file_path: 产品信息表文件路径
            order_file_path: 订单数据文件路径

        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            # 加载产品信息表
            self.product_df = pd.read_excel(product_file_path)

            # 清理产品数据：移除标题行，重置索引
            if '商家编码' in self.product_df.columns:
                self.product_df = self.product_df[self.product_df['商家编码'] != '商家编码'].reset_index(drop=True)

            # 加载订单数据
            self.order_df = pd.read_excel(order_file_path)

            print(f"产品数据加载完成: {len(self.product_df)} 条记录")
            print(f"订单数据加载完成: {len(self.order_df)} 条记录")

            return True
        except Exception as e:
            print(f"数据加载错误: {e}")
            return False


    def analyze_uploaded_files(self, product_file_path: str, order_file_path: str) -> Dict[str, Any]:
        """分析上传的文件结构"""
        analysis = {"product_file": None, "order_file": None}

        try:
            # 分析产品文件
            if os.path.exists(product_file_path):
                df = pd.read_excel(product_file_path, nrows=5)
                analysis["product_file"] = {
                    "columns": df.columns.tolist(),
                    "sample_data": df.head(3).fillna("").to_dict('records'),
                    "total_columns": len(df.columns)
                }

            # 分析订单文件
            if os.path.exists(order_file_path):
                df = pd.read_excel(order_file_path, nrows=5)
                analysis["order_file"] = {
                    "columns": df.columns.tolist(),
                    "sample_data": df.head(3).fillna("").to_dict('records'),
                    "total_columns": len(df.columns)
                }

        except Exception as e:
            analysis["error"] = str(e)

        return analysis

    def clean_order_data(self, filter_options: Dict[str, Any] = None) -> pd.DataFrame:
        """
        清理订单数据，包含去重和过滤功能

        按订单级过滤金额与状态，保留订单内所有行（包括0元赠品/返现行）

        Args:
            filter_options: 过滤选项，包含店铺筛选等参数

        Returns:
            pd.DataFrame: 清理后的订单数据
        """
        if self.order_df is None:
            return pd.DataFrame()

        df = self.order_df.copy()

        # ✅ 关键修复3：订单数据预处理去重，移除完全重复的订单行
        original_order_rows = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        dedup_order_rows = len(df)
        if original_order_rows != dedup_order_rows:
            print(f"⚠️ 订单原始数据去重: {original_order_rows} -> {dedup_order_rows} 行 (去除了 {original_order_rows - dedup_order_rows} 个重复行)")

        filters = []

        # 订单标记列
        order_mark_columns = [c for c in df.columns if any(k in str(c).lower() for k in ['订单标记','标记','mark'])]
        if order_mark_columns:
            mc = order_mark_columns[0]
            filters.append(df[mc].astype(str).str.contains('空单', na=False) == False)
            print(f"发现订单标记列: {mc}")
        else:
            print("警告：未找到订单标记列")

        # 金额列（买家实付）
        amount_columns = [c for c in df.columns if any(k in str(c).lower() for k in ['买家实付','实付','金额','付款'])]
        amount_col = amount_columns[0] if amount_columns else None
        if amount_col:
            # 统一为数值
            df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
            print(f"发现买家实付列: {amount_col}")
        else:
            print("警告：未找到买家实付列")

        # 状态列
        status_columns = [c for c in df.columns if any(k in str(c).lower() for k in ['状态','status'])]
        for sc in status_columns:
            s = df[sc].astype(str)
            filters.append(s != '关闭')
            filters.append(~s.str.contains('退款', na=False))
            filters.append(s != '[线下订单]')
            print(f"发现状态列: {sc}")

        # 订单号列（用于“订单级”过滤）
        order_id_cols = [c for c in df.columns if any(k in str(c).lower() for k in ['订单号','订单编号','order'])]
        order_id_col = order_id_cols[0] if order_id_cols else None

        # 应用基础过滤（标记/状态）
        base_filter = np.logical_and.reduce(filters) if filters else np.ones(len(df), dtype=bool)
        base_df = df[base_filter].copy()

        # ——关键：订单级金额过滤（合计>0的订单全部保留其所有行）
        if amount_col and order_id_col:
            order_sum = base_df.groupby(order_id_col)[amount_col].transform('sum')
            keep_orders = order_sum > 0
            cleaned_df = base_df[keep_orders].copy()
        elif amount_col:
            # 无订单号时，只能行级兜底
            cleaned_df = base_df[base_df[amount_col] > 0].copy()
        else:
            cleaned_df = base_df.copy()

        # 店铺筛选（可选）
        if filter_options and 'selected_shops' in filter_options:
            selected = filter_options['selected_shops'] or []
            if selected:
                shop_cols = [c for c in df.columns if any(k in str(c).lower() for k in ['店铺','shop'])]
                if shop_cols:
                    cleaned_df = cleaned_df[cleaned_df[shop_cols[0]].isin(selected)]

        # ——统计信息（行数 vs 订单数）
        original_lines = len(df)
        cleaned_lines = len(cleaned_df)
        if order_id_col:
            original_orders = int(df[order_id_col].nunique())
            cleaned_orders = int(cleaned_df[order_id_col].nunique())
            print(f"原始：{original_lines} 行 / {original_orders} 单；清理后：{cleaned_lines} 行 / {cleaned_orders} 单")
        else:
            print(f"原始：{original_lines} 行；清理后：{cleaned_lines} 行（无订单号列，无法统计订单数）")

        return cleaned_df


    def match_products_with_orders(self, order_df: pd.DataFrame) -> pd.DataFrame:
        """
        匹配产品信息和订单信息，自动处理重复数据

        根据商品编码将产品信息表与订单数据进行匹配，
        包含自动去重逻辑防止重复数据产生

        Args:
            order_df: 清理后的订单数据

        Returns:
            pd.DataFrame: 匹配后的数据
        """
        if self.product_df is None or order_df.empty:
            return pd.DataFrame()

        # 获取列名信息用于匹配

        # 查找商品编码列
        product_sku_cols = []
        for col in self.product_df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['商家编码', 'sku', '编号', '商品编码', '货号', 'code']):
                product_sku_cols.append(col)

        order_sku_cols = []
        for col in order_df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['商品编码', 'sku', '编号', '商家编码', '货号', 'code']):
                order_sku_cols.append(col)

        # 检查是否找到可匹配的编码列

        if not product_sku_cols or not order_sku_cols:
            print("警告：未找到匹配的商品编码列")
            # 如果无法匹配，至少要保留订单数据，并手动创建一个成本列用于后续处理
            order_df = order_df.copy()
            order_df['匹配状态'] = '未匹配'
            return order_df

        # 尝试多个组合进行匹配
        best_matched_df = None
        best_match_count = 0

        for product_col in product_sku_cols:
            for order_col in order_sku_cols:
                print(f"\n尝试匹配: 产品表[{product_col}] <-> 订单表[{order_col}]")

                # 准备数据
                product_df = self.product_df.copy()
                temp_order_df = order_df.copy()

                product_df[product_col] = product_df[product_col].astype(str).str.strip()
                temp_order_df[order_col] = temp_order_df[order_col].astype(str).str.strip()

                # ✅ 关键修复1：产品表去重，避免同一商品编码对应多个产品记录导致重复
                product_before_dedup = len(product_df)
                product_df = product_df.drop_duplicates(subset=[product_col], keep='first')
                product_after_dedup = len(product_df)
                if product_before_dedup != product_after_dedup:
                    print(f"⚠️ 产品表去重: {product_before_dedup} -> {product_after_dedup} 行 (去除了 {product_before_dedup - product_after_dedup} 个重复商品编码)")

                # 进行数据匹配

                # 匹配逻辑
                matched_df = temp_order_df.merge(
                    product_df,
                    left_on=order_col,
                    right_on=product_col,
                    how='left',
                    suffixes=('_order', '_product')
                )

                matched_count = len(matched_df[matched_df[product_col].notna()])
                # 记录匹配结果

                if matched_count > best_match_count:
                    best_match_count = matched_count
                    best_matched_df = matched_df
                    # 更新最佳匹配结果

        if best_matched_df is not None and best_match_count > 0:
            # 使用最佳匹配结果

            # ✅ 关键修复2：最终结果去重，确保没有完全重复的行
            original_rows = len(best_matched_df)
            best_matched_df = best_matched_df.drop_duplicates().reset_index(drop=True)
            final_rows = len(best_matched_df)
            if original_rows != final_rows:
                print(f"⚠️ 最终结果去重: {original_rows} -> {final_rows} 行 (去除了 {original_rows - final_rows} 个重复行)")

            return best_matched_df
        else:
            print("\n警告：所有匹配尝试都失败！")
            # 返回原始订单数据，但添加标记
            order_df = order_df.copy()
            order_df['匹配状态'] = '匹配失败'
            return order_df

    def calculate_costs_and_profits(self, matched_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算成本和利润

        从产品表获取成本信息，计算总成本、利润和毛利率
        优先使用产品侧(_product)列，确保成本数据的准确性

        Args:
            matched_df: 匹配后的数据

        Returns:
            pd.DataFrame: 包含成本利润信息的完整数据
        """
        if matched_df.empty:
            return pd.DataFrame()

        df = matched_df.copy()

        # —— 只从【产品表】来的列里找成本（带 _product 后缀优先）
        # 允许的关键词仅限成本相关，避免“一口价/最低报价/实际价格”等被误判
        def is_cost_name(name: str) -> bool:
            n = str(name).lower()
            return any(k in n for k in ['成本', '进货', '采购', 'cost'])

        # 先找带 _product 的成本列（确保来自产品表）
        product_cost_cols = [c for c in df.columns if c.endswith('_product') and is_cost_name(c)]
        # 再兜底：产品表原始列名（无后缀，但只在订单侧不存在同名时才会这样）
        if not product_cost_cols and self.product_df is not None:
            product_cost_cols = [c for c in self.product_df.columns if is_cost_name(c) and c in df.columns]

        if product_cost_cols:
            unit_cost_col = product_cost_cols[0]
            df['单位成本'] = pd.to_numeric(df[unit_cost_col], errors='coerce').fillna(0)
        else:
            df['单位成本'] = 0.0

        # —— 数量（优先这些名字）
        qty_candidates = [c for c in df.columns if any(k in str(c).lower() for k in
                            ['数量','件数','qty','num','购买数量','下单数量','宝贝总数量'])]
        if qty_candidates:
            qty_col = qty_candidates[0]
            df['数量'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1)
        else:
            df['数量'] = 1

        # —— 可选收入（不影响“成本正确”）
        amount_cols = [c for c in df.columns if any(k in str(c).lower() for k in
                        ['买家实付','实付','付款','应付','支付','金额','收款','成交价','支付金额'])]
        if amount_cols:
            amount_col = amount_cols[0]
            df['销售收入'] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0).round(2)
        else:
            df['销售收入'] = 0.0

        # —— 计算
        df['总成本'] = (df['单位成本'] * df['数量']).round(2)
        df['利润'] = (df['销售收入'] - df['总成本']).round(2)
        df['毛利率'] = np.where(df['销售收入'] > 0, (df['利润'] / df['销售收入']).round(4), 0)

        # 清理和验证数据

        df['数据处理时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df.replace([np.inf, -np.inf], 0, inplace=True)
        df.fillna(0, inplace=True)
        return df





    def get_available_shops(self) -> List[str]:
        """获取所有可用的店铺列表"""
        if self.order_df is None:
            return []

        shop_columns = []
        for col in self.order_df.columns:
            if any(keyword in str(col).lower() for keyword in ['店铺', 'shop']):
                shop_columns.append(col)

        if shop_columns:
            return sorted(self.order_df[shop_columns[0]].unique().tolist())
        return []

    def detect_duplicates(self, df: pd.DataFrame, description: str = "") -> Dict[str, Any]:
        """检测数据框中的重复情况并返回详细报告"""
        if df.empty:
            return {"total_rows": 0, "duplicate_rows": 0, "duplicate_rate": 0}

        total_rows = len(df)
        unique_rows = len(df.drop_duplicates())
        duplicate_rows = total_rows - unique_rows
        duplicate_rate = round(duplicate_rows / total_rows * 100, 2) if total_rows > 0 else 0

        report = {
            "description": description,
            "total_rows": total_rows,
            "unique_rows": unique_rows,
            "duplicate_rows": duplicate_rows,
            "duplicate_rate": duplicate_rate
        }

        # 如果有重复，尝试找出重复最多的字段组合
        if duplicate_rows > 0:
            # 检查关键字段的重复情况
            key_fields = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(k in col_str for k in ['订单号', '商品编码', '商家编码', 'sku']):
                    key_fields.append(col)

            if key_fields:
                field_duplicates = {}
                for field in key_fields:
                    if field in df.columns:
                        total_vals = len(df[field])
                        unique_vals = len(df[field].dropna().unique())
                        dup_vals = total_vals - unique_vals
                        field_duplicates[field] = {
                            "total": total_vals,
                            "unique": unique_vals,
                            "duplicates": dup_vals,
                            "duplicate_rate": round(dup_vals / total_vals * 100, 2) if total_vals > 0 else 0
                        }
                report["field_duplicates"] = field_duplicates

        return report

    def safe_json_convert(self, obj):
        """安全的JSON转换，处理NaN和特殊值"""
        if isinstance(obj, (np.integer, np.floating)):
            if np.isnan(obj) or np.isinf(obj):
                return 0
            return float(obj)
        elif isinstance(obj, dict):
            return {key: self.safe_json_convert(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.safe_json_convert(item) for item in obj]
        elif pd.isna(obj):
            return None
        return obj

    def get_summary_statistics(self, processed_df: pd.DataFrame) -> Dict[str, Any]:
        if processed_df.empty:
            return {}

        shop_cols = [c for c in processed_df.columns if any(k in str(c).lower() for k in ['店铺', 'shop'])]
        total_cost = float(pd.to_numeric(processed_df.get('总成本', 0), errors='coerce').fillna(0).sum())
        total_revenue = float(pd.to_numeric(processed_df.get('销售收入', 0), errors='coerce').fillna(0).sum())
        total_profit = round(total_revenue - total_cost, 2)

        return self.safe_json_convert({
            'total_records': int(len(processed_df)),
            'total_shops': int(processed_df[shop_cols[0]].nunique()) if shop_cols else 0,
            'total_cost': total_cost,
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'avg_margin': float(pd.to_numeric(processed_df.get('毛利率', 0), errors='coerce').fillna(0)[pd.to_numeric(processed_df.get('销售收入', 0), errors='coerce').fillna(0) > 0].mean()) if total_revenue > 0 else 0.0
        })


    def analyze_by_shop(self, processed_df: pd.DataFrame) -> Dict[str, Any]:
        if processed_df.empty:
            return {}

        shop_cols = [c for c in processed_df.columns if any(k in str(c).lower() for k in ['店铺', 'shop'])]
        if not shop_cols:
            return {}
        shop_col = shop_cols[0]

        out = {}
        for shop in processed_df[shop_col].dropna().unique():
            sub = processed_df[processed_df[shop_col] == shop]
            total_cost = float(pd.to_numeric(sub.get('总成本', 0), errors='coerce').fillna(0).sum())
            total_rev = float(pd.to_numeric(sub.get('销售收入', 0), errors='coerce').fillna(0).sum())
            profit = round(total_rev - total_cost, 2)
            margin = float(pd.to_numeric(sub.get('毛利率', 0), errors='coerce').fillna(0)[pd.to_numeric(sub.get('销售收入', 0), errors='coerce').fillna(0) > 0].mean()) if total_rev > 0 else 0.0
            out[str(shop)] = self.safe_json_convert({
                'shop_name': str(shop),
                'total_orders': int(len(sub)),
                'total_cost': total_cost,
                'total_revenue': total_rev,
                'total_profit': profit,
                'avg_margin': margin
            })
        return out


    def process_data(self, filter_options: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        执行完整的数据处理流程

        包括数据清理、匹配、成本计算、去重和统计分析

        Args:
            filter_options: 过滤选项

        Returns:
            Tuple[pd.DataFrame, Dict[str, Any]]: 处理后的数据和分析结果
        """
        print("开始数据处理...")

        # 重置去重统计
        self.dedup_stats = {}

        cleaned_orders = self.clean_order_data(filter_options)
        if cleaned_orders.empty:
            return pd.DataFrame(), {}

        matched_data = self.match_products_with_orders(cleaned_orders)
        processed_data = self.calculate_costs_and_profits(matched_data)

        # ✅ 关键修复4：最终数据智能去重，基于关键业务字段避免重复
        if not processed_data.empty:
            before_final_dedup = len(processed_data)

            # 检测处理前的重复情况
            before_dedup_report = self.detect_duplicates(processed_data, "处理完成后、最终去重前")
            self.dedup_stats['before_final_dedup'] = before_dedup_report

            # 找到关键字段用于去重（订单号+商品编码+规格等）
            key_columns = []

            # 订单号
            order_cols = [c for c in processed_data.columns if any(k in str(c).lower() for k in ['订单号','订单编号','order'])]
            if order_cols:
                key_columns.append(order_cols[0])

            # 商品编码
            sku_cols = [c for c in processed_data.columns if any(k in str(c).lower() for k in ['商品编码','商家编码','sku','货号'])]
            if sku_cols:
                key_columns.append(sku_cols[0])

            # 规格名称（如果存在）
            spec_cols = [c for c in processed_data.columns if any(k in str(c).lower() for k in ['规格','spec','型号'])]
            if spec_cols:
                key_columns.append(spec_cols[0])

            # 如果找到了关键字段，基于这些字段去重
            if key_columns:
                processed_data = processed_data.drop_duplicates(subset=key_columns, keep='first').reset_index(drop=True)
                after_final_dedup = len(processed_data)
                if before_final_dedup != after_final_dedup:
                    print(f"⚠️ 最终业务去重: {before_final_dedup} -> {after_final_dedup} 行 (基于 {key_columns} 去除了 {before_final_dedup - after_final_dedup} 个重复业务记录)")

                # 检测最终去重后的情况
                after_dedup_report = self.detect_duplicates(processed_data, "最终去重后")
                self.dedup_stats['after_final_dedup'] = after_dedup_report
                self.dedup_stats['final_dedup_key_columns'] = key_columns

        # 统计：行数 + 订单数
        order_id_cols = [c for c in processed_data.columns if any(k in str(c).lower() for k in ['订单号','订单编号','order'])]
        order_id_col = order_id_cols[0] if order_id_cols else None
        cleaned_order_count = int(processed_data[order_id_col].nunique()) if order_id_col else 0

        analysis = {
            'summary': self.get_summary_statistics(processed_data),
            'shop_analysis': self.analyze_by_shop(processed_data),
            'processing_info': {
                'original_lines': len(self.order_df) if self.order_df is not None else 0,
                'cleaned_lines': len(cleaned_orders),
                'cleaned_orders': cleaned_order_count,  # ✅ 真正的"单数"
                'matched_lines': len(processed_data),
                'processed_time': datetime.now().isoformat()
            },
            'deduplication_stats': self.dedup_stats  # ✅ 添加去重统计信息
        }
        self.processed_data = processed_data
        print("数据处理完成!")
        return processed_data, analysis


    def export_processed_data(self, output_path: str = "processed_data.xlsx") -> bool:
        """导出处理后的数据"""
        if self.processed_data is None or self.processed_data.empty:
            return False

        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 主数据表
                self.processed_data.to_excel(writer, sheet_name='处理后数据', index=False)

            print(f"数据已导出到: {output_path}")
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False