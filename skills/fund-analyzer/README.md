# Fund Analyzer Skill

A professional-grade fund analysis toolkit powered by AI.

## Quick Start

```bash
# Analyze a fund
openclaw skill fund-analyzer analyze 501220.SH --year 2025

# Compare two funds
openclaw skill fund-analyzer compare 501220.SH 005741.OF

# Build volatility database
openclaw skill fund-analyzer build-db --year 2025
```

## Features

- **Complete Holdings Analysis**: 5-quarter deep dive with sector tracking
- **Volatility-Based Peer Comparison**: Compare with true peers only
- **9-Dimension AI Analysis**: Proven framework from industry experts
- **Quality Control**: Built-in checklists prevent common errors

## Documentation

- [SKILL.md](SKILL.md) - Full skill documentation
- [templates/prompts.md](templates/prompts.md) - AI analysis prompts
- [config.yaml](config.yaml) - Configuration options

## Requirements

- Tushare Pro API access
- Python 3.8+
- Dependencies: tushare, pandas, markdown, weasyprint

## License

MIT - Open source for investment research.
