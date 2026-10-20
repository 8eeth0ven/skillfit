# 排障与监控

> 纪律：先看变更史再动手；每一步命令结论按 SKILL.md 产物约定落盘。

## §1 通用排障五步法

| 步 | 做什么 | 关键问题 | 产出 |
|---|---|---|---|
| 1 现象 | 收集报错原文、影响面、开始时间、持续还是间歇 | 谁在什么时间开始受什么影响？ | 一句话现象 + 起始时间 |
| 2 变更史 | 翻最近 24-72h 的发布/配置/证书/扩缩/依赖升级 | 出问题前最后动过什么？ | 变更清单或「确无变更」 |
| 3 分层定位 | 按 §2 从外到内逐层探针，逐层断言正常/异常 | 断在哪两层之间？ | 定位到单层 |
| 4 最小复现 | 收敛到一条命令稳定复现 | 能 100% 复现吗？ | 可复现命令 |
| 5 修复验证 | 用第 4 步同一命令验证 + 盯指标 15 分钟 | 修好了且没引入新问题？ | 修复记录 + 回滚路径 |

第 2 步最常被跳过也最省时间——七成线上事故由变更引起。查变更史：`kubectl rollout history deploy/app`、`helm history <release>`、`git log --since='3 days ago' --oneline -- deploy/`。

## §2 分层检查表（从外到内）

| 层 | 典型症状 | 一条命令探针 |
|---|---|---|
| DNS | 解析失败 / 解析到旧 IP / 部分用户打不开 | `dig +short app.example.com @8.8.8.8`（对比本地与公共 DNS 结果是否一致） |
| 网络 | 连接超时 / 拒绝 / 跨机房慢 | `nc -zv 10.0.0.5 3306`（端口连通）；丢包定位 `mtr -rwb 20 10.0.0.5` |
| 负载均衡 | 502/504、后端流量不均 | `curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' http://lb.example.com/healthz`；后端配置 `nginx -T 2>/dev/null \| grep -A5 upstream` |
| 应用 | 5xx / 慢 / 反复重启 | `kubectl logs <pod> --previous --tail=100`（崩因）；`kubectl top pod`（资源水位） |
| DB | 慢查询 / 连接耗尽 / 锁等待 | MySQL：`mysql -e 'SHOW PROCESSLIST;'`；PG：`psql -c "SELECT state,count(*) FROM pg_stat_activity GROUP BY state;"` |
| 缓存 | 响应变慢且 DB 压力同步涨 | `redis-cli info stats \| grep -E 'keyspace_hits\|keyspace_misses'`，命中率 = hits/(hits+misses)，< 90% 就该查 |

K8s 集群内 DNS 探针（Pod 起了但服务互连不通时）：

```bash
kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -- nslookup kubernetes.default
# 能解析 → CoreDNS 正常，问题在应用或网络策略
```

宿主机侧快速定位（容器外场景）：

```bash
top -b -n1 | head -15                        # CPU 大户
ps aux --sort=-%mem | head -8                # 内存大户
df -h | awk '$5+0 > 80'                      # 磁盘占用超 80% 的挂载点
ss -tan state established | wc -l            # 当前 ESTABLISHED 连接数
```

## §3 日志定位速查

### K8s 三板斧（按顺序打）

```bash
kubectl logs -f <pod> -c <container> --tail=200 --timestamps   # 1. 当前日志，-f 实时跟踪
kubectl logs <pod> --previous --tail=100                        # 2. 上次崩溃前的日志（CrashLoop 必用）
kubectl describe pod <pod>                                      # 3. Events 段看调度/镜像/探针
```

describe Events 关键字速译：

| Events 里看到 | 含义 |
|---|---|
| `OOMKilled`（Exit Code 137） | 内存超 limit 被内核杀 |
| `Back-off restarting failed container` | 崩溃循环，去看第 2 板斧 |
| `Failed to pull image ...` | 镜像名/tag/凭证问题 |
| `Readiness probe failed` | 就绪不过 → 被 Service 摘除（表现：没流量） |
| `Liveness probe failed` | 存活不过 → 被强杀重启（表现：莫名重启） |
| `FailedScheduling` | 资源不足 / 节点选择器不匹配 |

### journalctl（systemd 服务）

