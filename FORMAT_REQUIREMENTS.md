# Format Requirements

This plugin should use a single, consistent text format policy to avoid mojibake on Windows and during AstrBot deployment.

## Required Encoding

- Python source files: `UTF-8`
- JSON / YAML / TOML / Markdown: `UTF-8`
- `metadata.yaml`: prefer `UTF-8 with BOM` if AstrBot or the editor shows Chinese incorrectly
- Do not save files as `GBK`, `ANSI`, or `UTF-16`

## Python Files

- Save `.py` files in `UTF-8`
- Prefer adding this header on source files that may be edited on Windows:

```python
# -*- coding: utf-8 -*-
```

## JSON and Config Files

- JSON must remain strictly valid
- Keep key names stable; do not rename or reorder fields unless required
- Use plain ASCII punctuation for keys and structural characters
- Chinese text content is allowed in string values, but file encoding must remain `UTF-8`

## PowerShell UTF-8 Setup

Before checking Chinese output in Windows PowerShell, run:

```powershell
chcp 65001
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
```

## VS Code

- Reopen files with `UTF-8` if Chinese looks broken
- Save files as `UTF-8`
- If a metadata file is still misread, save that file as `UTF-8 with BOM`

## Practical Rules

- If Chinese becomes garbled, check file encoding first, then terminal encoding
- Do not mix full-width punctuation, smart quotes, or hidden characters into config syntax
- Keep all project text files on one encoding standard instead of mixing local defaults
