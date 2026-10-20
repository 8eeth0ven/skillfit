#!/bin/zsh
# humanizer 全量重跑（面板可见）：旧prompt CLI M2/M4 作废 → 4模型重产 → 4判官含自评重评 → 聚合
cd "/Users/Zhuanz/Desktop/Skills&Model-Benchmark" || exit 1
exec > >(tee -a 结果/run-重跑-humanizer.log) 2>&1
source 密钥.env
B=~/.zcode/skills/skill-bench/tools/bench.py
echo "[$(date '+%F %T')] humanizer 重跑队列启动 pid=$$"
for i in $(seq 1 60); do
  echo "[$(date '+%F %T')] 第 $i 轮排队等 bench 锁..."
  while [ -f 结果/.bench.lock ] && kill -0 $(cat 结果/.bench.lock 2>/dev/null) 2>/dev/null; do sleep 60; done
  while pgrep -f "bench\.py (run|score)" >/dev/null 2>&1; do sleep 60; done
  sleep 20
  if python3 $B run --skills humanizer --models deepseek-v4.1-flash,space-bunny,glm-5.3-flash,kimi-k2.7 --modes M2,M4 -P 32 && \
     python3 $B run --skills humanizer --models kimi-k2.7 --modes M1,M3 -P 8 && \
     python3 $B score --skills humanizer --scorers deepseek-v4.1-flash,glm-5.3-flash,space-bunny,kimi-k2.7 -P 32 && \
     python3 $B agg --skills humanizer; then
    echo "[$(date '+%F %T')] humanizer 4×4 全量重跑完成（新prompt+门禁+自评口径）"
    exit 0
  fi
  echo "[$(date '+%F %T')] 本轮被锁挤掉或失败，10 分钟后重试"
  sleep 600
done