```bash
journalctl -u nginx -n 200 --no-pager               # 最近 200 行
journalctl -u myapp --since "30 min ago" -p err      # 近 30 分钟错误级别
journalctl -u myapp --since today | grep -i timeout  # 今天 + 关键词过滤
journalctl -p 3 -xb                                  # 本次开机以来的 err 级以上
```

### nginx access.log 分析（combined 格式，awk 直接跑）

```bash
cd /var/log/nginx
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -20    # top 来源 IP（找刷量）
awk '{print $7}' access.log | sort | uniq -c | sort -rn | head -20    # top URL（找热点/异常路径）
awk '$9>=500{c++}END{printf "%.2f%%\n",c/NR*100}' access.log          # 5xx 占比
awk '{print substr($4,14,5)}' access.log | uniq -c                    # 每分钟请求量（定位突增时刻）
awk '$9==499{print $7}' access.log | sort | uniq -c | sort -rn | head # 499=客户端提前断开（上游慢旁证）
```

要看耗时需先改 log_format 加 `$request_time`：`log_format rt '$remote_addr [$time_local] "$request" $status $request_time';`，然后 `awk '{print $NF}' access.log | sort -rn | head -20` 即 top 耗时请求。

## §4 监控最小集（四个黄金指标）

| 指标 | 看什么 | 告警阈值起点（持续时长 → 级别） |
|---|---|---|
| 延迟 | P99 而非平均值（平均会被分布掩盖） | 内部 API P99 > 500ms 持续 5m；面向用户页面 > 1s 持续 5m |
| 流量 | QPS、带宽的环比变化 | 环比跌 50% 持续 10m（上游断连/被摘流量）；涨 3 倍（被打/重试风暴） |
| 错误 | 5xx 占总请求比例 | > 1% 持续 5m → 页面告警；> 5% 持续 1m → 电话告警 |
| 饱和度 | CPU / 内存 / 磁盘 / 连接池 / 队列 | CPU > 80% 持续 10m；内存 > 85%；磁盘 > 80%（> 90% 升紧急）；DB 连接池占用 > 80% |

PromQL 直接抄：

```promql
# 5xx 比例
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
# P99 延迟
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

告警三要素：可行动（收到就知道做什么）、有阈值（见上表）、有升级路径（超时未处理转谁）。缺任何一条的告警先删再建——没有告警的监控只是图表。

## §5 常见翻车表（判定 + 处置）

| 翻车 | 判定 | 处置 |
|---|---|---|
| OOMKilled | describe 见 `Reason: OOMKilled`、`LAST STATE: Exit Code 137`、重启计数涨 | `kubectl top pod` 看真实峰值 → limits.memory 调到峰值 1.5 倍；内存持续爬升是泄漏，先抓 heap dump 再说 |
| CrashLoopBackOff | STATUS 直接显示；`kubectl logs --previous` 看崩因 | 九成是配置错/依赖连不上：查 ConfigMap/Secret 是否挂对、依赖地址是否可达；改完 `kubectl rollout restart` |
| ImagePullBackOff | describe Events：`not found`（tag 不存在）/ `unauthorized`（无凭证）/ `toomanyrequests`（仓库限流） | 核对镜像名与 tag；补 imagePullSecrets；限流换镜像源或登录 |
| 证书过期 | `openssl s_client -connect host:443 -servername host </dev/null 2>/dev/null \| openssl x509 -noout -dates` | 续期后必须 reload：`nginx -s reload`；K8s 侧 cert-manager 自动续 + reloader 滚动；告警提前 30 天 |
| DNS 不通（集群内） | Pod 内 nslookup 失败但宿主机正常 | 1) `kubectl -n kube-system get pods -l k8s-app=kube-dns`（CoreDNS 活着没）；2) 看 Pod `/etc/resolv.conf` 是否指向 kube-dns Service；3) 外部域名解析慢查 ndots:5，改 dnsConfig 或用 FQDN |
| Pod 活着但没流量 | Running 且 Ready 但 Service 不转发 | `kubectl get endpoints <svc>`：后端为空 = 标签不匹配或探针摘除；对照 Service selector 与 Pod labels |

判定优先级纪律：翻车表只负责对号入座；现象不在表里 → 回 §1 五步法从头走，别瞎试命令。
