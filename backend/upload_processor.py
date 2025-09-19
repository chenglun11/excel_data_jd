"""
文件上传数据处理器
支持上传Excel文件并进行数据处理
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os
import json

class UploadProcessor:
    def __init__(self):
        self.product_df = None
        self.order_df = None
        self.processed_data = None

    def load_from_files(self, product_file_path: str, order_file_path: str):
        """从上传的文件加载数据"""
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

    # def clean_order_data(self, filter_options: Dict[str, Any] = None) -> pd.DataFrame:
    #     """清理订单数据"""
    #     if self.order_df is None:
    #         return pd.DataFrame()

    #     df = self.order_df.copy()

    #     # 过滤条件
    #     filters = []

    #     # 1. 查找并过滤订单标记为空单的记录
    #     order_mark_columns = []
    #     for col in df.columns:
    #         if any(keyword in str(col).lower() for keyword in ['订单标记', '标记', 'mark']):
    #             order_mark_columns.append(col)

    #     if order_mark_columns:
    #         order_mark_col = order_mark_columns[0]
    #         # 过滤掉标记为空单的订单（注意：空值(NaN)是正常的，我们要过滤的是明确标记为"空单"的）
    #         filters.append(df[order_mark_col] != '空单')
    #         filters.append(~df[order_mark_col].str.contains('空单', na=False))
    #         print(f"发现订单标记列: {order_mark_col}")
    #     else:
    #         print("警告：未找到订单标记列")

    #     # 2. 查找买家实付列（可能有不同的名称）
    #     amount_columns = []
    #     for col in df.columns:
    #         if any(keyword in str(col).lower() for keyword in ['买家实付', '实付', '金额', '付款']):
    #             amount_columns.append(col)

    #     # 使用第一个找到的金额列，确保有实际付款
    #     if amount_columns:
    #         amount_col = amount_columns[0]
    #         # 过滤掉金额为空或者为0的订单
    #         filters.append(df[amount_col].notna())
    #         filters.append(df[amount_col] > 0)
    #         print(f"发现买家实付列: {amount_col}")
    #     else:
    #         print("警告：未找到买家实付列")

    #     # 3. 查找订单状态列
    #     status_columns = []
    #     for col in df.columns:
    #         if any(keyword in str(col).lower() for keyword in ['状态', 'status']):
    #             status_columns.append(col)

    #     # 过滤已关闭的订单、退款订单、线下订单
    #     for status_col in status_columns:
    #         filters.append(df[status_col] != '关闭')
    #         filters.append(~df[status_col].str.contains('退款', na=False))
    #         filters.append(df[status_col] != '[线下订单]')
    #         print(f"发现状态列: {status_col}")

    #     # 应用过滤条件
    #     if filters:
    #         final_filter = np.logical_and.reduce(filters)
    #         cleaned_df = df[final_filter].copy()
    #     else:
    #         cleaned_df = df.copy()

    #     # 店铺筛选
    #     if filter_options and 'selected_shops' in filter_options:
    #         selected_shops = filter_options['selected_shops']
    #         if selected_shops:
    #             shop_columns = []
    #             for col in df.columns:
    #                 if any(keyword in str(col).lower() for keyword in ['店铺', 'shop']):
    #                     shop_columns.append(col)

    #             if shop_columns:
    #                 shop_col = shop_columns[0]
    #                 cleaned_df = cleaned_df[cleaned_df[shop_col].isin(selected_shops)]

    #     print(f"原始订单: {len(df)}, 清理后: {len(cleaned_df)} (已排除空单、退款、关闭等无效订单)")
    #     return cleaned_df

    def clean_order_data(self, filter_options: Dict[str, Any] = None) -> pd.DataFrame:
        """清理订单数据（按订单级过滤金额与状态；保留订单内所有行，包括0元赠品/返现行）"""
        if self.order_df is None:
            return pd.DataFrame()

        df = self.order_df.copy()
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
        """匹配产品信息和订单信息"""
        if self.product_df is None or order_df.empty:
            return pd.DataFrame()

        # 打印所有列名用于调试
        print(f"产品信息表列名: {list(self.product_df.columns)}")
        print(f"订单信息表列名: {list(order_df.columns)}")

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

        print(f"找到的产品编码列: {product_sku_cols}")
        print(f"找到的订单编码列: {order_sku_cols}")

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

                # 打印样本数据用于调试
                print(f"产品编码样本: {product_df[product_col].head(5).tolist()}")
                print(f"订单编码样本: {temp_order_df[order_col].head(5).tolist()}")

                # 匹配逻辑
                matched_df = temp_order_df.merge(
                    product_df,
                    left_on=order_col,
                    right_on=product_col,
                    how='left',
                    suffixes=('_order', '_product')
                )

                matched_count = len(matched_df[matched_df[product_col].notna()])
                print(f"匹配成功: {matched_count} / {len(temp_order_df)} 条订单")

                if matched_count > best_match_count:
                    best_match_count = matched_count
                    best_matched_df = matched_df
                    print(f"更新最佳匹配: {matched_count} 条")

        if best_matched_df is not None and best_match_count > 0:
            print(f"\n最终使用最佳匹配结果: {best_match_count} / {len(order_df)} 条订单")
            return best_matched_df
        else:
            print("\n警告：所有匹配尝试都失败！")
            # 返回原始订单数据，但添加标记
            order_df = order_df.copy()
            order_df['匹配状态'] = '匹配失败'
            return order_df

    # def calculate_costs_and_profits(self, matched_df: pd.DataFrame) -> pd.DataFrame:
    #     """处理成本显示（只使用产品信息表中的成本）"""
    #     if matched_df.empty:
    #         return pd.DataFrame()

    #     df = matched_df.copy()

    #     # 只查找产品信息表的成本列
    #     cost_cols = []
    #     for col in df.columns:
    #         col_str = str(col).lower()
    #         if any(keyword in col_str for keyword in ['成本', 'cost']) and not any(exclude in col_str for exclude in ['买家', '实付', '金额']):
    #             cost_cols.append(col)

    #     if cost_cols:
    #         cost_col = cost_cols[0]
    #         df[cost_col] = pd.to_numeric(df[cost_col], errors='coerce')
    #         matched_rows = df[cost_col].notna().sum()

    #         if matched_rows > 0:
    #             # 只使用匹配成功且有成本数据的订单
    #             df['实际成本'] = df[cost_col]
    #             print(f"使用产品信息表成本: {cost_col}")
    #             print(f"匹配到成本的订单: {matched_rows} / {len(df)}")
    #             print(f"成本样本: {df[df[cost_col].notna()][cost_col].head(5).tolist()}")

    #             # 对于没有匹配到成本的订单，设置成本为0（不能用买家实付）
    #             no_cost_rows = len(df) - matched_rows
    #             if no_cost_rows > 0:
    #                 print(f"警告: {no_cost_rows} 条订单未匹配到产品成本，这些订单的成本将为0")
    #         else:
    #             print("错误: 产品信息表成本列无有效数据")
    #             df['实际成本'] = 0
    #     else:
    #         print("错误: 未找到产品信息表成本列")
    #         df['实际成本'] = 0

    #     # 清理NaN值和无效值
    #     df = df.fillna(0)
    #     df = df.replace([np.inf, -np.inf], 0)

    #     # 添加处理标记
    #     df['数据处理时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    #     return df
    def calculate_costs_and_profits(self, matched_df: pd.DataFrame) -> pd.DataFrame:
        """总成本只来自【产品表】；优先产品侧(_product)列；数量正确时成本也会正确。"""
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
            print(f"使用产品侧成本列: {unit_cost_col}")
        else:
            df['单位成本'] = 0.0
            print("⚠️ 未在产品侧找到成本列（如 成本/进货/采购/cost），单位成本=0")

        # —— 数量（优先这些名字）
        qty_candidates = [c for c in df.columns if any(k in str(c).lower() for k in
                            ['数量','件数','qty','num','购买数量','下单数量','宝贝总数量'])]
        if qty_candidates:
            qty_col = qty_candidates[0]
            df['数量'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1)
            print(f"使用数量列: {qty_col}")
        else:
            df['数量'] = 1
            print("ℹ️ 未找到数量列，默认数量=1")

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

        # —— 诊断：哪些行的成本=0（很可能是没匹配到产品或产品成本空）
        zero_cost_rows = df[df['单位成本'] == 0]
        if not zero_cost_rows.empty:
            sample = zero_cost_rows.head(5)
            # 尝试找出被用于匹配的订单/产品编码列（打印看看）
            order_code_cols = [c for c in df.columns if any(k in str(c).lower() for k in ['商品编码','商家编码','sku','货号','【线上】商品编码'])]
            cols_to_show = ['订单号'] + order_code_cols + ['商品名称','规格名称'] if '订单号' in df.columns else order_code_cols + ['商品名称','规格名称']
            print("⚠️ 单位成本=0 的样例（前5行）:")
            print(sample[ [c for c in cols_to_show if c in sample.columns] ].to_string(index=False))

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

    # def analyze_by_shop(self, processed_df: pd.DataFrame) -> Dict[str, Any]:
    #     """按店铺分析数据"""
    #     if processed_df.empty:
    #         return {}

    #     shop_columns = []
    #     for col in processed_df.columns:
    #         if any(keyword in str(col).lower() for keyword in ['店铺', 'shop']):
    #             shop_columns.append(col)

    #     if not shop_columns:
    #         return {}

    #     shop_col = shop_columns[0]
    #     shop_analysis = {}

    #     for shop in processed_df[shop_col].unique():
    #         if pd.isna(shop):
    #             continue

    #         shop_data = processed_df[processed_df[shop_col] == shop]

    #         analysis = {
    #             'shop_name': str(shop),
    #             'total_orders': int(len(shop_data)),
    #             'total_cost': 0
    #         }

    #         # 直接使用买家实付列作为成本数据源
    #         cost_cols = []
    #         amount_cols = []  # 买家实付列实际存储的是成本

    #         for col in shop_data.columns:
    #             col_str = str(col).lower()
    #             if any(keyword in col_str for keyword in ['买家实付', '实付']):
    #                 amount_cols.append(col)
    #             elif any(keyword in col_str for keyword in ['实际成本']):  # 我们创建的成本列
    #                 cost_cols.append(col)

    #         # 优先使用我们创建的"实际成本"列，否则直接使用买家实付列
    #         if cost_cols:
    #             cost_col = cost_cols[0]
    #             analysis['total_cost'] = float(shop_data[cost_col].sum()) if not shop_data[cost_col].isna().all() else 0
    #         elif amount_cols:
    #             cost_col = amount_cols[0]
    #             analysis['total_cost'] = float(shop_data[cost_col].sum()) if not shop_data[cost_col].isna().all() else 0

    #         # 确保所有值都是JSON兼容的
    #         analysis = self.safe_json_convert(analysis)
    #         shop_analysis[str(shop)] = analysis

    #     return shop_analysis

    # def get_summary_statistics(self, processed_df: pd.DataFrame) -> Dict[str, Any]:
    #     """获取汇总统计信息"""
    #     if processed_df.empty:
    #         return {}

    #     # 查找相关列
    #     shop_columns = []
    #     for col in processed_df.columns:
    #         col_str = str(col).lower()
    #         if any(keyword in col_str for keyword in ['店铺', 'shop']):
    #             shop_columns.append(col)

    #     summary = {
    #         'total_records': int(len(processed_df)),
    #         'total_shops': int(processed_df[shop_columns[0]].nunique()) if shop_columns else 0,
    #         'total_cost': 0
    #     }

    #     # 只使用我们创建的"实际成本"列（来自产品信息表）
    #     cost_columns = []
    #     for col in processed_df.columns:
    #         if col == '实际成本':
    #             cost_columns.append(col)

    #     if cost_columns:
    #         cost_col = cost_columns[0]
    #         summary['total_cost'] = float(processed_df[cost_col].sum()) if not processed_df[cost_col].isna().all() else 0
    #         print(f"统计总成本: {summary['total_cost']}")
    #     else:
    #         print("警告：未找到实际成本列")
    #         summary['total_cost'] = 0

    #     # 确保所有值都是JSON兼容的
    #     summary = self.safe_json_convert(summary)
    #     return summary

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
        print("开始数据处理...")

        cleaned_orders = self.clean_order_data(filter_options)
        if cleaned_orders.empty:
            return pd.DataFrame(), {}

        matched_data = self.match_products_with_orders(cleaned_orders)
        processed_data = self.calculate_costs_and_profits(matched_data)

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
                'cleaned_orders': cleaned_order_count,  # ✅ 真正的“单数”
                'matched_lines': len(processed_data),
                'processed_time': datetime.now().isoformat()
            }
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

                # 店铺汇总
                shop_columns = []
                amount_columns = []
                for col in self.processed_data.columns:
                    col_str = str(col).lower()
                    if any(keyword in col_str for keyword in ['店铺', 'shop']):
                        shop_columns.append(col)
                    elif any(keyword in col_str for keyword in ['买家实付', '实付']):
                        amount_columns.append(col)

                # if shop_columns:
                #     shop_col = shop_columns[0]
                #     agg_dict = {}

                #     if amount_columns:
                #         agg_dict[amount_columns[0]] = 'sum'

                #     if '总成本' in self.processed_data.columns:
                #         agg_dict['总成本'] = 'sum'

                #     if '利润' in self.processed_data.columns:
                #         agg_dict['利润'] = 'sum'

                #     if '毛利率' in self.processed_data.columns:
                #         agg_dict['毛利率'] = 'mean'

                #     if agg_dict:
                #         shop_summary = self.processed_data.groupby(shop_col).agg(agg_dict).round(2)
                #         shop_summary.to_excel(writer, sheet_name='店铺汇总')


            print(f"数据已导出到: {output_path}")
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False