# 部署说明

## nginx配置

1. 将 `nginx-simple.conf` 复制到nginx配置目录
2. 根据实际情况修改配置文件中的路径和端口

### 使用nginx配置

```bash
# 复制配置文件到nginx配置目录
sudo cp nginx-simple.conf /etc/nginx/sites-available/excel-data-jd
sudo ln -s /etc/nginx/sites-available/excel-data-jd /etc/nginx/sites-enabled/

# 测试nginx配置
sudo nginx -t

# 重启nginx
sudo systemctl restart nginx
```

### 或者直接添加到主配置文件

将 `nginx-simple.conf` 的内容添加到 `/etc/nginx/nginx.conf` 的 `http` 块中。

## 后端服务

1. 启动FastAPI后端服务（端口6532）：
```bash
cd backend
python main_upload.py
# 或者
uvicorn main_upload:app --host 0.0.0.0 --port 6532
```

## 前端服务

1. 如果使用Next.js开发服务器（端口3000）：
```bash
cd admin-panel
npm run dev
```

2. 如果使用生产构建：
```bash
cd admin-panel
npm run build
npm start
```

## 域名配置

确保以下域名解析到你的服务器：
- `apis.lchnan.cn` -> 服务器IP（用于API服务）
- `shop.lchnan.cn` -> 服务器IP（用于前端服务）

## 防火墙设置

确保以下端口开放：
- 80（nginx HTTP）
- 443（nginx HTTPS，如果使用SSL）
- 3000（Next.js，如果直接暴露）
- 6532（FastAPI后端，仅内部访问）

## SSL证书（可选）

如果需要HTTPS，可以使用Let's Encrypt：

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d apis.lchnan.cn -d shop.lchnan.cn

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 故障排除

1. 检查nginx状态：`sudo systemctl status nginx`
2. 查看nginx错误日志：`sudo tail -f /var/log/nginx/error.log`
3. 检查FastAPI服务：`curl http://localhost:6532/`
4. 检查CORS问题：浏览器开发者工具 -> Network 标签页

## 注意事项

- nginx配置中的CORS设置会覆盖FastAPI中的CORS设置
- 文件上传限制在nginx中设置为100MB
- 确保FastAPI服务在nginx重启前已经启动