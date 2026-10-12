#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill-bench 批跑器 v3（通道A：codebuddy CLI + OpenAI 兼容 API 双通道）
v3 吸收的开源机制（来源见 知识库/交叉评分.md §判官配置规则 与对话记录）:
  断言层(anthropics/skills, microsoft/skills) / 触发正负例(OpenAI eval-skills) /
  M4 等长对照(SkillsBench 自认未做的坑) / Hake 归一化增益(SkillsBench) /
  --trials 多试验+中位(Arena) / 家族去重票(PoLL+Apple correlated errors) / 反冗长条款(verbosity bias 文献)
rubric/权重/SkillScore 的文档版在 ../知识库/ —— 改脚本必同步改文档，反之亦然。

用法（项目根 ~/Desktop/Skills&Model-Benchmark 下）:
  python3 .../bench.py doctor --models glm-5.3,deepseek-v4-pro
  python3 .../bench.py check  --skills humanizer                 # 断言层速览（不花钱）
  nohup python3 .../bench.py run   --skills humanizer --models glm-5.3,kimi-k3-2 --modes M1,M2,M3,M4 --trials 3 -P 6 > 结果/run.log 2>&1 &
  nohup python3 .../bench.py score --skills humanizer --scorers glm-5.3,deepseek-v4-pro,kimi-k3-2 -P 6 > 评分/run.log 2>&1 &
  python3 .../bench.py agg   --skills humanizer
  python3 .../bench.py site

模型写法: CLI 直接写 id；API 写 别名@api（api路由.json + BENCH_API_KEY）。M3 仅 CLI 可跑。
台账为 v2 列（含试验列）；v1 旧台账请删除重跑（当前无存量数据）。
"""
import argparse, csv, json, os, random, re, shutil, statistics, subprocess, sys, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

PROXY = {"https_proxy": "http://127.0.0.1:7897", "http_proxy": "http://127.0.0.1:7897"}
SKILLS_DIR = Path.home() / ".zcode/skills"
PROJ = Path("~/Desktop/Skills&Model-Benchmark").expanduser()
TDIR, RDIR, SDIR, REPDIR = PROJ / "任务集", PROJ / "结果", PROJ / "评分", PROJ / "报告"
LOCK = RDIR / ".bench.lock"
TIMEOUT, RETRY, MIN_SCORERS = 600, 2, 2
API_TIMEOUT, API_RETRY = int(os.environ.get("BENCH_API_TIMEOUT", 300)), 5  # 直连并发不稳时可降（#16：直连16并发会挂死连接）
DIMS = ["正确性", "完整性", "技能遵循", "表达清晰"]
WEIGHTS = {"M1": {"正确性": .55, "完整性": .30, "表达清晰": .15},
           "*":  {"正确性": .40, "完整性": .25, "技能遵循": .20, "表达清晰": .15}}
SS_W, SS_STAB, SS_TRIG = 60.0, 20.0, 20.0
FAMS = [("glm", "GLM"), ("deepseek", "DeepSeek"), ("kimi", "Kimi"), ("minimax", "MiniMax"),
        ("hy", "Hy"), ("step", "Step"), ("space", "SpaceBunny")]
FILLER = ("Markdown 是一种轻量标记语言。标题用井号开头，列表用短横线。段落之间空一行。"
          "代码块用三个反引号包围。链接写法为方括号加圆括号。表格由竖线与短横线构成。") * 40

RUBRIC = """你是评分官，对一份匿名任务产物打分。只依据本 prompt 材料，禁止猜测产出者是谁，禁止无证据打分。
评分维度（0-5 整数）：
- 正确性：关键要求做对没、有无编造。5=验收点全对无编造；3=主对但有遗漏小错；1=关键点错或编造。若下方给出确定性断言结果，正确性必须与断言事实一致。
- 完整性：下方评分参考必答点覆盖度。5=全覆盖且展开；3=覆盖过半；1=几乎未覆盖。
- 技能遵循：产物附带的技能文档是否被按方法执行（无技能文档产物此维输出 null）。5=全程按方法且用对节；3=用了一半；1=完全无视。
- 表达清晰：结构可读、能否直接用。5=直接可用；3=能读但松散；1=混乱难读。
硬条款：冗长不加分，信息密度优先，产物长度不影响任何维度分。
判定口径（必须与维度分一致）：加权≥4.0→PASS；2.5~3.9→CONDITIONAL；<2.5→FAIL。依据一句话；证据必须原样引用产物正文一行。
只输出 JSON，字段：正确性、完整性、技能遵循、表达清晰、判定、依据、证据。"""

SCORE_SCHEMA = {"type": "object",
                "properties": {**{d: {"type": "integer"} for d in DIMS},
                               "判定": {"type": "string"}, "依据": {"type": "string"}, "证据": {"type": "string"}},
                "required": ["正确性", "完整性", "表达清晰", "判定", "依据"]}


def ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg): print(f"[{ts()}] {msg}", flush=True)


def fam(m):
    m = m.lower()
    for p, f in FAMS:
        if m.startswith(p): return f
    return m.split("@")[0].split("-")[0]


import fcntl


def single_instance(tag="mono"):
    """按 tag 分锁：每模型一条生产车道可并行（各 CLI 模型独立限速，用户 2026-10-10 裁定）；score 全局独占。"""
    lock = RDIR / f".bench.lock.{re.sub(r'[^\w]', '-', tag)[:60]}"
    if lock.exists():
        try:
            old = int(lock.read_text().strip())
            os.kill(old, 0)
            sys.exit(f"另一同车道 bench.py 在跑 pid={old}（tag={tag}），先收场再开")
        except ValueError:
            pass
        except ProcessLookupError:
            pass
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(str(os.getpid()))


def ledger(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", newline="") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # 多车道并发追加安全
        w = csv.writer(f)
        w.writerow(row.values())
        fcntl.flock(f, fcntl.LOCK_UN)


def api_cfg():
    f = PROJ / "api路由.json"
    return json.loads(f.read_text()) if f.exists() else {}


import threading

_KC = {"i": 0}
_KL = threading.Lock()
_KEY_COOLDOWN = {}  # key -> 冷却截止时间戳（429/SSL/5xx 进冷却，到期自动回归）


def _next_key(keys):
    now = time.time()
    healthy = [k for k in keys if _KEY_COOLDOWN.get(k, 0) < now]
    if not healthy:
        healthy = keys  # 全在冷却则硬上（总比停摆好）
    with _KL:
        k = healthy[_KC["i"] % len(healthy)]
        _KC["i"] += 1
        return k


def _cool_key(key, err, secs=10):
    if any(t in err for t in ("429", "SSL", "HTTP Error", "timed out")):
        _KEY_COOLDOWN[key] = time.time() + secs
        log(f"key#{keys_index(key)} 冷却 {secs}s（{err[:40]}）")


def keys_index(key):
    raw = os.environ.get("BENCH_API_KEYS", "")
    ks = [k.strip() for k in raw.split(",") if k.strip()]
    return ks.index(key) + 1 if key in ks else "?"


def api_keys(cfg):
    raw = os.environ.get("BENCH_API_KEYS") or os.environ.get(cfg.get("key_env", "BENCH_API_KEY"), "")
    return [k.strip() for k in raw.split(",") if k.strip()]


_POOL = {"mgr": None}


def _proxy_alive():
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", 7897), timeout=2)
        s.close()
        return True
    except Exception:
        return False


def _pool():
    """API 连接池：代理可用走代理，死了自动直连（Clash 进程会挂，直连时通时不通，#16）。"""
    if _POOL["mgr"] is None:
        import urllib3
        to = urllib3.Timeout(connect=15, read=API_TIMEOUT)
        if os.environ.get("BENCH_API_DIRECT") or not _proxy_alive():
            _POOL["mgr"] = urllib3.PoolManager(num_pools=2, maxsize=96, block=True, timeout=to, retries=False)
        else:
            _POOL["mgr"] = urllib3.ProxyManager(
                PROXY["https_proxy"], num_pools=2, maxsize=96, block=True, timeout=to, retries=False)
    return _POOL["mgr"]


def call_api(alias, prompt, schema=None, timeout=TIMEOUT):
    """anthropic 兼容端点（实证免费通道，经验#15）：POST {base}/v1/messages，x-api-key 头。"""
    cfg = api_cfg()
    base = cfg.get("base") or os.environ.get("BENCH_API_BASE", "")
    keys = api_keys(cfg)
    if not base or not keys:
        return "", "api未配：项目根 api路由.json(base) + 密钥环境变量（BENCH_API_KEYS 可逗号分隔多key轮换）"
    name = cfg.get("models", {}).get(alias, alias)
    if schema:
        prompt += "\n只输出符合要求的 JSON，不要输出任何其他内容。"
    body = {"model": name, "max_tokens": int(os.environ.get("BENCH_API_MAXTOK", "8192")), "temperature": 0,
            "messages": [{"role": "user", "content": prompt}]}
    th = os.environ.get("BENCH_API_THINKING", "off")
    if th == "off":
        body["thinking"] = {"type": "disabled"}  # 32s→6s（#17）；端点可能改规则拒绝（#23 1210）
    elif th == "low":
        body["thinking"] = {"type": "enabled",
                            "budget_tokens": int(os.environ.get("BENCH_THINK_BUDGET", "1024"))}  # 思考预算可调（#23）
    err = ""
    for i in range(API_RETRY + 1):
        key = _next_key(keys)
        time.sleep(random.uniform(0, 1.2))  # 握手错峰：并发新建 TLS 同瞬发出会约半数被 reset，抖动摊开
        try:
            resp = _pool().request(
                "POST", base.rstrip("/") + "/v1/messages", body=json.dumps(body),
                headers={"Content-Type": "application/json", "x-api-key": key,
                         "anthropic-version": "2023-06-01"})
            if 200 <= resp.status < 300:
                blocks = json.loads(resp.data).get("content", [])
                out = "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text").strip()
                if out: return out, ""
                err = "empty(no text block)"
            else:
                err = f"HTTP {resp.status} {resp.data[:80]}"
                body_txt = resp.data.decode("utf-8", "ignore")
                if "1113" in body_txt:
                    _cool_key(key, "1113余额不足", 21600)  # 永久性耗尽：冷却6h，别再浪费轮询位（#15）
                elif resp.status == 429:
                    _cool_key(key, err, 10)
        except Exception as e:
            err = str(e)[:150]
            if "proxy" in err.lower():  # 代理进程死亡：切直连并立即重建池（下次尝试生效）
                _POOL["mgr"] = None
                os.environ["BENCH_API_DIRECT"] = "1"
                _cool_key(key, err, 0)
                continue
            _cool_key(key, err, 10)
        if i < RETRY: time.sleep(min(8, 2 ** (i + 1)))  # 实测 2/4/8s 指数退避
    return "", err


def call(model, prompt, tools="", schema=None, timeout=TIMEOUT, extra=None):
    """model 带 @api 后缀走 API 直连，否则走 codebuddy CLI。绝不传 --fallback-model。"""
    if "@" in model:
        alias, route = model.split("@", 1)
        if route == "api":
            return call_api(alias, prompt, schema, timeout)
    cmd = ["codebuddy", "-p", "--model", model]
    if tools is not None: cmd += ["--tools", tools]
    if schema: cmd += ["--json-schema", json.dumps(schema, ensure_ascii=False)]
    if extra: cmd += extra
    err = ""
    for i in range(RETRY + 1):
        try:
            r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                               timeout=timeout, env={**os.environ, **PROXY})
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip(), ""
            err = f"rc={r.returncode} {r.stderr.strip()[:150]}"
        except subprocess.TimeoutExpired:
            err = "timeout"
        if i < RETRY: time.sleep(3 * (i + 1))
    return "", err or "empty"


# ---------- 任务/产物解析 ----------

def split_fm(txt):
    m = re.match(r"^---\n(.*?)\n---\n?", txt, re.S)
    if not m: return {}, txt
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, txt[m.end():]


