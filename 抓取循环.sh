#!/bin/zsh
# 抓取循环（面板可见）：只占采集锁，与测试/补漏完全并行
cd "$(dirname "$0")" || exit 1
exec > >(tee -a 结果/run-抓取.log) 2>&1
source 密钥.env
echo "[$(date '+%F %T')] 抓取循环启动 pid=$$（5k 高星 8 路翻页 + awesome 反展开 + 趋势 3 路，无上限）"
while true; do
  echo "[$(date '+%F %T')] === 采集开始 ==="
  python3 ~/.zcode/skills/skill-bench/tools/collect.py --update --min-stars 5000 --trending --seed 5000
  echo "[$(date '+%F %T')] === 采集完成，休眠 1800s ==="
  sleep 1800
done
