#!/bin/zsh
# 网页实时刷新（面板可见）：启动立即刷一轮，之后每5分钟；页面每2分钟自重载
cd "/Users/Zhuanz/Desktop/Skills&Model-Benchmark" || exit 1
exec > >(tee -a 结果/run-网页刷新.log) 2>&1
LOCK=结果/.webrefresh.lock
if [ -f "$LOCK" ] && kill -0 $(cat "$LOCK" 2>/dev/null) 2>/dev/null; then
  echo "[$(date '+%F %T')] 已有实例 pid=$(cat $LOCK)，退出"; exit 0
fi
echo $$ > "$LOCK"; trap 'rm -f "$LOCK"' EXIT
source 密钥.env
B=~/.zcode/skills/skill-bench/tools/bench.py
MARK=结果/.webmark
[ -f "$MARK" ] || touch "$MARK"
echo "[$(date '+%F %T')] 网页刷新循环启动 pid=$$（立即首轮，之后5分钟一轮）"
while true; do
  DIRTY=$(python3 - "$MARK" <<'EOF'
import sys, pathlib
cut = pathlib.Path(sys.argv[1]).stat().st_mtime
out = [d.name for d in pathlib.Path('评分').iterdir()
       if d.is_dir() and (d / '映射表.json').exists()
       and any(f.stat().st_mtime > cut for f in d.rglob('*.json'))]
print(','.join(sorted(out)))
EOF
)
  if [ -n "$DIRTY" ]; then
    N=$(echo "$DIRTY" | tr ',' '\n' | grep -c .)
    echo "[$(date '+%F %T')] 增量聚合 $N 个技能"
    python3 $B agg --skills "$DIRTY" 2>/dev/null || \
      echo "$DIRTY" | tr ',' '\n' | while read -r s; do [ -n "$s" ] && python3 $B agg --skills "$s" 2>/dev/null; done
  else
    echo "[$(date '+%F %T')] 无新评分（仅刷进度）"
  fi
  python3 $B site
  touch "$MARK"
  sleep 300
done
