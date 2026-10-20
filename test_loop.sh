#!/bin/zsh
# 测试循环（面板可见）：只占 bench 锁；与抓取完全并行；4 件套全员互评含自评
cd "$(dirname "$0")" || exit 1
exec > >(tee -a runs/run-测试.log) 2>&1
source secrets.env
export BENCH_SKIP_MODELS="glm-5.3@api"
B=~/.zcode/skills/skill-bench/tools/bench.py
# 优先级序（用户 2026-10-10 裁定）：glm-5.3-flash 免费优先；hy4 免费窗口 23:55 已硬停（历史数据保留）；kimi 暂停中
# kimi-k2.7 用户 2026-10-10 14:05 裁定「先停一停」：暂摘，恢复=加回 M 并把已评门槛改回 5
M="glm-5.3-flash@api,deepseek-v4.1-flash,space-bunny"
echo "[$(date '+%F %T')] 测试循环启动 pid=$$（五件套=$M）"
while true; do
  while [ -f runs/.bench.lock ] && kill -0 $(cat runs/.bench.lock 2>/dev/null) 2>/dev/null; do
    echo "[$(date '+%F %T')] 等 bench 锁（pid $(cat runs/.bench.lock 2>/dev/null) 持有中）..."
    sleep 60
  done
  sleep 5; rm -f runs/.bench.lock
  SKILLS=$(python3 - <<'EOF'
import json, re
db = json.load(open('library/库.json'))
def sname(e):
    return re.sub(r'[^\w\-]', '-', e['skill']+'__'+e['repo'].split('/')[0])[:60]  # 与 collect.seed_tasks 同款清洗
print(','.join(sname(e) for e in db['条目'] if e['状态']=='待评(已建题)'))
EOF
)
  N=$(echo "$SKILLS" | tr ',' '\n' | grep -c .)
  echo "[$(date '+%F %T')] 待评 $N 个技能，起跑（kimi 缺格自动增量补）"
  if [ -n "$SKILLS" ]; then
    python3 $B run --skills "$SKILLS" --models "$M" --modes M2 -P 32 && \
    python3 $B score --skills "$SKILLS" --scorers "$M" -P 32 && \
    python3 $B agg --skills "$SKILLS" && \
    python3 $B site
    python3 - <<'EOF'
import json, csv
db = json.load(open('library/库.json'))
ok_models = {}
try:
    for r in csv.DictReader(open('runs/台账.csv')):
        if r['状态'] == 'ok':
            ok_models.setdefault(r['技能'], set()).add(r['模型'])
except FileNotFoundError:
    pass
n = 0
import re as _re
def _sname(e):
    return _re.sub(r'[^\w\-]', '-', e['skill']+'__'+e['repo'].split('/')[0])[:60]
for e in db['条目']:
    sname = _sname(e)
    if e['状态'] == '待评(已建题)' and len(ok_models.get(sname, ())) >= 4:  # kimi 暂停期 4 模型口径
        e['状态'] = '已评'; n += 1
json.dump(db, open('library/库.json', 'w'), ensure_ascii=False, indent=1)
print(f'已评回写 {n} 个技能')
EOF
  else
    echo "[$(date '+%F %T')] 暂无待评，休眠 300s"
  fi
  sleep 300
done
