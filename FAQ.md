# 常见问题解答 (FAQ)

## 🔧 配置和部署问题

### Q1: 配置文件没有自动生成怎么办？

**问题**：使用 `docker run` 命令后，`/home/myptyun/config/config.yaml` 文件没有自动创建。

**原因**：
1. 宿主机目录不存在
2. 配置目录使用了 `:ro` (只读) 标志
3. 容器没有权限创建文件

**解决方案**：

#### 方案 1：使用初始化脚本
```bash
# 下载并运行初始化脚本
chmod +x init_config.sh
./init_config.sh

# 编辑配置文件
nano /home/myptyun/config/config.yaml

# 启动容器（注意不要使用 :ro）
docker run -d \
  --name qbit-smart-controller \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /home/myptyun/config:/app/config \
  -v /home/myptyun/data:/app/data \
  -e TZ=Asia/Shanghai \
  qbit-controller
```

#### 方案 2：手动创建配置文件
```bash
# 创建目录
mkdir -p /home/myptyun/config /home/myptyun/data/logs

# 创建配置文件
cat > /home/myptyun/config/config.yaml << 'EOF'
lucky_devices:
  - name: "我的Lucky设备"
    api_url: "http://192.168.1.100:16601/api/webservice/rules?openToken=YOUR_TOKEN"
    weight: 5.0
    enabled: true

qbittorrent_instances:
  - name: "我的QB实例"
    host: "http://192.168.1.101:8080"
    username: "admin"
    password: "your_password"
    enabled: true

controller_settings:
  poll_interval: 2
  limit_on_delay: 5
  limit_off_delay: 30
  retry_interval: 10
  limited_download: 1024
  limited_upload: 512
  normal_download: 0
  normal_upload: 0

web_settings:
  host: "0.0.0.0"
  port: 5000
EOF

# 设置权限
chmod 644 /home/myptyun/config/config.yaml
```

#### 方案 3：使用部署脚本
```bash
# 使用自动化部署脚本
chmod +x deploy_docker_cmd.sh
./deploy_docker_cmd.sh init
```

---

### Q2: 前端无法删除或编辑实例怎么办？

**问题**：在 Web 界面中删除默认实例或编辑实例后，无法保存更改。

**原因**：
- 配置目录使用了 `:ro` (只读) 标志挂载
- 容器无法写入配置文件

**解决方案**：

1. **停止并删除现有容器**：
```bash
docker stop qbit-smart-controller
docker rm qbit-smart-controller
```

2. **重新启动容器，不使用 `:ro` 标志**：
```bash
docker run -d \
  --name qbit-smart-controller \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /home/myptyun/config:/app/config \
  -v /home/myptyun/data:/app/data \
  -e TZ=Asia/Shanghai \
  qbit-controller
```

3. **验证配置可写**：
```bash
# 检查容器内的权限
docker exec qbit-smart-controller ls -la /app/config/

# 尝试在 Web 界面保存配置
```

---

### Q3: 容器启动后无法访问 Web 界面？

**问题**：容器启动成功，但无法访问 `http://localhost:5000`

**排查步骤**：

1. **检查容器状态**：
```bash
docker ps -f name=qbit-smart-controller
```

2. **查看容器日志**：
```bash
docker logs qbit-smart-controller
```

3. **检查端口映射**：
```bash
docker port qbit-smart-controller
```

4. **测试健康检查**：
```bash
curl http://localhost:5000/health
```

5. **检查防火墙**：
```bash
sudo ufw status
sudo ufw allow 5000/tcp
```

---

### Q4: 配置文件权限问题？

**问题**：容器无法读取或写入配置文件。

**解决方案**：

```bash
# 检查文件权限
ls -la /home/myptyun/config/
ls -la /home/myptyun/data/

# 重新设置权限
sudo chown -R $USER:$USER /home/myptyun/config
sudo chown -R $USER:$USER /home/myptyun/data
sudo chmod -R 755 /home/myptyun/config
sudo chmod -R 755 /home/myptyun/data

# 如果使用特定用户运行容器
sudo chown -R 1000:1000 /home/myptyun/config
sudo chown -R 1000:1000 /home/myptyun/data
```

---

## 🌐 连接问题

### Q5: 无法连接到 qBittorrent 实例？

**问题**：Web 界面显示 qBittorrent 实例离线或连接失败。

**排查步骤**：

1. **检查 qBittorrent 是否运行**：
```bash
# 从宿主机测试
curl http://192.168.1.101:8080

# 从容器内测试
docker exec qbit-smart-controller curl http://192.168.1.101:8080
```

2. **检查网络连通性**：
```bash
# Ping 测试
docker exec qbit-smart-controller ping 192.168.1.101

# Telnet 测试
telnet 192.168.1.101 8080
```

