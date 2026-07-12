# PineconeX Documentation

> **Version:** v0.1.1-alpha · **Last updated:** 2026-07-07

PineconeX is a SaaS platform for backtesting and live-trading **Pine Script® v6** strategies against real market data. Write your strategy once — backtest it, sweep its parameters, validate that the edge is real, then deploy it live against a connected broker, all from the same interface.

---

## Table of Contents

- [Getting started](#getting-started)
- [Strategies](#strategies)
  - [Learning Pine Script v6](#learning-pine-script-v6)
- [Backtest](#backtest)
- [Debugging with log.info()](#debugging-with-loginfo)
- [Parameter Sweep](#parameter-sweep)
- [Validation](#validation)
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

### Learning Pine Script v6

PineconeX runs standard **Pine Script v6**, so the official TradingView documentation is your primary language reference:

- **[Pine Script v6 User Manual](https://www.tradingview.com/pine-script-docs/)** — the language guide: syntax, types, execution model, and how-to tutorials.
- **[Pine Script v6 Reference Manual](https://www.tradingview.com/pine-script-reference/v6/)** — the full API reference for every built-in function, variable, and keyword (`ta.*`, `strategy.*`, `str.*`, …).
- **[TradingView Community Scripts](https://www.tradingview.com/scripts/)** — thousands of published open-source strategies and indicators to learn from and adapt.

> **PineconeX runs Pine headless** — there is no chart, so chart/UI calls (`plot`, `hline`, drawings, tables, …) are accepted but silently ignored, and a few primitives diverge from TradingView (e.g. `alertcondition()` is repurposed for notifications, indexing an indicator call directly returns `na`). The language is the same; the runtime is backtest/live execution rather than a chart. These differences are called out throughout this guide where they matter.

### Creating a strategy

1. Click **New strategy**.
2. Give it a name and paste or write your Pine Script v6 `strategy()` code.
3. Click **Validate** to check for syntax errors.
4. Save — the strategy is now available in the Backtest, Sweep, Validation, and Live launchers.

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
      { tf: "1D", htf: "1W", ltf: "60m", length: 20, threshold: 0.5 },
      { tf: "60m", length: 10 }
    ]
  }
]
```

`symbol`, `tf`, `htf`, and `ltf` are **reserved keys**; every other key must match the variable name of one of your `input.*()` calls. The Params editor validates them against the parsed inputs in real time.

- **`tf`** — the primary bar resolution for that config.
- **`htf`** — optional **higher** timeframe (for `request.security`). On the Backtest form it pre-selects the higher-timeframe dataset; on live bots it maps to your strategy's `htf` input.
- **`ltf`** — optional **lower / intrabar** timeframe (for `request.security_lower_tf`). On the Backtest form it pre-selects the **Intrabar TF** dataset; on a live bot it sets the intrabar warmup resolution fetched from the broker feed. (Sweep supports intrabar too, but picks it from its own form control rather than from this key. The Significance test rejects an intrabar series — see [Validation](#validation).)

All three timeframe keys accept the same [timeframe strings](#timeframe-syntax) as the pickers.

#### Timeframe syntax

Timeframes use a uniform, minute-based notation everywhere in PineconeX (the Params JSON5, the Data catalog, and the Backtest / Sweep / Validation / Live pickers). Use these exact strings — they are case-sensitive:

| String | Resolution |
|--------|-----------|
| `1m`   | 1 minute |
| `5m`   | 5 minutes |
| `15m`  | 15 minutes |
| `30m`  | 30 minutes |
| `60m`  | 1 hour |
| `90m`  | 90 minutes |
| `1D`   | Daily |
| `1W`   | Weekly |
| `1M`   | Monthly |

Intraday resolutions are written in **minutes** (`<n>m`); daily and above use `1D` / `1W` / `1M`. The legacy `1H` (= `60m`) and `4H` (= `240m`) aliases are still accepted for backward compatibility, but prefer the minute form.

> **Live bots** trade the broker feed directly (no stored dataset), so they omit weekly/monthly and the 1-minute step — the available live timeframes are `5m`, `15m`, `30m`, `60m`, `90m`, `1D`. Keep a config's `tf` within this set if you plan to run it live.

### Trading costs & fill realism

The engine simulates the standard Pine Script v6 `strategy()` cost and fill-assumption arguments, so your backtests can reflect real-world frictions. These apply to **Backtest, Parameter Sweep, and Validation** runs (live bots submit real orders instead):

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
- **`percent_of_equity` uses your real broker equity.** A live bot reads your connected account's current equity to size the order and refreshes it as the account value changes. Backtest, sweep, and validation runs use the strategy's `initial_capital` instead.

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
| **Timeframe** | Bar resolution for the primary series (`1M`, `1W`, `1D`, `90m`, `60m`, `30m`, `15m`, `5m`, `1m`). See [Timeframe syntax](#timeframe-syntax). |
| **Higher timeframe** | Optional — the `request.security` series. Pre-fillable from the `htf` key in your [JSON5 params](#parameter-overrides-json5). |
| **Intrabar TF** | Optional — the `request.security_lower_tf` (intrabar) series. Pre-fillable from the `ltf` key in your [JSON5 params](#parameter-overrides-json5). |
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

## Debugging with `log.info()`

When a strategy isn't trading the way you expect, the fastest way to see *why* is to print the values your logic depends on. PineconeX supports the standard Pine Script v6 logging functions:

| Function | Use for |
|----------|---------|
| `log.info(msg)` | General trace output — values, flags, "did this branch run?" |
| `log.warning(msg)` | Something unusual but non-fatal. |
| `log.error(msg)` | A condition your strategy treats as a hard problem. |

Each message shows up in the run's **Logs** panel (Backtest, Sweep, and Validation results all have one), and streams live in a bot's **Logs** view for live trading. In a backtest each line is prefixed with the **bar timestamp** it was emitted on, so you can line the output up against the chart.

### Printing values

`log.*` takes a **single string** argument — so to print a number, a boolean, or a series value you convert it with `str.tostring()` and join the pieces with `+`:

```pine
//@version=6
strategy("Debug demo", overlay = true)

fast = ta.ema(close, 10)
slow = ta.ema(close, 30)
cross_up = ta.crossover(fast, slow)

// Print the values every bar
log.info("close=" + str.tostring(close) + " fast=" + str.tostring(fast, "0.00") + " slow=" + str.tostring(slow, "0.00") + " cross_up=" + str.tostring(cross_up))

if cross_up
    strategy.entry("Long", strategy.long)
    log.info("ENTRY long @ " + str.tostring(close, "0.00"))
```

A few things to know:

- **`str.tostring(value, "0.00")`** applies a format string — here, two decimal places. Handy for prices and indicator values that would otherwise print a long float.
- **Booleans and `na` print directly** — `str.tostring(cross_up)` gives `true` / `false`, and a `na` value prints as `na`, so you can see exactly when a value is missing.
- **Series and `ta.*` results log their current-bar value automatically.** You don't need to index them — `str.tostring(ta.rsi(close, 14))` prints this bar's RSI. (To inspect a *past* value, assign it to a variable first and index that: `r = ta.rsi(close, 14)` then `str.tostring(r[1])` — see the note on [indexing indicator values](#history-buffer-max_bars_back).)
- **No `{0}` placeholders.** Unlike TradingView, PineconeX does not support format-placeholder logging (`log.info("x={0}", x)`) — only the first argument is read, so build the whole string with `+`.

### Tracing *why* a signal did or didn't fire

The most useful pattern is logging the individual conditions that gate an entry, so you can see which one is blocking:

```pine
long_ok = cross_up and close > slow and strategy.position_size == 0

if ta.crossover(fast, slow)
    log.info("cross seen | above_slow=" + str.tostring(close > slow) + " flat=" + str.tostring(strategy.position_size == 0) + " -> entry=" + str.tostring(long_ok))
```

Now every time the EMAs cross you get one line showing exactly which guard passed or failed — far quicker than guessing.

### Keep the log readable

Logging **every bar** floods the panel and (for live bots) counts against the captured-log size cap. Gate your debug output behind the condition you actually care about so you only print on the interesting bars:

```pine
// Only log around a potential signal, not on every bar
if cross_up or cross_down
    log.info("signal bar: " + str.tostring(close, "0.00"))
```

> **Tip:** Leave the `log.*` calls gated behind an `input.bool(false, "Debug")` toggle so you can flip verbose tracing on and off without editing the strategy:
> ```pine
> debug = input.bool(false, "Debug logging")
> if debug
>     log.info("state: " + str.tostring(myVar))
> ```

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

## Validation

A backtest tells you what happened. Validation asks whether to believe it.

Both tests place your result against a distribution the strategy was **not** fitted to — that is
what separates them from a backtest with different settings. **Premium plan.**

### Significance — is the edge real, or luck?

The price series is **bar-permuted** hundreds of times: each bar is decomposed into its gap and its
intrabar moves, those are shuffled independently, and valid OHLC bars are rebuilt. The result keeps
the return distribution and the candle geometry but **destroys the cross-bar sequence** — the very
thing a strategy claims to exploit.

The strategy is re-run on every permutation, giving a null distribution of what it scores on noise.
The **p-value** is how often noise did as well as the real thing. Low = the edge is structural.

| Field | Description |
|-------|-------------|
| **Permutations** | Null-distribution size (default 200). The smallest p-value you can measure is 1/(N+1), so N=50 can never report below 0.02. |
| **Test statistic** | `Net P&L %` (default), `Profit factor`, or `Win rate`. |
| **Permutation type** | **Bar** destroys all serial structure. **Block** shuffles N-bar chunks, preserving structure shorter than N — a less strict null for longer-horizon edges. |
| **How the parameters were chosen** | See below. This is the most important control on the page. |
| **Seed** | Omit for a time-seeded run; the effective seed is echoed so any run is reproducible. |

#### The p-value trap

The default, **Fixed params**, re-runs the strategy's authored input defaults on every permutation.
Its null is *"what this one rule scores on noise"* — which is only valid if you chose those numbers
**without looking at the data**.

But the obvious workflow is the opposite: run a Sweep, take the winner, paste it in as the default,
then test it. There, a fixed null is **optimistically biased**. It cannot see that you tried 157
candidates, and the best of 157 noise draws is high *by construction* — that is data-mining bias,
and no number of permutations fixes it.

So tell the test what you actually did. Pick the same search you ran (Grid, Random, Bayesian, …)
and it is **re-run inside every permutation**, so the null becomes *"the best score this strategy
family can be fitted to noise"*. Optimize with Bayesian, test with Bayesian.

This costs what it is worth: `Fixed` is one backtest per permutation, `Grid` is the entire grid. A
200-permutation test over a 157-point grid is 31,400 backtests. The price of the correction is
proportional to the bias it removes.

#### Out-of-sample

There is no separate mode, because out-of-sample is a **date range**. Sweep on 2016–2019, then run
Significance on 2020 with the parameters fixed. Those bars were never touched by the search, so
`Fixed` is the *correct* null there — there is no search to correct for.

> An intrabar timeframe is rejected. Sub-bar structure cannot be synthesized from permuted bars, so
> intra-bar stop/limit fills would be priced against a path that does not exist.

### Stress — which market does the strategy need?

An Ornstein-Uhlenbeck process with Poisson jumps is calibrated to your real series, then a grid of
**half-life × jump intensity** is simulated and the strategy is run over many synthetic paths per
cell. The output is an **operating envelope**: the regions where it survives, and how much jump risk
it absorbs before it breaks.

> **This is not a significance test, and must not be read as one.** The generator makes mean
> reversion true *by construction*, so a mean-reversion strategy beating it proves nothing, and a
> trend-follower will look bad for reasons that have nothing to do with fragility. Run **Significance
> first** as the gate — Stress only discriminates among strategies that already passed it.

---

## Live Trading

Deploy a strategy as a live bot that connects to a broker and executes orders in real time.

> **Available on every plan.** The Free plan includes **1 live trading job** with a limited lifetime (bots are stopped at the end of the trading day); Pro and Premium raise the concurrency limit and run without that daily stop.

### Launching a bot

1. Go to **Live** and connect a broker (see [Brokers](#brokers)).
2. Select a strategy and symbol.
3. Choose the timeframe (`5m`, `15m`, `30m`, `60m`, `90m`, `1D` — see [Timeframe syntax](#timeframe-syntax)).
4. Enable **Auto-restart** if you want the bot to restart automatically after a crash.
5. Click **Launch**.

### Monitoring

Running bots are listed with their status (`running`, `stopped`, `failed`). Click **Logs** on any bot to stream its container output in real time. Bot lifecycle events (started, stopped, crashed, restarted) are recorded in the event log and can be exported as CSV.

If Telegram notifications are configured, each bot also sends a periodic **heartbeat**. A multi-symbol basket sends a single combined overview — one message with a per-symbol table (price, position, live P&L) and a net-P&L summary, colored green/red by profit and loss:

![Telegram heartbeat overview for a multi-symbol basket](images/telegram-heartbeat.png)

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

Fetched market data is cached so repeat jobs run instantly without re-downloading. A dataset that hasn't been used by any job for an extended period is automatically removed from the catalog to save storage. Nothing is lost permanently — the next backtest, sweep, or validation run that needs it simply re-fetches it from the source, and any dataset that is still in regular use is never evicted.

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

## Plans *

| | Free | Pro | Premium |
|--|------|-----|-----|
| Strategies | 5 | Unlimited | Unlimited |
| Concurrent jobs | 1 | 5 | 10 |
| Live trading | 1 job (limited lifetime) | Yes | Yes |
| Backtesting | Yes | Yes | Yes |
| Parameter sweep | Yes | Yes | Yes |
| Validation (significance + stress) | — | — | Yes |

GitHub-imported strategies do not count against the strategy quota on any plan.

Upgrade your plan under **Account → Plan**.

> **(*)** This table is non-binding and may fall out of sync. The [pricing page](https://pineconex.com/#pricing) is the authoritative source for plan features and limits.

---

## Support

- **Website:** [pineconex.com](https://pineconex.com)
- **Telegram:** link shown on the Support page inside the app.
- **Email:** support@pineconex.com
- **General inquiries:** info@pineconex.com
