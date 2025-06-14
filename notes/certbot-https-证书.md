# navydev.top 和 obz.navydev.top 共享证书

## 步骤一：准备环境

首先，创建必要的目录结构：

```bash
# 创建 Certbot 数据目录
mkdir -p ./data/certbot/conf
mkdir -p ./data/certbot/www
```

## 步骤二：配置 DNS 记录

确保您的域名 DNS 设置正确：

1. `navydev.top` 的 A 记录指向您的服务器 IP
2. `rss.navydev.top` 的 A 记录指向同一 IP
3. `obz.navydev.top` 的 A 记录指向同一 IP
4. `crabtris.navydev.top` 的 A 记录指向同一 IP
5. 域名备案也已经通过

## 步骤三：临时 Nginx 配置

创建一个基本的 Nginx 配置用于证书验证：

```bash
# 使用临时配置
cp ./config/nginx/nginx.conf ./config/nginx/nginx.conf.bak
cp ./config/nginx/nginx_initial.conf ./config/nginx/nginx.conf
```

## 步骤四：更新 Docker Compose 配置

确保 docker-compose.yml 中的卷映射正确配置：

```yaml
volumes:
  - ./data/certbot/conf:/etc/letsencrypt:ro
  - ./data/certbot/www:/var/www/certbot:ro
```

## 步骤五：启动 Nginx 服务

```bash
docker compose restart nginx
```

## 步骤六：申请多域名证书

使用 Certbot 为多个域名申请单个证书（使用 HTTP 验证）：

```bash
# 在 docker-compose 同级目录, 只更改 -d 参数就好
certbot certonly --webroot   \
--webroot-path=$(pwd)/data/certbot/www  \
--config-dir=$(pwd)/data/certbot/conf   \
--work-dir=$(pwd)/data/certbot/conf   \
--logs-dir=$(pwd)/data/certbot/conf/logs   \
-d obz.navydev.top   \
--email wsgggws@gmail.com   \
--agree-tos --no-eff-email
```

这会为多个域名创建一个共享证书，无需 DNS 验证。

## 步骤七：验证证书是否生成成功

```bash
ls -la ./data/certbot/conf/live/
```

## 步骤八：配置 Nginx 使用共享证书

创建完整的 Nginx 配置：

```bash
cp ./config/nginx/nginx.conf.bak ./config/nginx/nginx.conf
```

## 步骤九：重启 Nginx 应用新配置

```bash
docker compose restart nginx
# 如果有些卷什么的有添加，如 conf.d/, 需要 --build 进行重新加载
# docker compose up --build -d nginx
```

## 步骤十：设置自动续期

为证书设置自动续期：

```bash

# 添加执行权限
chmod +x ./scripts/renew_cert.sh

# 添加定时任务（每月两次）
(crontab -l 2>/dev/null; echo "0 3 1,15 * * $(pwd)/scripts/renew_cert.sh >> $(pwd)/certbot_renew.log 2>&1") | crontab -
```

由于使用的是 HTTP 验证（而非 DNS 验证），这可以完全自动化续期。
