# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

### Email (139邮箱)

- SMTP服务器: smtp.139.com
- 端口: 465 (SSL)
- 发件人: 18817205079@139.com
- 授权码: ab96ed0b496fd94f6e00
- 用途: 发送基金分析报告

### PDF解析

- **Skill位置**: `/root/.openclaw/workspace/skills/pdf-parser/`
- **依赖**: pdfplumber (已安装)
- **脚本**:
  - `extract_text.py` - 提取全部文本
  - `extract_tables.py` - 提取表格(JSON)
  - `extract_metadata.py` - 提取元数据
- **用法示例**:
  ```bash
  python3 skills/pdf-parser/scripts/extract_text.py file.pdf
  python3 skills/pdf-parser/scripts/extract_tables.py file.pdf
  ```