def section(body, name):
    m = re.search(rf"^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return m.group(1).strip() if m else ""


def load_task(path: Path):
    """返回 (frontmatter, 用户Prompt, 评分参考, 断言列表)。"""
    fm, body = split_fm(path.read_text())
    asserts = []
    for line in section(body, "断言").splitlines():
        line = line.strip().lstrip("-").strip()
        if ":" in line:
            k, v = line.split(":", 1)
            if k.strip() in ("禁含", "禁正则", "必含", "必正则") and v.strip():
                asserts.append({"kind": k.strip(), "val": v.strip()})
    return fm, section(body, "用户Prompt"), section(body, "评分参考"), asserts


def run_assertions(asserts, body):
    """确定性断言层：返回 (过N, 未过描述列表)。判官与报告共用。"""
    bad = []
    for a in asserts:
        kind, val = a["kind"], a["val"]
        try:
            if kind == "禁含" and val in body: bad.append(f"禁含「{val}」仍出现")
            elif kind == "禁正则" and re.search(val, body): bad.append(f"禁正则「{val}」仍命中")
            elif kind == "必含" and val not in body: bad.append(f"必含「{val}」缺失")
            elif kind == "必正则" and not re.search(val, body): bad.append(f"必正则「{val}」未命中")
        except re.error:
            bad.append(f"断言正则非法「{val}」")
    return len(asserts) - len(bad), bad


def skill_docs(skill, cap=48_000):
    f = TDIR / skill / "技能文件.txt"
    if not f.exists(): sys.exit(f"缺 {f}")
    parts = []
    for line in f.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            p = Path(line).expanduser()
            doc = p.read_text()
            if len(doc) > cap:  # 大文档截断：快扫只需核心规则；全文大 prompt 是超时/SSL断源（迭代经验#10）
                doc = doc[:cap] + "\n\n（……文档超长已截断，仅保留前部分……）"
            # 头部禁写绝对路径：CLI agent 模型见路径就想 Read，工具被禁后调用意图泄漏进产物（迭代经验#11）
            parts.append(f"### 技能文档：{skill}（全文已在下方完整给出，无需读取任何文件）\n\n{doc}")
    return "\n\n".join(parts)


def filler_docs(skill, n):
    """M4 等长对照：取字母序下一个其他 skill 的文档，截到与目标技能文档等长（长度安慰剂对照）。"""
    names = sorted(d.name for d in SKILLS_DIR.iterdir()
                   if d.is_dir() and (d / "SKILL.md").exists() and d.name != skill)
    doc = ""
    if names:
        p = SKILLS_DIR / names[0] / "SKILL.md"
        doc = p.read_text()[:max(n, 200)]
    return (doc + FILLER)[:n] if len(doc) < n else doc


def manifest():
    rows = []
    for d in sorted(SKILLS_DIR.iterdir()):
        sk = d / "SKILL.md"
        if not sk.exists(): continue
        fm, _ = split_fm("\n".join(sk.read_text().splitlines()[:40]))
        rows.append(f"- {fm.get('name', d.name)} | {fm.get('description', '')[:120]} | 路径: {sk}")
    return "\n".join(rows)


# ---------- run ----------

LEAK_RE = re.compile(r"<tool_call>|｜｜DSM|\]<\]minimax|<\|tool\||multi_tool_use")
HARDEN = ("\n\n【硬性要求】你的上一次输出包含工具调用标记或过短，已被判无效。本次必须直接输出最终答案的"
          "纯文本本身：禁止读取文件、禁止调用工具、禁止执行命令、禁止输出任何调用/指令标记。")


def valid_out(out):
    """产物有效性门禁（迭代经验#11）：工具泄漏或 <100 字 = 无效，不是可评分产物。"""
    return bool(out) and len(out) >= 100 and not LEAK_RE.search(out)


def cell_prompt(skill, task_path, mode):
    _, uprompt, _, _ = load_task(task_path)
    if mode == "M1":
        return uprompt, []
    if mode == "M2":
        return (f"【技能文档】以下文档必须完整遵循：\n\n{skill_docs(skill)}\n\n"
                f"【通道约束】本通道为纯文本：禁止读取任何文件、禁止调用任何工具、禁止执行任何命令；"
                f"文档中提到的外部文件/脚本一律视为不需要，基于给定内容直接作答。\n\n【任务】\n{uprompt}"), []
    if mode == "M4":
        docs = skill_docs(skill)
        return (f"【参考材料】以下是背景参考材料：\n\n{filler_docs(skill, len(docs))}\n\n"
                f"【通道约束】纯文本作答，禁止读取文件/调用工具/执行命令。\n\n【任务】\n{uprompt}"), []
    p = (f"【已安装技能清单】\n{manifest()}\n\n"
         f"你可以用 Read 工具读取清单中你认为需要的技能文件（绝对路径）。"
         f"回答第一行必须写「已读：<你实际读取的每个路径>」，然后完成任务。\n\n【任务】\n{uprompt}")
    return p, ["--permission-mode", "auto"]


def write_cell(dest, skill, task, model, mode, trial, status, dur, out):
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"---\n技能: {skill}\n任务: {task}\n模型: {model}\n模式: {mode}\n试验: {trial}\n"
                    f"耗时: {dur}s\n时间: {ts()}\n状态: {status}\n---\n\n{out}\n")
    ledger(RDIR / "台账.csv", {"ts": ts(), "技能": skill, "任务": task, "模型": model,
                               "模式": mode, "试验": trial, "状态": status, "路径": str(dest)})


def run_cell(skill, task_path, model, mode, trial):
    name = f"{task_path.stem}-{mode}" + ("" if trial == 1 else f"-t{trial}")
    dest = RDIR / skill / model / f"{name}.md"
    if mode == "M3" and "@" in model:
        write_cell(dest, skill, task_path.stem, model, mode, trial, "fail:api-no-tools", 0,
                   "（API 通道无工具链，M3 触发模拟仅限 CLI 模型）")
        return f"{skill}/{model}/{name} -> fail:api-no-tools"
    prompt, extra = cell_prompt(skill, task_path, mode)
    tools = "Read" if mode == "M3" else ""
    t0 = time.time()
    out, err = call(model, prompt, tools=tools, extra=extra)
    if out and mode != "M3" and not valid_out(out):  # 门禁：泄漏/过短自动硬化重跑一次（M3 依赖工具，不适用）
        out2, _ = call(model, prompt + HARDEN, tools=tools, extra=extra)
        if valid_out(out2):
            out, err = out2, ""
        else:
            out = out2 or out
    dur = int(time.time() - t0)
    if out and mode != "M3" and not valid_out(out):
        status = f"fail:invalid-output({len(out)}字)"
    else:
        status = "ok" if out else f"fail:{err}"
    write_cell(dest, skill, task_path.stem, model, mode, trial, status, dur, out)
    return f"{skill}/{model}/{name} -> {status}"


def done_cells():
    done = set()
    led = RDIR / "台账.csv"
    if led.exists():
        for r in csv.DictReader(open(led)):
            if r.get("状态") == "ok" and r.get("路径") and Path(r["路径"]).exists():
                done.add((r.get("技能"), r.get("任务"), r.get("模型"), r.get("模式"), r.get("试验", "1")))
    return done


