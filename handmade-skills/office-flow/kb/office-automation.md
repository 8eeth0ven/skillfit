# 三件套自动化（Office 文件程序化处理）

> 场景对号 → 工具定死 → 先 3 条试跑 → 全量。所有"读不到/写坏"先查本表陷阱节。

## §1 工具选型矩阵

| 操作 | docx | xlsx | pptx |
|---|---|---|---|
| 读文本/数据 | python-docx；只要文本可 `unzip -p f.docx word/document.xml` 快抽 | pandas（分析）/ openpyxl（保格式细节） | python-pptx（文本框遍历） |
| 写/生成 | python-docx（模板法最稳） | openpyxl（样式/公式）/ xlsxwriter（只写更快） | python-pptx（版式占位符法） |
| 改样式保版式 | python-docx 改样式引用，别重建段落 | openpyxl `keep_vba=True` 仅 xlsm | python-pptx 直接改 shape 属性 |
| 批量转 PDF | LibreOffice 无头 `soffice --headless --convert-to pdf`（保真最高） | 同左 | 同左 |
| 表格数据计算 | 不适用 | pandas 读 → 算 → openpyxl 写回 | 不适用 |

选型铁律：**要"内容"用内容库（docx/pptx 遍历），要"数据"用数据库（pandas），要"样式"用对应 office 库**。混着用先想清楚谁是产出方。

## §2 各格式速查与陷阱

### docx（python-docx）

```python
from docx import Document
doc = Document("in.docx")
for p in doc.paragraphs: print(p.style.name, p.text)   # 段落
for t in doc.tables:                                     # 表格
    for row in t.rows: print(c.text for c in row.cells)
```

| 陷阱 | 现象 | 解法 |
|---|---|---|
| 样式继承怪异 | 直接设 run.font.size 无效 | 样式在段落 style 上，改 `doc.styles['Normal']` 或新建 style |
| 表格合并单元格 | row.cells 返回重复 cell 对象 | 用 `(t._tbl)` lxml 层处理，或按 `cell._tc` 去重 |
| 修订/批注 | paragraphs 漏修订内容 | 修订在 w:ins/w:del 节点，需 lxml 遍历 `document.element` |
| 批量生成 | 逐份新建太慢/格式漂移 | **模板法**：占位符 `{{name}}` 写模板，`docx-mailmerge2` 或手工替换 run |

### xlsx（openpyxl / pandas 分工）

```python
import openpyxl
wb = openpyxl.load_workbook("in.xlsx", data_only=False)  # 公式本体
wbv = openpyxl.load_workbook("in.xlsx", data_only=True)  # 缓存计算值(需Excel存过)
```

| 陷阱 | 现象 | 解法 |
|---|---|---|
| 公式读出 `=SUM(...)` 字符串 | data_only=False 是特性 | 三路：①data_only=True 读缓存 ②pandas+formulas 库重算 ③LibreOffice 无头重存后再读 |
| 日期变数字 | 读到 44927 这类序列值 | `cell.is_date` 判定；openpyxl 自动转 datetime（前提格式是日期格式）；pandas 加 `parse_dates` |
| 前导零丢失（电话/工号） | 007 → 7 | 读时 `dtype=str`；写时先 `'007'` 字符串 + `number_format='@'` |
| 合并单元格 | 只有左上角有值其余 None | 读：`ws.merged_cells` 补值；写：先 `unmerge` 或按左上角写 |
| 大文件 OOM | 10万行×多列 load 全量爆 | `read_only=True` 流式读；写用 `write_only=True`；分析直接 pandas 分块 `chunksize` |
| xlsxwriter 不能读 | 它是纯写库 | 混合需求一律 openpyxl |

**pandas vs openpyxl 分工**：算数/聚合/清洗 → pandas；样式/公式/图表对象/合并格 → openpyxl。两边导数据走 `DataFrame` 中转。

### pptx（python-pptx）

| 需求 | 做法 |
|---|---|
| 按模板批量生成 | 母版定版式 → 代码只填占位符：`slide.placeholders[idx].text = x`（**不要**凭空加文本框，版式会乱） |
| 遍历全部文字 | `for shape in slide.shapes: if shape.has_text_frame:` |
| 图表数据绑定 | `chart.replace_data(CategoryChartData(...))`，图表类型建时定死 |
| 图片批量换 | 定位 `shape.shape_type == PICTURE` → `shape._element` 替换 blip 引用 |
| 逐页一致性 | 母版改一次全局生效；页内手改的不受母版管——批量任务禁止页内手改 |

## §3 批量处理骨架（试 3 条 → 全量）

```python
# 伪骨架：增量落盘 + 失败不中断
import pathlib, shutil, json
SRC, OUT = pathlib.Path("原件"), pathlib.Path("输出")
ledger = []
for i, f in enumerate(SRC.glob("*.docx")):
    try:
        shutil.copy(f, f.with_suffix(".docx.bak"))          # 备份
        # ... 处理 → OUT/f.name
        ledger.append({"file": f.name, "ok": True})
    except Exception as e:
        ledger.append({"file": f.name, "ok": False, "err": str(e)[:100]})
    if i % 10 == 0: pathlib.Path("台账.json").write_text(json.dumps(ledger, ensure_ascii=False))
```

纪律回扣：全量前先用前 3 个文件走完整链路并人工抽查输出。

## §4 跨格式转换矩阵（无损性标注）

| 从 \ 到 | pdf | docx | xlsx | txt/md | html |
|---|---|---|---|---|---|
| docx | LibreOffice 无头（≈无损，字体需装） | — | 表格可抽（有损：样式丢） | pandoc（基本无损） | pandoc（图片需同目录） |
| xlsx | LibreOffice（分页可能截断列！） | 数据可写（公式丢） | — | pandas.to_csv（值，公式丢） | pandas.to_html（值） |
| pptx | LibreOffice（≈无损） | 文本可抽（版式丢） | 不适用 | 文本遍历导出 | 不适用 |
| pdf | — | pdf2docx（**排版还原中等**，表格可） | pdfplumber 表格→DataFrame（准确率看线框） | 文本层直接抽（§PDF-1） | 同左 |
| md | pandoc+latex（数学式需装环境） | pandoc | 表格语法→pandas→xlsx | — | pandoc |

有损必抽查：转换后抽 2-3 份人工对照（文本完整/表格结构/图片三件），不达标换路线重转，不硬交。

## §5 常见翻车表

| 翻车 | 根因 | 修法 |
|---|---|---|
| 打开文件报 zip 错 | 文件其实是 .doc/.xls 老格式或伪装后缀 | `file f.docx` 验明正身；老格式先 `soffice --convert-to docx` |
| 写完样式全丢 | 用 pandas.to_excel 覆盖了原文件 | 永远写新文件；要保样式用 openpyxl 载入原文件改后另存 |
| 中文乱码 | csv 用系统默认编码打开 | 读写都显式 `encoding="utf-8-sig"`（BOM 兼容 Excel） |
| 打开提示"修复" | 写入时没关文件句柄/并发写 | with 块；批量写串行或按文件分锁 |
| 公式全变 #REF! | openpyxl 搬 sheet 跨 workbook | 公式引用是字符串不自动改写，搬完 sed 替换表名或用 xlwings（走真 Excel） |
