# 体检三板斧：首次接触数据的标准动作

数据到手不体检就分析 = 白干。本篇 6 节，按编号顺序用。

## §1 三板斧体检（任何新 df 的第一动作）

```python
import pandas as pd

df.info()                          # 板斧一：行数、列 dtype、非空计数、内存
df.describe(include='all').T       # 板斧二：数值分布 + 类别 top/freq + 基数
# 板斧三：结构三查
df.nunique(dropna=False).sort_values()   # 每列唯一值数 → 认主键、看基数
df.isna().mean().sort_values(ascending=False)  # 每列缺失比例
df.duplicated().sum()              # 完全重复行数
```

看什么：行数对不上预期先查数据来源；主键候选（nunique == 行数的列）；缺失 >50% 的列；describe 里 min/max 有没有穿越业务常识（负金额、年龄 999）。

**describe 逐列看点清单**：

| 列类型 | 看 | 异常信号 |
|--------|-----|----------|
| 数值 | min/max/mean/50% | mean 远偏 50% → 重尾；min/max 穿越常识 → §5 |
| 类别 | unique/top/freq | top 占比 >90% → 近常量列，分析价值低；unique=行数 → 可能是 id 误当维度 |
| 计数列 | std=0 | 全相同 → 直接弃 |

**超内存数据（>2GB）**：先抽样体检再全量算——`pd.read_csv(p, skiprows=lambda i: i % 100 != 0)` 抽 1% 看 dtype 与分布，确认代码逻辑后再全量后台跑。

null 热力用排序代替绘图：

```python
miss = df.isna().mean().sort_values(ascending=False)
# 按行看缺失组合（哪几列总是同时缺 → 缺失机制线索）
df.isna().value_counts().head()
```

## §2 dtype 陷阱表

| 陷阱 | 症状 | 修复 |
|------|------|------|
| object 藏 mixed | `describe` 的 top 是数字但列是 object | `df[c].map(type).value_counts()` 定位，再统一 `pd.to_numeric(s, errors='coerce')`，查 coerce 后 NaN 新增数 |
| 日期是字符串 | dtype=object，排序按字典序 | `df['dt'] = pd.to_datetime(df['dt'], errors='coerce')`；先看 `df['dt'].isna().sum()` 有没有涨（涨=格式不纯，统一 `format='%Y-%m-%d'`） |
| id 被读成 int | 身份证/手机号出现科学计数 | 读时指定：`pd.read_csv(p, dtype={'user_id': str})`；已读成 int 只能重读 |
| 前导零丢失 | 0123 变 123 | 读时 `dtype=str` 才能防；已丢无法恢复，回源数据重导 |
| 布尔变 0/1 int | `True/False` 全是数字 | `df['f'] = df['f'].astype(bool)`，但先确认没有 NaN（NaN→astype(bool) 会变 True，先 `fillna(-1).map({1:True,0:False,-1:pd.NA})`） |
| 数值被读成 object | 求和报错/带千分位逗号 | `pd.to_numeric(s.astype(str).str.replace(',', ''), errors='coerce')` |
| 低基数字符串占内存 | 千万行 object 列 | `df['cat'] = df['cat'].astype('category')`，分析结论不变、速度变快 |

## §3 缺失值处置决策表（删/填/标记三选一）

| 条件 | 动作 | 依据 |
|------|------|------|
| 缺失 >60% 且无业务含义 | 弃列 | 填出来全是编的 |
| 缺失随机、行数多、占比 <5% | 删行 `df.dropna(subset=[c])` | 损失小、无偏 |
| 缺失本身有含义（如取消时间=未取消） | 标记：`df['canceled'] = df['cancel_dt'].notna()` | 缺失即信息，删=删掉正样本 |
| 时序数值列 | 插值 `df['v'] = df['v'].interpolate()`，记录填补条数 | 删会断时间轴 |
| 类别列缺失 | 填 `'未知'` 单独成组 | 不让缺失污染最大类 |
| 均值/中位数填补 | 仅建模前用；分析/出报告场景禁用 | 扭曲分布、压低方差，图和分位数会失真 |

铁律：任何填补都要记账——`填补列 | 方式 | 条数`，写进笔记本；两种填补方式结果差很多时，说明结论不 robust，置信度降级。

**先判缺失机制再选动作**：

