"""
京东店铺数据处理器
实现商品编号匹配、成本计算、店铺筛选等功能
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class DataProcessor:
    def __init__(self, dataset_path: str = "../dataset"):
        self.dataset_path = dataset_path
        self.product_df = None
        self.order_df = None
        self.processed_data = None
        self._load_data()

    def _load_data(self):
        """加载Excel数据"""
        try:
            # 加载产品信息表
            product_file = f"{self.dataset_path}/产品信息表-总.xlsx"
            self.product_df = pd.read_excel(product_file)

            # 清理产品数据：移除标题行，重置索引
            self.product_df = self.product_df[self.product_df['商家编码'] != '商家编码'].reset_index(drop=True)

            # 加载订单数据
            order_file = f"{self.dataset_path}/订单9.14.xlsx"
            self.order_df = pd.read_excel(order_file)

            print(f"产品数据加载完成: {len(self.product_df)} 条记录")
            print(f"订单数据加载完成: {len(self.order_df)} 条记录")

        except Exception as e:
            print(f"数据加载错误: {e}")

    def clean_order_data(self, filter_options: Dict[str, Any] = None) -> pd.DataFrame:
        """
        清理订单数据
        - 过滤空单（订单标记为空）
        - 过滤已关闭订单
        - 过滤线下订单
        """
        if self.order_df is None:
            return pd.DataFrame()

        df = self.order_df.copy()

        # 过滤条件
        filters = []

        # 1. 过滤空单（订单标记为空的认为是正常订单）
        # 注意：订单标记为空是正常的，我们要过滤的是买家实付为空的订单
        filters.append(df['买家实付'].notna())

        # 2. 过滤已关闭的订单
        filters.append(df['线上订单状态'] != '关闭')
        filters.append(df['明细状态'] != '关闭')

        # 3. 过滤线下订单
        filters.append(df['线上订单状态'] != '[线下订单]')

        # 4. 过滤退款订单
        filters.append(~df['明细状态'].str.contains('退款', na=False))

        # 应用所有过滤条件
        final_filter = np.logical_and.reduce(filters)
        cleaned_df = df[final_filter].copy()

        # 店铺筛选
        if filter_options and 'selected_shops' in filter_options:
            selected_shops = filter_options['selected_shops']
            if selected_shops:
                cleaned_df = cleaned_df[cleaned_df['店铺名称'].isin(selected_shops)]

        print(f"原始订单: {len(df)}, 清理后: {len(cleaned_df)}")
        return cleaned_df

    def match_products_with_orders(self, order_df: pd.DataFrame) -> pd.DataFrame:
        """
        匹配产品信息和订单信息
        通过商品编码进行匹配
        """
        if self.product_df is None or order_df.empty:
            return pd.DataFrame()

        # 准备产品数据
        product_df = self.product_df.copy()

        # 清理并转换数据类型
        product_df['商家编码'] = product_df['商家编码'].astype(str).str.strip()
        order_df['商品编码'] = order_df['商品编码'].astype(str).str.strip()

        # 匹配逻辑：使用商品编码进行匹配
        matched_df = order_df.merge(
            product_df[['商家编码', '商品', 'SKU', '成本', '实际价格', '一口价']],
            left_on='商品编码',
            right_on='商家编码',
            how='left'
        )

        print(f"匹配成功: {len(matched_df[matched_df['商家编码'].notna()])} / {len(order_df)} 条订单")
        return matched_df

    def calculate_costs_and_profits(self, matched_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算成本和利润
        - 将买家实付处理为实际销售额
        - 使用产品表中的成本信息
        - 计算利润和毛利率
        """
        if matched_df.empty:
            return pd.DataFrame()

        df = matched_df.copy()

        # 数据类型转换
        def safe_convert_to_float(series):
            return pd.to_numeric(series, errors='coerce')

        df['买家实付'] = safe_convert_to_float(df['买家实付'])
        df['成本'] = safe_convert_to_float(df['成本'])
        df['实际价格'] = safe_convert_to_float(df['实际价格'])

        # 计算利润
        df['利润'] = df['买家实付'] - df['成本']

        # 计算毛利率
        df['毛利率'] = np.where(
            df['买家实付'] > 0,
            df['利润'] / df['买家实付'],
            0
        )

        # 添加处理标记
        df['数据处理时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return df

    def analyze_by_shop(self, processed_df: pd.DataFrame) -> Dict[str, Any]:
        """按店铺分析数据"""
        if processed_df.empty:
            return {}

        shop_analysis = {}

        for shop in processed_df['店铺名称'].unique():
            shop_data = processed_df[processed_df['店铺名称'] == shop]

            analysis = {
                'shop_name': shop,
                'total_orders': len(shop_data),
                'total_revenue': shop_data['买家实付'].sum(),
                'total_cost': shop_data['成本'].sum(),
                'total_profit': shop_data['利润'].sum(),
                'avg_profit_margin': shop_data['毛利率'].mean(),
                'top_products': shop_data.groupby('商品名称').agg({
                    '买家实付': 'sum',
                    '利润': 'sum',
                    '订单号': 'count'
                }).round(2).head().to_dict('index')
            }

            shop_analysis[shop] = analysis

        return shop_analysis

    def get_summary_statistics(self, processed_df: pd.DataFrame) -> Dict[str, Any]:
        """获取汇总统计信息"""
        if processed_df.empty:
            return {}

        summary = {
            'total_records': len(processed_df),
            'total_shops': processed_df['店铺名称'].nunique(),
            'total_products': processed_df['商品编码'].nunique(),
            'total_revenue': float(processed_df['买家实付'].sum()),
            'total_cost': float(processed_df['成本'].sum()),
            'total_profit': float(processed_df['利润'].sum()),
            'avg_profit_margin': float(processed_df['毛利率'].mean()),
            'date_range': {
                'start': processed_df.index.min(),
                'end': processed_df.index.max()
            },
            'shop_distribution': processed_df['店铺名称'].value_counts().head(10).to_dict()
        }

        return summary

    def get_available_shops(self) -> List[str]:
        """获取所有可用的店铺列表"""
        if self.order_df is None:
            return []

        return sorted(self.order_df['店铺名称'].unique().tolist())

    def process_data(self, filter_options: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        完整的数据处理流程
        返回: (处理后的数据, 分析结果)
        """
        print("开始数据处理...")

        # 1. 清理订单数据
        cleaned_orders = self.clean_order_data(filter_options)

        if cleaned_orders.empty:
            return pd.DataFrame(), {}

        # 2. 匹配产品信息
        matched_data = self.match_products_with_orders(cleaned_orders)

        # 3. 计算成本和利润
        processed_data = self.calculate_costs_and_profits(matched_data)

        # 4. 生成分析报告
        analysis = {
            'summary': self.get_summary_statistics(processed_data),
            'shop_analysis': self.analyze_by_shop(processed_data),
            'processing_info': {
                'original_orders': len(self.order_df) if self.order_df is not None else 0,
                'cleaned_orders': len(cleaned_orders),
                'matched_orders': len(processed_data[processed_data['商家编码'].notna()]),
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
                shop_summary = self.processed_data.groupby('店铺名称').agg({
                    '买家实付': 'sum',
                    '成本': 'sum',
                    '利润': 'sum',
                    '毛利率': 'mean',
                    '订单号': 'count'
                }).round(2)
                shop_summary.to_excel(writer, sheet_name='店铺汇总')

                # 产品汇总
                product_summary = self.processed_data.groupby(['商品名称', '商品编码']).agg({
                    '买家实付': 'sum',
                    '成本': 'sum',
                    '利润': 'sum',
                    '毛利率': 'mean',
                    '订单号': 'count'
                }).round(2)
                product_summary.to_excel(writer, sheet_name='产品汇总')

            print(f"数据已导出到: {output_path}")
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False

# 测试代码
if __name__ == "__main__":
    processor = DataProcessor()

    # 获取可用店铺
    shops = processor.get_available_shops()
    print(f"可用店铺数量: {len(shops)}")
    print("前10个店铺:", shops[:10])

    # 处理数据（选择前5个店铺作为示例）
    filter_options = {
        'selected_shops': shops[:5]  # 选择前5个店铺
    }

    processed_df, analysis = processor.process_data(filter_options)

    print("\n=== 处理结果摘要 ===")
    print(f"处理后记录数: {len(processed_df)}")
    if analysis.get('summary'):
        summary = analysis['summary']
        print(f"总收入: ¥{summary.get('total_revenue', 0):,.2f}")
        print(f"总成本: ¥{summary.get('total_cost', 0):,.2f}")
        print(f"总利润: ¥{summary.get('total_profit', 0):,.2f}")
        print(f"平均毛利率: {summary.get('avg_profit_margin', 0):.2%}")

    # 导出数据
    if not processed_df.empty:
        processor.export_processed_data()