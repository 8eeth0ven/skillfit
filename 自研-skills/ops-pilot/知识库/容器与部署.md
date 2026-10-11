# 容器与部署

> 本篇只放能直接抄的模板和能直接对照的表；命令均可直接执行。

## §1 Dockerfile 速查

### §1.1 分层缓存优化序

原理：Docker 逐指令分层缓存，**任一层失效，其后所有层重建**。排序原则 = 变化频率升序：

| 序 | 放什么 | 示例 | 失效频率 |
|---|---|---|---|
| 1 | 基础镜像/目录/环境变量 | `FROM node:20.17-alpine`、`WORKDIR /app`、`ENV NODE_ENV=production` | 几乎不变 |
| 2 | 系统包 | `RUN apk add --no-cache curl` | 月级 |
| 3 | 依赖清单 + 安装 | `COPY package*.json ./` → `RUN npm ci` | 依赖变更时 |
| 4 | 业务源码 | `COPY . .` | 每次提交 |
| 5 | 构建/入口 | `RUN npm run build`、`CMD` | 随代码变 |

```dockerfile
# 反面：COPY . . 放依赖安装前 → 改一行代码，全量依赖重装
# 正面：先清单后源码
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY . .
RUN npm run build
```

### §1.2 多阶段构建模板

作用：编译器/构建工具留在 builder 层，最终镜像只留产物（Go 镜像可从 1GB+ 压到 20MB 内）：

```dockerfile
FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/app .

FROM alpine:3.20
RUN adduser -D -u 10001 app
COPY --from=build /out/app /usr/local/bin/app
USER app
ENTRYPOINT ["app"]
```

Node 同理：builder 阶段 `npm ci` 装依赖，再把 `node_modules` 与产物 `COPY --from` 进运行镜像，node-gyp 等编译工具链不进最终层。

### §1.3 常见坏味道表

| 坏味道 | 后果 | 修正 |
|---|---|---|
| `FROM xxx:latest` | 构建不可复现，今天好明天坏 | 固定版本 tag（`node:20.17-alpine`），关键镜像再锁 digest |
| 默认 root 运行 | 容器逃逸后直接是 root | `USER app` 建低权用户（见 §1.2 模板） |
| 无 .dockerignore | `.git/`、`node_modules/`、日志进层：体积大 + 源码泄漏 | 根目录加 .dockerignore：`node_modules`、`.git`、`*.log`、`.env` |
| secrets 写进 ARG/ENV | `docker history` 可见明文 | BuildKit：`RUN --mount=type=secret,id=k ...`，构建时 `--secret id=k,src=k.txt` |
| apt/apk 缓存留层 | 平白多几十 MB | 同层内清理：`RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*` |
| 一条指令一行 RUN | 层数多、缓存粒度差 | 相关动作用 `&&` 合并进一个 RUN |
| 把 EXPOSE 当防护 | EXPOSE 仅声明，不拦访问 | 端口管控靠网络策略/防火墙 |

自查大层：`docker history myapp:1.2.3 --format '{{.Size}}\t{{.CreatedBy}}' | sort -hr | head`。

## §2 docker-compose 要素表

| 要素 | 作用 | 缺了会怎样 |
|---|---|---|
| healthcheck | 判定容器「真活着」（进程在且能服务） | 假活容器照样接流量 |
| depends_on + condition | 等 db 健康后才起 app | app 启动即连库失败、反复重启 |
| deploy.resources.limits | CPU/内存上限 | 单容器吃光宿主机，邻居全挂 |
| restart: unless-stopped | 崩溃自动拉起 | 崩了没人管 |

最小完整示例：

```yaml
services:
  app:
    image: myapp:1.2.3
    restart: unless-stopped
    ports: ["8080:8080"]
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/healthz"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 20s
    depends_on:
      db: {condition: service_healthy}
    deploy:
      resources:
        limits: {cpus: "2", memory: 512M}
  db:
    image: postgres:16.4
    restart: unless-stopped
    environment: {POSTGRES_PASSWORD: changeme}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      retries: 5
    volumes: ["pgdata:/var/lib/postgresql/data"]
volumes:
  pgdata:
```

注意：`depends_on` 不带 `condition` 只保证启动顺序不保证健康；健康检查必须打应用自身端点，别用 `nc localhost` 假探活。

## §3 K8s 最小可用清单（五件套）

