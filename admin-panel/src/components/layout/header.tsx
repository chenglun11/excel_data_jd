import { SidebarTrigger } from "@/components/ui/sidebar"

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-6">
      <div className="flex items-center gap-4">
        <SidebarTrigger />
        <h1 className="text-xl font-semibold">京东店铺数据管理系统</h1>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">
          数据处理平台
        </span>
      </div>
    </header>
  )
}