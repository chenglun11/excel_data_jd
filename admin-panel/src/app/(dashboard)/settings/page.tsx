"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import {
  Settings,
  Server,
  Database,
  Palette,
  Download,
  Save,
  RotateCcw,
  CheckCircle,
  Wifi,
  WifiOff
} from "lucide-react"
import { useConfig, DEFAULT_CONFIG } from "@/lib/config"
import { debugApi } from "@/lib/debug"
import { uploadDiagnostic, type DiagnosticResult } from "@/lib/upload-diagnostic"
import { corsDetector, type CorsTestResult } from "@/lib/cors-detector"
import { devCorsHelper } from "@/lib/dev-cors-helper"
import { devDebug } from "@/lib/dev-debug"
import { noAuthTest } from "@/lib/no-auth-test"

export default function SettingsPage() {
  const { config, updateApiConfig, updateProcessingConfig, updateUiConfig, updateExportConfig, resetConfig } = useConfig()
  const [saved, setSaved] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [diagnosticResults, setDiagnosticResults] = useState<DiagnosticResult[]>([])
  const [showDiagnostic, setShowDiagnostic] = useState(false)
  const [corsResults, setCorsResults] = useState<CorsTestResult[]>([])
  const [showCors, setShowCors] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleReset = () => {
    resetConfig()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const testConnection = async () => {
    setTesting(true)
    setTestResult(null)

    try {
      const result = await debugApi.testConnection()
      setTestResult(result)
      debugApi.logConfig()
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : '测试失败'
      })
    } finally {
      setTesting(false)
    }
  }

  const runDiagnostic = async () => {
    setTesting(true)
    setDiagnosticResults([])
    setShowDiagnostic(true)

    try {
      const results = await uploadDiagnostic.runFullDiagnostic()
      setDiagnosticResults(results)
    } catch (error) {
      setDiagnosticResults([{
        success: false,
        step: '诊断失败',
        message: error instanceof Error ? error.message : '未知错误'
      }])
    } finally {
      setTesting(false)
    }
  }

  const testCors = async () => {
    setTesting(true)
    setCorsResults([])
    setShowCors(true)

    try {
      const results = await corsDetector.detectCorsIssues()
      setCorsResults(results)
    } catch (error) {
      setCorsResults([{
        step: 'CORS 检测失败',
        success: false,
        message: error instanceof Error ? error.message : '未知错误'
      }])
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">系统设置</h1>
        <p className="text-muted-foreground">
          配置应用程序的各项参数和行为
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API 配置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              API 配置
            </CardTitle>
            <CardDescription>
              配置后端 API 服务器连接参数
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="baseUrl">API 基础地址</Label>
              <Input
                id="baseUrl"
                value={config.api.baseUrl}
                onChange={(e) => updateApiConfig({ baseUrl: e.target.value })}
                placeholder="http://localhost:6532"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="timeout">请求超时时间 (毫秒)</Label>
              <Input
                id="timeout"
                type="number"
                value={config.api.timeout}
                onChange={(e) => updateApiConfig({ timeout: parseInt(e.target.value) || 30000 })}
                placeholder="30000"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>包含凭据</Label>
                <p className="text-sm text-muted-foreground">
                  在 API 请求中包含认证凭据
                </p>
              </div>
              <Switch
                checked={config.api.credentials}
                onCheckedChange={(checked) => updateApiConfig({ credentials: checked })}
              />
            </div>

            <Separator />

            {/* 连接测试 */}
            <div className="space-y-2">
              <div className="grid grid-cols-3 gap-2">
                <Button
                  variant="outline"
                  onClick={testConnection}
                  disabled={testing}
                  size="sm"
                >
                  {testing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 mr-2" />
                      测试中...
                    </>
                  ) : (
                    <>
                      <Wifi className="h-4 w-4 mr-2" />
                      快速测试
                    </>
                  )}
                </Button>

                <Button
                  variant="outline"
                  onClick={testCors}
                  disabled={testing}
                  size="sm"
                >
                  {testing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 mr-2" />
                      检测中...
                    </>
                  ) : (
                    <>
                      <WifiOff className="h-4 w-4 mr-2" />
                      CORS检测
                    </>
                  )}
                </Button>

                <Button
                  variant="outline"
                  onClick={runDiagnostic}
                  disabled={testing}
                  size="sm"
                >
                  {testing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 mr-2" />
                      诊断中...
                    </>
                  ) : (
                    <>
                      <Settings className="h-4 w-4 mr-2" />
                      完整诊断
                    </>
                  )}
                </Button>
              </div>

              {testResult && (
                <div className={`flex items-center gap-2 p-3 rounded-lg ${
                  testResult.success
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}>
                  {testResult.success ? (
                    <Wifi className="h-4 w-4" />
                  ) : (
                    <WifiOff className="h-4 w-4" />
                  )}
                  <span className="text-sm">{testResult.message}</span>
                </div>
              )}

              {showCors && corsResults.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">CORS 检测结果:</h4>
                  {corsResults.map((result, index) => (
                    <div key={index} className={`p-3 rounded-lg border ${
                      result.success
                        ? 'bg-green-50 border-green-200'
                        : 'bg-red-50 border-red-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        {result.success ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <WifiOff className="h-4 w-4 text-red-600" />
                        )}
                        <span className="text-sm font-medium">{result.step}</span>
                      </div>
                      <p className="text-sm text-gray-600 mb-1">{result.message}</p>
                      {result.fix && (
                        <details className="text-xs text-blue-600 bg-blue-50 p-2 rounded border border-blue-200">
                          <summary className="cursor-pointer font-medium">💡 查看解决方案</summary>
                          <pre className="mt-2 whitespace-pre-wrap">{result.fix}</pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {showDiagnostic && diagnosticResults.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">诊断结果:</h4>
                  {diagnosticResults.map((result, index) => (
                    <div key={index} className={`p-3 rounded-lg border ${
                      result.success
                        ? 'bg-green-50 border-green-200'
                        : 'bg-red-50 border-red-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        {result.success ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <WifiOff className="h-4 w-4 text-red-600" />
                        )}
                        <span className="text-sm font-medium">{result.step}</span>
                      </div>
                      <p className="text-sm text-gray-600 mb-1">{result.message}</p>
                      {result.fix && (
                        <p className="text-xs text-blue-600 bg-blue-50 p-2 rounded border border-blue-200">
                          💡 解决方案: {result.fix}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* 开发环境 CORS 助手 */}
              {process.env.NODE_ENV === 'development' && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <h5 className="text-sm font-medium text-yellow-800 mb-2">
                    🛠️ 开发环境 CORS 配置助手
                  </h5>
                  <p className="text-xs text-yellow-700 mb-3">
                    如果上传失败，很可能是后端缺少 CORS 配置。点击下方按钮复制配置代码到后端。
                  </p>
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={async () => {
                        const success = await devCorsHelper.copyConfigToClipboard()
                        if (success) {
                          alert('CORS 配置已复制到剪贴板！请粘贴到后端代码中。')
                        } else {
                          alert('复制失败，请手动复制配置代码。')
                        }
                      }}
                      className="w-full text-xs"
                    >
                      📋 复制 CORS 配置代码
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={async () => {
                        devDebug.checkDevEnvironment()
                        devDebug.checkBrowserSupport()
                        const results = await devDebug.testDifferentMethods()
                        const uploadTest = await devDebug.testUploadEndpoint()
                        console.log('📊 测试结果汇总:', { results, uploadTest })
                        alert('调试信息已输出到控制台，请按 F12 查看')
                      }}
                      className="w-full text-xs"
                    >
                      🔍 运行完整调试
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={async () => {
                        console.clear()
                        const authCheck = await noAuthTest.checkAuthRequirement()
                        const endpointTests = await noAuthTest.testAllEndpoints()
                        console.log('🎯 无认证模式测试完成:', { authCheck, endpointTests })
                        alert('无认证测试完成，请查看控制台结果')
                      }}
                      className="w-full text-xs"
                    >
                      🔓 测试无认证模式
                    </Button>
                    <details className="text-xs">
                      <summary className="cursor-pointer text-yellow-700 hover:text-yellow-800">
                        查看配置代码
                      </summary>
                      <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                        {devCorsHelper.generateCorsConfig()}
                      </pre>
                    </details>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 数据处理配置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              数据处理配置
            </CardTitle>
            <CardDescription>
              配置数据处理和文件上传的相关参数
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>包含已关闭订单</Label>
                <p className="text-sm text-muted-foreground">
                  处理数据时包含已关闭的订单
                </p>
              </div>
              <Switch
                checked={config.processing.includeClosedOrders}
                onCheckedChange={(checked) => updateProcessingConfig({ includeClosedOrders: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>包含线下订单</Label>
                <p className="text-sm text-muted-foreground">
                  处理数据时包含线下订单
                </p>
              </div>
              <Switch
                checked={config.processing.includeOfflineOrders}
                onCheckedChange={(checked) => updateProcessingConfig({ includeOfflineOrders: checked })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxFileSize">最大文件大小 (MB)</Label>
              <Input
                id="maxFileSize"
                type="number"
                value={Math.round(config.processing.maxFileSize / 1024 / 1024)}
                onChange={(e) => updateProcessingConfig({
                  maxFileSize: (parseInt(e.target.value) || 50) * 1024 * 1024
                })}
                placeholder="50"
              />
            </div>

            <div className="space-y-2">
              <Label>支持的文件格式</Label>
              <div className="flex gap-2">
                {config.processing.supportedFormats.map((format) => (
                  <Badge key={format} variant="secondary">
                    {format}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 界面配置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              界面配置
            </CardTitle>
            <CardDescription>
              自定义界面主题和显示选项
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="theme">主题</Label>
              <Select
                value={config.ui.theme}
                onValueChange={(value: 'light' | 'dark' | 'system') => updateUiConfig({ theme: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">浅色</SelectItem>
                  <SelectItem value="dark">深色</SelectItem>
                  <SelectItem value="system">跟随系统</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="language">语言</Label>
              <Select
                value={config.ui.language}
                onValueChange={(value: 'zh' | 'en') => updateUiConfig({ language: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="zh">中文</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pageSize">每页显示条数</Label>
              <Input
                id="pageSize"
                type="number"
                value={config.ui.pageSize}
                onChange={(e) => updateUiConfig({ pageSize: parseInt(e.target.value) || 20 })}
                placeholder="20"
              />
            </div>
          </CardContent>
        </Card>

        {/* 导出配置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              导出配置
            </CardTitle>
            <CardDescription>
              配置数据导出的默认设置
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="defaultFormat">默认导出格式</Label>
              <Select
                value={config.export.defaultFormat}
                onValueChange={(value: 'xlsx' | 'csv') => updateExportConfig({ defaultFormat: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="xlsx">Excel (.xlsx)</SelectItem>
                  <SelectItem value="csv">CSV (.csv)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>包含表头</Label>
                <p className="text-sm text-muted-foreground">
                  导出时包含列标题
                </p>
              </div>
              <Switch
                checked={config.export.includeHeaders}
                onCheckedChange={(checked) => updateExportConfig({ includeHeaders: checked })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="dateFormat">日期格式</Label>
              <Input
                id="dateFormat"
                value={config.export.dateFormat}
                onChange={(e) => updateExportConfig({ dateFormat: e.target.value })}
                placeholder="YYYY-MM-DD"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* 操作按钮 */}
      <div className="flex items-center justify-between">
        <div>
          {saved && (
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm">设置已保存</span>
            </div>
          )}
        </div>

        <div className="flex gap-4">
          <Button
            variant="outline"
            onClick={handleReset}
            className="flex items-center gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            重置为默认
          </Button>

          <Button
            onClick={handleSave}
            className="flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            保存设置
          </Button>
        </div>
      </div>

      {/* 当前配置预览 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            当前配置预览
          </CardTitle>
          <CardDescription>
            查看当前应用程序的配置信息
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="text-sm bg-muted p-4 rounded-lg overflow-auto">
            {JSON.stringify(config, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}