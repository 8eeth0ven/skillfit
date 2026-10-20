# 结论与图表：从数字到能交付的判断

## §1 从描述到结论的检查单（说「A 比 B 好」之前逐条打勾）

| # | 检查项 | 速查问题 | 未过怎么办 |
|---|--------|----------|------------|
| 1 | 相关≠因果 | X 和 Y 同涨，有没有第三个变量同时驱动？ | 改措辞为「X 与 Y 正相关」，不写「带动/导致」 |
| 2 | 辛普森悖论 | 分组结论和汇总结论方向一致吗？ | `df.groupby(['组','细分']).agg(...)` 两层各算一遍；方向相反 → 只报分层结论，报混杂变量 |
| 3 | 基数陷阱 | 最小分组的 n 是多少？ | n<30 的格子不报百分比，只报方向；或合并小组 |
| 4 | 幸存者偏差 | 样本是怎么被筛出来的？没进样本的是谁？ | 问数据来源的过滤条件；「老用户留存高」可能只是差用户早走了 |
| 5 | 均值被拉偏 | 均值和中位数差多远？ | 差距大 → 同时报 `mean/median/p95`，图表配箱线 |
| 6 | 时间窗效应 | 结论换个起止日还成立吗？ | 换窗口重算一次（前后各挪 7 天），不稳 → 置信度降级 |

辛普森速查代码：

```python
# 汇总与分层方向不一致 = 触发
df.groupby('渠道')['转化'].mean()                          # 汇总方向
df.groupby(['渠道','城市'])['转化'].mean().unstack()       # 分层方向
```

## §2 常见指标口径表（分母歧义是报表事故第一来源）

| 指标 | 分母歧义 | 推荐口径（写进笔记本） |
|------|----------|------------------------|
| DAU | 按设备还是账号？跨端去重吗？ | 当日有 ≥1 次活跃行为的去重用户数；去重键、跨端规则必须写死 |
| 次日留存 | 分母是「当日新增」还是「当日全体活跃」？ | D1 留存 = D0 新增用户在 D1 回访数 ÷ D0 新增数；分母只认新增 |
| 转化率 | 分母是访问数、会话数还是用户数？ | 三选一并注明；漏斗各层分母 = 上一层完成数 |
| ARPU / ARPPU | 全体用户还是付费用户？收入含退款吗？ | ARPU=总收入÷活跃用户；ARPPU=付费收入÷付费用户；退款规则写明 |
| 环比/同比 | 周期对齐了吗？ | 同比按同月同日对齐；环比注意大月 31 天 vs 28 天，改日均 |
| 流失率 | 「多久没来」算流失？观察窗多长？ | 如「30 天未活跃」；定义与观察窗必须同时写死 |
| GMV | 含退款/取消订单吗？含刷单吗？ | 拆成 下单额 / 有效额 两列报，不单报一个数 |

同期群留存标准代码（分母自动正确）：

```python
# df: user_id, active_dt
first = df.groupby('user_id')['active_dt'].min().rename('first_dt')
df = df.merge(first, on='user_id')
df['period'] = (df['active_dt'] - df['first_dt']).dt.days
cohort = df.pivot_table(index='first_dt', columns='period',
                        values='user_id', aggfunc='nunique')
ret = cohort.div(cohort[0], axis=0)   # 每行分母=该 cohort D0 人数
print(ret[1].mean())                  # 次留均值
```

## §3 图表选型表

| 目的 | 常用图型 | 关键规则 |
|------|----------|----------|
| 比较（类别间大小） | 条形图 | 类别名长 → 横向 `barh`；数值排序后再画 |
| 分布（单变量形状） | 直方图 / 箱线 | 直方图试 bins=30/50/100 看稳不稳；偏态数据箱线+中位数标注 |
| 构成（部分占整体） | 堆叠条形 | 见下方饼图禁用线 |
| 关系（两数值变量） | 散点图 | >1 万点改 `hexbin` 或抽样 + `alpha=0.3`，防止黑块 |
| 趋势（随时间变化） | 折线图 | 先按 §6 体检时区/缺失时段；日均 vs 周均要平滑说明 |

**饼图禁用线**：类别 >5 禁用；任意两块占比接近（差 <3pp）禁用（人眼分不出）；需要精确比较禁用。满足全部条件（≤5 类、占比分明、只看构成不看比较）才允许，否则一律换条形。

快速看形状（选型拿不准先跑这两行）：

```python
df['amt'].hist(bins=50)                              # 分布形状 → 重偏态则结论补中位数
df.plot(x='x', y='y', kind='scatter', alpha=0.3)     # 关系 → 点多先 df.sample(5000)
```

## §4 pandas 惯用式速查

```python
# 长转宽（透视）：一行为实体，一列一指标
w = df.pivot_table(index='city', columns='product', values='amt',
                   aggfunc='sum', fill_value=0)

# 宽转长：画分面图/入库前的标准形
l = w.reset_index().melt(id_vars='city', var_name='product', value_name='amt')

# 分箱：业务切点用 cut，等频用 qcut
df['age_band'] = pd.cut(df['age'], bins=[0,18,35,60,150],
                        labels=['未成年','青年','中年','老年'])
df['amt_quartile'] = pd.qcut(df['amt'], 4, labels=['Q1','Q2','Q3','Q4'],
                             duplicates='drop')

# merge 必带 validate + 前后行数核对（接 data-checkup.md §4）
m = pd.merge(a, b, on='user_id', how='left', validate='one_to_one')
assert len(m) == len(a), '行数变了，键不唯一被放大'

# 窗口：滚动/展开/位移
s = df.set_index('dt').sort_index()['amt']
s.rolling('7D').mean()        # 时间窗 7 天（要求 DatetimeIndex）
s.rolling(7).mean()           # 行窗 7 行（含义不同，别混用）
s.shift(1)                    # 昨日值：算日环比 (s/s.shift(1)-1)
s.expanding().mean()          # 累计均值

# groupby-agg 后立刻 reset_index，防后续 merge 键错位
g = df.groupby(['city','product'])['amt'].agg(['sum','mean']).reset_index()
```

## §5 图表美化最小集（图发给别人前逐条打勾）

| # | 项 | 要求 |
|---|----|------|
| 1 | 轴标签+单位 | x/y 轴都有名字；金额写「元/万元」、比例写「%」 |
| 2 | 样本量注释 | 标题或角注写 `n=…`；分组图每格基数差异大时单独标注 |
| 3 | 标题写结论 | 「A 渠道次留高 8pp」而不是「渠道留存对比」 |
| 4 | 色盲安全 | 用 `tab10` 的蓝/橙为主；禁红绿配对表达正反义 |
| 5 | y 轴不静默截断 | 截断必须加断轴标记或注明；柱状图 y 从 0 开始 |

模板（三件套全含）：

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
ax.bar(g['city'], g['retention'], color='#1f77b4')
ax.set_xlabel('城市'); ax.set_ylabel('次日留存率 (%)')
ax.set_title('B 城市次留领先其余城市 6pp 以上（n=12,437）')
for x, v in zip(g['city'], g['retention']):
    ax.text(x, v + 0.5, f'{v:.1f}%', ha='center')   # 数值直标
fig.savefig('fig/01-城市次留对比.png', bbox_inches='tight')
```

发布前最后一问：读者只看标题和图，能复述出结论吗？不能 → 回 §5 第 3 条重写标题，或图没画对。