| 机制 | 判定线索 | 可用动作 |
|------|----------|----------|
| 完全随机（与任何列无关） | 缺失行和其他行分布一致 | 删/填都行，结论影响小 |
| 有条件缺失（取决于其他列） | 按某列分组后缺失率差异大：`df.groupby('渠道')['v'].apply(lambda s: s.isna().mean())` | 只能标记或分组处理，直接删会删偏样本 |
| 缺失取决于自身值（低薪者不填薪资） | 无从直接验证，靠业务常识 | 只能标记保留，禁填禁删 |

## §4 重复与粒度（groupby / merge 前必开）

**主键判定**：

```python
key = ['order_id']
df.groupby(key).size().max()       # ==1 则 key 是主键；>1 则不唯一
df.duplicated(subset=key).sum()    # key 重复行数
```

**groupby 前先验粒度**（不验就聚合 = 常见翻倍来源）：

```python
df.groupby(['city', 'product']).size().value_counts()
# 全是 1 → 城市×产品粒度唯一，可放心聚合
# 出现 3、7 等 → 一城一产品多行（如多次下单），聚合前先想清楚要 行数、金额和 还是 去重用户数
```

**两种重复要分清**：

| 类型 | 判定 | 处置 |
|------|------|------|
| 完全重复行 | `df.duplicated().sum() > 0` | 直接 `df = df.drop_duplicates()` |
| 业务重复（同实体多条） | 主键不唯一但行内容不同 | 不是脏数据，先问业务（多版本？多状态？），禁直接删 |

**merge 前后各查一次行数**：左表 n1 + 右表 n2 → 合并后行数涨了就是键不唯一导致笛卡尔放大（详见 conclusions-and-charts.md §4 validate）。

**聚合自查输出**（每次大聚合后跑，30 秒防翻倍）：

```python
print(len(df), '->', len(g))            # 聚合前后行数：分组行数应= 分组键 nunique
assert g['city'].nunique() == df['city'].nunique(), '分组键被聚合丢了'
g['sum'].sum() - df['amt'].sum()        # 金额守恒检验：应=0（过滤/剔除过则差额=剔除额）
```

## §5 异常值三法适用表

| 方法 | 适用 | 不适用 | 代码 |
|------|------|--------|------|
| IQR | 偏态分布、金额类（默认首选） | 需要严格正态假设的场合 | `q1,q3 = s.quantile([.25,.75]); iqr=q3-q1; ok = s.between(q1-1.5*iqr, q3+1.5*iqr)` |
| z-score | 近似正态（身高、测量误差） | 偏态/重尾（会被极端值本身污染） | `z = (s-s.mean())/s.std(); ok = z.abs() < 3` |
| 业务上限 | 有领域规则：年龄 0–150、折扣 0–10、金额 ≥0 | 无明确规则的探索分析 | `ok = s.between(0, 150)` |

顺序建议：先业务上限（硬错误直接剔），再 IQR 看分布，z-score 仅正态时补充。剔除前先 `s[~ok]` 肉眼过一遍——「异常」可能正是结论本身（刷单、故障、大客户）。

## §6 时间序列体检

```python
ts = df.set_index('dt').sort_index()
```

| 检查 | 代码 | 判定 |
|------|------|------|
| 时区 | `ts.index.tz` 为 None → naive | 统一：naive 转 `ts.tz_localize('Asia/Shanghai')`；已带时区换算 `ts.tz_convert('UTC')`。混用两种是经典错位 |
| 缺失时段 | `pd.date_range(ts.index.min(), ts.index.max(), freq='D').difference(ts.index)` | 非空 = 有空洞，resample 前必须知道 |
| 重复时间戳 | `ts.index.duplicated().sum()` | >0 时同刻多条是「多实体」还是「重复写入」，先查 §4 |
| 顺序 | `ts.index.is_monotonic_increasing` | False 则 sort_index，否则 shift/rolling 全错 |
| 频率 | `ts.index.to_series().diff().value_counts()` | 主流间隔应为单一值；混着天和小时 → 先统一频率再分析 |

**频率统一**（diff 混杂时）：`ts['v'].resample('D').sum()` 落到日粒度；缺失日会自动补 NaN，此时回 §3 决定填不填，不许静默当 0。

重采样注意边界：`ts['v'].resample('W', label='left', closed='left').sum()`——不指定 label/closed，周归属默认右闭，跨周对比会差一天；输出周标签含义必须写进笔记本。
