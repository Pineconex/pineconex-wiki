# PineconEx Documentation

> **Version:** v0.1.0-alpha

PineconEx is a SaaS platform for backtesting and live-trading **Pine Script v6** strategies against real market data. Write your strategy once — backtest it, sweep its parameters, walk-forward validate it, then deploy it live against a connected broker, all from the same interface.

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
- **Open** — anyone with the link can view the code and results.
- **Protected** — link required plus you grant access per user.

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

PineconEx reads the `minval` and `maxval` from each annotated input to define the search bounds automatically.

### Sweep modes

| Mode | Description |
|------|-------------|
| **Grid** | Exhaustive 2-D grid over the two swept parameters. Best when you need to see the full landscape. |
| **Random** | Uniform random sampling across all swept parameters. Fast, unbiased exploration. |
| **Bayesian** | Surrogate UCB optimiser. Explores efficiently — finds good regions with far fewer trials than Grid. |
| **Monte Carlo** | Simulated annealing with random restarts. Good at escaping local optima. |
| **RBF Optimise** | Cubic RBF surrogate model. Fewest evaluations needed; smart interpolation between sample points. |

### Results

- **Heatmap** — net profit (or any metric) plotted as a colour grid over the two swept parameters. Reveals whether good performance is isolated (fragile) or spread across a region (robust).
- **Ranked runs** — all completed trials sorted by the chosen metric. Click any row to drill into that run's full backtest results.

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

---

## Market Data

The **Data** page shows the market data catalog: every symbol and timeframe combination that has been fetched and is available for backtesting.

Each entry shows the data source, timeframe, date range, and row count. Use the **Fetch** button to trigger a data update for a symbol/timeframe that is missing or stale.

### Supported sources

| Source | Coverage |
|--------|----------|
| **Saxo Bank** | European equities (DAX, CAC40, AEX, BEL20) + US equities. Requires a connected Saxo account. |
| **Massive** | Broad market data via the Massive API. |

---

## Brokers

Connect a broker under **Account** or on the **Live** page.

### Saxo Bank

1. Click **Connect Saxo** and choose **Simulation** or **Live** environment.
2. You are redirected to Saxo's OAuth login.
3. After authorisation, your account is linked. Select which Saxo account to trade on.

> The simulation environment (`sim`) uses Saxo's paper-trading gateway. Recommended for testing before going live.

### Interactive Brokers

A browser-based OAuth connection to IBKR that does not require TWS to be running locally.

1. Click **Connect IBKR Web**.
2. Log in via IBKR's OAuth page.
3. After authorisation, the connection is active.

### Lightspeed Connect

Enter your Lightspeed API key, account ID, and environment. Optionally provide a custom WebSocket URL for advanced setups.

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

- **Telegram:** link shown on the Support page inside the app.
- **Email:** support@pineconex.com
- **General inquiries:** info@pineconex.com
