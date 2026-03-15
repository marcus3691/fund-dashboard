# Fund Analysis AI Prompts
# 9-Dimension Analysis Framework

## Prompt 1: Investment Philosophy

```
You are analyzing fund {fund_code} ({fund_name}) for {year}.

Based on the following data:
- Annual return: {annual_return}%
- Volatility: {volatility}%
- Top sectors: {top_sectors}
- Quarterly holdings evolution: {holdings_summary}

Provide a ONE-SENTENCE summary of the fund manager's investment philosophy.
This should capture the core strategy in a concise, memorable way.

Format: "[Strategy type] focused on [core approach], characterized by [key features]"

Example: "A sector-rotation strategy centered on precious metals and strategic resources, using high-frequency quarterly rebalancing to capture commodity cycles"
```

## Prompt 2: Strategy Characteristics

```
Analyze the investment strategy of {fund_name} ({fund_code}) based on:

HOLDINGS DATA:
{quarterly_holdings}

Calculate and describe:
1. Industry concentration (single sector max %)
2. Rebalancing frequency (how often top holdings change)
3. Holding period (short-term <1Q, medium 2-3Q, long-term >4Q)
4. Style characteristics (offensive/defensive, high/low turnover)

Be specific with numbers from the data.
```

## Prompt 3: Key Metrics

```
Based on the fund's holdings evolution:

{sector_evolution}

What metrics do you think the fund manager primarily tracks?
Consider:
- Commodity prices (gold, rare earth, etc.)
- Macroeconomic indicators
- Policy changes
- Sector-specific data

List 3-5 key metrics and explain why they matter for this strategy.
```

## Prompt 4: Rebalancing Logic

```
Analyze the quarterly rebalancing decisions for {fund_name}:

QUARTERLY CHANGES:
{quarterly_changes}

NAV PERFORMANCE:
{monthly_nav}

For each quarter:
1. What changed in the portfolio?
2. What was the likely rationale?
3. How did NAV perform after the change?

Verify: Did the rebalancing improve returns? Provide evidence.
```

## Prompt 5: Peer Comparison

```
Compare {fund_name} with volatility-matched peers:

TARGET FUND:
- Code: {fund_code}
- Return: {target_return}%
- Volatility: {target_volatility}%
- Sharpe: {target_sharpe}

PEER GROUP ({peer_group}):
{peer_data}

Provide:
1. Rank within peer group (X/N) for return, sharpe, risk control
2. Key strengths vs peers
3. Key weaknesses vs peers
4. One-sentence positioning within the group
```

## Prompt 6: Environment Fit

```
Based on the fund's strategy and {year} performance:

SUITABLE ENVIRONMENTS:
- When does this strategy work best?
- What market conditions favor this approach?
Rate 1-5 stars for each scenario.

UNSUITABLE ENVIRONMENTS:
- When does this strategy underperform?
- What conditions hurt this approach?
Rate 1-5 stars for each scenario.

Be specific: bull/bear markets, sector rotations, volatility regimes, etc.
```

## Prompt 7: Trading Strategy

```
For investors considering {fund_name}, provide:

BUY SIGNALS:
- When should you buy? (3-5 specific triggers)
- Entry price/level suggestions

SELL/EXIT SIGNALS:
- When should you sell? (3-5 specific triggers)
- Stop-loss levels

HOLDING PERIOD:
- Recommended duration
- Rebalancing frequency for investors

RISK MANAGEMENT:
- Position sizing recommendations
- Maximum portfolio allocation
- Risk warnings
```

## Prompt 8: Capability Circle

```
Assess the fund manager's capabilities:

STRENGTHS (Retain):
- What does the manager do well? (3-5 points)
- Evidence from {year} performance
- Core competencies

WEAKNESSES (Improve):
- What are the limitations? (3-5 points)
- Evidence from drawdowns/underperformance
- Capability gaps

CAPABILITY TRAPS:
- What might appear to be a strength but is actually a risk?
- "The most concentrated sector is not the alpha source"
- Potential blind spots
```

## Prompt 9: Improvement Plan

```
If you were advising this fund manager, what would you recommend?

EXPAND CAPABILITIES:
- What new skills/strategies should they develop? (2-3 items)
- Why would this help?

RETAIN STRENGTHS:
- What core competencies should they keep? (2-3 items)
- Why are these critical?

IMPROVE OPERATIONS:
- Risk management enhancements
- Position sizing adjustments
- Sector concentration limits
- Cash management

Be specific and actionable.
```

## Master Prompt: Full Analysis

```
You are a professional fund analyst using AI-driven methodology.

Analyze fund {fund_code} ({fund_name}) for {year} using the following data:

=== PERFORMANCE DATA ===
{performance_data}

=== HOLDINGS DATA (5 Quarters) ===
{holdings_data}

=== PEER COMPARISON ===
{peer_comparison}

Provide a comprehensive analysis covering:

1. INVESTMENT PHILOSOPHY (one sentence)
2. STRATEGY CHARACTERISTICS (concentration, frequency, style)
3. KEY METRICS (what the manager tracks)
4. REBALANCING LOGIC (quarterly changes + rationale)
5. PEER COMPARISON (ranking, strengths, weaknesses)
6. ENVIRONMENT FIT (suitable/unsuitable markets)
7. TRADING STRATEGY (buy/sell signals for investors)
8. CAPABILITY CIRCLE (strengths, weaknesses, traps)
9. IMPROVEMENT PLAN (what to expand/retain)

Be objective, data-driven, and specific. Include both positive and negative assessments.
```

## Quality Control Checklist

```
Before finalizing the report, verify:

DATA QUALITY:
□ All numbers are from Tushare (not external sources)
□ 5 quarters of holdings data are complete
□ NAV data covers full year (>200 days)
□ Calculations are correct (return, volatility, sharpe)

ANALYSIS QUALITY:
□ Peer comparison uses correct fund types (FOF vs FOF)
□ Rebalancing logic has evidence (positions + NAV)
□ Both strengths and weaknesses are included
□ Inferences are labeled as "inferred"
□ No real-time prices are used

OUTPUT QUALITY:
□ Report structure follows template
□ All 9 dimensions are covered
□ Tables are properly formatted
□ Conclusions are supported by data
```
