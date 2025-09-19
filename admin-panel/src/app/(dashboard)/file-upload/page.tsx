"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"
// import {
//   Alert,
//   AlertDescription,
//   AlertTitle,
// } from "@/components/ui/alert"
import {
  Upload,
  FileSpreadsheet,
  Play,
  Download,
  Search,
  CheckCircle,
  AlertCircle,
  Loader2,
  Trash2,
  Store
} from "lucide-react"
import { apiRequest } from "@/lib/auth"

interface UploadedFiles {
  product_file: string
  order_file: string
}

interface FileAnalysis {
  product_file?: {
    columns: string[]
    sample_data: Record<string, unknown>[]
    total_columns: number
  }
  order_file?: {
    columns: string[]
    sample_data: Record<string, unknown>[]
    total_columns: number
  }
  error?: string
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

interface Shop {
  name: string
  selected: boolean
}

export default function FileUploadPage() {
  const [productFile, setProductFile] = useState<File | null>(null)
  const [orderFile, setOrderFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFiles | null>(null)
  const [, setFileAnalysis] = useState<FileAnalysis | null>(null)
  const [shops, setShops] = useState<Shop[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [result, setResult] = useState<ProcessingResult | null>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>, type: 'product' | 'order') => {
    const file = e.target.files?.[0]
    if (file) {
      if (type === 'product') {
        setProductFile(file)
      } else {
        setOrderFile(file)
      }
    }
  }

  const uploadFiles = async () => {
    if (!productFile || !orderFile) {
      alert("请选择产品信息表和订单信息表")
      return
    }

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('product_file', productFile)
      formData.append('order_file', orderFile)

      const response = await fetch('http://apis.lchnan.cn/upload/files', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      })

      const data = await response.json()

      if (data.success) {
        setUploadedFiles(data.files)
        setFileAnalysis(data.analysis)

        // 加载店铺列表
        await loadShops()

        alert("文件上传成功！")
      } else {
        alert("上传失败: " + data.detail)
      }
    } catch (error) {
      console.error("上传错误:", error)
      alert("上传失败")
    } finally {
      setUploading(false)
    }
  }

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
    if (!uploadedFiles) {
      alert("请先上传文件")
      return
    }

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
      alert("处理失败")
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
        // 触发下载
        const downloadUrl = `http://apis.lchnan.cn${data.download_url}`
        window.open(downloadUrl, '_blank')
        alert(`数据导出成功！文件名: ${data.filename}`)
      }
    } catch (error) {
      console.error("导出失败:", error)
      alert("导出失败")
    }
  }

  const clearFiles = async () => {
    try {
      const response = await fetch('http://apis.lchnan.cn/files/clear', {
        method: 'DELETE',
        credentials: 'include'
      })

      if (response.ok) {
        setUploadedFiles(null)
        setFileAnalysis(null)
        setShops([])
        setResult(null)
        setProductFile(null)
        setOrderFile(null)
        alert("文件清理完成")
      }
    } catch (error) {
      console.error("清理失败:", error)
      alert("清理失败")
    }
  }

  const filteredShops = getFilteredShops()
  const selectedCount = getSelectedShops().length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">文件上传处理</h1>
        <p className="text-muted-foreground">
          上传产品信息表和订单表Excel文件进行数据处理分析
        </p>
      </div>

      {/* 文件上传区域 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            文件上传
          </CardTitle>
          <CardDescription>
            请上传产品信息表和订单信息表的Excel文件
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 产品信息表上传 */}
            <div className="space-y-2">
              <Label htmlFor="product-file">产品信息表 (.xlsx/.xls)</Label>
              <div className="flex items-center space-x-2">
                <Input
                  id="product-file"
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => handleFileSelect(e, 'product')}
                  className="file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                <FileSpreadsheet className="h-5 w-5 text-blue-500" />
              </div>
              {productFile && (
                <p className="text-sm text-green-600">
                  已选择: {productFile.name} ({(productFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>

            {/* 订单信息表上传 */}
            <div className="space-y-2">
              <Label htmlFor="order-file">订单信息表 (.xlsx/.xls)</Label>
              <div className="flex items-center space-x-2">
                <Input
                  id="order-file"
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => handleFileSelect(e, 'order')}
                  className="file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
                />
                <FileSpreadsheet className="h-5 w-5 text-green-500" />
              </div>
              {orderFile && (
                <p className="text-sm text-green-600">
                  已选择: {orderFile.name} ({(orderFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Button
              onClick={uploadFiles}
              disabled={!productFile || !orderFile || uploading}
              className="flex-1"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  上传中...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  上传文件
                </>
              )}
            </Button>

            {uploadedFiles && (
              <>
                <Button variant="outline" onClick={clearFiles}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  清理文件
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>


      {/* 处理控制和结果展示 */}
      {uploadedFiles && shops.length > 0 && (
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
              <div className="max-h-64 overflow-y-auto space-y-2">
                {filteredShops.map((shop) => (
                  <div key={shop.name} className="flex items-center space-x-2">
                    <Checkbox
                      checked={shop.selected}
                      onCheckedChange={() => toggleShop(shop.name)}
                    />
                    <Label className="text-sm leading-relaxed cursor-pointer" onClick={() => toggleShop(shop.name)}>
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
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
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
              <CardTitle>处理结果</CardTitle>
            </CardHeader>
            <CardContent>
              {!result ? (
                <div className="text-center py-12 text-muted-foreground">
                  <FileSpreadsheet className="h-12 w-12 mx-auto mb-4 opacity-50" />
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
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="text-center p-6 border rounded-lg">
                          <div className="text-3xl font-bold text-blue-600">
                            {(result.analysis.summary.total_records as number) || 0}
                          </div>
                          <div className="text-sm text-muted-foreground">订单数</div>
                        </div>
                        <div className="text-center p-6 border rounded-lg bg-orange-50">
                          <div className="text-3xl font-bold text-orange-600">
                            ¥{((result.analysis.summary.total_cost as number) || 0).toLocaleString()}
                          </div>
                          <div className="text-sm text-muted-foreground font-medium">总成本</div>
                        </div>
                      </div>

                      {/* 数据表格预览 */}
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
                                  {/* 显示重要列：店铺、商品编码、成本、订单标记 */}
                                  {['店铺', '商品编码', '商家编码', '成本', '买家实付', '订单标记'].map((priorityCol, index) => {
                                    const foundCol = result.data.columns.find(col =>
                                      col.includes(priorityCol) || col.toLowerCase().includes(priorityCol.toLowerCase())
                                    )
                                    if (foundCol) {
                                      return <TableHead key={index}>{foundCol}</TableHead>
                                    }
                                    return null
                                  }).filter(Boolean)}
                                  {/* 如果还有空间，显示其他列 */}
                                  {result.data.columns.filter(col =>
                                    !['店铺', '商品编码', '商家编码', '成本', '买家实付', '订单标记'].some(priority =>
                                      col.includes(priority) || col.toLowerCase().includes(priority.toLowerCase())
                                    )
                                  ).slice(0, 2).map((col, index) => (
                                    <TableHead key={`other-${index}`}>{col}</TableHead>
                                  ))}
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {result.data.records.slice(0, 10).map((record, index) => (
                                  <TableRow key={index}>
                                    {/* 显示对应的数据 */}
                                    {['店铺', '商品编码', '商家编码', '成本', '买家实付', '订单标记'].map((priorityCol, colIndex) => {
                                      const foundCol = result.data.columns.find(col =>
                                        col.includes(priorityCol) || col.toLowerCase().includes(priorityCol.toLowerCase())
                                      )
                                      if (foundCol) {
                                        const value = record[foundCol]
                                        return (
                                          <TableCell key={colIndex} className="max-w-[150px] truncate">
                                            {typeof value === 'number' && (foundCol.includes('金额') || foundCol.includes('成本') || foundCol.includes('利润'))
                                              ? `¥${value.toFixed(2)}`
                                              : typeof value === 'number' && foundCol.includes('毛利率')
                                              ? `${(value * 100).toFixed(1)}%`
                                              : String(value || '')
                                            }
                                          </TableCell>
                                        )
                                      }
                                      return null
                                    }).filter(Boolean)}
                                    {/* 其他列 */}
                                    {result.data.columns.filter(col =>
                                      !['店铺', '商品编码', '商家编码', '成本', '买家实付', '订单标记'].some(priority =>
                                        col.includes(priority) || col.toLowerCase().includes(priority.toLowerCase())
                                      )
                                    ).slice(0, 2).map((col, colIndex) => {
                                      const value = record[col]
                                      return (
                                        <TableCell key={`other-${colIndex}`} className="max-w-[150px] truncate">
                                          {typeof value === 'number' && (col.includes('金额') || col.includes('成本') || col.includes('利润'))
                                            ? `¥${value.toFixed(2)}`
                                            : typeof value === 'number' && col.includes('毛利率')
                                            ? `${(value * 100).toFixed(1)}%`
                                            : String(value || '')
                                          }
                                        </TableCell>
                                      )
                                    })}
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
      )}
    </div>
  )
}