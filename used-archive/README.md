# 已停用的批次修复脚本

本目录保留两份曾用于处理历史评测批次的脚本，仅供查阅。

![早期批次和后来重采样的记录需要按试验区分](../docs/assets/guide-historical.svg)

**请勿再次运行。** `rerun-legacy.py` 和 `quarantine-toolleak.py` 无法区分旧提示词生成的记录和后续重新采样的记录，会把已修正的数据再次标为无效。

查验现有结果请使用[测量审计指南](../docs/measurement-audit.md)中的只读方法。
