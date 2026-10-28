#!/bin/zsh
# 测试循环（面板可见）：只占 bench 锁；与抓取完全并行；4 件套全员互评含自评
cd "$(dirname "$0")" || exit 1
mkdir -p runs
exec > >(tee -a runs/run-测试.log) 2>&1
[ ! -f secrets.env ] || source secrets.env
export BENCH_SKIP_MODELS="glm-5.3@api"
B="$PWD/tools/bench.py"
# 默认保留历史通道；运行前通过 BENCH_LOOP_MODELS 配置当前可用模型。
M="${BENCH_LOOP_MODELS:-glm-5.3-flash@api,deepseek-v4.1-flash,space-bunny}"
export BENCH_LOOP_MODELS="$M"
echo "[$(date '+%F %T')] 测试循环启动 pid=$$（配置模型=$M）"
while true; do
  while [ -f runs/.bench.lock ] && kill -0 $(cat runs/.bench.lock 2>/dev/null) 2>/dev/null; do
    echo "[$(date '+%F %T')] 等 bench 锁（pid $(cat runs/.bench.lock 2>/dev/null) 持有中）..."
    sleep 60
  done
  sleep 5; rm -f runs/.bench.lock
  SKILLS=$(python3 - <<'EOF'
import json, re
db = json.load(open('library/db.json'))
def sname(e):
    return re.sub(r'[^\w\-]', '-', e['skill']+'__'+e['repo'].split('/')[0])[:60]  # 与 collect.seed_tasks 同款清洗
print(','.join(sname(e) for e in db['条目'] if e['状态']=='待评(已建题)'))
EOF
)
  N=$(echo "$SKILLS" | tr ',' '\n' | grep -c .)
  echo "[$(date '+%F %T')] 待评 $N 个技能，起跑（kimi 缺格自动增量补）"
  if [ -n "$SKILLS" ]; then
    python3 "$B" run --skills "$SKILLS" --models "$M" --modes M2 -P 32 && \
    python3 "$B" score --skills "$SKILLS" --scorers "$M" -P 32 && \
    python3 "$B" agg --skills "$SKILLS" && \
    python3 "$B" site
    python3 - <<'EOF'
import json, csv, os
expected = {m for m in os.environ["BENCH_LOOP_MODELS"].split(",") if m}
db = json.load(open('library/db.json'))
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
    if e['状态'] == '待评(已建题)' and expected and expected.issubset(ok_models.get(sname, set())):
        e['状态'] = '已评'; n += 1
json.dump(db, open('library/db.json', 'w'), ensure_ascii=False, indent=1)
print(f'已评回写 {n} 个技能')
EOF
  else
    echo "[$(date '+%F %T')] 暂无待评，休眠 300s"
  fi
  sleep 300
done
