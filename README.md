# PineconeX Documentation

> **Version:** v0.1.7-alpha

PineconeX is a SaaS platform for backtesting and live-trading **Pine Script® v6** strategies against real market data. Write your strategy once — backtest it, sweep its parameters, validate that the edge is real, then deploy it live against a connected broker, all from the same interface.

**Equities and crypto.** Alongside European and US stocks, PineconeX trades **crypto** — USD and EUR spot pairs on **Bitstamp**, and the US-dollar pairs on **Alpaca**. Crypto markets never close, and the venues' order models differ from an equity broker's in ways that change how a stop-loss behaves — [read this before deploying a crypto bot](#crypto).

---

## Table of Contents

- [Getting started](#getting-started)
- [Strategies](#strategies)
  - [Learning Pine Script v6](#learning-pine-script-v6)
  - [Same-bar stop and target (the bar magnifier)](#same-bar-stop-and-target-the-bar-magnifier)
- [Backtest](#backtest)
- [Debugging with log.info()](#debugging-with-loginfo)
- [Parameter Sweep](#parameter-sweep)
- [Validation](#validation)
- [Machine Learning Models](#machine-learning-models)
  - [Training a regime model on the platform (HMM)](#training-a-regime-model-on-the-platform-hmm)
- [Gamma Exposure (GEX)](#gamma-exposure-gex)
- [Regime-aware sizing (VMSC)](#regime-aware-sizing-vmsc)
- [Live Trading](#live-trading)
  - [Performance](#performance)
  - [Execution routing](#execution-routing)
  - [Options routing (Alpaca)](#options-routing-alpaca)
  - [Multi-symbol baskets](#multi-symbol-baskets)
  - [Crypto](#crypto)
- [Tick data vs. bar data](#tick-data-vs-bar-data)
  - [Enabling it](#enabling-it)
  - [The tape.* namespace](#the-tape-namespace)
- [Market Data](#market-data)
  - [What a bar contains (OHLCV)](#what-a-bar-contains-ohlcv)
  - [Price structure — what the market did before your strategy](#price-structure--what-the-market-did-before-your-strategy)
  - [Supported sources](#supported-sources)
  - [Data quality: what is checked when data is fetched](#data-quality-what-is-checked-when-data-is-fetched)
  - [Reading another symbol (request.security)](#reading-another-symbol-requestsecurity-do-not-mix-vendors)
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

For the trading side rather than the language, the **[Learn hub](https://pineconex.com/learn)** collects the books, talks and guides we recommend on systematic trading, backtesting and validation.

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

### Same-bar stop and target (the bar magnifier)

When one bar's range touches **both** a resting stop and a resting take-profit, the bar's four prices cannot say which one price reached first. The engine's default is to book the **take-profit** — optimistic, and it flatters every bracket strategy.

`strategy(use_bar_magnifier = true)` resolves those ties from finer data instead:

| Where | How a tie is resolved |
|-------|-----------------------|
| **Backtest** and **Sweep** | The engine walks the **Intrabar (LTF)** sub-bars inside the ambiguous bar and books whichever leg price actually reached first. A single sub-bar that touches both legs is itself ambiguous, so the **stop** wins there. If no sub-bar covers the bar, it falls back to the optimistic default rather than inventing a worse result from missing data. |
| **Significance** and **Stress** | The permutation null rebuilds every bar, so real sub-bars cannot apply. The tie is resolved from the recomposed bar's own OHLC with a driftless Brownian bridge — `P(low before high) = (high − open) / (high − low)` — booking the more likely leg first, with an exact 50/50 breaking to the stop. Deterministic on purpose: the only randomness stays the seeded shuffle, so the p-value remains reproducible. |

- **In a backtest or sweep the flag needs an intrabar series.** Without one it is a silent no-op (a warning appears in the log) — pick an **Intrabar TF** on the form, or set `ltf` in your [JSON5 params](#parameter-overrides-json5). Validation needs no series; it resolves ties from the bar itself.
- **It is opt-in and inert by default.** A strategy without the flag produces byte-identical results to before.
- **Expect the numbers to get worse when you switch it on** — that is the point. On real 15-minute sub-bars under a 1-hour chart, a bracket strategy moved from a 62% win rate and 1.70 profit factor to 55% and 1.28. Nothing was lost; the optimistic bias was removed.

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

> Sizing each order from the market's current volatility, instead of a fixed cash or equity fraction, is a separate feature: see [Regime-aware sizing (VMSC)](#regime-aware-sizing-vmsc).

#### Margin and leverage (`margin_long` / `margin_short`)

Both default to **100** — full cash cover, no leverage — exactly as Pine Script v6 does, and an entry that would need more money than the account has is **not opened**. So `default_qty_type = strategy.percent_of_equity, default_qty_value = 400` no longer quietly borrows four times your equity; it is capped at what you can actually pay for.

If you *want* leverage, say so: `strategy(..., margin_long = 25)` is 4× (25% of the position value must be covered). An explicit `margin_long = 0` also maps to 100 rather than to "unlimited" — reading a 0% requirement literally would mean infinite leverage, which is the most dangerous possible interpretation.

> **This changes historical backtest numbers.** A strategy that was implicitly over-leveraging now reports lower, realistic results, because the entries it could not afford are no longer taken. TradingView would not have taken them either — this is what makes a PineconeX backtest and a TradingView backtest of the same script agree.

> **Our margin limit is not your broker's.** It never goes over the wire — an order carries only a quantity, and your broker applies its own Reg T / maintenance rules independently. The two never talk, which is exactly why ours must not be looser than theirs. On a live bot, see [Margin monitoring](#margin-monitoring).

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
| **Intrabar TF** | Optional — the `request.security_lower_tf` (intrabar) series. Pre-fillable from the `ltf` key in your [JSON5 params](#parameter-overrides-json5). Also the series [`use_bar_magnifier`](#same-bar-stop-and-target-the-bar-magnifier) resolves same-bar stop/target ties from — without it, the flag does nothing. |
| **Date range** | Start and end date for the historical window. |
| **Data source** | Which feed the bars come from — Yahoo, Saxo, Alpaca, Bitstamp, Massive or IBKR. Only the sources that actually carry the selected symbol are offered. See [Supported sources](#supported-sources). |

### Results

Once the job completes, the results page shows:

- **Equity curve** — cumulative net profit over the backtest period.
- **Drawdown** — underwater equity plotted over time.
- **Trade list** — every entry and exit with date, price, P&L, and run-up / drawdown.
- **Metrics** — net profit, gross profit/loss, max drawdown, Sharpe ratio, win rate, profit factor, average trade, number of trades, and more.
- **Logs** — raw container output for debugging.
- **AI analysis** — optional one-click AI narrative summarising performance (requires a configured AI provider).

> The report used to carry a **Data** block (Hurst, variance ratio, price structure). It has moved
> to the Data page's [Structure tab](#price-structure--what-the-market-did-before-your-strategy),
> because it described the *price series* — so it was identical for every strategy ever run on that
> dataset, the same three numbers on every winner and every loser, sitting next to figures that
> really were the strategy's.

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
| **RBF Optimise** | Cubic RBF surrogate model. Fewest evaluations needed; smart interpolation between sample points. The only mode that *steers* — it hill-climbs the chosen objective. Based on [Costa & Nannicini, *RBFOpt* (2016)](https://arxiv.org/pdf/1605.00998.pdf). |
| **Grid** | Exhaustive 2-D grid over the two swept parameters. Best when you need to see the full landscape. |
| **Random** | Uniform random sampling across all swept parameters. Fast, unbiased exploration. |

### Objective

The steering mode (RBF Optimise) hill-climbs a single number — the **objective**. Grid and Random
don't steer, so they have no objective: they emit every trial and you rank the results afterwards
by any metric.

Built-in objectives: `net_pnl_pct` (default), `return_over_dd`, `sharpe`, `profit_factor`,
`expectancy`, `win_rate`, and `max_dd_pct` (minimised).

**Custom expression.** Pick *Custom expression…* to write your own objective as an arithmetic
formula over the trial metrics, for example:

```
net_pnl_pct - 0.5 * max_dd_pct + 0.1 * trades
```

- Variables: `net_pnl_pct`, `max_dd_pct`, `trades`, `win_rate`, `profit_factor`, `expectancy`,
  `sharpe`, `return_over_dd`. Operators: `+ - * / ( )` and numbers.
- The search **maximises** the expression as written — a penalty term gets a minus sign.
  `max_dd_pct` is a positive percentage (a 12% drawdown is `12`), so subtract it to punish risk.
- A trial below the **Min trades** floor can never win, custom objectives included — otherwise a
  config that barely trades can score arbitrarily well (a division by zero, e.g. a zero-drawdown
  fluke in `pnl / dd`, is also disqualified rather than winning by infinity).

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

Your strategy is then run against every one of those scrambled series. If it only made money because
it happened to catch real moves in the real order, it will fall apart on them. If it keeps making
money on scrambled prices, it was never reading the market — it was reading the return distribution,
which any rule can do.

The headline number is how often the scrambled series did **as well as or better than** the real
one. Two out of two hundred means your result is hard to get by luck. Ninety out of two hundred
means it is not.

| Field | Description |
|-------|-------------|
| **Permutations** | How many scrambled series to test against (default 200). More is finer-grained: with only 50, the best result you can possibly report is "1 in 51". |
| **Test statistic** | What counts as "doing well" — `Net P&L %` (default), `Return / drawdown`, `Sharpe`, `Profit factor`, `Expectancy`, `Win rate`, or a **custom expression** over the trial metrics (same syntax as the Sweep objective, e.g. `net_pnl_pct - 0.5 * max_dd_pct`). It is both the reported statistic and, for a searching procedure, the objective the search hill-climbs inside every permutation. |
| **Permutation type** | **Bar** scrambles every bar independently — the strictest test. **Block** shuffles chunks of N bars, keeping short-term patterns intact. Use Block if your edge is meant to play out over days rather than bars. |
| **Where the settings came from** | The most important control on the page. See below. |
| **Seed** | Leave empty for a random run. The seed used is reported back, so any run can be reproduced exactly. |

#### If you found your settings with a Sweep, say so

This is the one setting that can quietly invalidate the whole test.

**Fixed params** (the default) runs your strategy with the numbers written into the script, exactly
as they are, on every shuffled series. That is the right test *if you chose those numbers yourself*
— from theory, from a book, from experience.

It is the **wrong** test if you found them with a Sweep.

Here is why. A Sweep tries many combinations and hands you the best one. Try enough combinations on
*random* data and one of them will look good too — that is guaranteed, and the more you tried, the
better the winner looks. So a strategy whose settings came out of a Sweep starts with a head start
that has nothing to do with the market. Testing it as if you had picked those numbers by hand hides
that head start completely, and gives you a reassuring result you have not earned. Running more
shuffles does not help: the bias is in *how the settings were found*, not in how many times you test
them.

So tell it what you actually did. Pick the same search you ran — Grid, Random, or RBF —
and that entire search is repeated against every shuffled series. Now your strategy has to beat not
just noise, but *the best result anyone could squeeze out of noise by tuning just as hard as you
did*. That is a fair fight, and it is the only one worth winning.

Expect it to be **much slower**. Fixed params runs your strategy once per shuffle; any other option
re-runs your whole Sweep per shuffle. A test that took seconds can take tens of minutes — and the
bigger the Sweep you ran, the longer it takes, because the bigger the Sweep, the more of a head
start there is to cancel out.

#### Out-of-sample

There is no separate mode, because out-of-sample is a **date range**. Sweep the parameters on an
earlier slice of history, then run Significance on a later slice you held back — with the parameters
fixed. Those bars were never seen by the search, so **Fixed params is the right choice there**:
there was no search on that data to correct for.

> An intrabar timeframe is not allowed here. Scrambling the bars invents a price path that never
> happened, and there is no honest way to say where inside such a bar a stop or limit would have
> filled. Rather than give you a plausible-looking number built on a fiction, the test refuses to
> run. Drop the intrabar timeframe and try again.

### Stress — which market does the strategy need?

Instead of shuffling your real prices, Stress **invents new markets**. It measures two things about
your instrument — how strongly it snaps back after a move, and how often it gaps violently — then
simulates a whole grid of markets around those values: calmer and choppier, quieter and more
jump-prone. Your strategy is run over many simulated price paths in each one.

The result is a map of **where your strategy works**: which market conditions it needs, and how much
sudden gap risk it can absorb before it breaks. A strategy that only survives in one small corner of
that map is one to be careful with — real markets do not stay in a corner.

> **Stress cannot tell you whether your edge is real — only Significance can.** The markets it
> invents are built to snap back after a move, so a mean-reversion strategy will look good on them no
> matter what, and a trend-following one will look bad no matter what. Neither result means anything
> on its own.
>
> **Run Significance first.** If your strategy cannot beat scrambled prices, nothing Stress says
> matters. Once it has passed, Stress tells you which markets it needs in order to keep working.

---

## Machine Learning Models

You can train a model **offline** — in Python, on your own machine — and then call it from a
strategy with `ml.predict()`. The model runs inside the job container on every bar, the same way
in a backtest and in a live bot, so what you validate is exactly what you trade.

PineconeX does not train models for you and does not host a training environment. It runs the
finished model. The format is **ONNX**, the open standard that PyTorch, TensorFlow/Keras and
scikit-learn can all export to.

> **Machine learning models are a [Premium](#plans) feature.**

> **A model is not an edge.** Bolting a neural network onto six popular indicators does not create
> alpha — those features have been mined by everyone for decades, and a model fit to them usually
> learns nothing that survives out-of-sample. Treat ML as one more thing to **validate**, not as a
> shortcut past validation. The most reliable use is *meta-labelling*: let a model filter the trades
> of a strategy that already passed [Significance](#significance--is-the-edge-real-or-luck), rather
> than asking it to find trades from scratch.

### Uploading a model

Go to the **Models** page, choose an `.onnx` file and give it a name. Names may contain letters,
digits, `.`, `_` and `-`. Re-uploading the same name creates a **new version** (`v2`, `v3`, …); the
old versions stay available so a strategy pinned to one keeps working.

- Maximum size is **20 MB**. Real trading models — boosted-tree-sized or a small neural net — are a
  few KB to a few MB; only very deep forests or sequence models approach the cap.
- On upload the file is checked to be a valid ONNX graph, and its input width (number of features)
  is read from it. A file that is not ONNX, or is too large, is rejected with a message.
- Machine learning models are a **Premium** feature (see [Plans](#plans)); on Premium you may store
  any number of them.

### Calling a model from Pine

Declare the model at the top of the strategy with a `//@model=` line, then call it. The model
receives an **array of features** and returns a number:

```pine
//@version=6
//@model=my-model            // latest version — or my-model:3 to pin one

strategy("ML example")

f1 = ta.rsi(close, 14) / 100
f2 = (close - ta.sma(close, 50)) / ta.stdev(close, 50)
f3 = ta.atr(14) / close

score = ml.predict("my-model", array.from(f1, f2, f3))

if not na(score) and score > 0.6 and strategy.position_size == 0
    strategy.entry("L", strategy.long)
if not na(score) and score < 0.4
    strategy.close("L")
```

- `ml.predict(name, features)` returns the first output of the model as a single number (a
  regressor's prediction, or a probability). `ml.predict_all(name, features)` returns the **whole
  output vector** as an array — use it for multi-class or multi-horizon models.
- **`na` in, `na` out.** If any feature is `na` — which it will be during the warm-up bars while
  `ta.*` fills its history — the model is not run and the result is `na`. Guard every use with
  `not na(...)` as above, so a warm-up bar can never place an order.
- The number of features you pass **must** match what the model was trained on, or the strategy
  stops with a clear error. That is deliberate — a size mismatch is a silent-disaster bug in every
  other ML setup.
- A `//@model=` for a model you have not uploaded is caught when you validate the strategy, before
  any job runs.

### Three ways to use a model

The array you pass and the number you get back are just data — how you *use* the number is the
strategy design. The three common shapes:

- **Direction** — the model predicts up/down and you trade its call. The hardest to make work; this
  is asking the model to *be* the edge.
- **Filter (meta-labelling)** — you already have entry rules; the model scores each candidate setup
  and you only take the ones it rates highly. This keeps the edge you have and drops the trades most
  likely to fail. The most productive of the three.
- **Trigger / sizing** — the model's output shifts a threshold or the position size rather than
  making the yes/no call itself.

### Getting the features right — the one thing that breaks silently

A model is only as good as the promise that **the features at training time are identical to the
features at prediction time**. `ta.rsi` re-implemented in pandas is *not* the same series as
`ta.rsi` in the interpreter — the warm-up, the smoothing and the rounding all differ — and a model
trained on the wrong numbers will look fine and trade badly.

The safe way is to let PineconeX produce your training data, so it comes from the same engine that
will run the model:

1. Write a throwaway strategy that computes your features and prints them once per bar with
   [`log.info()`](#debugging-with-loginfo):

   ```pine
   //@version=6
   strategy("feature dump")
   f1 = ta.rsi(close, 14) / 100
   f2 = (close - ta.sma(close, 50)) / ta.stdev(close, 50)
   f3 = ta.atr(14) / close
   log.info(str.tostring(f1) + "," + str.tostring(f2) + "," + str.tostring(f3) + "," + str.tostring(close))
   ```
2. Run it as a normal [backtest](#backtest) over the history you want, then download the job log —
   each line is one bar's features.
3. Train offline on that file, build your labels there (labels look into the future, so they must
   never be computed on-platform), and export the model to ONNX.
4. Upload, and use the **exact same feature expressions** in the real strategy.

### What ONNX exports work

Inference uses a self-contained CPU engine, which supports the **core ONNX maths operators**
(matrix multiply, add, the common activations) — everything a linear model or a neural network
needs. It does **not** support the specialised `ai.onnx.ml` operators, and this catches people out:

- **scikit-learn decision trees, random forests and gradient boosting** export to a
  `TreeEnsemble` operator that is **not** supported and will be rejected at run time.
- A scikit-learn **`Pipeline` with a `StandardScaler`** exports a `Scaler` operator that is also not
  supported.

Export models built from core maths instead: linear / logistic regression, an **MLP**
(`sklearn.neural_network`, or PyTorch/Keras), or trees converted to a plain tensor graph (e.g. with
[Hummingbird](https://github.com/microsoft/hummingbird)). If you need feature standardisation, fold
the mean/scale into the graph as ordinary subtract/divide steps rather than a `StandardScaler`
pipeline stage, and export the classifier **without** the ZipMap step
(`options={"zipmap": False}` in `skl2onnx`) so it returns a plain array.

> **Determinism.** The same model file and the same bars always produce the same prediction, in a
> backtest and in a live bot alike. There is no GPU and no randomness at prediction time — that is a
> feature, not a limitation, because it is what makes a backtest trustworthy.

### Training a regime model on the platform (HMM)

Everything above assumes you trained a model elsewhere and uploaded it. There is one model the
platform will fit **for** you, on the **Train ONNX** tab of the Models page: a **Gaussian hidden
Markov model** of the instrument's volatility regimes.

It is a **Gaussian hidden Markov model**, fitted by **Baum-Welch (expectation-maximisation)** —
the states are Gaussians over your chosen features, and the fit estimates their means, variances
and the probabilities of moving between them, all at once. Emissions are diagonal, meaning features
are treated as independent given the state, so pick features that are close to orthogonal rather
than two measures of the same thing. The fit is deterministic: the same inputs give a byte-identical
model.

It learns, unsupervised, that a market alternates between a quiet state and a turbulent one — how
far apart those states are, how long each tends to last, and how likely a switch is on any given
bar. You never label anything, which is the point: nobody can honestly label which historical bars
were "calm", and labelling them by what happened next is lookahead.

Pick the instrument, a timeframe, and **two date windows**. The model is fitted on the training
window only and then scored on the test window with its parameters frozen. The windows may not
overlap and there is no single-window form — fitting and scoring on the same bars makes any regime
model look excellent while telling you nothing, so it is refused rather than allowed and warned
about. When the job finishes the model appears in your registry like any uploaded one, versioned
the same way.

**How it is used is unusual, and worth understanding before you write the Pine.** The model is
stateless: it scores *one bar* and returns how typical that bar is under each regime. Those are
not probabilities and do not sum to 1. Which regime you are actually *in* depends on the whole
history, so that part is computed in your strategy, one line of Bayes per bar:

```
belief_now = normalise( (belief_yesterday × transitions) × today's_evidence )
```

The result **is** a probability vector — `0.15` really does mean "15% chance we are in that state
right now". The model carries its own transition matrix and emission means in its output, so you
never copy numbers out of the results into your script; a refit is a version bump and nothing else.

Two ready-made strategies in `templates/hmm/` implement the recursion for you:

- **`hmm_regime_gate.pine`** — take entries only in the regime you choose. Exits are never gated:
  a regime flip must not leave you holding a position with the exit rule switched off.
- **`hmm_position_sizing.pine`** — take every entry, but size it against the volatility you expect
  next. The model's emission means give a genuine forward volatility estimate, so this is real
  volatility targeting rather than "scale the position by a probability", which has no units.
- **`hmm_vmsc_basket_regime.pine`** — advanced. Regimes of a whole **basket** rather than one
  instrument, by training on [VMSC](#regime-aware-sizing-vmsc) instead of a price series (set
  `features: "vmsc"` and pass a `universe` instead of a symbol). A state is then a property of the
  market: "dispersed, many independent opportunities" versus "one position wearing twelve tickers",
  the state in which a basket strategy's assumed diversification quietly stops existing. It also
  replaces the thing everyone writes by hand — `v > 0.30 and msc < 0.35`, two numbers you guessed,
  flickering day to day — with fitted, persistent states and a probability you can size on.

**Which regime to trade in is not obvious, and the intuitive answer is often wrong.** "Only trade
when the market is calm" sounds like risk management. Measured on the S&P 500 daily, on a
mean-reversion strategy, it turned +7.8% into −4.0%, while trading *only in the turbulent regime*
gave +14.3% on a third of the drawdown. Mean reversion needs volatility to revert from; in a calm
grind upward a sharp dip is a real change of direction, not noise to be bought. Test both
directions, and then run [Significance](#significance--is-the-edge-real-or-luck) — picking the
better of two directions on one instrument is selection, not evidence.

**When to retrain.** Less often than you would think. The bar-by-bar belief update already tracks
regime changes; retraining is only for when the regimes themselves drift. The job reports the
average log-likelihood on both windows — if the test figure later falls well below what the fit
achieved, the market no longer looks like anything the model knows, and *that* is the signal to
refit. A calendar is not.

### The discipline

The model changes nothing about how you decide whether a strategy is worth trading:

1. **Backtest** it, out-of-sample — train on an earlier slice, test on a later slice the model has
   never seen.
2. Run **[Significance](#significance--is-the-edge-real-or-luck)** on the held-out slice. A model
   adds parameters and parameters overfit, so this matters *more* with ML, not less. If the filtered
   strategy cannot beat scrambled prices, the model found a pattern in noise.
3. Only then consider it for **[live](#live-trading)** — and paper-trade it first, like any strategy.

A live bot always runs the platform's promoted engine version, so a model reaches live trading the
same way any engine feature does.

---

## Gamma Exposure (GEX)

**Gamma Exposure (GEX)** measures where options market-makers ("dealers") have to hedge, which tells
you where their hedging **pins** the underlying (suppresses moves) or **accelerates** it. PineconeX
computes GEX from the live options chain (open interest × gamma across every strike) and exposes it
to your strategy as a `gex.*` namespace — the same way `ml.*` exposes a model. There is no
TradingView equivalent.

### The levels

Each field is an ordinary `series float` you read like `close`:

| Field | Meaning |
|---|---|
| `gex.net` | net dealer gamma. **Sign is the regime**: `> 0` = pinning / mean-reverting; `< 0` = trending / accelerating |
| `gex.flip` | the zero-gamma price — the pivot between those two regimes |
| `gex.pin` | the max-gamma strike — the price **magnet** that price gravitates to in a positive-gamma regime |
| `gex.call_wall` / `gex.put_wall` | the strongest resistance (above) and support (below) strikes; `…v` variants give their magnitude |
| `gex.g1…g5` / `gex.g1v…g5v` | the five heaviest gamma strikes (price + signed magnitude: `+` call, `−` put) |

You read these levels in Pine like any `series float` (pin `//@runtime=2026.08.06-gex` or newer). The
usual approach: tag the regime from `gex.net`'s sign and spot vs `gex.flip`, then use the walls and
`gex.pin` as levels — fade toward them in positive gamma, chase breakouts in negative. GEX is a
leading indicator of the *volatility regime*, best combined with price action rather than used as a
signal on its own.

### Availability — read this before you build on it

GEX needs live options data, and that shapes where it works:

- **Live trading on Saxo** works today: the bot fetches the Saxo options chain (European / Eurex
  underlyings) each bar and injects real dealer gamma. Pin `//@runtime=2026.08.06-gex` or newer.
- **Backtesting a GEX strategy currently trades nothing.** Historical options chains aren't retained,
  so `gex.*` reads `na` on past bars and the strategy safely no-ops. GEX strategies are **validated
  and paper-traded live**, not backtested, until a historical options data source is added.
- When `gex.*` is `na` (no data / warmup / unsupported symbol), non-finite levels are filtered out of
  order prices, so the strategy simply does nothing rather than trading on a bad level.

GEX is **data you wire into your own strategy** — PineconeX never pushes gamma levels to you as
buy/sell recommendations.

---

## Regime-aware sizing (VMSC)

**VMSC** measures the *market regime* of a basket of symbols you name, and hands it to your strategy
as a daily reading through a `vmsc.*` namespace. It answers two questions a single symbol's chart
cannot:

- **V**, how much the basket's members move **individually** (the cross-sectional mean of per-name
  annualised realised volatility).
- **MSC**, how much of that movement is the **same** movement (mean squared pairwise correlation over
  the basket, `0` = independent, `1` = effectively one position).

The distinction is the point. High V with low MSC is many independent opportunities; high MSC is one
position wearing twelve tickers, quietly leveraged. Volatility is opportunity *and* risk, so you
select for it and then size against it. Correlation is only ever risk, so it can only ever shrink a
position. There is no TradingView equivalent, so a script using `vmsc.*` runs on PineconeX only.

### Reading it in Pine

```pine
//@version=6
//@runtime=2026.07.29-vmsc

// The basket the regime is measured over. This exact statement is what names the universe.
group = array.from(
     "NASDAQ:NVDA", "NASDAQ:AMD", "NASDAQ:INTC", "NASDAQ:ON", "NASDAQ:NXPI", "NASDAQ:LSCC",
     "NASDAQ:TSEM", "NASDAQ:AOSL", "NASDAQ:INDI", "NASDAQ:NVTS", "NYSE:STM", "NYSE:MX")

[v, msc, score] = vmsc.calculate(group)
```

| Value | Meaning |
|---|---|
| `v` | cross-sectional mean of per-name annualised volatility (`0.35` = 35% a year) |
| `msc` | mean squared pairwise correlation over the basket, bias-corrected, in `[0, 1]` |
| `score` | `v / max(msc, 0.05)`. The floor keeps the ratio finite in a decorrelated market, which is where the estimate is weakest |

All three are ordinary `series float`s: index them (`msc[1]`), window them with `ta.*`, plot them.

**The argument to `vmsc.calculate()` is the universe.** PineconeX reads the array at the call site
before the run, resolves each ticker, and precomputes the series, so the declaration has to be
readable without executing the script:

- assign it at **global scope, starting at the left margin** (not inside an `if`, a `for`, or a
  function);
- use a literal `array.from("EXCHANGE:TICKER", ...)` of quoted strings, not `array.push` and not a
  computed list;
- at least **3 symbols** (a mean squared *pairwise* correlation needs more than one pair);
- every constituent needs **daily (1D) history** already fetched on the platform.

Break any of those and the job is **rejected at launch with the reason**, rather than started with
readings that are silently `na`. The engine re-checks the basket on the first bar and hard-errors if
it does not match what was precomputed, so the script and the data can never drift apart.

> **Guard the readings with `nz()`.** Where a reading is unavailable (warmup, the validator, a live
> bot) it is `na`, and an `na` quantity does not cancel an order in Pine, it falls back to
> `default_qty_value`. Sizing a position from an unguarded `na` trades the default size while looking
> regime-aware. The reference template sets `default_qty_value = 0` as a tripwire for exactly this.

### How the series behaves

- **Daily, and lagged one day.** A reading stamped for date *D* is computed from returns through
  *D*'s close, so it becomes visible on *D+1*. An intraday strategy reads the most recent daily
  value, held flat through the session. No lookahead.
- **The lookback is 60 trading days**, fixed and not configurable. Measurement showed the knob does
  not earn its place (mean MSC over a semiconductor basket is 0.217 at 60 days and 0.216 at 120),
  while a window under about 20 days turns the correlation estimate into a readout of the window
  length rather than of the market.
- **Membership is per-date.** A constituent contributes on the dates where it has a full window, so a
  2021 listing does not erase everyone else's 2015 history.
- **Corporate-action cliffs are dropped, not averaged.** A single unadjusted split in one member
  would otherwise inflate V and distort that name's every correlation for a whole window.
- **Computed once per basket, then cached and shared.** The first job naming a new basket pulls each
  member's daily history and is slower to start; every later job reading the same basket is instant.
  Changing the membership is automatically a different basket, never an edit to the old series.

### Where it works

| Job type | VMSC |
|---|---|
| Backtest, sweep, significance, stress | Full support |
| **Live bots** | **Not delivered yet.** The readings are `na`, so an `nz()`-guarded strategy sizes neutrally and trades its base size |

That live gap matters if you built the sizing rule and then deploy it: the bot will trade, and it
will trade *flat-sized*. Until it is wired, treat VMSC as a backtest and research feature.

### What it is actually good for

The proven use is **volatility targeting**: divide the position by the symbol's own volatility so a
calm month and a panicked month risk the same amount of money. Measured across three baskets (88
names, 4,051 trades, one account per name, identical entry and exit signals in every run, so only the
order size differed):

| Basket | Names | Trades | Drawdown | Average size |
|---|---|---|---|---|
| US semiconductors | 12 | 257 | 19.6% → 10.6% (−46%) | 0.68× |
| DAX | 36 | 1,777 | 21.2% → 18.4% (−13%) | 0.95× |
| CAC 40 | 40 | 2,017 | 23.4% → 21.2% (−10%) | 1.00× |

CAC 40 is the cleanest case, because there is nothing to trade off: the same average position size,
the same return (2.10% vs 2.07%), and a tenth of the drawdown simply gone. Drawdown improved on 27 of
those 40 names individually, which is well above chance.

Three things to know before you copy it:

1. **Judge it on drawdown, never on raw profit.** A rule that trades smaller can always be made to
   look bad on net return, because trading smaller is *how it works*. On the semiconductor basket the
   volatility-targeted run earned less in absolute terms and more per unit of risk; re-levered to the
   control's drawdown it returns roughly 28% more at the same risk.
2. **Keep the base size well under 1× the account.** At 1× the account is already fully invested, so
   the multiplier can only ever shrink a position and never grow one, and the rule quietly stops
   working while reporting perfectly normal numbers. The reference template uses 0.4×.
3. **Size *down* into volatility, not up.** The opposite sign was tested and lost: it put more size on
   the trades that turned out wildest. Volatility being the source of profit is an argument for
   *choosing* volatile markets, not for buying more shares of one.

**`msc` is a gauge, not yet a sizing input.** The risk of N positions scales with
`sqrt(N × [1 + (N−1) × correlation])`, so at N = 1, one symbol in one account, the correlation term is
exactly 1 and drops out at any strength. Sizing on `msc` there shrinks positions for no reason. Read
it instead as a warning light: a high `msc` means the basket has collapsed into a single bet and your
diversification is imaginary. It becomes a real sizing input once several symbols share one account.

The **Reference: risk-adjusted position sizing** template in the strategy picker is a complete,
commented working example (40 CAC 40 names, SuperTrend signal, a response knob you can set to 0 to
reproduce the control run).

---

## Live Trading

Deploy a strategy as a live bot that connects to a broker and executes orders in real time.

> **Available on every plan.** The Free plan includes **1 live trading job** with a limited lifetime (bots are stopped at the end of the trading day); Pro and Premium raise the concurrency limit and run without that daily stop.

### Launching a bot

1. Go to **Live** and connect a broker (see [Brokers](#brokers)).
2. Select a strategy and symbol — or tick **Basket** to trade several symbols with one bot (see [Multi-symbol baskets](#multi-symbol-baskets)).
3. Choose the timeframe (`5m`, `15m`, `30m`, `60m`, `90m`, `1D` — see [Timeframe syntax](#timeframe-syntax)).
4. Enable **Auto-restart** if you want the bot to restart automatically after a crash.
5. Check the **Execution routing** card below the form — it decides where the orders actually go (see [Execution routing](#execution-routing)).
6. Click **Launch**.

### Monitoring

Running bots are listed with their status (`running`, `stopped`, `failed`). Click **Logs** on any bot to stream its container output in real time. Bot lifecycle events (started, stopped, crashed, restarted) are recorded in the event log and can be exported as CSV.

If Telegram notifications are configured, each bot also sends a periodic **heartbeat**. A multi-symbol basket sends a single combined overview — one message with a per-symbol table (price, position, live P&L) and a net-P&L summary, colored green/red by profit and loss:

![Telegram heartbeat overview for a multi-symbol basket](images/telegram-heartbeat.png)

### Auto-restart

When auto-restart is on, the platform will restart the bot automatically if it crashes, up to a configured limit. The restart count is shown on the bot card.

### Performance

**Live → Performance** compares your running bots against each other. It is realized only: a trade
enters the figures when it closes at a price the broker gave us, and not before. Open positions
have no result yet and live on their own page.

Every figure is a **ratio**, never an absolute amount, because absolute figures are not comparable
between bots. A round trip is scored as `(exit − entry) / entry` — a price return — so a €500
account and a €500,000 account running the same strategy on the same instrument produce the same
number, and bots on different brokers, currencies and timeframes can be ranked side by side.

| Column | What it tells you |
|---|---|
| **Avg / trade**, **Median** | The edge per trade. A large gap between them means one outlier is carrying the average — common at small sample sizes. |
| **Sharpe** | Reward per unit of risk (mean ÷ standard deviation of the trade returns). The closest single number to "better". |
| **SQN** | The same ratio scaled by how much evidence backs it, so a bot with two lucky trades cannot top the ranking. The table sorts on this by default. |
| **Exposure**, **% / mkt-day** | How hard the capital worked rather than sat idle. Two bots at the same return per trade are not equivalent if one is in the market 10% of the time and the other 90%. |
| **Share** | What fraction of the position size deployed on *that account* this bot is getting. |
| **Max DD**, **Max L** | Worst fall of the cumulative trade-return series, and the longest losing run. |

Every column sorts (click again to reverse) and every column filters — `contains` on the text
columns, `min`/`max` on the numbers. A row near the top on SQN and near the bottom on Share is a
strategy earning well on less of the money than its peers. **The page shows that and stops there;
it does not tell you what to do about it.**

> **Two things these numbers are not.** They are **gross** — commissions and broker fees are not
> included, so they are not comparable with your backtests, which run a 0.2% commission; a strategy
> with a real but sub-fee edge looks fine here and is not. And they are **strategy performance, not
> account performance**: every figure comes from what the bot itself did, so trades you placed by
> hand in the same account, fills that landed after a bot stopped, and broker liquidations are not
> in them. Your broker account remains the source of truth for money.

Sharpe is deliberately **not annualised**: scaling it by trades-per-year needs a rate a two-day-old
bot does not have and assumes trades are independent, which they are not. Read it as reward per
unit of risk, per trade.

Bars under about ten closed trades are flagged: a ranking built on two trades is luck, not edge,
and the Trades column's `min` filter is the first one to reach for.

### How orders are executed

It is important to understand how a live bot turns a strategy signal into a broker order:

- **Bots act on bar close.** On each new completed bar, the bot evaluates your strategy. A plain `strategy.entry` becomes a **market order** at that moment.
- **`limit=` and `stop=` become real broker orders.** `strategy.entry(limit=…)` places an actual resting limit order at your broker — it may fill later, or never. And `strategy.exit(limit=…, stop=…)` places a native **OCO** pair on Saxo and Alpaca equities: a resting stop and a resting take-profit, linked by the broker so that whichever one fills cancels the other. The stop moves as your strategy trails it.
- **The entry price is the broker's real fill, not the bar close.** The bot reads the executed price back from the broker (Saxo, Alpaca, Bitstamp), so `strategy.position_avg_price` — and any stop or target computed from it — is based on what you actually paid, not on a bar close that is already minutes stale.
- **Every order carries a reference back to the bot that placed it.** Orders are tagged
  `pcx-<strategy>-<job>-…` in your broker's own order history (Alpaca and Bitstamp `client_order_id`,
  Saxo `ExternalReference`), so a trade in your broker's report can be traced to a specific bot
  rather than guessed at from the symbol and the time — which is ambiguous as soon as two bots on
  one account trade the same instrument.
- **PineconeX does not track your live profit & loss.** It records lifecycle events (started, stopped, crashed) and the signals it acted on, but it does not reconcile partial fills or rejections into a running P&L. **Your broker account is the source of truth** for real positions, fills, and P&L — always confirm there.

> Live results can still differ from a backtest on identical signals: a backtest fills at modelled prices at the bar close, while a live order fills at whatever the market gives you — and a live resting stop can be hit *inside* a bar, where a backtest would only have seen the bar's close. The divergence is by design: live is native, backtest is simulated.

> **Stopping a live bot cancels its resting orders — it does not close the position.** On shutdown the bot cancels the entry and exit orders it left at the broker (a resting order with no bot behind it is a hazard: a stop-loss is a sell, and a sell with nothing behind it can *open a short*). What it holds is yours, so it is left alone and named in the log as unprotected. **Close the position yourself in your broker's interface** if you do not intend to relaunch — a relaunched bot re-adopts the position and re-protects it. (On Bitstamp nothing rests at the exchange in the first place — see [Crypto](#crypto).)

### Execution routing

The **Execution routing** card on the launch form decides where a signal ends up. There are three routes, and they combine:

| Route | What it does |
|-------|--------------|
| **Execute orders on the broker** | The default. PineconeX places the order on your connected broker account. Unchecking it makes the bot **signal-only**: it evaluates the strategy, fires the webhook, and sends nothing to your broker. |
| **Webhook URL** | Order events are POSTed to your own `http(s)` endpoint — the strategy's `alert_message` when it has one, a structured event otherwise. Mainly to hand execution to a third-party platform, but usable for plain notifications. Delivery only ever goes to the address you enter. |
| **Options routing** | Alpaca only. Each signal is scored across the shares and the option chain, and the better expression is placed. See below. |

> If a third-party platform executes off your webhook, **it owns the real position**. PineconeX then only tracks its own simulated one, which can drift from your actual account.

### Options routing (Alpaca)

Tick **Let the model choose shares, calls or puts per signal** and each signal is scored by a pricing model across the underlying shares and the option chain — a long can be expressed by buying shares or calls, a short by buying puts — and whichever gives the better risk-adjusted outcome is placed. A long option's premium is a hard maximum loss; a stop is not, because a gap can trade straight through it.

> **It is a fit question, not a feature toggle.** Options routing suits fast, directional strategies — momentum, breakouts, catalysts. On a slow or mean-reverting strategy the option decays while it waits for an exit signal and can expire worthless, losing the premium where the shares would have sat roughly flat. If the edge is not a near-term move, use shares.

Each bot carries its own settings; leave a field blank to use the runtime default shown as the placeholder:

| Setting | Meaning |
|---------|---------|
| **Capital ($)** | Cash the model may deploy per signal. |
| **Risk fraction (0–1)** | Fraction of that capital allowed to be lost on the stop — this is what sizes the position. |
| **Horizon (days)** | How long you expect to hold. Drives which expiry wins the scoring. |
| **Min DTE / Max DTE** | The expiry window the chain search considers, in days to expiry. Min DTE is floored at 1, so same-day (0DTE) contracts are unreachable from the product. |
| **Auto-roll before expiry** | On by default. A held option is rolled to a later expiry before it decays to nothing — the chain is re-scored exactly as the entry was, the near leg is closed and the further one opened. Your strategy reasons in the underlying's price and is blind to expiry, so without this a sideways market with no exit signal can let a position expire out from under it. |
| **Allow short** | Open a short expression when a sell signal arrives with nothing held. |
| **Dry run** | Score and log the decision, place nothing. The safe way to watch the model on a live feed. |

### Multi-symbol baskets

**Pro plan and above.** Tick **Basket** on the launch form to have a *single* bot trade several symbols in one process, over one shared timeframe and one broker account, instead of launching one bot per symbol. It counts as one job against your concurrency limit.

- **One combined heartbeat.** A basket sends a single Telegram overview — a per-symbol table (price, position, live P&L) plus a net summary — rather than one message per symbol.
- **One position per symbol**, evaluated at the same bar close across the basket.
- **Saxo, Alpaca and Bitstamp only.** Interactive Brokers and Lightspeed do not fit a shared connection, and a prop-firm futures basket would be a basket of contract months with its own roll for each — single symbol only there.

> Launching one bot per symbol remains the more controllable option: each has its own log, its own position and its own stop button, so you can shut one symbol down without touching the rest.

### Margin monitoring

A live bot checks the account's margin usage every 5 minutes on every broker that can lend — Saxo, Alpaca and prop-firm futures — and reports it in the log, so a margin call is visible before it acts on you. Bitstamp spot cannot borrow at all, so no margin call is possible there.

Margin is consumed by **borrowing**, not by holding: a cash-funded long uses none, and a bot on such an account simply logs *"no leverage in use"*. A blocked or restricted account is reported as such rather than as a healthy 0%. Note this is your broker's limit — the strategy's own cap is [`margin_long` / `margin_short`](#margin-and-leverage-margin_long--margin_short), and the two are enforced independently.

### Crypto

Crypto trades on **Bitstamp** (USD and EUR spot pairs) and **Alpaca** (US-dollar pairs). Pick the symbol under the **Crypto (USD)** or **Crypto (EUR)** index — the symbol list shows which venues carry it.

Your Pine Script does not change. What the *broker* does underneath changes a great deal, and the single most important difference is **what actually protects your position**:

| Venue | Stop-loss | Take-profit |
|-------|-----------|-------------|
| **Saxo** / **Alpaca equities** | Native, resting at the broker | Native, resting at the broker (OCO — a fill on one cancels the other) |
| **Alpaca crypto** | Native, resting at the broker | **Managed by the bot** — crypto allows only *one* resting exit, and that slot is given to the stop. The bot checks the target at each bar close and, when hit, cancels the stop and closes at market. |
| **Bitstamp** | **Managed by the bot** — Bitstamp spot has **no stop order at all** | Managed by the bot |

> **A Bitstamp stop-loss is not held at the exchange.** Bitstamp's spot market has no stop orders, no take-profits and no OCO — the API even *accepts* a stop price and answers `200 OK` with an order id, while creating nothing. So PineconeX never claims one: on Bitstamp, your stop is enforced **by the bot, at bar close**. If price gaps straight through your stop level between two bars, the bot exits on the next bar close, at whatever the market is then — not at your stop price. On a 24/7 market that gap is a real risk. Size accordingly, and prefer a shorter timeframe if the stop matters to you.

Other crypto specifics worth knowing:

- **Crypto never closes.** There is no session, no end-of-day. A bot on a 5m crypto chart runs through the night and the weekend.
- **Size is fractional.** Unlike equities, crypto orders are not rounded down to whole units — `0.0134` BTC is a valid order.
- **Fees land in different places.** On Alpaca the fee is taken **in the coin** (order 0.001 BTC, own slightly less); on Bitstamp it is taken **in the cash** (order 0.0002 BTC, receive exactly 0.0002 BTC). The bot sizes its exits from what the broker says you actually hold, so this does not strand dust — but it explains why the filled quantity may not equal the ordered one on Alpaca.
- **Neither venue allows shorting crypto.** A short entry is refused.

---

## Tick data vs. bar data

Everything else in PineconeX works on **bars**. A bar is the smallest unit of time the engine knows
about: your strategy runs once, at the close of each completed bar, and sees the five OHLCV numbers
that summarise it (see [What a bar contains](#what-a-bar-contains-ohlcv)). Everything that happened
*inside* that bar — the individual trades, the bid/ask spread, whether the high came before the low
— is gone by the time your script runs.

**Tick data is the layer underneath.** A tick is a single event on the wire: one trade printed, or
one change at the top of the order book. On a liquid US stock that is roughly 45 events per second,
peaking above 240 — thousands of ticks compressed into the four prices of a single 5-minute bar.

PineconeX can run a strategy on that layer instead, in a **live bot only**, through two pieces that
work together:

| | What it does |
|---|---|
| `calc_on_every_tick=true` | Re-runs your whole script on every real-time tick, against the still-forming bar, instead of once at bar close. |
| `tape.*` | A namespace giving the script **read access to the tick itself** — last trade price and the top-of-book quote. |

> **This goes beyond TradingView, and is not portable.** TradingView's `calc_on_every_tick` re-runs
> a script per tick but exposes no tick-level data — the script still only sees the forming bar's
> OHLC. `tape.*` is a PineconeX-exclusive namespace, like [`ml.*`](#machine-learning-models) and
> [`gex.*`](#gamma-exposure-gex). A script using it will not run on TradingView.

> **Preview feature.** The tick engine ships only on runtimes that include it — pin one with a
> `//@runtime=` line at the top of the strategy, as [GEX](#gamma-exposure-gex) does, or ask support
> which default runtime carries it. Today
> the tick path is **observation-first**: `tape.*` and the signals it produces are evaluated and
> logged on every tick, while order placement stays on the bar-close path unless intrabar ordering
> is enabled for your bot (see [What actually gets ordered](#what-actually-gets-ordered)).

### Enabling it

There is nothing to switch on in the interface. It is declared in the strategy itself, as an
argument to `strategy()`:

```pine
//@version=6
strategy("order flow", overlay=true, calc_on_every_tick=true)
```

That is the whole switch. When a bot launches, it checks each strategy in its basket for the flag,
and attaches a real-time feed only if at least one asks for it. A strategy without the flag behaves
exactly as before — one evaluation per completed bar.

**Backtests, sweeps and validation ignore it completely.** There is no tick history to replay: the
catalog stores bars, not ticks. In a backtest, a sweep, a significance or stress run — and in the
inline validator — every `tape.*` field reads `na`, so a tick strategy shows *no trades at all*.
This is deliberate and safe (a missing tick can never produce a garbage price level), but it means
**a `tape.*` strategy cannot be backtested**. You cannot validate its edge the normal way; treat
anything you build here as unproven until you have watched it on a paper account.

### Which feeds carry ticks

Tick data comes from a broker's streaming socket, not from the data catalog, so it depends entirely
on the data source your bot is running:

| Source | Tick feed | Notes |
|---|---|---|
| **Alpaca** (US equities) | Yes — real-time | The free **IEX** tape by default (a few percent of consolidated volume). The paid consolidated **SIP** tape is an operator setting. |
| **Alpaca** (crypto) | Yes — real-time | 24/7, so a tick strategy can be observed outside market hours. |
| **Bitstamp** (crypto) | Yes — real-time | Public feed, no API key needed: live trades **and** the top of the order book, 24/7. |
| **Saxo Bank** | Yes, but **delayed** | Quote-only and typically ~20 minutes behind without a real-time market-data subscription. **Observe-only** — see below. |
| **Yahoo**, **Massive**, **Interactive Brokers** | No | No tick path. `calc_on_every_tick` is accepted and simply never fires. |

If a strategy asks for ticks on a source that has none, the bot says so in its log and carries on
at bar close — it does not fail to start.

> **Alpaca allows one market-data connection per account** — so only **one tick-streaming bot per
> Alpaca account** can have the tape at a time. A second one is refused the stream (it backs off and
> keeps retrying, because it is the *other* bot that would have to stop). It still trades normally:
> orders and bar polling go over REST, so only `tape.*` is affected. Bots that do not set
> `calc_on_every_tick` never take the connection.

### The `tape.*` namespace

Every field is a `series float`, and every one is `na` until a tick supplies it:

| Field | Meaning |
|---|---|
| `tape.price` | Price of the last trade on this tick. |
| `tape.bid` / `tape.ask` | Top-of-book quote — the best bid and best offer. |
| `tape.bid_size` / `tape.ask_size` | Size resting at the top of the book (order-book imbalance). |

`na` is the safe default everywhere: in a backtest, before the first tick arrives, during warmup,
and on a partial tick. Many feeds send trades and quotes as *separate* events, so a trade-only tick
leaves `tape.bid`/`tape.ask` at `na` and a quote-only tick leaves `tape.price` at `na`. **Guard
every read** — `not na(tape.price)` — exactly as the smoke strategy below does. Non-finite values
are filtered out of orders and stops downstream, so an unguarded strategy does nothing rather than
firing at a nonsense price, but the guard is what makes the logic explicit.

**There is no tick lookback.** `tape.price[1]` reads `na` — the engine keeps no per-tick history, so
each re-run sees only the current tick plus the committed bar history. Anything comparing this tick
to the last one has to derive it from bar state.

> **Saxo's tape is not a trade tape.** A Saxo price subscription streams Bid/Ask/Mid — there are no
> trade prints — so `tape.price` is the **mid**, which by construction always sits *inside* the
> book. Any signal of the form "the trade lifted the offer" (`price >= ask`) is unsatisfiable on
> Saxo. The streamed quote also omits size, so `tape.bid_size` / `tape.ask_size` are unusable there.
> Combined with the delay, Saxo's tick path is for **observation only** — never let a stale quote
> drive an order.

### How often your script actually re-runs

Not on every tick. A liquid symbol can push hundreds of events per second, and re-running a whole
strategy that often would simply fall behind. Instead the bot **coalesces**: every arriving tick is
merged into a per-symbol accumulator (cheap — it just overwrites the latest trade and quote), and
the script re-runs once on the freshest merged state, no more often than that symbol's own cadence.

That cadence is **derived from your strategy**, not configured. At warmup the bot times 200 real
re-runs of your script and spaces re-runs at 4× the measured cost, clamped between **5 ms and 1 s**.
A cheap strategy therefore re-runs at close to tick speed; a deep-history one spreads out. The bot
prints the measured figure when it starts:

```
[AAPL] intrabar re-run ≈310µs → coalesce ≥5ms between re-runs (≤200/s), 4× margin
```

Two consequences worth internalising:

- **`tape.*` is the *latest* tick, not every tick.** Trades that arrived between two re-runs were
  merged, not queued. You cannot count prints, sum tick volume, or reconstruct a trade sequence from
  it — it is a live snapshot of the tape, not a recording of it.
- **A heavier strategy sees a coarser tape.** If you need reaction speed, keep the tick path's logic
  short and let the expensive indicators run at bar close.

### Writing tick logic: the one rule that surprises people

Each intrabar re-run happens on a **throwaway clone** of your script's state. The committed state
only ever advances at a real bar close. That is what makes it safe to re-run the same forming bar
hundreds of times — but it also means:

> **Anything written to a `var` during a tick re-run is discarded.** A `var` counter incremented on
> every tick will appear to advance only once per bar, because only the bar-close run is kept.

So tick logic must be **stateless**: derivable from the current `tape.*` values plus committed bar
state. If you need memory across ticks, it belongs in the bar-close path.

Deduplication works the normal Pine way. A signal that is true intrabar will still be true on the
next re-run a few milliseconds later, so guard entries with the position itself:

```pine
if liftOffer and strategy.position_size == 0
    strategy.entry("L", strategy.long)
```

When a fill happens, the bot reflects it back into the committed state immediately, so the very next
re-run sees the position and the entry cannot fire twice.

### What actually gets ordered

The tick path is being rolled out in stages, and the current default is conservative:

- **Observation (default).** The script re-runs per tick, `tape.*` is live, and the orders the
  strategy *would* emit are counted and logged — but the orders themselves are still placed on the
  bar-close path. This lets you watch a tick strategy against a real feed with no order risk.
- **Early market entries (opt-in, per deployment).** The point of `calc_on_every_tick` is latency:
  submitting a market entry the instant the signal turns true, rather than waiting up to a full bar
  for the close. Only bare `strategy.entry` market orders take this path.
- **Still on bar close, always.** `limit=` / `stop=` entries, `strategy.exit` OCO pairs, and stop
  trailing. A resting order cannot be deduplicated by position size, so those stay where they are
  verified.

Exits and stops therefore behave exactly as documented under
[How orders are executed](#how-orders-are-executed) — enabling ticks changes *when a signal is
noticed*, not how the broker protects your position.

### A complete example

This is the smoke strategy used to exercise the path. It trades only when a real feed is attached,
and does nothing at all in a backtest:

```pine
//@version=6
// tape.* is PineconeX-exclusive — this script does not run on TradingView.
strategy("tape smoke", overlay=true, calc_on_every_tick=true)

px     = tape.price
bid    = tape.bid
ask    = tape.ask
spread = ask - bid

// Go long when a trade lifts the offer (buyer aggression) on a tight book;
// flatten when a trade hits the bid.
tight     = not na(spread) and spread <= 0.05
liftOffer = not na(px) and not na(ask) and px >= ask
hitBid    = not na(px) and not na(bid) and px <= bid

if tight and liftOffer and strategy.position_size == 0
    strategy.entry("L", strategy.long, alert_message="tape LIFT @ {{close}}")

if hitBid and strategy.position_size > 0
    strategy.close("L", alert_message="tape HIT-BID @ {{close}}")
```

Note the shape of it: every read guarded with `na(...)`, no `var` state, and the position used as
the dedup lock. That is the template.

---

## Market Data

The **Data** page shows the market data catalog: every symbol and timeframe combination that has been fetched and is available for backtesting.

Each entry shows the data source, timeframe, date range, and row count. Use the **Fetch** button to trigger a data update for a symbol/timeframe that is missing or stale.

### What a bar contains (OHLCV)

Every dataset is stored as **OHLCV bars** — one row per bar of the chosen timeframe — and those five columns are exactly what your strategy sees. In Pine they are the built-in series `open`, `high`, `low`, `close` and `volume`: the first traded price of the bar, the highest and lowest price reached during it, the last price before it closed, and the total quantity traded. There are no tick or quote-level fields — a bar is the smallest unit of time the engine knows about, so anything that happened *inside* it (the order in which the high and the low were hit, the spread, individual trades) is not recoverable. That is why a backtest fills at bar prices while a live bot fills at whatever the broker gets, and why the two can diverge on the same signal. (A **live bot** can reach the tick layer through [`calc_on_every_tick` and `tape.*`](#tick-data-vs-bar-data) — but that is a real-time stream, not stored data, so it is unavailable to a backtest.)

Pine also derives four **average-price series** from those fields, and you can use them anywhere a price is expected — as a smoother, less noisy input to an indicator, for example:

| Series | Formula | Typical use |
|--------|---------|-------------|
| `hl2` | `(high + low) / 2` | The bar's median price — the classic "typical price" for pivots and channels. |
| `hlc3` | `(high + low + close) / 3` | Median weighted toward the close; the standard input for VWAP-style and volume-profile work. |
| `ohlc4` | `(open + high + low + close) / 4` | The bar's full average — the smoothest of the four. |
| `hlcc4` | `(high + low + close + close) / 4` | Like `hlc3` but double-weighting the close. |

You are not limited to those: any arithmetic on the raw fields is a valid series, so `(high + low + open) / 3` or `close - open` work just as well. Writing `ta.sma(ohlc4, 20)` instead of `ta.sma(close, 20)` gives a moving average that reacts to the whole bar rather than to one instant of it — often a meaningful difference on higher timeframes, where a single closing print carries a lot of noise.

> **Volume is not universal.** Equity and crypto sources carry real traded volume, but **FX bars do not** — Saxo returns bid/ask quotes for FX with no trade field, so volume arrives as `0`. A strategy that filters on volume will therefore never trigger on an FX symbol. Check the series before you depend on it. When a daily dataset is resampled to weekly or monthly, volume is **summed** across the period while OHLC is taken as first/max/min/last, which is the correct aggregation.

### Price structure — what the market did before your strategy

The **Data** page has two tabs. **Datasets** is about acquiring data; **Structure** is about
characterising it. They are different activities, and the second one asks a question no backtest
can answer for you: *what does this market do on its own?*

Three headline numbers:

| | |
|---|---|
| **Variance ratio** | Below 1, multi-bar moves are **smaller** than the sum of their parts — steps partly cancel, i.e. the market reverts. Above 1 they reinforce, i.e. it trends. At 1 it is a random walk. The `z` beside it says whether the reading is real or sampling noise. |
| **Price structure** | The verdict — *mean reverting*, *trending*, or *random walk* — read off the variance ratio and its z. |
| **Lag-1 autocorrelation** | How much one bar's return relates to the previous bar's. Negative = reversion, positive = continuation. |

> **"Random walk" is a statement about the measurement as much as about the market.** A short
> window simply cannot detect a small effect, so the panel tells you how small an effect these bars
> *could* have resolved. Read that sentence before concluding an instrument has no structure — the
> honest answer is often "this sample cannot tell", which is not the same claim.

**Why not Hurst?** Because it answers a different question. The R/S Hurst exponent measures
long-range dependence across many horizons, while a mean-reversion strategy trades the *one-step*
kind. Measured on artificial series whose behaviour is known by construction, a Hurst rule cannot
return "mean reverting" for any realistic market: a series that reverts by definition still reports
Hurst 0.573, which such a rule calls "trending". The variance ratio separates those cases cleanly.
Hurst is still shown where it appears — it is simply not the number to act on.

**Return autocorrelation by lag.** One bar per lag: how much a bar's return relates to the return
that many bars earlier. Lag 1 is the previous bar, lag 30 is thirty bars back — so on a 60m dataset
that is one hour ago and roughly three-and-a-half sessions ago. Blue below zero is reversion, amber
above is continuation, and the shaded strip is the 95% band. Bars inside it are indistinguishable
from noise.

> The band is *per lag*, so across 30 lags roughly 1.5 bars are expected to clear it **by chance
> alone**. A lone coloured bar out in the tail is usually exactly that. It counts for something when
> it is part of a run starting at lag 1, or when it lands on a meaningful period — near one bar per
> session apart, for instance, it is time-of-day seasonality rather than memory.

This chart also decides the **block size** for a [Significance](#significance--is-the-edge-real-or-luck)
test: how far the memory reaches is how big a block has to be for shuffling to be fair.

**Structure over time.** "Mean reverting" is a claim that can stop being true, and one number over
a decade cannot say whether the structure held throughout or died years ago. The walking window
re-measures the same metrics over a fixed-length window that slides forward, so a regime change
becomes visible. Each point is dated at the **end** of its window, so no point uses bars from its
own future.

> Read it as a moving average, not as a series of events: neighbouring windows share most of their
> bars, so a turn means something once it persists for about a window's width — not at the first
> wobble.

**Strategy fit** scores the same bars against each trading archetype, 0–100. It describes the
instrument's price structure — it is **not** a recommendation to trade it, and a high score is not
a prediction. When the variance ratio cannot be distinguished from a random walk, *Mean Reversion*
and *Momentum* are dimmed: those two rest on it, and inside that band the bars genuinely cannot
tell reverting from trending, so the numbers are the limit of the measurement rather than a
finding. *Scalping* needs live spread and depth data and is not computed yet.

### Supported sources

| Source | Coverage | Notes |
|--------|----------|-------|
| **Yahoo** | Equities + crypto | The default. No account needed. **Will not serve any intraday range older than 730 days** — for older intraday bars, use Bitstamp (crypto) or Saxo (equities). |
| **Saxo Bank** | European equities (DAX, CAC40, AEX, BEL20) + US equities | Requires a connected Saxo account. Saxo carries no crypto. |
| **Alpaca** | US equities + US-dollar crypto pairs | Requires a connected Alpaca account. Crypto history **begins 2021-01-01**. |
| **Bitstamp** | Crypto — USD and EUR spot pairs, plus a few FX pairs | **No account or API key needed** — it is a public feed. Timeframes `1m`, `5m`, `15m`, `30m`, `60m`, `1D`. |
| **Massive** | Broad market data via the Massive API | — |
| **Interactive Brokers** | Equities | Requires IBKR (TWS/Gateway) configured. |

The source list offered for a symbol is filtered to the sources that actually carry it — a source that has no ticker for the symbol is not selectable.

> **For deep intraday crypto history, use Bitstamp.** It is the only source that reaches it: Yahoo cuts intraday off at 730 days and Alpaca's crypto data starts in 2021, while Bitstamp's public series goes back to **2011** and quotes real BTC/USD (not a USDT proxy). A multi-year hourly Bitcoin backtest is only reproducible from this source.

### Data quality: what is checked when data is fetched

Every dataset is scanned the moment it is fetched, in one pass over the bars, before it is stored. The findings are attached to the catalog entry and shown on the Data page. **The data itself is never modified by the scan**, so what you get is what the vendor sent, plus a note about what looks wrong with it.

Four things are flagged:

| Finding | What it means |
|---------|---------------|
| `cliff` | A close-to-close move large enough to be suspicious. Usually a mishandled corporate action: a split or a large dividend that the vendor applied to some bars and not others. |
| `non_positive` | A bar with a close or low at or below zero. Always broken data. |
| `ohlc_incoherent` | `high` below `low`, or an open or close outside the bar's own range. Structurally impossible. |
| `ts_disorder` | Bars out of chronological order, or duplicated timestamps. |

The cliff threshold depends on the asset class, because "impossibly large" is not the same number everywhere. Stocks and ETFs warn at a 40% single-bar move and mark 90% as almost certainly a corporate-action error. Crypto, which genuinely does move 20 to 30% in a day, only warns at 60% and marks 150%. Forex is tightest, since majors move around 1% a day: 8% is an event worth checking, 30% is a defect.

**Why this matters more than it sounds.** A split cliff is not noise, it is a fake 300% overnight gain sitting in your price history. An optimizer will find it and build a strategy around it, and the backtest will look extraordinary. One real example in this catalog: a daily series showed a +295% single-bar move on 2006-05-18, which was a 4-for-1 split applied to the later bars only. Nothing about the strategy is wrong in that case; the edge is entirely in the data.

A flagged dataset is still usable, and often the flag is a real event rather than a defect. The point is that you get told, so you can look at the bar before trusting a result that depends on it. Where a finding is a genuine defect, the Data page offers repairs: sorting, removing duplicate timestamps, dropping non-positive bars, and rescaling every bar before a given date by a ratio, which is the manual fix for a split the vendor got wrong. A repair re-scans afterwards and reports whether the series now comes back clean.

Note that **nothing is adjusted for dividends automatically**, and sources differ in how they handle splits. Two vendors can hand you materially different histories for the same instrument, which is the other reason not to mix them.

### Reading another symbol (`request.security`): do not mix vendors

`request.security("NASDAQ:MSFT", "D", close)` pulls a second instrument into your strategy: a pair spread, an index filter, a correlated leg, a volatility gauge. The platform resolves a data source **per symbol**, so the peer you ask for can easily arrive from a different vendor than the one serving your chart.

> **Fetch every symbol in a cross-symbol strategy from the same source.** Data from two vendors is not interchangeable, and mixing it is the most common way a cross-symbol strategy produces confident, wrong numbers. The Data page shows the source each symbol and timeframe was fetched from; set them all to one source before you build on the result.

The reason this deserves a warning rather than a footnote is that it fails *quietly*. Nothing errors. The peer arrives, the values are finite and plausible, the strategy trades on them, and the report looks like any other. Three things differ between vendors, in rough order of how easy they are to miss.

**1. Bar timestamps.** Vendors stamp the same daily session at different times: Saxo writes daily bars at 00:00 UTC, Alpaca at 04:00, Yahoo at 07:00 or 08:00 depending on daylight saving. Nothing in the prices reveals it. Because a no-repaint read means "the last peer bar at or before this bar", a peer stamped later than your chart fails that test for its own session, and **yesterday's** peer value is served instead, on nearly every bar and in one direction only. PineconeX normalises daily and higher bars to the day, so this specific case is handled for you. It is worth knowing about anyway, because it is why your peer series is not stamped the way the vendor sent it.

**2. Which intraday bars exist at all.** This one cannot be repaired by shifting timestamps, because it is a coverage difference rather than an offset. Measured on two sources for the same NASDAQ listing at 15 minutes: one serves 26 bars per day (13:30 to 19:45 UTC, the regular session only), the other serves 44 (08:00 to 20:00, including pre-market and after-hours). Lining those up would mean inventing bars that one vendor never recorded. So **an intraday peer must come from the same source as the job**, and if no source can serve it there, the job is refused with an explanation instead of running on a gap-filled series.

**3. The prices themselves.** Sources disagree about split and dividend adjustment, about which venues they consolidate, and about how a bar is built from quotes. A spread, ratio or correlation computed across two vendors is partly measuring the vendors rather than the two instruments. For pair trading this is easily enough to manufacture a relationship that is not there, or to hide one that is.

Three related limits worth knowing:

- **A cross-symbol peer never silently returns `na`.** If it cannot be resolved, the job is refused up front, naming the call and the reason. This matters because `na` is not an error in Pine: a strategy reading `na` simply never fires, and the report then says "no signal" when the truth is "no data".
- **Backtest and live read different plumbing.** A backtest reads the peer from the stored data catalog; a live bot fetches it from your broker. Same strategy, potentially a different vendor. Validate a cross-symbol strategy against the source you actually intend to trade on.
- **Peers on different exchanges do not align intraday.** Two venues keep different trading hours and different holiday calendars, so their intraday bars do not correspond even when both are stamped correctly. Daily is fine; intraday across exchanges is not supported.

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

Connect an Alpaca account to trade US equities **and crypto** (the US-dollar pairs).

1. Click **Connect Alpaca** and choose **Paper** or **Live** environment.
2. Enter your Alpaca API key and secret.
3. After connecting, your account is linked and ready to trade.

> The paper environment uses Alpaca's paper-trading API. Recommended for testing before going live.

### Bitstamp

Bitstamp is a crypto **exchange** — USD and EUR spot pairs. Your coins and cash sit at Bitstamp itself and orders go into its own book.

1. Create an API key on Bitstamp with permissions to **trade**, **view your balances**, and **view your transactions**.
2. Click **Connect Bitstamp** and choose **Sandbox** or **Live**.
3. Paste the key and secret. They are verified against Bitstamp before they are stored.

> **Sandbox is Bitstamp's only paper mode** — `Live` is real money on the real exchange. There is no third option.

> **The "view your transactions" permission is not optional.** Bitstamp's order status carries no fill price, so a bot's *only* way to learn what its order actually paid is your transaction history. A key without that permission is rejected at connect rather than failing mid-trade.

Two things about Bitstamp that do not apply to a stock broker, and that will otherwise surprise you:

- **A spot holding is a balance, not a position.** Bitstamp stores no average entry price anywhere, so a bot reconstructs its cost basis from your fill history. A coin that was **deposited** (or bought more than 30 days ago, outside the API's transaction window) has no purchase price the bot can find — so it **refuses to trade that holding** and says so in the log, rather than inventing an entry price and computing wrong P&L, stops and take-profits from it. **Fund a Bitstamp bot's account by buying the coin, not by depositing it.**
- **Spot is long-only.** A short entry is refused — there is nothing to borrow.

### Prop-firm futures (Tradovate)

CME futures through a prop-firm account, over the Tradovate gateway. **New — treat it as a preview and run it on a demo account first.**

1. Click **Configure** on the *Tradovate API* card and pick your firm.
2. Enter your Tradovate login plus the **App ID**, **CID** and **Secret** your firm issued with the account. API market data must be enabled on the account, or no bars can be fetched.
3. The credentials are verified against the gateway before they are stored. The card then shows **Demo** or **Funded**.

> **Your firm's risk rules are invisible to the bot.** The daily loss limit, the trailing drawdown and the flat-by time are enforced on the firm's side: a breach flattens every position and locks the account mid-session, with none of the bot's own orders filling. The bot halts when it notices rather than re-entering, but it cannot prevent it. Futures are leveraged whenever a position is open — see [Margin monitoring](#margin-monitoring).

> **The bot does not roll contracts.** It trades the front month resolved at launch, so stop and relaunch it before expiry. Baskets are single-symbol only on this broker for the same reason.

---

## Plans *

| | Free | Pro | Premium |
|--|------|-----|-----|
| Strategies | 5 | Unlimited | Unlimited |
| Concurrent jobs | 1 | 5 | 10 |
| Backtesting | Yes | Yes | Yes |
| Parameter sweep | Yes | Yes | Yes |
| Validation (significance + stress) | — | — | Yes |
| Machine learning models | — | — | Yes |
| Live trading | 1 job (limited lifetime) | Yes | Yes |
| Multi-symbol basket (universe) jobs | — | Yes | Yes |
| Telegram notifications | — | Yes | Yes |
| Webhook signals | — | Yes | Yes |
| Multi-timeframe support | — | — | Yes |
| On-premise hosted infrastructure | — | Yes | Yes |
| Premium US market data (Massive: 5-yr history, corporate actions) | — | Yes | Yes |

GitHub-imported strategies do not count against the strategy quota on any plan.

Upgrade your plan under **Account → Plan**.

> **(*)** This table is non-binding and may fall out of sync. The [pricing page](https://pineconex.com/#pricing) is the authoritative source for plan features and limits.

---

## Support

- **Website:** [pineconex.com](https://pineconex.com)
- **Learn:** [pineconex.com/learn](https://pineconex.com/learn) — books, talks and guides on systematic trading.
- **Web API:** [pineconex.com/api-docs](https://pineconex.com/api-docs) — the REST reference for driving your account programmatically (strategies, backtests, sweeps, validation, live bots).
- **AI skill:** [pineconex.com/skill](https://pineconex.com/skill) — the packaged skill that lets an AI assistant operate the same API on your behalf.
- **Telegram:** link shown on the Support page inside the app.
- **Email:** support@pineconex.com
- **General inquiries:** info@pineconex.com