def adaptive_map(fn, items, P, label):
    """自适应并发：min(P,8) 起步指数爬到 P，零失败就翻倍，失败/429 减半+退避（key 已全局轮转）。"""
    C, results, i = max(2, min(P, 8)), [], 0
    while i < len(items):
        batch = items[i:i + C]; i += C
        with ThreadPoolExecutor(len(batch)) as ex:
            futs = [ex.submit(fn, *it) for it in batch]
            for f in as_completed(futs):
                r = f.result(); results.append(r); log(r)
        fails = sum(1 for r in results[-len(batch):] if "fail" in r)
        if fails:
            C = max(2, C // 2)
            time.sleep(min(60, 5 * fails))
            log(f"{label}: 本批失败 {fails}，并发退避至 {C} 重试")
        elif C < P:
            C = min(P, C * 2)
            log(f"{label}: 批零失败，并发爬升至 {C}")
    return results


def cmd_run(a):
    single_instance(a.models)  # 每模型一条车道锁，多车道并行
    cells, done = [], done_cells()
    for skill in a.skills.split(","):
        tasks = sorted((TDIR / skill).glob("T*.md"))
        if not tasks:
            log(f"跳过 {skill}：任务集缺 T*.md（名字不匹配或未建题，不影响其余）")
            continue
        for t in tasks:
            for m in a.models.split(","):
                for mode in a.modes.split(","):
                    for tr in range(1, a.trials + 1):
                        if (skill, t.stem, m, mode, str(tr)) in done:
                            log(f"跳过已成功 {skill}/{m}/{t.stem}-{mode}-t{tr}")
                            continue
                        cells.append((skill, t, m, mode, tr))
    log(f"待跑 {len(cells)} 格，自适应并发上限 {a.P}（8 起步，零失败翻倍，遇错减半）")
    results = adaptive_map(run_cell, cells, a.P, "run")
    fail = sum(1 for r in results if "-> fail" in r)
    log(f"完成。失败 {fail} 格（详见 结果/台账.csv）")


# ---------- 断言层 ----------

def collect_artifacts(skills):
    arts = []
    skip = [m for m in os.environ.get("BENCH_SKIP_MODELS", "").split(",") if m]
    for skill in skills:
        for f in sorted((RDIR / skill).glob("*/*.md")):
            fm, body = split_fm(f.read_text())
            if not fm.get("模型") or fm["模型"] in skip: continue
            if str(fm.get("状态", "")).startswith("fail"): continue  # fail 格不评分：等内容重产（#16）
            tfm, _, ref, asserts = load_task(TDIR / skill / (fm["任务"] + ".md"))
            arts.append({"file": f, "skill": skill, "task": fm["任务"], "model": fm["模型"],
                         "mode": fm["模式"], "body": body.strip(), "ref": ref,
                         "触发": tfm.get("触发", "正"), "asserts": asserts})
    return arts


def cmd_check(a):
    print("| 技能 | 模型 | 任务 | 模式 | 断言 |")
    print("|---|---|---|---|---|")
    for art in collect_artifacts(a.skills.split(",")):
        if not art["asserts"]:
            print(f"| {art['skill']} | {art['model']} | {art['task']} | {art['mode']} | （无断言） |")
            continue
        ok, bad = run_assertions(art["asserts"], art["body"])
        print(f"| {art['skill']} | {art['model']} | {art['task']} | {art['mode']} | {ok}/{len(art['asserts'])}"
              + (f" ✗ {'；'.join(bad[:3])} |" if bad else " ✓ |"))


# ---------- score ----------

def parse_json(out):
    m = re.search(r"\{.*\}", out, re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception: return None


def weighted(j, mode):
    w = WEIGHTS["M1" if mode == "M1" else "*"]
    s, tot = 0.0, 0.0
    for d, wt in w.items():
        v = j.get(d)
        if isinstance(v, (int, float)) and 0 <= v <= 5:
            s += v * wt; tot += wt
    return round(s / tot, 2) if tot else None


def score_cell(art, code, scorer, self_mode=False):
    body = art["body"].replace(art["model"], "▇▇").replace(art["model"].split("@")[0], "▇▇")
    docs = skill_docs(art["skill"])[:6000] if art["mode"] in ("M2", "M3") else "（本产物无技能文档）"
    a_txt = "（本任务无确定性断言）"
    if art["asserts"]:
        ok, bad = run_assertions(art["asserts"], art["body"])
        a_txt = f"通过 {ok}/{len(art['asserts'])}" + (f"；未过：{'；'.join(bad)}" if bad else "（全部通过）")
        (SDIR / art["skill"] / code / "断言.json").parent.mkdir(parents=True, exist_ok=True)
        (SDIR / art["skill"] / code / "断言.json").write_text(
            json.dumps({"过": ok, "总": len(art["asserts"]), "未过": bad}, ensure_ascii=False, indent=1))
    prompt = (f"{RUBRIC}\n\n【确定性断言结果】{a_txt}\n\n【技能文档】\n{docs}\n\n"
              f"【任务评分参考】\n{art['ref']}\n\n【匿名产物 {code}】\n{body}")
    out, err = call(scorer, prompt, tools="", schema=SCORE_SCHEMA)
    j = parse_json(out) if out else None
    if not j or j.get("判定") == "INVALID":
        # 判官失败不落盘文件（文件存在会永久堵住重评）+ 返回 fail 标记触发自适应退避（429 风暴教训）
        ledger(SDIR / "台账.csv", {"ts": ts(), "技能": art["skill"], "代号": code, "评分者": scorer,
                                   "判定": ("自评" if self_mode else "") + "INVALID",
                                   "总分": None, "路径": ""})
        return (f"{art['skill']}/{code} x {scorer}{'(自评)' if self_mode else ''} "
                f"-> fail:judge-invalid({(err or out or '解析失败')[:40]})")
    dest = SDIR / art["skill"] / code / (f"{scorer}.自评.json" if self_mode else f"{scorer}.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"评分者": scorer, "自评": self_mode, **j}, ensure_ascii=False, indent=1))
    total = weighted(j, art["mode"])
    ledger(SDIR / "台账.csv", {"ts": ts(), "技能": art["skill"], "代号": code, "评分者": scorer,
                               "判定": ("自评" if self_mode else "") + str(j.get("判定", "")),
                               "总分": total, "路径": str(dest)})
    return f"{art['skill']}/{code} x {scorer}{'(自评)' if self_mode else ''} -> {j.get('判定')} {total}"


def cmd_score(a):
    single_instance(f"score.{a.scorers}")  # 按判官集分锁：多判官车道可并行（哈希代号下安全，#19/#20）
    arts = collect_artifacts(a.skills.split(","))
    random.Random(2026).shuffle(arts)
    for art in arts:  # 代号按技能内编号，映射表每技能一份（防多批互相覆盖）
        pass
    cnt, mapping_all = {}, {}
    import hashlib
    for art in arts:
        s = art["skill"]
        # 代号=产物路径哈希：跨评分进程永久稳定（序号代号线索：产物清单一变即错挂分数，#19）
        code = "A" + hashlib.md5(str(art["file"]).encode()).hexdigest()[:8]
        art["code"] = code
        mapping_all.setdefault(s, {})[code] = {k: str(v) for k, v in art.items()
                                               if k in ("file", "skill", "task", "model", "mode", "触发")}
    for s, mapping in mapping_all.items():
        mp = SDIR / s / "映射表.json"
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(json.dumps(mapping, ensure_ascii=False, indent=1))
    log(f"产物 {len(arts)} 份已匿名化（映射表每技能一份，仅存本地，禁外传）")
    jobs, warn = [], []
    for art in arts:
        base = lambda m: m.split("@")[0]  # 同 base 名（含 @api 变体）视为同模型，互斥防自评
        ss = [s for s in a.scorers.split(",") if base(s) != base(art["model"])]
        if len(ss) < MIN_SCORERS:
            warn.append(f"{art['skill']}/{art['task']}-{art['mode']} 评分者不足({len(ss)})")
        for s in ss:
            if not list((SDIR / art["skill"] / art["code"]).glob(f"{s}.json")):
                jobs.append((art, art["code"], s, False))
        if a.self and art["model"] in a.scorers.split(",") and \
           not list((SDIR / art["skill"] / art["code"]).glob(f"{art['model']}.自评.json")):
            jobs.append((art, art["code"], art["model"], True))  # 对角线自评（仅判官池内模型；暂停模型不发起调用）
    if len(jobs) == 0 and warn:  # 全部产物都无评者才退；部分不足=该车道不覆盖它们（别的车道管），跳过继续（#20）
        sys.exit("评分者不足，扩 --scorers 清单再跑：\n" + "\n".join(warn[:5]))
    if warn:
        log(f"本车道跳过评分者不足的产物 {len(warn)} 项（由其他判官车道覆盖）")
    fams = {fam(s) for s in a.scorers.split(",")}
    if os.environ.get("BENCH_FIXED_POOL"):  # 固定满载池：不排队尾不等爬坡（波次批会卡最慢判官，#20）
        log(f"待评 {len(jobs)} 份，固定并发池 {a.P}（无爬坡无波次）")
        with ThreadPoolExecutor(a.P) as ex:
            futs = [ex.submit(score_cell, *j) for j in jobs]
            for f in as_completed(futs): log(f.result())
    else:
        log(f"待评 {len(jobs)} 份，自适应并发上限 {a.P}；判官家族 {sorted(fams)}（同家族多票聚合时只计一票）")
        adaptive_map(score_cell, jobs, a.P, "score")
    log("评分完成")


# ---------- agg ----------

def cmd_agg(a):
    for skill in a.skills.split(","):
        mp = SDIR / skill / "映射表.json"
        mp = mp if mp.exists() else SDIR / "映射表.json"  # 兼容旧全局映射
        mapping = json.loads(mp.read_text())
        skip_models = {m for m in os.environ.get("BENCH_SKIP_MODELS", "").split(",") if m}
        by_model, bias_acc, rows_detail = {}, {}, []
        champs, judge_acc, trig, assert_sum = {}, {}, {}, {"过": 0, "总": 0}
        review = {"判定不一致": 0, "断言全挂": []}
        self_bias, self_acc = {}, {}  # 自评（--self）：自评分−他评中位；只测自偏，禁入总分
        totals = {}   # (model, task, mode) -> 家族去重票后的产物总分
        gains = {}    # (model, task) -> {"M2-M1":…, "hake":…, "M2-M4":…, "M4-M1":…}
        for code, meta in mapping.items():
            if meta["skill"] != skill or meta.get("model") in skip_models: continue  # 暂停模型不入榜（kimi，用户 2026-10-10 裁定）
            jsl = list((SDIR / skill / code).glob("*.json"))
            js = [json.loads(p.read_text()) for p in jsl
                  if p.name != "断言.json" and not p.name.endswith(".自评.json")]
            self_js = [json.loads(p.read_text()) for p in jsl if p.name.endswith(".自评.json")]
            if not js: continue
            mode, model = meta["mode"], meta["model"]
            jt = [t for t in (weighted(j, mode) for j in js) if t is not None]
            if not jt: continue
            for j, t in zip(js, jt):  # 复盘线索：判定与分值脱节检测
                v = j.get("判定")
                if (v == "PASS" and t < 3.5) or (v == "FAIL" and t >= 3.5):
                    review["判定不一致"] += 1
            # 家族去重票：同家族判官先取均值算 1 票，跨家族票取中位（PoLL/Apple）
            fv = {}
            for j, t in zip(js, jt):
                fv.setdefault(fam(j["评分者"]), []).append(t)
            total = round(statistics.median([statistics.mean(v) for v in fv.values()]), 2)
            for j in self_js:  # 对角线自偏测量
                st = weighted(j, mode)
                if st is not None:
                    self_bias.setdefault(model, []).append(st - statistics.median(jt))
                    self_acc.setdefault((model, mode), []).append(st)
            totals[(model, meta["task"], mode)] = total
            med = {}
            for d in DIMS:
                vals = [j.get(d) for j in js if isinstance(j.get(d), (int, float))]
                if vals: med[d] = statistics.median(vals)
            by_model.setdefault((model, mode), []).append(total)
            if mode == "M2":
                cur = champs.get(meta["task"])
                if not cur or total > cur[1]: champs[meta["task"]] = (model, total)
            for j, t in zip(js, jt):
                bias_acc.setdefault(j["评分者"], []).append(t - statistics.median(jt))
                judge_acc.setdefault((model, j["评分者"], mode), []).append(t)
            aj = SDIR / skill / code / "断言.json"
            if aj.exists():
                d = json.loads(aj.read_text()); assert_sum["过"] += d["过"]; assert_sum["总"] += d["总"]
                if d["总"] and d["过"] == 0:
                    review["断言全挂"].append(f"{meta['task']}/{model}/{mode}")
            rows_detail.append({"代号": code, "模型": model, "任务": meta["task"], "模式": mode,
                                **med, "总分": total})
        for (model, task), _g in {(m, t): 1 for (m, t, mo) in totals}.items():
            g = {}
            if (model, task, "M2") in totals and (model, task, "M1") in totals:
                d21 = round(totals[(model, task, "M2")] - totals[(model, task, "M1")], 2)
                g["M2-M1"] = d21
                m1 = totals[(model, task, "M1")]
                g["hake"] = round(d21 / (5 - m1), 3) if (0 < d21 and m1 < 4.99) else None  # 只在正增益时报；负增益分母小会爆表
            if (model, task, "M2") in totals and (model, task, "M4") in totals:
                g["M2-M4"] = round(totals[(model, task, "M2")] - totals[(model, task, "M4")], 2)
            if (model, task, "M4") in totals and (model, task, "M1") in totals:
                g["M4-M1"] = round(totals[(model, task, "M4")] - totals[(model, task, "M1")], 2)
            if g: gains[(model, task)] = g
        for code, meta in mapping.items():  # M3 触发准确率（正例命中 + 负例不误触）
            if meta["skill"] != skill or meta["mode"] != "M3": continue
            body = split_fm(Path(meta["file"]).read_text())[1]
            first = next((l for l in body.splitlines() if l.strip()), "")
            read_target = (str(SKILLS_DIR / skill) + "/") in first  # 带斜杠防 skill 误吃 skill-bench
            trig.setdefault(meta["model"], []).append(read_target if meta.get("触发", "正") == "正" else not read_target)
        skill_score = {}
        for (m, mode), v in by_model.items():
            if mode != "M2": continue
            stab = max(0.0, SS_STAB - statistics.pstdev(v) * 8)
            tr = trig.get(m)
            trig_s = (sum(tr) / len(tr) * SS_TRIG) if tr else SS_TRIG / 2
            skill_score[m] = round(statistics.mean(v) / 5 * SS_W + stab + trig_s, 1)
        producers = sorted({p for (p, j, m) in judge_acc if m == "M2"})
        judges = sorted({j for (p, j, m) in judge_acc if m == "M2"})
        mat = {p: {j: round(statistics.mean(judge_acc[(p, j, "M2")]), 2)
                   for j in judges if (p, j, "M2") in judge_acc} for p in producers}
        for p in producers:  # 对角线填自评均值（标"自"，行均/列均已排除）
            sv = self_acc.get((p, "M2"))
            if sv: mat[p][p] = round(statistics.mean(sv), 2)
        clues = []  # 复盘线索（自迭代输入）：逐条处置后记入 知识库/迭代经验.md
        if review["判定不一致"]:
            clues.append(f"判定与分值脱节 {review['判定不一致']} 处 → rubric 已加判定口径，复现则查判官")
        if review["断言全挂"]:
            clues.append(f"断言 0/N 全挂 {len(review['断言全挂'])} 格（题目或断言写错信号）：{review['断言全挂'][:3]}")
        neg = [f"{m}/{t}" for (m, t), g in gains.items() if (g.get("M2-M1") or 0) < 0]
        if neg:
            clues.append(f"负增益 {len(neg)} 格：{neg[:4]}（负例题负增益=设计预期，其余=skill 拖后腿，报告点名）")
        weak_trig = [m for m, v in trig.items() if v and sum(v) / len(v) < 0.5]
        if weak_trig:
            clues.append(f"触发准确率<50%：{weak_trig}（description 质量，改该技能 SKILL.md 触发词后复测）")
        biased = [s for s, v in bias_acc.items() if abs(statistics.mean(v)) > 1.0]
        if biased:
            clues.append(f"判官偏差超阈：{biased}（按 交叉评分 §偏差处理 处置）")
        for m, v in self_bias.items():
            if statistics.mean(v) > 1.0:
                clues.append(f"自偏超阈：{m} +{statistics.mean(v):.2f}（高估自己，报告已披露）")
        rep = [f"# {skill} 横评报告（{ts()}）", "",
               f"- 任务数 {len({m['task'] for m in mapping.values() if m['skill'] == skill})}"
               f"，模型 {len({m['model'] for m in mapping.values() if m['skill'] == skill})} 个"
               f"，判官 {len(judges)} 名（受控判官；同家族多票聚合时只计一票）",
               f"- 确定性断言层：{assert_sum['过']}/{assert_sum['总']} 通过",
               f"- SkillScore = M2均分/5×{SS_W:.0f} + 稳定{SS_STAB:.0f}−8σ + 触发准确率×{SS_TRIG:.0f}（无M3记{SS_TRIG/2:.0f}）", "",
               "## 总榜（SkillScore，降序）", "| 模型 | 家族 | SkillScore | M2均分 | σ | 触发准确率 |", "|---|---|---|---|---|---|"]
        for m, v in sorted(skill_score.items(), key=lambda x: -x[1]):
            tr = trig.get(m)
            rep.append(f"| {m} | {fam(m)} | **{v}** | {statistics.mean(by_model[(m, 'M2')]):.2f} | "
                       f"{statistics.pstdev(by_model[(m, 'M2')]):.2f} | "
                       f"{(str(sum(tr)) + '/' + str(len(tr))) if tr else '-'} |")
        rep += ["", "## N×N 交叉方阵（M2；行=生产者，列=判官，对角线=自评·不入行均/列均）",
                "| 生产者＼判官 | " + " | ".join(judges) + " | 行均 |",
                "|---|" + "---|" * (len(judges) + 1)]
        for p in producers:
            cells, vals = [], []
            for j in judges:
                v = mat[p].get(j)
                if j == p and v is not None:
                    cells.append(f"{v:.2f}自")
                else:
                    cells.append(f"{v:.2f}" if v is not None else "—")
                    if v is not None: vals.append(v)
            rep.append(f"| {p} | " + " | ".join(cells) +
                       (f" | {statistics.mean(vals):.2f} |" if vals else " | - |"))
        colm = {j: statistics.mean([mat[p][j] for p in producers if j in mat[p] and p != j])
                for j in judges if any(j in mat[p] and p != j for p in producers)}
        rep.append("| 列均（判官严格度，越低越严） | " + " | ".join(
            f"{colm[j]:.2f}" for j in judges if j in colm) +
            (f" | {statistics.mean(list(colm.values())):.2f} |" if colm else " | - |"))
        rep += ["", "## 冠军表", "| 任务 | 模型 | 分 |", "|---|---|---|"]
        for t, (m, s) in sorted(champs.items()): rep.append(f"| {t} | {m} | {s} |")
        rep += ["", "## 增益（hake=吃掉多少剩余提升空间；M2-M4 为剔除长度安慰剂后的纯内容增益）",
                "| 模型 | 任务 | M2−M1 | hake | M2−M4 | M4−M1 |", "|---|---|---|---|---|---|"]
        for (m, t), g in sorted(gains.items()):
            rep.append(f"| {m} | {t} | {g.get('M2-M1', '-')} | {g.get('hake', '-')} | "
                       f"{g.get('M2-M4', '-')} | {g.get('M4-M1', '-')} |"
                       + (" ⚠负增益" if g.get("M2-M1", 1) < 0 else ""))
        rep += ["", "## 触发准确率（M3，正例命中+负例不误触）", "| 模型 | 准确 |", "|---|---|"]
        for m, v in trig.items(): rep.append(f"| {m} | {sum(v)}/{len(v)} |")
        rep += ["", "## 评分者偏差", "| 评分者 | 家族 | bias | 判定 |", "|---|---|---|---|"]
        for s, v in bias_acc.items():
            b = statistics.mean(v)
            tag = "作废复评" if abs(b) > 1.5 else ("降权0.5" if abs(b) > 1.0 else "ok")
            rep.append(f"| {s} | {fam(s)} | {b:+.2f} | {tag} |")
        for m, v in sorted(self_bias.items()):
            rep.append(f"| {m}（自评） | {fam(m)} | {statistics.mean(v):+.2f} | 自偏测量，不入总分 |")
        rep += ["", "## 复盘线索（自迭代输入；逐条处置后记入 知识库/迭代经验.md）"]
        rep += [f"- {c}" for c in clues] or ["- （本批无异常线索）"]
        rep += ["", "## 明细", "| 代号 | 模型 | 任务 | 模式 | " + " | ".join(DIMS) + " | 总分 |",
                "|---|---|---|---|" + "---|" * (len(DIMS) + 1)]
        for r in rows_detail:
            rep.append("| " + " | ".join(str(r.get(k) if r.get(k) is not None else "-") for k in
                        ["代号", "模型", "任务", "模式"] + DIMS + ["总分"]) + " |")
        REPDIR.mkdir(exist_ok=True)
        (REPDIR / f"{datetime.now():%Y%m%d}-{skill}.md").write_text("\n".join(rep))
        if rows_detail:
            fields = ["代号", "模型", "任务", "模式"] + DIMS + ["总分"]  # 固定列序：M1 行缺技能遵循，首行推导会崩
            with open(REPDIR / f"{skill}-明细.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
                w.writeheader()
                w.writerows([{k: r.get(k) for k in fields} for r in rows_detail])
        agg_out = {"skill": skill, "generated": ts(), "skill_score": skill_score,
                   "best": max(skill_score, key=skill_score.get) if skill_score else None,
                   "leaderboard": [{"模型": m, "家族": fam(m), "SkillScore": v}
                                   for m, v in sorted(skill_score.items(), key=lambda x: -x[1])],
                   "m2_mean": {m: round(statistics.mean(v), 2) for (m, mo), v in by_model.items() if mo == "M2"},
                   "m1_mean": {m: round(statistics.mean(v), 2) for (m, mo), v in by_model.items() if mo == "M1"},
                   "m4_mean": {m: round(statistics.mean(v), 2) for (m, mo), v in by_model.items() if mo == "M4"},
                   "gains": {f"{m}|{t}": g for (m, t), g in gains.items()},
                   "trigger_accuracy": {m: f"{sum(v)}/{len(v)}" for m, v in trig.items()},
                   "assert": assert_sum, "复盘线索": clues, "self_bias": {m: round(statistics.mean(v), 2)
                                                                           for m, v in self_bias.items()},
                   "judge_matrix_M2": mat, "tasks": rows_detail}
        (REPDIR / f"{skill}-聚合.json").write_text(json.dumps(agg_out, ensure_ascii=False, indent=1))
        log(f"报告 -> {REPDIR}/{datetime.now():%Y%m%d}-{skill}.md (+聚合.json +明细.csv)")


# ---------- cross（三维 N×N×A：同功能组技能以第一个为基准对比） ----------

def cmd_cross(a):
    skills = a.skills.split(",")
    base = skills[0]
    aggs = {}
    for s in skills:
        f = REPDIR / f"{s}-聚合.json"
        if not f.exists(): sys.exit(f"缺 {f}（{s} 还没 agg）")
        aggs[s] = json.loads(f.read_text())

    def taskmap(ag):
        return {r["任务"]: r["总分"] for r in ag["tasks"] if r["模式"] == "M2"}

    tmaps = {s: taskmap(aggs[s]) for s in skills}
    common = sorted(set.intersection(*[set(t) for t in tmaps.values()])) if len(skills) > 1 else []
    rows = []
    for t in common:
        row = {"任务": t}
        for s in skills:
            row[s] = tmaps[s].get(t)
        for s in skills[1:]:
            v, b = row[s], row[base]
            row[f"Δ({s}-基准)"] = round(v - b, 2) if v is not None and b is not None else None
        rows.append(row)
    组名 = a.group or "+".join(skills)
    out = {"组": 组名, "基准": base, "skills": skills, "generated": ts(), "任务对比": rows,
           "SkillScore对比": {s: aggs[s]["skill_score"] for s in skills},
           "最佳搭配": {s: aggs[s].get("best") for s in skills},
           "judge_matrices_M2": {s: aggs[s]["judge_matrix_M2"] for s in skills}}
    REPDIR.mkdir(exist_ok=True)
    (REPDIR / f"三维-{组名}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    rep = [f"# 三维对比：{组名}（基准 = {base}，{ts()}）", "",
           "同功能组技能在同一任务集上对比；Δ 为对基准技能的分差（M2 家族去重票总分）。", "",
           "| 任务 | " + " | ".join(skills) + " | " + " | ".join(f"Δ({s}−基准)" for s in skills[1:]) + " |",
           "|---|" + "---|" * (len(skills) + len(skills) - 1)]
    for r in rows:
        cells = [str(r[s] if r[s] is not None else "-") for s in skills]
        cells += [str(r[f"Δ({s}-基准)"] if r[f"Δ({s}-基准)"] is not None else "-") for s in skills[1:]]
        rep.append("| " + r["任务"] + " | " + " | ".join(cells) + " |")
    rep += ["", "## SkillScore 对比（每技能各自的 模型×判官方阵 已存 judge_matrices_M2）", ""]
    for s in skills:
        sc = aggs[s]["skill_score"]
        best = aggs[s].get("best")
        top3 = sorted(sc.items(), key=lambda x: -x[1])[:3] if sc else []
        rep.append(f"- **{s}**：最佳搭配 {best}；模型Top3 " +
                   "、".join(f"{m}={v}" for m, v in top3))
    (REPDIR / f"{datetime.now():%Y%m%d}-三维-{组名}.md").write_text("\n".join(rep))
    log(f"三维对比 -> {REPDIR}/三维-{组名}.json (+md)")


# ---------- selfscore（wiki 自评：判官池给 skill-bench 自己的 llm-wiki 打分） ----------

WIKI_DIMS = ["自洽准确", "可操作", "简洁", "导航有效"]
WIKI_RUBRIC = """你是文档质量评审官，评审一份 agent 知识库（llm-wiki）的页面。维度（0-5 整数）：
- 自洽准确：口径/命令/路径前后一致，无过时表述（若下方给了一致性检查结果，以结果为准）
- 可操作：照着能直接执行（命令可复制、输入输出明确、路径存在）
- 简洁：无冗余重复，符合「短表+按需开节」原则
- 导航有效：能让读者快速判断本页管什么、细节去哪找
判定：PASS / CONDITIONAL / FAIL；点评一句话。只输出 JSON：自洽准确、可操作、简洁、导航有效、判定、点评。"""
WIKI_SCHEMA = {"type": "object",
               "properties": {**{d: {"type": "integer"} for d in WIKI_DIMS},
                              "判定": {"type": "string"}, "点评": {"type": "string"}},
               "required": WIKI_DIMS + ["判定"]}


def cmd_selfscore(a):
    root = Path(__file__).resolve().parent.parent
    kb = root / "知识库"
    files = [root / "SKILL.md"] + sorted(kb.glob("*.md")) + [kb / "subagent" / "SUBAGENT-必读.md"]
    files = [f for f in files if f.exists() and not f.name.startswith("自评") and f.name != "迭代经验.md"]
    src = (root / "tools" / "bench.py").read_text()
    jk = (kb / "交叉评分.md").read_text()
    agg_doc = (kb / "聚合报告.md").read_text()
    sk = (root / "SKILL.md").read_text()
    fact = lambda name, ok: f"- {'✓' if ok else '✗ 不一致'} {name}"
    facts = "\n".join([
        fact("交叉评分.md 与 bench.py 判定口径（≥4.0→PASS）一致",
             ("≥4.0→PASS" in jk) == ("加权≥4.0→PASS" in src)),
        fact("聚合报告.md SkillScore 权重与 bench.py 常量（60/20/20）一致",
             ("60" in agg_doc) and ("SS_W, SS_STAB, SS_TRIG = 60.0, 20.0, 20.0" in src)),
        fact("SKILL.md 四模式 M1-M4 齐全", all(m in sk for m in ("M1", "M2", "M3", "M4"))),
    ])
    log(f"wiki 自评：{len(files)} 页 × {len(a.scorers.split(','))} 判官")

    def one(f, scorer):
        rel = f.relative_to(root)
        prompt = (f"{WIKI_RUBRIC}\n\n【一致性检查（脚本自动跑）】\n{facts}\n\n"
                  f"【待评审页面：{rel}】\n" + f.read_text()[:9000])
        out, err = call(scorer, prompt, tools="", schema=WIKI_SCHEMA)
        j = parse_json(out) if out else None
        return str(rel), scorer, (j or {"判定": "INVALID", "点评": f"解析失败 {err}"})

    res = {}
    with ThreadPoolExecutor(a.P) as ex:
        futs = [ex.submit(one, f, s) for f in files for s in a.scorers.split(",")]
        for fu in as_completed(futs):
            rel, scorer, j = fu.result()
            res.setdefault(rel, []).append(j)
            log(f"自评 {rel} x {scorer} -> {j.get('判定')}")
    rows, lows = [], []
    for rel in sorted(res):
        js = res[rel]
        med = {d: statistics.median([j[d] for j in js if isinstance(j.get(d), (int, float))])
               for d in WIKI_DIMS if any(isinstance(j.get(d), (int, float)) for j in js)}
        verdict = next((j.get("判定") for j in js if j.get("判定") not in (None, "INVALID")), "INVALID")
        note = next((j.get("点评") for j in js if j.get("点评")), "")
        rows.append({"文件": rel, **med, "判定": verdict, "点评": note[:80]})
        if any(v < 3.5 for v in med.values()):
            lows.append(f"{rel}（" + "，".join(f"{d}{v}" for d, v in med.items() if v < 3.5) + "）")
    sec = [f"\n## {ts()}（判官：{a.scorers}）", "",
           "| 文件 | " + " | ".join(WIKI_DIMS) + " | 判定 | 点评 |",
           "|---|" + "---|" * (len(WIKI_DIMS) + 2)]
    for r in rows:
        sec.append("| " + " | ".join(str(r.get(k) if r.get(k) is not None else "-")
                                     for k in ["文件"] + WIKI_DIMS + ["判定", "点评"]) + " |")
    if lows:
        sec += ["", "**低分点名（<3.5，按 迭代经验 流程处置后复评）**："] + [f"- {l}" for l in lows]
    sec.append("")
    p = kb / "自评.md"
    if not p.exists():
        p.write_text("# 自评（wiki 自己给自己打分 · 追加制；趋势看各维度中位数走势）\n")
    with open(p, "a") as f:
        f.write("\n".join(sec) + "\n")
    (kb / "自评.json").write_text(json.dumps({"generated": ts(), "pages": rows}, ensure_ascii=False, indent=1))
    log(f"自评落盘 -> {p}（+自评.json 快照）")


# ---------- site ----------

HTML = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="120"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SkillFit · 技能×模型契合度榜单</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#111827;--sub:#6b7280;--line:#e5e7eb;--acc:#2563eb;--acc2:#eef2ff;--ok:#059669;--okbg:#ecfdf5;--bad:#dc2626;--k:#eef2ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.65 -apple-system,"PingFang SC","Segoe UI",Roboto,sans-serif}
header{position:sticky;top:0;z-index:9;background:rgba(255,255,255,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.hbar{max-width:1180px;margin:0 auto;padding:10px 20px 0;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.brand{font-size:17px;font-weight:800}.brand i{color:var(--acc);font-style:normal}
.chip{background:var(--acc2);color:var(--acc);border-radius:999px;padding:2px 12px;font-size:12px;font-weight:600}
.chip.g{background:var(--okbg);color:var(--ok)}
.sp{flex:1}
.tabs{max-width:1180px;margin:0 auto;padding:8px 20px 0;display:flex;gap:6px;flex-wrap:wrap}
.tab{border:1px solid var(--line);background:#fff;border-radius:999px;padding:5px 16px;font-size:13px;font-weight:600;color:var(--sub);cursor:pointer}
.tab.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.wrap{max-width:1180px;margin:0 auto;padding:6px 20px 80px}
.page{display:none}.page.on{display:block}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:12px 0;box-shadow:0 1px 2px rgba(16,24,40,.04)}
h2.pt{font-size:15px;font-weight:700;margin:22px 0 4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:12px}
.mcard{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:#fff;display:flex;flex-direction:column;align-items:flex-start}
.mcard b{display:block;font-size:14px;margin-bottom:6px}
.mcard .tgs{margin-top:auto;padding-top:6px}
.mcard span{display:inline-block;background:var(--k);border-radius:8px;padding:1px 8px;margin:2px 3px 2px 0;font-size:12px;color:#3730a3}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--sub);text-align:left;padding:8px 10px;border-bottom:2px solid var(--line);white-space:nowrap}
td{padding:7px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
tr:hover td{background:#fafbff}
.tblwrap{overflow-x:auto}
.tblscroll{max-height:72vh;overflow:auto}
.tblscroll tr:first-child th{position:sticky;top:0;background:#fff;z-index:2;box-shadow:0 1px 0 var(--line)}
.crlayout{display:grid;grid-template-columns:190px 1fr;gap:16px;align-items:start}
.crnav{position:sticky;top:12px;max-height:calc(100vh - 30px);overflow-y:auto;font-size:12.5px;padding-right:4px}
.crnav .catlnk{display:block;margin:10px 0 3px;font-weight:700;color:var(--ink);font-size:12px;text-decoration:none;padding:2.5px 8px;border-radius:6px;cursor:pointer}
.crnav .catlnk:first-child{margin-top:0}
.crnav .catlnk:hover{background:#eef2f7}
.crnav .crgrp{display:none;margin:2px 0 6px}
.crnav .catlnk.open{background:#e8eefb}
.crnav .catlnk.open+.crgrp{display:block}
.crnav a{display:block;color:var(--sub);text-decoration:none;padding:2.5px 8px;border-radius:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.crnav a:hover{background:#eef2f7;color:var(--ink)}
.crnav a.on{background:var(--acc);color:#fff}
@media(max-width:860px){.crlayout{grid-template-columns:1fr}.crnav{position:static;max-height:220px;border:1px solid var(--line);border-radius:10px;padding:8px}}
.crmain{min-width:0}
.best td{background:var(--okbg);font-weight:700}
.num{font-weight:700;text-align:right}
th.num{text-align:right}
.win{background:var(--okbg);color:var(--ok);font-weight:700;border-radius:6px;padding:2px 8px;display:inline-block}
.neg{color:var(--bad);font-weight:600}.pos{color:var(--ok);font-weight:600}
.search{width:100%;max-width:420px;border:1px solid var(--line);border-radius:10px;padding:8px 14px;font-size:13px;margin:12px 0;outline:none}
.search:focus{border-color:var(--acc)}
details.sk{border:1px solid var(--line);border-radius:12px;background:#fff;margin:8px 0}
details.sk>summary{list-style:none;cursor:pointer;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;padding:11px 16px}
details.sk>summary::-webkit-details-marker{display:none}
details.sk>summary:hover{background:#fafbff;border-radius:12px}
.skname{font-weight:700;font-size:14px}
.skname a{color:var(--ink);text-decoration:none}
.gloss{color:var(--sub);font-size:12.5px}
.badge{background:var(--acc);color:#fff;border-radius:999px;padding:1px 10px;font-size:12px;font-weight:600}
.ss{margin-left:auto;color:var(--sub);font-size:12px}
.cap{font-size:12px;color:var(--sub);margin:14px 0 4px;font-weight:600}
.ticker{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.tk{border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:12px;color:var(--sub)}
.tk b{color:var(--ink)}
details.pendd summary{cursor:pointer;color:var(--sub);font-size:13px}
.pend{font-size:12px;color:var(--sub);line-height:2}
.foot{text-align:center;color:var(--sub);font-size:12px;margin-top:40px}
</style></head><body>
<header><div class="hbar">
<span class="brand">SkillFit</span>
<span class="chip g" id="c1"></span><span class="chip" id="c2"></span><span class="chip" id="c4"></span><span class="chip" id="c3"></span>
<span class="sp"></span><span style="font-size:12px;color:var(--sub)">measured, not guessed</span>
</div>
<div class="tabs">
<div class="tab on" data-t="ov">总览</div>
<div class="tab" data-t="sk">技能榜</div>
<div class="tab" data-t="cr">同类对比</div>
<div class="tab" data-t="c3">3D 矩阵</div>
<div class="tab" data-t="lv">实时动态</div>
</div></header>
<div class="wrap">
<div class="page on" id="pg-ov"></div>
<div class="page" id="pg-sk"></div>
<div class="page" id="pg-cr"></div>
<div class="page" id="pg-c3"><div class="card" style="font-size:13px;color:var(--sub);display:flex;gap:14px;align-items:center;flex-wrap:wrap"><span style="max-width:640px">3D 评分矩阵（N×N×A）：N×N = 生产者×判官的交叉判分面，A = 分层轴。<b>越绿越强、越红越弱</b>，拖拽旋转 · 滚轮缩放 · W/S 前进后退 · A/D 平移（近处方块自动淡化）· 悬停看格 · 层距可展开对照。</span>
<select id="c3cat" style="border:1px solid var(--line);border-radius:8px;padding:4px 10px;font-size:13px;background:#fff;outline:none"><option value="">全部总览（A=大类）</option></select></div>
<div class="card" style="padding:10px 14px">
<div id="c3box" style="height:600px;border-radius:10px;overflow:hidden;position:relative;background:#fafbfc"></div>
<div style="display:flex;align-items:center;gap:10px;font-size:12px;color:var(--sub);margin-top:8px;flex-wrap:wrap">
<span>判分均值</span><span style="width:150px;height:10px;border-radius:5px;background:linear-gradient(90deg,hsl(0,85%,42%),hsl(14,85%,46%),hsl(28,85%,50%),hsl(45,85%,54%),hsl(75,85%,58%),hsl(118,85%,62%))"></span><span id="c3rng"></span><span class="sp"></span><span>拖拽旋转 · 滚轮缩放 · 悬停看格</span>
</div></div></div>
<div class="page" id="pg-lv"></div>
<div class="foot">SkillFit · 技能×模型契合度基准 · 数据 5 分钟更新 / 页面 2 分钟重载（标签与搜索状态自动保留）</div>
</div>
<script>fetch('data.json').then(r=>r.json()).then(D=>{
const bg=v=>v==null?'':'background:hsl('+Math.round(v/5*120)+',64%,88%)';
const ent=Object.entries(D.skills||{});
const sc=e=>e[1].ss_v2||0;  // v2 百分位
const scored=ent.filter(e=>e[1].leaderboard&&e[1].leaderboard.length).sort((a,b)=>sc(b)-sc(a));
const pending=ent.filter(e=>!(e[1].leaderboard&&e[1].leaderboard.length));
document.getElementById('c1').textContent='已出分 '+scored.length;
document.getElementById('c2').textContent='待评分 '+pending.length;
const judged=scored.reduce((a,e)=>a+Object.values(e[1].judge_matrix_M2||{}).reduce((b,row)=>b+Object.keys(row||{}).length,0),0);
document.getElementById('c4').textContent='交叉判分 '+(judged>=10000?(judged/10000).toFixed(1)+' 万':judged);
if(D.live)document.getElementById('c3').textContent='快照 '+D.live.generated.slice(0,16);
/* 数据体检卡：五模型完成格 + 最佳搭配分布 */
const bestCnt={};scored.forEach(([s,A])=>{if(A.best){const m=A.best.split('@')[0];bestCnt[m]=(bestCnt[m]||0)+1}});
const progArr=(D.live&&D.live.progress)?D.live.progress:[];
const maxOk=Math.max(1,...progArr.map(p=>p['ok']||0));
const HEALTH=`<h2 class="pt">数据体检</h2><div class="card"><div class="cap">五模型完成格（每格 = 技能×模型 的一个产物单元）</div><div style="display:flex;flex-direction:column;gap:6px;padding:6px 16px 12px">${progArr.map(p=>`<div style="display:flex;align-items:center;gap:8px;font-size:13px"><span style="width:170px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${p['模型']}">${p['模型']}</span><div style="flex:1;height:10px;background:#edf0f4;border-radius:5px;overflow:hidden"><div style="width:${Math.round((p['ok']||0)/maxOk*100)}%;height:100%;background:var(--acc)"></div></div><b style="font-size:12px;min-width:46px;text-align:right">${p['ok']}</b></div>`).join('')}</div><div class="cap">最佳搭配分布（各模型在全库夺魁次数）</div><div style="display:flex;flex-wrap:wrap;gap:8px;padding:6px 16px 14px">${Object.entries(bestCnt).sort((a,b)=>b[1]-a[1]).map(([m,c])=>`<span class="badge">${m} × ${c}</span>`).join('')}</div></div>`;
/* ── Tab 1 总览 ── */
const HOWTO=`<div class="card"><details><summary style="cursor:pointer;font-weight:700">分数怎么算（点开看口径）</summary>
<div style="font-size:13px;color:var(--ink);line-height:1.9">
<b>SkillScore（0-100）</b> = M2 均分/5 × 60 ＋ max(0, 20−8σ) ＋ 触发准确率 × 20<br>
即：实力 60 分（带技能做题的判官均分）＋ 稳定性 20 分（跨任务波动 σ 越小越高）＋ 触发质量 20 分（该被触发时触发、不该时克制）。<br>
<b>四模式</b>：M1 裸跑基线 ｜ M2 加载技能文档 ｜ M3 触发模拟 ｜ M4 等长无关材料对照——增益 = M2−M1，纯内容增益 = M2−M4（剔除"上下文变长"的假增益）。<br>
<b>名次怎么排（v2）</b>：默认按<b>百分位</b>排。判官下手轻重不一样（deepseek 手最松，space-bunny 最严），原始分先按各判官的均值和波动做 z 校正，拉到同一把尺子上，再算全库名次。旧 SkillScore（90 分并排 884 个）保留在榜内表作绝对分参考。<br>
<b>判分</b>：每个模型既是选手又是评委（N×N 互评）：产物匿名哈希代号 → 四维打分（正确性/完整性/技能遵循/表达，0-5）→ 同家族评委只计 1 票 → 取中位数。方阵中<b>行均≈真实水平，列均=评委严格度，蓝框对角线=自评</b>（仅测自偏，不计入总分）。
</div></details></div>`;
document.getElementById('pg-ov').innerHTML=HOWTO
+(D['画像_模型强项']?`<h2 class="pt">模型强项速览</h2><div class="grid">${Object.entries(D['画像_模型强项']).map(([m,ts])=>`<div class="mcard"><b>${m}</b><div class="tgs">${ts.map(t=>`<span>${t}</span>`).join('')}</div></div>`).join('')}</div>`:'')
+(D['画像']?`<h2 class="pt">模型 × 分类画像 <span style="font-weight:400;color:var(--sub);font-size:12px">（平均 SkillScore，绿色=该项最高）</span></h2><div class="card tblwrap tblscroll"><table><tr><th>分类</th><th class="num">样本</th>${Object.keys(D['画像_模型强项']).map(m=>`<th class="num">${m}</th>`).join('')}</tr>${D['画像'].map(r=>{const ms=Object.keys(D['画像_模型强项']);const mx=Math.max(...ms.map(m=>r[m]??-1));return `<tr><td style="font-weight:600">${r['分类']}</td><td class="num">${r['样本']}</td>${ms.map(m=>`<td class="num">${r[m]===mx?`<span class="win">${r[m]}</span>`:r[m]??'-'}</td>`).join('')}</tr>`}).join('')}</table></div>`:'');
/* ── Tab 2 技能榜（折叠卡+搜索）── */
document.getElementById('pg-sk').innerHTML=`<input class="search" id="q" placeholder="搜索技能名 / 功能 / 最佳模型…">
<div style="font-size:12px;color:var(--sub);margin:-4px 0 10px;line-height:1.9">绿色行 = 该技能的最佳配对模型 ｜ 增益表：M2−M1 总增益 / hake = 吃掉多少剩余提升空间 / M2−M4 = 剔除长度安慰剂的纯内容增益（红=负增益，skill 拖后腿）｜ 方阵：行=生产者水平，列=判官严格度，蓝框=自评</div>`+
scored.map(([s,A])=>`
<details class="sk" data-k="${(s+' '+(A['功能']||'')+' '+(A.best||'')).toLowerCase()}">
<summary>${A.best?`<span class="badge">${A.best.split('@')[0]}</span>`:''}<span class="skname"><a href="#${s}" onclick="event.stopPropagation()">${s}</a></span>${A['功能']?`<span class="gloss">${A['功能']}</span>`:''}<span class="ss">第 ${A.rank_v2??'-'} 名 · 百分位 ${sc([s,A])}</span></summary>
<div style="padding:2px 16px 14px">
<div class="cap">SkillScore 榜</div><div class="tblwrap"><table>
<tr><th>模型</th><th>家族</th><th class="num">SkillScore</th><th class="num">M2 均分</th><th class="num">M1 均分</th><th class="num">触发准确率</th></tr>
${A.leaderboard.map(r=>`<tr class="${r['模型']===A.best?'best':''}"><td>${r['模型']}</td><td>${r['家族']}</td><td class="num">${r.SkillScore}</td><td class="num">${A.m2_mean[r['模型']]??'-'}</td><td class="num">${A.m1_mean[r['模型']]??'-'}</td><td class="num">${A.trigger_accuracy[r['模型']]||'-'}</td></tr>`).join('')}
</table></div>
${Object.keys(A.gains).length?`<div class="cap">增益（M2−M1 总 ｜ hake 剩余空间 ｜ M2−M4 纯内容）</div><div class="tblwrap"><table><tr><th>模型</th><th>任务</th><th class="num">M2−M1</th><th class="num">hake</th><th class="num">M2−M4</th></tr>${Object.entries(A.gains).map(([k,g])=>`<tr><td>${k.split('|')[0]}</td><td>${k.split('|')[1]}</td><td class="num ${(g['M2-M1']??0)<0?'neg':'pos'}">${g['M2-M1']??'-'}</td><td class="num">${g['hake']??'-'}</td><td class="num ${(g['M2-M4']??0)<0?'neg':'pos'}">${g['M2-M4']??'-'}</td></tr>`).join('')}</table></div>`:''}
${(()=>{const JM=A.judge_matrix_M2_adj||A.judge_matrix_M2;return Object.keys(JM).length?`<div class="cap">N×N 交叉方阵 · 判官严格度已校正（行=生产者 · 列=判官 · 蓝框=自评）</div><div class="tblwrap"><table><tr><th>生产者＼判官</th>${[...new Set(Object.values(JM).flatMap(Object.keys))].map(j=>`<th class="num">${j}</th>`).join('')}</tr>${Object.entries(JM).map(([p,row])=>`<tr><td style="font-weight:600">${p}</td>${[...new Set(Object.values(JM).flatMap(Object.keys))].map(j=>`<td class="num" style="${bg(row[j])};${j===p?'outline:1px solid var(--acc);outline-offset:-1px':''}">${row[j]!==undefined?row[j]:'—'}</td>`).join('')}</tr>`).join('')}</table></div>`:''})()}
</div></details>`).join('')
+(pending.length?`<div class="card"><details class="pendd"><summary>${pending.length} 个技能评分中，出分后自动上移</summary><p class="pend">${pending.map(([s])=>s).join(' · ')}</p></details></div>`:'');
/* ── Tab 3 同类对比（侧边栏大类导航 + 纵向转置表）── */
const crossArr=(D.cross||[]).slice().sort((a,b)=>(b['大类']||'~').localeCompare(a['大类']||'~')||b.skills.length-a.skills.length);
const crTopBtn=`<button id="crtop" title="回到最上面的大类" style="display:none;position:sticky;top:0;z-index:7;width:100%;border:1px solid var(--line);background:#fff;border-radius:8px;padding:4px 0;font-size:12px;font-weight:600;color:var(--ink);cursor:pointer;margin-bottom:4px">回到顶部 ↑</button>`;
const crossNav=`<nav class="crnav" id="crnav">${crTopBtn}${(()=>{const by={};crossArr.forEach((G,i)=>{const c=G['大类']||'其他';(by[c]=by[c]||[]).push(i)});
return Object.keys(by).sort((a,b)=>by[b].length-by[a].length).map(c=>`<a class="catlnk" href="#crg${by[c][0]}" data-cat="1">${c} · ${by[c].length}</a><div class="crgrp">`+by[c].map(i=>`<a href="#crg${i}" data-i="${i}" title="${crossArr[i]['组']}">${crossArr[i]['组']}</a>`).join('')+`</div>`).join('')})()}</nav>`;
const crossBody=crossArr.map((G,i)=>{
const tasks=[...new Set(G.任务对比.map(r=>r['任务']))];
const avg=m=>{const vs=G.任务对比.map(r=>r[m]).filter(v=>v!=null);return vs.length?(vs.reduce((a,b)=>a+b,0)/vs.length).toFixed(2):'-'};
return `<div class="card" id="crg${i}"><div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;margin-bottom:8px"><b style="font-size:15px">${G['组']}</b><span class="gloss">${G['大类']?G['大类']+' · ':''}基准：${G.基准}（分数最高）· ${G.skills.length} 个成员</span></div>
<div class="tblwrap"><table>
<tr><th style="min-width:220px">技能</th><th class="num">平均</th><th class="num">Δ vs 基准</th><th>最佳配对</th>${tasks.map(t=>`<th class="num">${t}</th>`).join('')}</tr>
${G.skills.map(m=>{const base=(m===G.基准);const dv=base?[]:(G.任务对比.map(r=>r['Δ('+m+'-基准)']).filter(v=>v!=null));
const davg=dv.length?(dv.reduce((a,b)=>a+b,0)/dv.length).toFixed(2):'—';
return `<tr class="${base?'best':''}"><td style="font-weight:600;white-space:normal;word-break:break-all">${m}</td><td class="num">${avg(m)}</td><td class="num ${base?'':(parseFloat(davg)<0?'neg':(parseFloat(davg)>0?'pos':''))}" style="${(!base&&parseFloat(davg)===0)?'color:var(--sub)':''}">${base?'基准':(davg>0?'+':'')+davg}</td><td style="font-size:12px;color:var(--sub)">${G.最佳搭配[m]?(G.最佳搭配[m].split('@')[0]):'-'}</td>${tasks.map(t=>{const r=G.任务对比.find(x=>x['任务']===t);return `<td class="num">${r&&r[m]!=null?r[m]:'-'}</td>`}).join('')}</tr>`}).join('')}
</table></div></div>`}).join('');
document.getElementById('pg-cr').innerHTML=`<div class="card" style="font-size:13px;color:var(--sub)">同类技能对比（N×N×A）：左侧按<b>大类</b>分组导航，点击跳转；每个功能分组内分数最高者为基准，Δ = 各任务 M2 总分与基准之差。共 ${crossArr.length} 组。</div>
<div class="crlayout">${crossNav}<div class="crmain">${crossBody}</div></div>`;
/* 侧边栏：大类默认折叠；点击=展开并跳首组（再次点=收起不跳）；滚动高亮自动展开所在大类 */
document.querySelectorAll('#crnav a.catlnk').forEach(a=>a.addEventListener('click',e=>{
  const opening=!a.classList.contains('open');
  if(!opening)e.preventDefault();   // 收起时不再跳转
  a.classList.toggle('open',opening);
}));
document.addEventListener('click',e=>{if(e.target.id==='crtop'){const nav=document.getElementById('crnav');if(nav)nav.scrollTop=0;window.scrollTo({top:0,behavior:'smooth'});nav.querySelector('#crtop').style.display='none'}});
const crHi=id=>{document.querySelectorAll('#crnav a').forEach(a=>a.classList.toggle('on','crg'+a.dataset.i===id));  // 仅高亮，不自动展开（展开只由用户点击控制）
  const nav=document.getElementById('crnav');const lnk=nav&&nav.querySelector('a.on');
  if(nav&&lnk&&lnk.offsetParent){  // 最小侵入滚入：高亮已在可视区不动；越界才补最小滚动量（贴底/贴顶），顶部大类尽量保留
    const top=lnk.offsetTop,vh=nav.clientHeight;
    if(top<nav.scrollTop+10)nav.scrollTop=Math.max(0,top-10);
    else if(top>nav.scrollTop+vh-30)nav.scrollTop=top-vh+30}
  const tb=document.getElementById('crtop');if(tb)tb.style.display=(nav&&nav.scrollTop>60)?'flex':'none';};
const crObs=new IntersectionObserver(es=>{es.forEach(en=>{if(en.isIntersecting)crHi(en.target.id)})},{rootMargin:'0px 0px -60% 0px',threshold:0});
crossArr.forEach((_,i)=>{const el=document.getElementById('crg'+i);if(el)crObs.observe(el)});
window.addEventListener('scroll',()=>{let cur=null;crossArr.forEach((_,i)=>{const el=document.getElementById('crg'+i);if(el&&el.getBoundingClientRect().top<140)cur=el.id});if(cur)crHi(cur)},{passive:true});
crHi('crg0');
/* ── Tab 4 实时 ── */
const rv=(D.live&&D.live.recent)?D.live.recent:[];
let rateNote='';
if(rv.length>=2){const tt=s=>{const[x,y,z]=String(s).split(':').map(Number);return x*3600+y*60+z};let d=tt(rv[0]['时间'])-tt(rv[rv.length-1]['时间']);if(d<0)d+=86400;if(d>0){const r=rv.length/(d/3600);rateNote=` · 最近 ${Math.round(d/60)} 分钟完成 ${rv.length} 格 ≈ ${r>=1?r.toFixed(0):r.toFixed(1)} 格/小时`}}
document.getElementById('pg-lv').innerHTML=`<div class="card" style="font-size:13px;color:var(--sub)">此页是流水线心跳：<b>格</b> = 一个（技能 × 模型）的产物单元，先由 5 个模型家族各自生产，再匿名互评计分；下表为最近落盘的判分记录。数据快照：${D.live?D.live.generated:''}${rateNote}</div>`+HEALTH
+(D.live?`<div class="card"><div class="ticker">${D.live.progress.map(p=>`<span class="tk"><b>${p['模型']}</b> ${p['ok']} 格</span>`).join('')}</div><div class="tblwrap"><table><tr><th>时间</th><th>最近完成</th><th>模型</th><th>状态</th></tr>${D.live.recent.map(r=>`<tr><td>${r['时间']}</td><td>${r['技能']}</td><td>${r['模型']}</td><td>${r['状态']}</td></tr>`).join('')}</table></div></div>`:'');
/* Tab 切换 + 状态记忆 */
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));document.querySelectorAll('.page').forEach(x=>x.classList.remove('on'));t.classList.add('on');document.getElementById('pg-'+t.dataset.t).classList.add('on');try{sessionStorage.setItem('sftab',t.dataset.t)}catch(e){}});
const saved=(()=>{try{return sessionStorage.getItem('sftab')}catch(e){return null}})();
if(saved&&document.getElementById('pg-'+saved)){document.querySelector('.tab[data-t="'+saved+'"]').click()}
/* 搜索过滤 */
const q=document.getElementById('q');
if(q){const val=(()=>{try{return sessionStorage.getItem('sfq')||''}catch(e){return''}})();q.value=val;
q.oninput=()=>{const v=q.value.trim().toLowerCase();try{sessionStorage.setItem('sfq',q.value)}catch(e){}
document.querySelectorAll('details.sk').forEach(d=>{d.style.display=(!v||d.dataset.k.includes(v))?'':'none'})};
q.oninput();}}
);</script>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
/* 3D 矩阵 v2：A 轴可切（全部=大类总览 / 某大类=Top20 技能层）；按需渲染省 GPU */
let c3booted=false;
document.addEventListener('click',e=>{const t=e.target.closest('.tab');if(t&&t.dataset.t==='c3'&&!c3booted){c3booted=true;bootC3()}},true);
async function bootC3(){
const box=document.getElementById('c3box');
let D,THREE,OrbitControls;
try{
D=await (await fetch('data.json')).json();
THREE=await import('three');
({OrbitControls}=await import('three/addons/controls/OrbitControls.js'));
}catch(err){box.innerHTML='<div style="padding:40px;text-align:center;color:var(--sub);font-size:13px">3D 组件加载失败（需要联网访问 jsdelivr CDN）：<br><code>'+err.message+'</code></div>';return}
if(!D.cube||!D.cube.cats.length){box.innerHTML='<div style="padding:40px;text-align:center;color:var(--sub)">暂无立方体数据</div>';return}
const {models}=D.cube;const NM=models.length;
const GAP=1.28;
const W=box.clientWidth||900,H=box.clientHeight||600;
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(38,W/H,0.1,300);
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setSize(W,H);renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
box.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;controls.dampingFactor=0.09;controls.enableZoom=true;controls.target.set(0,0,0);
let homePos=null;
const zoomBtn=(txt,fn)=>{const b=document.createElement('button');b.textContent=txt;
b.style.cssText='width:30px;height:30px;border:1px solid var(--line);background:#fff;border-radius:8px;font-size:15px;font-weight:700;color:var(--ink);cursor:pointer;box-shadow:0 1px 2px rgba(16,24,40,.08)';
b.onclick=fn;box.appendChild(b);return b};
const zb=document.createElement('div');
zb.style.cssText='position:absolute;right:12px;bottom:12px;display:flex;gap:6px;z-index:6';
const bIn=zoomBtn('+',()=>{camera.position.lerp(controls.target,0.16);updateFade();needsRender=true});
const bOut=zoomBtn('−',()=>{camera.position.lerp(controls.target,-0.22);updateFade();needsRender=true});
const bRst=zoomBtn('⟲',()=>{if(homePos){camera.position.copy(homePos);controls.target.set(0,0,0);needsRender=true}});
bRst.style.width='auto';bRst.style.padding='0 10px';bRst.textContent='重置';
const bGap=zoomBtn('收起层距',()=>{gapOpen=!gapOpen;bGap.textContent=gapOpen?'收起层距':'展开层距';
  const gap=gapOpen?baseGap*3.0:baseGap;
  build(cur.z,cur.cells,gap);needsRender=true});
bGap.style.width='auto';bGap.style.padding='0 10px';
zb.append(bOut,bIn,bGap,bRst);box.appendChild(zb);
let gapOpen=true,baseGap=2.6;
scene.background=new THREE.Color('#eef1f6');
scene.add(new THREE.AmbientLight(0xffffff,0.6));
const dl=new THREE.DirectionalLight(0xffffff,0.95);dl.position.set(8,14,10);scene.add(dl);
const dl2=new THREE.DirectionalLight(0xffffff,0.38);dl2.position.set(-10,8,-12);scene.add(dl2);
const geo=new THREE.BoxGeometry(1,1,1);
const edgeTex=(()=>{const cv=document.createElement('canvas');cv.width=cv.height=128;const c=cv.getContext('2d');
c.fillStyle='#ffffff';c.fillRect(0,0,128,128);
c.lineWidth=9;c.strokeStyle='rgba(38,48,74,.9)';c.strokeRect(0,0,128,128);
const t=new THREE.CanvasTexture(cv);t.anisotropy=4;return t})();
const mat=new THREE.MeshLambertMaterial({map:edgeTex});
const dummy=new THREE.Object3D();
let gridsMat=null,mesh=null,labelSprites=[],plates=[],grids=[],cur=null,needsRender=true,centers=[],baseCols=[],baseScales=[];
const FADE_BG=new THREE.Color('#eef1f6'),_fc=new THREE.Color(),_dv=new THREE.Vector3(),_dm=new THREE.Object3D();
function updateFade(){
  if(!mesh||!centers.length)return;
  for(let idx=0;idx<centers.length;idx++){
    const d=_dv.copy(centers[idx]).sub(camera.position).length();
    const t=Math.max(0,Math.min(1,(d-7.0)/4.0));   // 7.0 即开始让路，>11 恢复
    const sc=baseScales[idx]*(0.01+0.99*t);          // 近处缩至 1%，100% 不可见
    _dm.position.copy(centers[idx]);_dm.scale.set(sc,sc,sc);_dm.updateMatrix();
    mesh.setMatrixAt(idx,_dm.matrix);
    _fc.copy(FADE_BG).lerp(baseCols[idx],t);         // 颜色完全归背景（100% 透明）
    mesh.setColorAt(idx,_fc)}
  mesh.instanceMatrix.needsUpdate=true;mesh.instanceColor.needsUpdate=true;
  for(const sp of labelSprites){  // 分类/技能/模型名文字近距同步淡化（最高 90% 透明）
    const d2=sp.position.distanceTo(camera.position);
    const t2=Math.max(0,Math.min(1,(d2-7.0)/4.0));
    sp.material.opacity=t2}}
const label=(txt,px=44,boxed=false)=>{const cv=document.createElement('canvas');const ctx=cv.getContext('2d');
ctx.font='600 '+px+'px system-ui,PingFang SC,sans-serif';const w=ctx.measureText(txt).width;
cv.width=Math.ceil(w+24);cv.height=px+20;const c2=cv.getContext('2d');
if(boxed){c2.fillStyle='rgba(255,255,255,.88)';const r=10;c2.beginPath();
c2.roundRect(1,1,cv.width-2,cv.height-2,r);c2.fill();
c2.strokeStyle='rgba(90,105,140,.5)';c2.lineWidth=2;c2.stroke()}
c2.font='600 '+px+'px system-ui,PingFang SC,sans-serif';c2.fillStyle='rgba(35,42,60,.92)';c2.textBaseline='middle';
c2.fillText(txt,12,cv.height/2);
const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(cv),transparent:true}));
sp.scale.set(cv.width/128,cv.height/128,1);return sp};
function build(zLabels,cells,layerGap){
  if(mesh){scene.remove(mesh);mesh.dispose()}
  labelSprites.forEach(sp=>{scene.remove(sp);if(sp.material.map)sp.material.map.dispose();sp.material.dispose()});labelSprites=[];
  plates.forEach(pl=>{if(pl.geo){pl.geo.dispose();pl.mat.dispose()}else{scene.remove(pl)}});plates=[];
  grids.forEach(g=>{scene.remove(g);g.geometry.dispose()});grids=[];
  if(gridsMat){gridsMat.dispose();gridsMat=null}
  const NC=zLabels.length;
  const vals=cells.flat(2).filter(c=>c).map(c=>c.v).sort((a,b)=>a-b);
  const q=f=>vals[Math.min(vals.length-1,Math.max(0,Math.round(f*(vals.length-1))))];
  const lo=q(0.05),hi=q(0.95);   // P5-P95 分位截断：主体区间撑满红→绿，极端值夹边
  document.getElementById('c3rng').textContent=(vals[0]===lo?'':'≤')+hi.toFixed(2)+' 强 ←→ 弱 ≤'+ (vals[vals.length-1]===hi?'':lo.toFixed(2));
  document.getElementById('c3rng').textContent='弱 '+vals[0].toFixed(2)+' — 强 '+vals[vals.length-1].toFixed(2)+'（色标 P5–P95）';
  const colOf=v=>{const t=Math.max(0,Math.min(1,(v-lo)/(hi-lo||1)));const c=new THREE.Color();
    c.setHSL(0.33*t,0.85,0.42+0.2*t);return c};  // 饱和 0.85 + 亮度随分数走高：暗红→亮绿双通道
  mesh=new THREE.InstancedMesh(geo,mat,NC*NM*NM);
  let ptr=0;
  for(let k=0;k<NC;k++)for(let i=0;i<NM;i++)for(let j=0;j<NM;j++){
    const c=cells[k][i][j];
    dummy.position.set((i-(NM-1)/2)*GAP,(j-(NM-1)/2)*GAP,(k-(NC-1)/2)*layerGap);
    if(c){dummy.scale.set(1,1,1);mesh.setColorAt(ptr,colOf(c.v))}
    else{dummy.scale.set(0.16,0.16,0.16);mesh.setColorAt(ptr,new THREE.Color('#d7dce3'))}
    dummy.updateMatrix();mesh.setMatrixAt(ptr,dummy.matrix);ptr++}
  mesh.instanceMatrix.needsUpdate=true;scene.add(mesh);
  /* 记录格子中心与基色，供近距淡化 */
  centers=[];baseCols=[];baseScales=[];
  const bgColor=new THREE.Color('#eef1f6');const tmpC=new THREE.Color();
  for(let k=0;k<NC;k++)for(let i=0;i<NM;i++)for(let j=0;j<NM;j++){
    centers.push(new THREE.Vector3((i-(NM-1)/2)*GAP,(j-(NM-1)/2)*GAP,(k-(NC-1)/2)*layerGap));
    mesh.getColorAt(k*NM*NM+i*NM+j,tmpC);baseCols.push(tmpC.clone());
    baseScales.push(cells[k][i][j]?1:0.16)}
  const plateG=new THREE.BoxGeometry(NM*GAP+0.55,0.07,NM*GAP+0.55);
  const plateM=new THREE.MeshLambertMaterial({color:'#f8fafd'});
  zLabels.forEach((_,k)=>{const pl=new THREE.Mesh(plateG,plateM);
    pl.position.set(0,-(NM-1)/2*GAP-0.75,(k-(NC-1)/2)*layerGap);scene.add(pl);plates.push(pl)});
  /* 每层透明 N×N 网格线：格子归位对照（哪格=哪两个模型） */
  gridsMat=new THREE.LineBasicMaterial({color:0x9aa7c2,transparent:true,opacity:0.55});
  zLabels.forEach((_,k)=>{
    const pts=[];const half=(NM*GAP+0.55)/2;
    for(let i=0;i<=NM;i++){const t=-half+i*(2*half/NM);
      pts.push(t,-half,0,t,half,0, -half,t,0,half,t,0)}  // XY 平面网格线段
    const gg=new THREE.BufferGeometry();
    gg.setAttribute('position',new THREE.Float32BufferAttribute(pts,3));
    const grid=new THREE.LineSegments(gg,gridsMat);
    grid.position.set(0,-(NM-1)/2*GAP-0.71,(k-(NC-1)/2)*layerGap);
    scene.add(grid);grids.push(grid)});
  plates.push({geo:plateG,mat:plateM});
  const short=t=>{t=String(t).split('__')[0];return t.length>26?t.slice(0,25)+'…':t};
  zLabels.forEach((c,k)=>{const sp=label(short(c),58,true);sp.userData={full:c};
    sp.position.set(0,0,(k-(NC-1)/2)*layerGap-0.72);scene.add(sp);labelSprites.push(sp)});  // 嵌在层面正中（3×3格前方），穿越渐近时直读
  models.forEach((m,i)=>{const sp=label(m,48);sp.position.set((i-(NM-1)/2)*GAP,-(NM-1)/2*GAP-2.6,-(NC-1)/2*layerGap-3.4);scene.add(sp);labelSprites.push(sp);
  const sp2=label(m,48);sp2.position.set(-(NM-1)/2*GAP-2.5,(i-(NM-1)/2)*GAP,-(NC-1)/2*layerGap-3.4);scene.add(sp2);labelSprites.push(sp2);
  /* 远端面同样两排（转到背面也有坐标） */
  const sp3=label(m,48);sp3.position.set((i-(NM-1)/2)*GAP,-(NM-1)/2*GAP-2.6,(NC-1)/2*layerGap+2.6);scene.add(sp3);labelSprites.push(sp3);
  const sp4=label(m,48);sp4.position.set(-(NM-1)/2*GAP-2.5,(i-(NM-1)/2)*GAP,(NC-1)/2*layerGap+2.6);scene.add(sp4);labelSprites.push(sp4)});
  camera.position.set(NM*1.55,NM*1.05,NC*layerGap*0.72);controls.target.set(0,0,0);controls.update();homePos=camera.position.clone();
  needsRender=true;
}
const sel=document.getElementById('c3cat');
Object.keys(D.cube.byCat||{}).sort().forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c+'（Top '+D.cube.byCat[c].skills.length+' 技能）';sel.appendChild(o)});
sel.onchange=()=>{const v=sel.value;
  if(!v){cur={z:D.cube.cats,cells:D.cube.cells};baseGap=2.6}
  else{const B=D.cube.byCat[v];cur={z:B.skills,cells:B.cells};baseGap=2.2}
  build(cur.z,cur.cells,gapOpen?baseGap*3.0:baseGap)};
cur={z:D.cube.cats,cells:D.cube.cells};
build(D.cube.cats,D.cube.cells,2.6*3.0);
const tip=document.createElement('div');
tip.style.cssText='position:absolute;pointer-events:none;background:#1f2740;color:#fff;font-size:12px;line-height:1.7;padding:6px 10px;border-radius:8px;opacity:0;transition:opacity .12s;z-index:5;white-space:nowrap';
box.appendChild(tip);
const ray=new THREE.Raycaster();const mouse=new THREE.Vector2();
renderer.domElement.addEventListener('pointermove',e=>{
  const r=renderer.domElement.getBoundingClientRect();
  mouse.x=((e.clientX-r.left)/r.width)*2-1;mouse.y=-((e.clientY-r.top)/r.height)*2+1;
  ray.setFromCamera(mouse,camera);
  const hit=mesh?ray.intersectObject(mesh)[0]:null;
  if(hit&&hit.instanceId!=null&&cur){
    const NC=cur.z.length;
    const k=Math.floor(hit.instanceId/(NM*NM)),i=Math.floor(hit.instanceId%(NM*NM)/NM),j=hit.instanceId%NM;
    const c=cur.cells[k][i][j];
    tip.innerHTML='<b>'+cur.z[k]+'</b><br>生产者 '+models[i]+'<br>判官 '+models[j]+(c?'<br>判分 <b>'+c.v+'</b>'+(c.n?'（'+c.n+' 格均值）':''):'<br>（无判分）');
    tip.style.opacity=1;tip.style.left=Math.min(e.clientX-r.left+14,r.width-200)+'px';tip.style.top=(e.clientY-r.top+10)+'px';
    renderer.domElement.style.cursor='pointer';
  }else{tip.style.opacity=0;renderer.domElement.style.cursor='grab'}
  needsRender=true});
renderer.domElement.addEventListener('pointerleave',()=>{tip.style.opacity=0});
addEventListener('resize',()=>{const w2=box.clientWidth,h2=box.clientHeight;camera.aspect=w2/h2;camera.updateProjectionMatrix();renderer.setSize(w2,h2);needsRender=true});
controls.addEventListener('change',()=>{updateFade();needsRender=true});
/* 键盘平移：W/S 沿视线前后、A/D 左右，可"走进"立方体；近处格子自动淡化 */
const keys=new Set();
addEventListener('keydown',e=>{const k=e.key.toLowerCase();
  if(!['w','a','s','d'].includes(k))return;
  const pg=document.getElementById('pg-c3');if(!pg||!pg.classList.contains('on'))return;
  keys.add(k);needsRender=true});
addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));
const FWD=new THREE.Vector3(),RIGHT=new THREE.Vector3();
function moveCam(dt){
  if(!keys.size)return;
  const step=dt*26;
  camera.getWorldDirection(FWD);
  RIGHT.crossVectors(FWD,camera.up).normalize();
  if(keys.has('w')){camera.position.addScaledVector(FWD,step);controls.target.addScaledVector(FWD,step)}
  if(keys.has('s')){camera.position.addScaledVector(FWD,-step);controls.target.addScaledVector(FWD,-step)}
  if(keys.has('a')){camera.position.addScaledVector(RIGHT,-step);controls.target.addScaledVector(RIGHT,-step)}
  if(keys.has('d')){camera.position.addScaledVector(RIGHT,step);controls.target.addScaledVector(RIGHT,step)}
  updateFade();needsRender=true}
let lastT=performance.now();
(function loop(now){requestAnimationFrame(loop);const dt=Math.min(0.05,(now-lastT)/1000);lastT=now;
  controls.update();moveCam(dt);
  if(needsRender){renderer.render(scene,camera);needsRender=false}})(lastT);
}
</script>"""

def cmd_site(a):
    web = PROJ / "网站"
    (web / "skills").mkdir(parents=True, exist_ok=True)
    data = {"generated": ts(), "skills": {}}
    data["cross"] = [json.loads(p.read_text()) for p in sorted(REPDIR.glob("三维-*.json"))]
    # 去重：历史三维文件存在组内重复技能/重复任务行，保序去重
    for G in data["cross"]:
        G["skills"] = list(dict.fromkeys(G["skills"]))
        rows = {}
        for r in G.get("任务对比", []):
            rows[r["任务"]] = r
        G["任务对比"] = list(rows.values())
    # 3D 立方体：大类(Z层) × 生产者(X) × 判官(Y)，格值 = 大类内技能判分均值
    cm = PROJ / "本地库" / "大类映射.json"
    cat_map = json.loads(cm.read_text()) if cm.exists() else {}
    # 组→大类（组内技能投票）
    for G in data["cross"]:
        votes = {}
        for s in G.get("skills", []):
            c = cat_map.get(s)
            if c: votes[c] = votes.get(c, 0) + 1
        if votes:
            G["大类"] = max(votes, key=votes.get)
    led = RDIR / "台账.csv"
    prog = {}
    if led.exists():
        done = done_cells()
        for sk, task, m, mode, tr in done:
            if mode == "M2":
                prog[m] = prog.get(m, 0) + 1  # 完整 id 计数（@api 与 CLI 分开，和磁盘目录一一对应）
    data["progress"] = [{"模型": m, "ok": n} for m, n in sorted(prog.items(), key=lambda x: -x[1])]
    recent = []
    if led.exists():
        for r in list(csv.DictReader(open(led)))[-12:][::-1]:
            recent.append({"时间": r.get("ts", "")[-8:], "技能": r.get("技能", "")[:34],
                           "模型": r.get("模型", ""), "状态": r.get("状态", "")[:14]})
    data["live"] = {"generated": data["generated"], "progress": data["progress"], "recent": recent}
    for jf in sorted(REPDIR.glob("*-聚合.json")):
        agg = json.loads(jf.read_text())
        s = agg["skill"]
        cells = sorted({p.parent.name for p in (RDIR / s).glob("*/T*-M2.md")})
        agg["已产格"] = "、".join(cells) or "（待产）"
        gl = PROJ / "本地库" / "技能释义.json"
        if gl.exists():
            gloss = json.loads(gl.read_text())
            agg["功能"] = gloss.get(s, "")
        data["skills"][s] = agg
        dst = web / "skills" / s
        dst.mkdir(parents=True, exist_ok=True)
        ft = TDIR / s / "技能文件.txt"
        if ft.exists():
            for line in ft.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and Path(line).expanduser().exists():
                    shutil.copy(line, dst / Path(line).name)
    # SkillFit v2：判官严格度 z 校正 + 校正方阵 + tie-break 百分位（不重跑历史判分）
    try:
        from collections import defaultdict
        import statistics as _st
        jstat = defaultdict(list)
        for s, a in data["skills"].items():
            for p, row in (a.get("judge_matrix_M2") or {}).items():
                for j, v in (row or {}).items():
                    if v is not None:
                        jstat[j].append(v)
        jmu = {j: _st.mean(vs) for j, vs in jstat.items() if len(vs) >= 30}   # 样本≥30 才可信
        jsd = {j: (_st.pstdev([v for v in jstat[j]]) or 1.0) for j in jmu}
        def _adj(v, j):
            z = (v - jmu[j]) / jsd[j]
            return round(max(0.0, min(5.0, 3.0 + 0.75 * z)), 2)
        m2adj = {}
        for s, a in data["skills"].items():
            jm = a.get("judge_matrix_M2") or {}
            adjm = {}
            flat = []
            for pro, row in jm.items():
                adjm[pro] = {}
                for j, v in (row or {}).items():
                    if v is None or j not in jmu:
                        adjm[pro][j] = v
                    else:
                        av = _adj(v, j)
                        adjm[pro][j] = av
                        flat.append(av)
            a["judge_matrix_M2_adj"] = adjm
            a["m2_adj_mean"] = round(sum(flat) / len(flat), 3) if flat else 0.0
            m2adj[s] = a["m2_adj_mean"]
        def _num(x):
            try: return float(x)
            except (TypeError, ValueError): return 0.0
        def _key(s):
            a = data["skills"][s]
            sc = a.get("skill_score") or {}
            ss1 = _num(sc.get(a.get("best") or ""))
            ta = a.get("trigger_accuracy") or {}
            tab = _num(ta.get(a.get("best") or ""))
            return (-ss1, -m2adj.get(s, 0.0), -tab, s)
        order = sorted(data["skills"].keys(), key=_key)
        N = len(order)
        for r, s in enumerate(order):
            a = data["skills"][s]
            a["ss_v2"] = round(100.0 * (N - 1 - r) / max(1, N - 1), 1)
            a["rank_v2"] = r + 1
        data["v2"] = {"判官校正": {j: [round(jmu[j], 3), round(jsd[j], 3)] for j in jmu},
                      "并列残留": sum(1 for r in range(1, N) if _key(order[r])[:3] == _key(order[r-1])[:3])}
    except Exception as e:
        print(f"[{ts()}] v2 校正跳过：{e}")

    # 3D 立方体数据：总览层=大类(14层均值面)；byCat=大类下 Top20 技能层（N×N 判分面，A=技能）
    try:
        cube_sum, cube_cnt, mset = {}, {}, set()
        by_cat = {}  # 大类 -> [(技能, score, judge_matrix_M2)]
        for s, a in data["skills"].items():
            c = cat_map.get(s)
            if not c:
                continue
            jm = a.get("judge_matrix_M2_adj") or a.get("judge_matrix_M2") or {}
            if not jm:
                continue
            sc = a.get("skill_score") or {}
            score = max(sc.values()) if sc else 0
            by_cat.setdefault(c, []).append((s, score, jm))
            for p, row in jm.items():
                mset.add(p)
                for j, v in (row or {}).items():
                    mset.add(j)
                    k = (c, p, j)
                    cube_sum[k] = cube_sum.get(k, 0) + v
                    cube_cnt[k] = cube_cnt.get(k, 0) + 1
        models = sorted(m for m in mset if prog.get(m, 0) >= 200)  # 滤历史碎片通道（<200 格），只留主五车道
        cats = sorted({k[0] for k in cube_sum})
        cells = []
        for c in cats:
            layer = []
            for p in models:
                lane = []
                for j in models:
                    k = (c, p, j)
                    lane.append({"v": round(cube_sum[k] / cube_cnt[k], 2), "n": cube_cnt[k]} if k in cube_sum else None)
                layer.append(lane)
            cells.append(layer)
        byCat = {}
        for c, lst in by_cat.items():
            lst.sort(key=lambda x: -x[1])
            lst = lst[:20]  # A 轴技能层上限，防格子爆炸
            sk_cells = []
            for s, _score, jm in lst:
                layer = [[({"v": round(jm[p][j], 2)} if jm.get(p) and jm[p].get(j) is not None else None)
                          for j in models] for p in models]
                sk_cells.append(layer)
            byCat[c] = {"skills": [s for s, _, _ in lst], "cells": sk_cells}
        data["cube"] = {"models": models, "cats": cats, "cells": cells, "byCat": byCat}
    except Exception as e:
        print(f"[{ts()}] cube 构建跳过：{e}")
    (web / "data.json").write_text(json.dumps(data, ensure_ascii=False))
    # 模型×分类画像（用户 2026-10-11 需求：什么模型在什么分类突出）
    try:
        dbj = json.loads((PROJ / "本地库/库.json").read_text())
        grp = {re.sub(r"[^\w\-]", "-", e["skill"] + "__" + e["repo"].split("/")[0])[:60]:
               (e.get("功能组") or "其他") for e in dbj["条目"]}
        from collections import defaultdict
        acc = defaultdict(lambda: defaultdict(list))
        for s, a in data["skills"].items():
            g = grp.get(s)
            if not g or g in ("未分组", "其他"):
                continue
            for m, v in a.get("skill_score", {}).items():
                acc[g][m.split("@")[0]].append(v)
        prof = []
        for g, ms in acc.items():
            n = max(len(v) for v in ms.values())
            if n < 4:
                continue
            row = {"分类": g, "样本": n}
            for m, v in ms.items():
                row[m] = round(sum(v) / len(v), 1)
            prof.append(row)
        prof.sort(key=lambda r: -r["样本"])
        data["画像"] = prof
        models = sorted({m for r in prof for m in r if m not in ("分类", "样本")})
        per_model = {m: sorted(((r["分类"], r[m]) for r in prof if m in r), key=lambda x: -x[1])[:3]
                     for m in models}
        data["画像_模型强项"] = {m: [f"{g}({v})" for g, v in tops] for m, tops in per_model.items()}
        (web / "data.json").write_text(json.dumps(data, ensure_ascii=False))
        log(f"模型×分类画像 {len(prof)} 类 × {len(models)} 模型已写入")
    except Exception as e:
        log(f"画像生成跳过: {e}")
    (web / "index.html").write_text(HTML)
    log(f"网站 -> {web}/（纯静态：index.html + data.json + skills/，GitHub Pages 或任意静态托管直接扔）")


# ---------- doctor ----------

def cmd_doctor(a):
    print("| 模型 | 状态 | 延迟 | 输出 |")
    print("|---|---|---|---|")

    def one(m):
        t0 = time.time()
        out, err = call(m, "只回复两个字：正常", tools="", timeout=180)
        return m, "ok" if out else err, f"{time.time() - t0:.0f}s", (out or "")[:20].replace("\n", " ")
    with ThreadPoolExecutor(min(8, len(a.models.split(",")))) as ex:
        for row in ex.map(one, a.models.split(",")):
            print("| " + " | ".join(row) + " |", flush=True)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doctor"); d.add_argument("--models", required=True)
    c = sub.add_parser("check"); c.add_argument("--skills", required=True)
    r = sub.add_parser("run")
    r.add_argument("--skills", required=True); r.add_argument("--models", required=True)
    r.add_argument("--modes", default="M1,M2,M3"); r.add_argument("--trials", type=int, default=1)
    r.add_argument("-P", type=int, default=6)
    s = sub.add_parser("score")
    s.add_argument("--skills", required=True); s.add_argument("--scorers", required=True)
    s.add_argument("--self", dest="self", action="store_true", default=True,
                   help="对角线自评（默认开，用户裁定：人人互评含自评，自偏可量化）")
    s.add_argument("--no-self", dest="self", action="store_false")
    s.add_argument("-P", type=int, default=6)
    sf = sub.add_parser("selfscore"); sf.add_argument("--scorers", required=True); sf.add_argument("-P", type=int, default=2)
    g = sub.add_parser("agg"); g.add_argument("--skills", required=True)
    x = sub.add_parser("cross"); x.add_argument("--skills", required=True); x.add_argument("--group", default=None)
    sub.add_parser("site")
    a = p.parse_args()
    {"doctor": cmd_doctor, "check": cmd_check, "run": cmd_run, "score": cmd_score,
     "agg": cmd_agg, "cross": cmd_cross, "selfscore": cmd_selfscore, "site": cmd_site}[a.cmd](a)


if __name__ == "__main__":
    main()
