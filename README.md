# PineconeX Documentation

> **Version:** v0.1.0-alpha

PineconeX is a SaaS platform for backtesting and live-trading **Pine Script v6** strategies against real market data. Write your strategy once — backtest it, sweep its parameters, walk-forward validate it, then deploy it live against a connected broker, all from the same interface.

---

## Table of Contents

- [Getting started](#getting-started)
- [Strategies](#strategies)
- [Backtest](#backtest)
- [Parameter Sweep](#parameter-sweep)
- [Walk-Forward Analysis](#walk-forward-analysis)
- [Live Trading](#live-trading)
- [Market Data](#market-data)
- [Brokers](#brokers)
- [Plans](#plans)

---

## Getting started

Sign in at [pineconex.com](https://pineconex.com) with your **Google account**. No separate registration is required.

> **Tip:** We recommend signing in with your GitHub account — it enables seamless version management of your strategies directly from your repositories.

On first login you are placed on the **Free** plan. A free trial period gives you temporary access to Pro features so you can explore the platform before committing.

---

## Strategies

The **Strategies** page is your library of Pine Script v6 strategies. Each strategy has a Monaco-based code editor with Pine Script syntax highlighting and an inline validator that catches errors before you submit a job.

### Creating a strategy

1. Click **New strategy**.
2. Give it a name and paste or write your Pine Script v6 `strategy()` code.
3. Click **Validate** to check for syntax errors.
4. Save — the strategy is now available in the Backtest, Sweep, Walk-Forward, and Live launchers.

### Importing from GitHub

Link your GitHub account under **Account → GitHub**, then use **Import from GitHub** to pull any `.pine` file from your linked repository. Imported strategies stay in sync: changes pushed to GitHub are reflected automatically. GitHub-imported strategies do not count against your strategy quota.

### Sharing a strategy

Open a strategy and click the **Share** button. You can make it:

- **Private** — only you can see it.
- **Open** — anyone with the link gets a private, editable **copy** of the strategy added to their own account (a fork). They get the full code, but as their own copy — your original is untouched.
- **Protected** — link required *plus* you grant access per user. Granted users can run backtests and live bots with the strategy, but the **source code stays private** — it is never shown to them. The strategy is shared; the code is not.

### Parameter overrides (JSON5)

For each strategy you can define parameter overrides in **JSON5** format via the **Params** editor. This lets you store a set of symbol/timeframe combinations with their tuned input values, so jobs pick them up automatically without editing the Pine source.

Format:
```json5
[
  {
    symbol: "AAPL",
    configs: [
      { tf: "1D", htf: "1W", length: 20, threshold: 0.5 },
      { tf: "4H", length: 10 }
    ]
  }
]
```

Keys must match the variable names of your `input.*()` calls. The Params editor validates them against the parsed inputs in real time.

### Trading costs & fill realism

The engine simulates the standard Pine Script v6 `strategy()` cost and fill-assumption arguments, so your backtests can reflect real-world frictions. These apply to **Backtest, Parameter Sweep, and Walk-Forward** runs (live bots submit real orders instead):

| Argument | Effect |
|----------|--------|
| `commission_type` + `commission_value` | Per-trade commission, charged on both legs. Three modes: `strategy.commission.percent` (% of each fill's value), `strategy.commission.cash_per_contract` (fixed cash per share/contract), and `strategy.commission.cash_per_order` (flat cash per order). |
| `slippage` | Worsens the fill price of every **market and stop** order by a number of ticks (0.01 price units): buys fill higher, sells fill lower. Limit / take-profit fills are exempt. |
| `backtest_fill_limits_assumption` | Models unfilled limit orders: a limit (take-profit) order only fills after price moves this many ticks *past* its price, instead of the moment price touches it. |

All default to no cost (`0`), so a strategy without these arguments backtests frictionlessly. See the inline comments in the default strategy template for exact syntax.

### Position sizing

By default a strategy trades **one share/contract per order**. Control the order size with the standard Pine Script v6 `strategy()` arguments `default_qty_type` and `default_qty_value`:

| `default_qty_type` | Order size |
|--------------------|-----------|
| `strategy.fixed` | Exactly `default_qty_value` shares/contracts. |
| `strategy.cash` | As many whole shares as `default_qty_value` (in account currency) buys — `floor(value / price)`. |
| `strategy.percent_of_equity` | A position worth `default_qty_value` % of account equity — `floor(equity × value / 100 / price)`. |

```pine
strategy("My strategy", default_qty_type = strategy.percent_of_equity, default_qty_value = 10)
```

**Live bots — things to know:**

- **Whole shares only.** Equity orders are rounded **down** to whole shares; if the computed size is below one share the order is skipped. (Crypto keeps fractional size.) Because of the round-down, a `cash` or `percent_of_equity` order usually deploys slightly *less* than the nominal amount — e.g. $5,000 of a $294 stock buys 16 shares (≈ $4,714), not a fractional 16.9.
- **`percent_of_equity` uses your real broker equity.** A live bot reads your connected account's current equity to size the order and refreshes it as the account value changes. Backtest, sweep, and walk-forward runs use the strategy's `initial_capital` instead.

### Pyramiding

`strategy(pyramiding = N)` caps how many entries may be added in the **same direction** while a position is open. The default, `pyramiding = 0`, allows a single entry — additional same-direction entry signals are ignored until the position is closed. A reversal (an opposite-direction entry) is always allowed.

> **Current limitation:** a bot or backtest holds **one position at a time**, so a strategy trades a single lot regardless of the `pyramiding` value — setting it above `0` does not yet stack multiple lots.

### History buffer (`max_bars_back`)

`strategy(max_bars_back = N)` sets how many past bars the engine keeps so your code can reference earlier values of a **variable** (`myVar[n]`). **Omit it** and PineconeX **auto-sizes** the buffer to the deepest `[n]` lookback in your code — just like TradingView — so you never pay for history you don't reference.

Set it explicitly (0–5000) only when the depth can't be known ahead of time — e.g. a variable indexed by a **loop counter or another series** (`myVar[i]`). Then give the engine an upper bound, exactly as TradingView asks you to.

> Built-in series (`close[n]`, …) and `ta.*` functions always see full history regardless of this setting — it only bounds *user-variable* lookback.

> **Indexing an indicator's past value:** assign it to a **variable first**, then index the variable — `e = ta.ema(close, 20)` then `e[1]`. Indexing the call directly (`(ta.ema(close, 20))[1]`) returns `na` on PineconeX, unlike TradingView.

---

## Backtest

Run a single backtest of a strategy against a historical dataset.

### Configuration

| Field | Description |
|-------|-------------|
| **Strategy** | Select a strategy from your library. |
| **Symbol / Index** | Pick the market index, then the individual symbol. |
| **Timeframe** | Bar resolution for the primary series (1D, 4H, 1H, 15m, 5m, …). |
| **Higher timeframe** | Optional — maps to the `htf` input if your strategy uses one. |
| **Intrabar TF** | Optional — maps to an intrabar resolution input. |
| **Date range** | Start and end date for the historical window. |
| **Data source** | Saxo Bank or Massive. Saxo is the default for European equities. |

### Results

Once the job completes, the results page shows:

- **Equity curve** — cumulative net profit over the backtest period.
- **Drawdown** — underwater equity plotted over time.
- **Trade list** — every entry and exit with date, price, P&L, and run-up / drawdown.
- **Metrics** — net profit, gross profit/loss, max drawdown, Sharpe ratio, win rate, profit factor, average trade, number of trades, and more.
- **Logs** — raw container output for debugging.
- **AI analysis** — optional one-click AI narrative summarising performance (requires a configured AI provider).

### Comparing backtests

Select up to **5 completed backtests** from the history list using the checkboxes, then click **Compare**. The comparison view overlays equity curves and places metrics side by side for easy evaluation.

---

## Parameter Sweep

Systematically search the parameter space of a strategy to find robust configurations.

### Sweep annotation

Mark which inputs to sweep by adding `//@sweep` before their `input.*()` call:

```pine
//@sweep
fast = input.int(10, minval=2, maxval=50)
//@sweep
slow = input.int(30, minval=10, maxval=200)
```

PineconeX reads the `minval` and `maxval` from each annotated input to define the search bounds automatically.

### Sweep modes

| Mode | Description |
|------|-------------|
| **Grid** | Exhaustive 2-D grid over the two swept parameters. Best when you need to see the full landscape. |
| **Random** | Uniform random sampling across all swept parameters. Fast, unbiased exploration. |
| **Bayesian** | Surrogate UCB optimiser. Explores efficiently — finds good regions with far fewer trials than Grid. |
| **Monte Carlo** | Simulated annealing with random restarts. Good at escaping local optima. |
| **RBF Optimise** | Cubic RBF surrogate model. Fewest evaluations needed; smart interpolation between sample points. Based on [Costa & Nannicini, *RBFOpt* (2016)](https://arxiv.org/pdf/1605.00998.pdf). |

### Results

- **Heatmap** — net profit (or any metric) plotted as a colour grid over the two swept parameters. Reveals whether good performance is isolated (fragile) or spread across a region (robust).
- **Ranked runs** — all completed trials sorted by the chosen metric. Click any row to drill into that run's full backtest results.

### Time limits

Sweeps and backtests run under a maximum wall-clock time. A job that exceeds its limit is stopped automatically and marked **failed** — so a very large grid or a long date range may need to be narrowed to finish in time. Live bots are not time-limited.

---

## Walk-Forward Analysis

Walk-forward analysis guards against overfitting by repeatedly training on a window of history and immediately testing on the unseen period that follows.

### How it works

The total date range is split into **N windows**. For each window:

1. An in-sample period is used to optimise the strategy (via the configured sweep mode).
2. The best parameters found are applied to the immediately following out-of-sample period.
3. The out-of-sample result is recorded.

The final result is the concatenation of all out-of-sample periods, giving a realistic picture of how the strategy would have performed had you been re-optimising it live.

### Configuration

| Field | Description |
|-------|-------------|
| **Windows** | Number of train/test splits. More windows → shorter each, more data points. |
| **In-sample split** | Percentage of each window used for training (e.g. 70 % in-sample, 30 % out-of-sample). |
| **Trials per window** | Bayesian optimisation trials per in-sample period. |

### Results

Each window is shown as a card with its in-sample and out-of-sample metrics. The combined out-of-sample equity curve is plotted at the top.

---

## Live Trading

Deploy a strategy as a live bot that connects to a broker and executes orders in real time.

> **Pro or Premium plan required.** Live trading is not available on the Free plan.

### Launching a bot

1. Go to **Live** and connect a broker (see [Brokers](#brokers)).
2. Select a strategy and symbol.
3. Choose the timeframe (1D, 1H, 15m, 5m).
4. Enable **Auto-restart** if you want the bot to restart automatically after a crash.
5. Click **Launch**.

### Monitoring

Running bots are listed with their status (`running`, `stopped`, `failed`). Click **Logs** on any bot to stream its container output in real time. Bot lifecycle events (started, stopped, crashed, restarted) are recorded in the event log and can be exported as CSV.

### Auto-restart

When auto-restart is on, the platform will restart the bot automatically if it crashes, up to a configured limit. The restart count is shown on the bot card.

### How orders are executed

It is important to understand how a live bot turns a strategy signal into a broker order:

- **Bots act on bar close.** On each new completed bar, the bot evaluates your strategy. When the strategy opens or closes a position, the bot submits a **market order** to your connected broker at that moment.
- **The reported price is the bar close (the signal price), not the actual fill.** PineconeX records and displays the entry/exit at the closing price of the signal bar. The bot submits the order but does **not** read back the broker's true execution price — so any **slippage** between the signal price and the real fill is not reflected in PineconeX.
- **PineconeX does not track your live profit & loss.** It records lifecycle events (started, stopped, crashed) and the signals it acted on, but it does not reconcile actual fills, partial fills, or rejections. **Your broker account is the source of truth** for real positions, fills, and P&L — always confirm there.

> Because of this, live results can differ from a backtest even on identical signals: a backtest fills at modelled prices, while a live order fills at whatever the market gives you. Treat the bot's reported prices as the *signal* price, and your broker statement as the *settled* price.

---

## Market Data

The **Data** page shows the market data catalog: every symbol and timeframe combination that has been fetched and is available for backtesting.

Each entry shows the data source, timeframe, date range, and row count. Use the **Fetch** button to trigger a data update for a symbol/timeframe that is missing or stale.

### Supported sources

| Source | Coverage |
|--------|----------|
| **Saxo Bank** | European equities (DAX, CAC40, AEX, BEL20) + US equities. Requires a connected Saxo account. |
| **Alpaca** | US equities. |
| **Massive** | Broad market data via the Massive API. |

### Data retention

Fetched market data is cached so repeat jobs run instantly without re-downloading. A dataset that hasn't been used by any job for an extended period is automatically removed from the catalog to save storage. Nothing is lost permanently — the next backtest, sweep, or walk-forward that needs it simply re-fetches it from the source, and any dataset that is still in regular use is never evicted.

---

## Brokers

Connect a broker under **Account** or on the **Live** page.

### Saxo Bank

1. Click **Connect Saxo** and choose **Simulation** or **Live** environment.
2. You are redirected to Saxo's OAuth login.
3. After authorisation, your account is linked. Select which Saxo account to trade on.

> The simulation environment (`sim`) uses Saxo's paper-trading gateway. Recommended for testing before going live.

### Alpaca

Connect an Alpaca account to trade US equities.

1. Click **Connect Alpaca** and choose **Paper** or **Live** environment.
2. Enter your Alpaca API key and secret.
3. After connecting, your account is linked and ready to trade.

> The paper environment uses Alpaca's paper-trading API. Recommended for testing before going live.

---

## Plans

| | Free | Pro | Premium |
|--|------|-----|-----|
| Strategies | 5 | Unlimited | Unlimited |
| Concurrent jobs | 1 | 5 | 10 |
| Live trading | — | Yes | Yes |
| Backtesting | Yes | Yes | Yes |
| Parameter sweep | Yes | Yes | Yes |
| Walk-forward | Yes | Yes | Yes |

GitHub-imported strategies do not count against the strategy quota on any plan.

Upgrade your plan under **Account → Plan**.

---

## Support

- **Website:** [pineconex.com](https://pineconex.com)
- **Telegram:** link shown on the Support page inside the app.
- **Email:** support@pineconex.com
- **General inquiries:** info@pineconex.com
