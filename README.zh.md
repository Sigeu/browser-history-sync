# Browser History Sync — 浏览器历史同步

[English](README.md)

在 Firefox 系和 Chromium 系浏览器之间合并浏览历史记录，也支持同种浏览器的不同配置间合并。

## 为什么需要这个工具

浏览器自带的历史同步通常只有 3 个月窗口，且经常同步失败。这个工具让你完全掌控：合并多份配置的历史记录、跨浏览器迁移、或者备份数据——全离线运行，无需云端。

## 原理

Firefox 和 Chromium 都用 SQLite 存储历史记录。工具从一个数据库读取访问记录，将目标库中缺失的记录写入，以 `(url, visit_timestamp)` 进行去重。

| 浏览器 | 数据库文件 | 核心表 |
|--------|-----------|--------|
| **Firefox 系** (Firefox, Zen, Waterfox 等) | `places.sqlite` | `moz_places`, `moz_historyvisits` |
| **Chromium 系** (Chrome, Edge, Vivaldi, Brave, Opera 等) | `History` | `urls`, `visits` |

## 使用

```bash
python3 -m browser_history_sync <数据库1> <数据库2> [选项]
```

工具会自动识别两个数据库的类型，确定同步方向。

**示例：**

```bash
# 将 Chromium 历史合并到 Firefox（Linux）
python3 -m browser_history_sync \
    ~/.config/google-chrome/Default/History \
    ~/.mozilla/firefox/xxxx.default-esr/places.sqlite

# 将 Firefox 历史合并到 Chromium（macOS）
python3 -m browser_history_sync \
    ~/Library/Application\ Support/Firefox/Profiles/xxxx.default/places.sqlite \
    ~/Library/Application\ Support/Google/Chrome/Default/History

# 合并两个 Firefox 配置（Windows）
python3 -m browser_history_sync \
    "C:\Users\<You>\AppData\Roaming\Mozilla\Firefox\Profiles\xxxx.default\places.sqlite" \
    "C:\Users\<You>\AppData\Roaming\Mozilla\Firefox\Profiles\yyyy.default\places.sqlite"
```

**选项：**

| 参数 | 默认 | 说明 |
|------|------|------|
| `--commit-every N` | 500 | 每 N 条记录提交一次 |
| `--include-hidden` | — | 包含隐藏 URL（子框架资源等） |

> **重要：** 运行前请关闭所有浏览器。浏览器运行时数据库文件会被锁定。

## 幂等性

多次同步同一对数据库，结果不变——仅添加新记录，不会重复或覆盖。

```
第1次同步：库A → 库B  →  库B 增加库A中有但库B中没有的记录
第2次同步：库A → 库B  →  无变化（所有记录已存在）
```

## 环境要求

Python 3.10+（仅标准库，无需 pip 安装）

## 文件结构

```
browser_history_sync/
  __main__.py           CLI 入口 (python -m browser_history_sync)
  __init__.py
  common.py             共享类型、时间戳转换、数据库类型检测
  reader_chromium.py    读取 Chromium History → 访问记录列表
  reader_firefox.py     读取 Firefox places.sqlite → 访问记录列表
  writer_chromium.py    写入访问记录到 Chromium History
  writer_firefox.py     写入访问记录到 Firefox places.sqlite
  sync_engine.py        同步编排逻辑
```

## 许可

Apache 2.0
