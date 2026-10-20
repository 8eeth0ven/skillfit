# 明细目录（总索引）

> 用法：先定位"管什么"，再开命中文件的命中节；禁止通读。

| 文件 | 管什么 | 何时开 |
|---|---|---|
| office-automation.md | 工具选型矩阵、docx/xlsx/pptx 各自速查与陷阱、跨格式转换矩阵 | 读写/批量处理 Office 文件 |
| pdf-and-career-docs.md | PDF 文本层判定、表格提取、合并拆分水印、生成三路、OCR、简历模板与 ATS | 一切 PDF 操作 / 做简历 |

## 开节速查

```bash
grep -n "^## \|^### " kb/office-automation.md
grep -n "^## \|^### " kb/pdf-and-career-docs.md
```

## 组合拳

- 批量改 Word → `三件套 §1 选型` → `§2 docx` → 备份纪律（SKILL.md）
- PDF 抽数字 → `PDF §1 判层` → `§1 表格提取` → 失败转 `§3 OCR`
- 做简历 → `PDF §4` 全节走
- 全链转换（如 docx→pdf）→ `三件套 §4 转换矩阵` 查有损标注
