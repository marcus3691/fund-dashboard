# Fund Analyzer Skill

AI-driven fund analysis toolkit for professional investment research.

## Description

This skill provides a complete framework for analyzing mutual funds and ETFs using:
- NAV (Net Asset Value) data analysis
- Quarterly holding reports analysis  
- Peer comparison based on volatility and style
- AI-powered attribution and insight generation

Based on the methodology from "AI Fund Research" (圆手酱) and "Large Models are Killing Fund Research" (老工).

## Installation

```bash
# The skill will be auto-loaded by OpenClaw
# Requires: tushare, pandas, markdown, weasyprint
```

## Quick Start

### Analyze a single fund

```bash
# Using the CLI
# Analyze specific period
openclaw skill fund-analyzer analyze 501220.SH --start 2023-06-01 --end 2025-12-31

# Or analyze full year
openclaw skill fund-analyzer analyze 501220.SH --year 2025

# Or in conversation
"Analyze fund 国泰行业轮动A from June 2023 to December 2025"
```

### Compare funds

```bash
# Compare two funds over same period
openclaw skill fund-analyzer compare 501220.SH 005741.OF --start 2023-06-01 --end 2025-12-31

# Or in conversation  
"Compare 国泰行业轮动A and 南方君信A from 2023 to 2025"
```

### Build volatility database

```bash
# Build full-market fund database for specific period
openclaw skill fund-analyzer build-db --start 2023-06-01 --end 2025-12-31
```

## Features

### 1. Flexible Time-Range Holding Analysis
- Extracts top 15 holdings for ALL quarter-end nodes within analysis period
- Includes: start date (period beginning) + all quarter-ends + end date (period end)
- Example: For 2023-06 to 2025-12, analyzes: 2023Q2, 2023Q3, 2023Q4, 2024Q1, 2024Q2, 2024Q3, 2024Q4, 2025Q1, 2025Q2, 2025Q3, 2025Q4
- Tracks position changes (add/reduce/exit) across the full timeline
- Industry distribution evolution
- Sector-specific deep dives (e.g., rare earth, gold)

### 2. Volatility-Based Peer Comparison
- Groups funds by volatility (low/med/high)
- Compares with style-matched peers only
- Calculates Sharpe ratio, max drawdown
- Ranks within peer group

### 3. AI-Powered 9-Dimension Analysis
Following the proven framework:
1. Investment philosophy (one-sentence summary)
2. Strategy characteristics
3. Key metrics tracked
4. Rebalancing logic
5. Peer comparison within volatility group
6. Suitable/unsuitable environments
7. Buy/sell strategies
8. Capability circle analysis
9. Performance improvement recommendations

### 4. Quality Control Checklist
- Data source verification (Tushare only)
- No unverified real-time prices
- Peer comparison correctness (FOF vs FOF, not ETF)
- Double-verified rebalancing logic (positions + NAV)
- Balanced positive/negative assessments

## Data Sources

- **Primary**: Tushare Pro API (fund_nav, fund_portfolio, fund_basic, fund_manager)
- **Coverage**: Chinese mutual funds (股票型, 混合型, FOF)
- **Frequency**: Quarterly holdings, daily NAV

## Output

### Reports Generated
1. `fund_analysis_{code}_{start}_{end}.md` - Markdown report
2. `fund_analysis_{code}_{start}_{end}.pdf` - PDF report
3. `peer_comparison_{code}_{start}_{end}.md` - Peer analysis
4. `fund_data/volatility_groups_{start}_{end}.json` - Volatility database

### Report Structure
```
1. Fund Basic Information
2. Performance Analysis (NAV data for full period)
3. Complete Quarter-End Holdings Analysis
   - Holdings at period START date
   - Holdings at ALL quarter-end nodes within period
   - Holdings at period END date
   - Industry evolution across full timeline
   - Sector-specific analysis
4. Peer Comparison (volatility-matched)
5. AI 9-Dimension Analysis
6. Summary & Investment Recommendation
```

## Configuration

Edit `config.yaml`:

```yaml
tushare:
  token: "your_tushare_token"
  server: "http://tushare.xyz"

analysis:
  # Default analysis period
  default_period:
    start: "2025-01-01"
    end: "2025-12-31"
  
  # Number of top holdings to extract per quarter-end
  top_holdings: 15
  
  # Volatility grouping for peer comparison (%)
  volatility_groups:
    low: [0, 10]
    mid_low: [10, 15]
    medium: [15, 20]
    high: [20, 30]
    extreme: [30, 100]
    
output:
  format: ["md", "pdf"]
  directory: "./fund_analysis_reports"
```

## Best Practices

### Do's
✅ Always verify data is from Tushare
✅ Analyze ALL quarter-end nodes within the period (not fixed 5 quarters)
✅ Include period start and end dates in holdings analysis
✅ Compare with correct peer group (same fund type)
✅ Verify rebalancing with both holdings + NAV changes
✅ Include both strengths and weaknesses
✅ Label inferences clearly

### Don'ts
❌ Use real-time stock/commodity prices
❌ Compare FOF with ETFs (different nature)
❌ Assume fixed "5 quarters" - adapt to analysis period
❌ Include unverified rankings
❌ Make claims without data support
❌ Only write positive assessments

## Examples

### Example 1: Multi-Year Analysis

**Input**: "Analyze 国泰行业轮动A (501220.SH) from June 2023 to December 2025"

**Key Findings**:
- Analyzed 11 quarter-end nodes: 2023Q2-Q4, 2024Q1-Q4, 2025Q1-Q4
- Successfully rotated from gold+property to gold+rare earth to gold+silver
- Rare earth position peaked at 100% in 2025Q1, reduced to 16% in 2025Q4
- Ranked #1 among 4 FOF peers (58.55% return, Sharpe 2.98)
- High volatility (19.65%) but superior risk-adjusted returns

### Example 2: Peer Comparison

**Input**: "Compare 国泰行业轮动A vs 南方君信A from 2023 to 2025"

**Output**:
| Metric | 国泰行业轮动A | 南方君信A |
|---|---|---|
| Period Return | 85.32% | 45.67% |
| Volatility | 21.45% | 8.92% |
| Sharpe | 3.89 | 4.89 |
| Style | Aggressive/Offensive | Stable/Growth |

## Troubleshooting

### Issue: "Insufficient data for analysis"
**Solution**: Check if fund has complete NAV data for the specified period (>100 trading days)

### Issue: "Cannot find peers for comparison"
**Solution**: Expand volatility range or include more fund types

### Issue: "PDF generation failed"
**Solution**: Install weasyprint dependencies (cairo, pango)

## References

1. 圆手酱《AI基金研究》- https://mp.weixin.qq.com/s/S8sJNYuMtxcUgFovLV2pww
2. 老工《大模型正在杀死基金研究》- https://mp.weixin.qq.com/s/bIeekCG7BUkz_xcD8_p7Gw

## Version History

- v1.0.0 (2026-03-08): Initial release
  - 9-dimension AI analysis
  - Volatility-based peer comparison
  - Flexible time-range holdings analysis
  - Quality control checklist

## License

MIT License - Open source for investment research community.
