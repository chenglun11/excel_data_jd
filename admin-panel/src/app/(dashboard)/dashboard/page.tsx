import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Package, ShoppingCart, BarChart3, TrendingUp } from "lucide-react"

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">仪表板</h1>
        <p className="text-muted-foreground">欢迎使用京东店铺数据管理系统</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总产品数</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,234</div>
            <p className="text-xs text-muted-foreground">
              +10.1% 与上月相比
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总订单数</CardTitle>
            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">567</div>
            <p className="text-xs text-muted-foreground">
              +5.4% 与上月相比
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总销售额</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">¥89,123</div>
            <p className="text-xs text-muted-foreground">
              +12.3% 与上月相比
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">增长率</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">+8.2%</div>
            <p className="text-xs text-muted-foreground">
              相比上个季度
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>数据文件概览</CardTitle>
            <CardDescription>当前可处理的Excel文件</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span>产品信息表-总.xlsx</span>
              <Badge variant="secondary">9.5MB</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span>店铺日账单9月.xlsx</span>
              <Badge variant="secondary">64KB</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span>订单9.14.xlsx</span>
              <Badge variant="secondary">375KB</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>快速操作</CardTitle>
            <CardDescription>常用的数据处理操作</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg cursor-pointer hover:bg-accent">
                <Package className="h-8 w-8 mb-2 text-blue-500" />
                <h3 className="font-medium">产品分析</h3>
                <p className="text-sm text-muted-foreground">分析产品数据</p>
              </div>
              <div className="p-4 border rounded-lg cursor-pointer hover:bg-accent">
                <ShoppingCart className="h-8 w-8 mb-2 text-green-500" />
                <h3 className="font-medium">订单报告</h3>
                <p className="text-sm text-muted-foreground">生成订单报告</p>
              </div>
              <div className="p-4 border rounded-lg cursor-pointer hover:bg-accent">
                <BarChart3 className="h-8 w-8 mb-2 text-purple-500" />
                <h3 className="font-medium">账单分析</h3>
                <p className="text-sm text-muted-foreground">财务数据分析</p>
              </div>
              <div className="p-4 border rounded-lg cursor-pointer hover:bg-accent">
                <TrendingUp className="h-8 w-8 mb-2 text-orange-500" />
                <h3 className="font-medium">趋势分析</h3>
                <p className="text-sm text-muted-foreground">数据趋势预测</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}