3. **如果 qBittorrent 在同一机器上**：
```yaml
# 使用 Docker 默认网关
host: "http://172.17.0.1:8080"

# 或使用 host.docker.internal
host: "http://host.docker.internal:8080"
```

4. **检查 qBittorrent 设置**：
   - 确认 Web UI 已启用
   - 确认允许远程连接
   - 用户名密码正确

---

### Q6: Lucky 设备连接失败？

**问题**：无法获取 Lucky 设备的连接数据。

**排查步骤**：

1. **测试 API 访问**：
```bash
curl "http://192.168.1.100:16601/api/webservice/rules?openToken=YOUR_TOKEN"
```

2. **检查 Token 是否正确**：
   - 登录 Lucky 管理界面
   - 进入「系统设置」→「API 管理」
   - 重新获取或生成 Token

3. **检查网络连通性**：
```bash
ping 192.168.1.100
telnet 192.168.1.100 16601
```

---

## 📊 运行问题

### Q7: 容器频繁重启？

**问题**：容器一直在重启循环中。

**排查步骤**：

1. **查看日志**：
```bash
docker logs --tail 100 qbit-smart-controller
```

2. **检查配置文件语法**：
```bash
# 验证 YAML 语法
cat /home/myptyun/config/config.yaml
```

3. **检查资源限制**：
```bash
# 检查系统资源
free -h
df -h
```

4. **临时移除重启策略测试**：
```bash
docker run -d \
  --name qbit-smart-controller \
  -p 5000:5000 \
  -v /home/myptyun/config:/app/config \
  -v /home/myptyun/data:/app/data \
  qbit-controller
```

---

### Q8: 日志文件太大？

**问题**：日志文件占用大量磁盘空间。

**解决方案**：

1. **清理旧日志**：
```bash
# 清理 7 天前的日志
find /home/myptyun/data/logs -name "*.log" -mtime +7 -delete
```

2. **配置 Docker 日志限制**：
```bash
docker run -d \
  --name qbit-smart-controller \
  --log-driver json-file \
  --log-opt max-size=50m \
  --log-opt max-file=5 \
  -p 5000:5000 \
  -v /home/myptyun/config:/app/config \
  -v /home/myptyun/data:/app/data \
  qbit-controller
```

3. **设置自动清理**：
```bash
# 添加到 crontab
crontab -e

# 每天凌晨清理旧日志
0 2 * * * find /home/myptyun/data/logs -name "*.log" -mtime +7 -delete
```

---

## 🔄 更新和维护

### Q9: 如何更新到最新版本？

**步骤**：

1. **备份配置和数据**：
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz -C /home/myptyun config data
```

2. **停止并删除旧容器**：
```bash
docker stop qbit-smart-controller
docker rm qbit-smart-controller
```

3. **拉取最新代码**：
```bash
cd ~/qbit-smart-controller
git pull origin main
```

4. **重新构建镜像**：
```bash
docker build -t qbit-controller .
```

5. **启动新容器**：
```bash
docker run -d \
  --name qbit-smart-controller \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /home/myptyun/config:/app/config \
  -v /home/myptyun/data:/app/data \
  -e TZ=Asia/Shanghai \
  qbit-controller
```

---

### Q10: 如何备份和恢复配置？

**备份**：
```bash
# 备份配置和数据
tar -czf qbit-backup-$(date +%Y%m%d_%H%M%S).tar.gz \
  -C /home/myptyun config data

# 移动到备份目录
mkdir -p ~/backups
mv qbit-backup-*.tar.gz ~/backups/
```

**恢复**：
```bash
# 停止容器
docker stop qbit-smart-controller

# 恢复备份
tar -xzf ~/backups/qbit-backup-20241017_120000.tar.gz \
  -C /home/myptyun

# 重启容器
docker start qbit-smart-controller
```

---

## 💡 最佳实践

### 推荐的部署命令

```bash
docker run -d \
  --name qbit-smart-controller \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=50m \
  --log-opt max-file=5 \
  -p 5000:5000 \
  -v /home/myptyun/config:/app/config \
  -v /home/myptyun/data:/app/data \
  -e TZ=Asia/Shanghai \
  -e PYTHONUNBUFFERED=1 \
  -e LOG_LEVEL=INFO \
  --health-cmd="curl -f http://localhost:5000/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  qbit-controller
```

### 配置文件最佳实践

1. **定期备份配置文件**
2. **使用强密码**
3. **定期更新 Token**
4. **监控日志文件大小**
5. **定期检查容器健康状态**

---

**需要更多帮助？** 查看完整手册：[MANUAL.md](MANUAL.md)