| 对象 | 管什么 | 一句话边界 |
|---|---|---|
| Deployment | 无状态副本数、滚动更新、回滚 | 有状态用 StatefulSet，别硬塞 |
| Service | 一组 Pod 的稳定入口 + 集群内负载均衡 | ClusterIP 集群内 / NodePort 节点端口 / LoadBalancer 云 LB |
| Ingress | 七层路由（域名/path）+ TLS 终止 | 只管 HTTP(S)；四层走 Service |
| ConfigMap | 非敏感配置（文件/环境变量） | 改后需滚动重启才生效 |
| Secret | 敏感配置（仅 base64 编码，非加密） | 真加密要配 KMS/Vault |

Deployment 骨架（带探针与资源，可直接改）：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: {name: app}
spec:
  replicas: 3
  strategy:
    rollingUpdate: {maxSurge: 1, maxUnavailable: 0}
  selector: {matchLabels: {app: app}}
  template:
    metadata: {labels: {app: app}}
    spec:
      containers:
      - name: app
        image: registry.example.com/app:1.2.3
        ports: [{containerPort: 8080}]
        resources:
          requests: {cpu: 100m, memory: 128Mi}
          limits: {cpu: "500m", memory: 256Mi}
        livenessProbe: {httpGet: {path: /healthz, port: 8080}, periodSeconds: 10}
        readinessProbe: {httpGet: {path: /ready, port: 8080}, periodSeconds: 5}
```

Service 与 Ingress（紧凑骨架）：

```yaml
apiVersion: v1
kind: Service
metadata: {name: app}
spec:
  selector: {app: app}
  ports: [{port: 80, targetPort: 8080}]
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata: {name: app}
spec:
  ingressClassName: nginx
  tls: [{hosts: [app.example.com], secretName: app-tls}]
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend: {service: {name: app, port: {number: 80}}}
```

ConfigMap/Secret 用命令式创建更快：

```bash
kubectl create configmap app-config --from-file=config.yaml
kubectl create secret generic db-secret --from-literal=DB_PASSWORD='xxx'
# 挂载：envFrom 引用或 volume 挂载；改后 kubectl rollout restart deploy/app 生效
```

## §4 发布策略对照表

| 策略 | 额外资源 | 回滚速度 | 爆炸半径 | 实现复杂度 | 适用 |
|---|---|---|---|---|---|
| 滚动 | 约 25%（3 副本 maxSurge=1） | 慢：再滚一轮，分钟级 | 新旧共存，全量用户分摊风险 | 低（K8s 原生默认） | 常规迭代、可接受短暂共存 |
| 蓝绿 | 100%（双份全量环境） | 快：流量切回旧环境，秒级 | 切换瞬间全有或全无 | 中（双环境 + 流量开关） | 大改版、要求秒级回滚 |
| 灰度/金丝雀 | 5-10% | 快：流量比例调回，秒级 | 先放 5% 用户验证 | 高（Argo Rollouts / 网关权重路由） | 高风险变更、大流量服务 |

选型口诀：**能灰度不蓝绿，能蓝绿不裸滚动**；日常小改动滚动足够。滚动参数语义：`maxUnavailable: 0` = 更新期间可用副本数不减，`maxSurge: 1` = 最多临时多起 1 个新副本（先加新再删旧，最稳组合）。

## §5 回滚三件套

优先用前两件，第三件是纪律兜底：

| 件 | 命令 | 前提 |
|---|---|---|
| 1. kubectl 回滚 | `kubectl rollout history deploy/app` 看版本 → `kubectl rollout undo deploy/app --to-revision=3` | revision 历史还在（默认留 10 个） |
| 2. helm 回滚 | `helm history myapp` 看 revision → `helm rollback myapp 1 --wait --timeout 5m` | 应用是 helm 装的 |
| 3. 镜像 tag 兜底 | `kubectl set image deploy/app app=registry.example.com/app:1.2.3` | tag 不可变（见下） |

镜像 tag 纪律：**禁 latest、禁可变 tag**（如 `stable`），一律 `git-<sha>` 或 `v<semver>`。tag 可变 = 历史 revision 指向会漂移的同一 tag，回滚形同虚设。

回滚后验证三连（结果按 SKILL.md 产物约定落盘）：

```bash
kubectl rollout status deploy/app --timeout=120s    # 滚动是否完成
curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/healthz
kubectl get pods -l app=app -o wide                 # 全部 Running 且 READY n/n
```
