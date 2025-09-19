"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"
import {
  Play,
  Download,
  Search,
  TrendingUp,
  Package,
  Store,
  AlertCircle,
  CheckCircle
} from "lucide-react"
import { apiRequest } from "@/lib/auth"

interface Shop {
  name: string
  selected: boolean
}

interface ProcessingResult {
  success: boolean
  message: string
  data: {
    records: Record<string, unknown>[]
    total_records: number
    columns: string[]
  }
  analysis: {
    summary: Record<string, unknown>
    shop_analysis: Record<string, unknown>
    processing_info: Record<string, unknown>
  }
}

export default function DataProcessingPage() {
  const [shops, setShops] = useState<Shop[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  // const [showFilters, setShowFilters] = useState(false)

  // 加载店铺列表
  useEffect(() => {
    loadShops()
  }, [])

  const loadShops = async () => {
    try {
      const response = await apiRequest("/data/shops")
      const data = await response.json()

      setShops(data.shops.map((shop: string) => ({
        name: shop,
        selected: false
      })))
    } catch (error) {
      console.error("加载店铺失败:", error)
    }
  }

  const toggleShop = (shopName: string) => {
    setShops(prev => prev.map(shop =>
      shop.name === shopName
        ? { ...shop, selected: !shop.selected }
        : shop
    ))
  }

  const selectAllShops = () => {
    const filteredShops = getFilteredShops()
    const allSelected = filteredShops.every(shop => shop.selected)

    setShops(prev => prev.map(shop =>
      filteredShops.includes(shop)
        ? { ...shop, selected: !allSelected }
        : shop
    ))
  }

  const getFilteredShops = () => {
    return shops.filter(shop =>
      shop.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }

  const getSelectedShops = () => {
    return shops.filter(shop => shop.selected)
  }

  const processData = async () => {
    setProcessing(true)
    try {
      const selectedShops = getSelectedShops().map(shop => shop.name)

      const response = await apiRequest("/data/process", {
        method: "POST",
        body: JSON.stringify({
          selected_shops: selectedShops.length > 0 ? selectedShops : null,
          include_closed_orders: false,
          include_offline_orders: false
        })
      })

      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error("数据处理失败:", error)
    } finally {
      setProcessing(false)
    }
  }

  const exportData = async () => {
    try {
      const selectedShops = getSelectedShops().map(shop => shop.name)

      const response = await apiRequest("/data/export", {
        method: "POST",
        body: JSON.stringify({
          selected_shops: selectedShops.length > 0 ? selectedShops : null,
          include_closed_orders: false,
          include_offline_orders: false
        })
      })

      const data = await response.json()
      if (data.success) {
        alert(`数据导出成功！文件名: ${data.filename}`)
      }
    } catch (error) {
      console.error("导出失败:", error)
    }
  }

  const filteredShops = getFilteredShops()
  const selectedCount = getSelectedShops().length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">数据处理</h1>
        <p className="text-muted-foreground">
          处理京东店铺数据，匹配商品信息并计算成本利润
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 店铺筛选面板 */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Store className="h-5 w-5" />
              店铺筛选
            </CardTitle>
            <CardDescription>
              选择需要处理的店铺数据
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 搜索框 */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索店铺..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* 全选按钮 */}
            <div className="flex items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                onClick={selectAllShops}
              >
                {filteredShops.every(shop => shop.selected) ? "取消全选" : "全选"}
              </Button>
              <Badge variant="secondary">
                已选择 {selectedCount} / {shops.length}
              </Badge>
            </div>

            {/* 店铺列表 */}
            <div className="max-h-96 overflow-y-auto space-y-2">
              {filteredShops.map((shop) => (
                <div key={shop.name} className="flex items-center space-x-2">
                  <Checkbox
                    checked={shop.selected}
                    onCheckedChange={() => toggleShop(shop.name)}
                  />
                  <Label className="text-sm leading-relaxed">
                    {shop.name}
                  </Label>
                </div>
              ))}
            </div>

            <Separator />

            {/* 处理按钮 */}
            <div className="space-y-2">
              <Button
                className="w-full"
                onClick={processData}
                disabled={processing}
              >
                {processing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    处理中...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    开始处理
                  </>
                )}
              </Button>

              {result && result.success && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={exportData}
                >
                  <Download className="h-4 w-4 mr-2" />
                  导出数据
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 结果显示面板 */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              处理结果
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!result ? (
              <div className="text-center py-12 text-muted-foreground">
                <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>请选择店铺并点击&quot;开始处理&quot;</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* 处理状态 */}
                <div className="flex items-center gap-2">
                  {result.success ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  <span className={result.success ? "text-green-700" : "text-red-700"}>
                    {result.message}
                  </span>
                </div>

                {result.success && result.analysis?.summary && (
                  <>
                    {/* 汇总统计 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-4 border rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                          {(result.analysis.summary.total_records as number) || 0}
                        </div>
                        <div className="text-sm text-muted-foreground">订单数</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          ¥{((result.analysis.summary.total_revenue as number) || 0).toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">总收入</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="text-2xl font-bold text-orange-600">
                          ¥{((result.analysis.summary.total_cost as number) || 0).toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">总成本</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          {(((result.analysis.summary.avg_profit_margin as number) || 0) * 100).toFixed(1)}%
                        </div>
                        <div className="text-sm text-muted-foreground">平均毛利率</div>
                      </div>
                    </div>

                    {/* 数据表格 */}
                    {result.data.records.length > 0 && (
                      <div className="border rounded-lg">
                        <div className="p-4 border-b">
                          <h3 className="font-medium">
                            处理后数据预览 (前10条)
                          </h3>
                        </div>
                        <div className="overflow-x-auto">
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>店铺名称</TableHead>
                                <TableHead>商品名称</TableHead>
                                <TableHead>商品编码</TableHead>
                                <TableHead>买家实付</TableHead>
                                <TableHead>成本</TableHead>
                                <TableHead>利润</TableHead>
                                <TableHead>毛利率</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {result.data.records.slice(0, 10).map((record, index) => (
                                <TableRow key={index}>
                                  <TableCell className="max-w-[200px] truncate">
                                    {String(record.店铺名称 || '')}
                                  </TableCell>
                                  <TableCell className="max-w-[150px] truncate">
                                    {String(record.商品名称 || '')}
                                  </TableCell>
                                  <TableCell>{String(record.商品编码 || '')}</TableCell>
                                  <TableCell>¥{((record.买家实付 as number) || 0).toFixed(2)}</TableCell>
                                  <TableCell>¥{((record.成本 as number) || 0).toFixed(2)}</TableCell>
                                  <TableCell>¥{((record.利润 as number) || 0).toFixed(2)}</TableCell>
                                  <TableCell>
                                    {(((record.毛利率 as number) || 0) * 100).toFixed(1)}%
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}