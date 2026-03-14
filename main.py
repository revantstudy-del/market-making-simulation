import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

os.makedirs("output_plots", exist_ok=True)

def simulate_price(S0=100, mu=0.0001, sigma=0.01, steps=1000):
    prices = [S0]
    for _ in range(steps):
        dW = np.random.normal(0, 1)
        S_new = prices[-1] * np.exp((mu - 0.5 * sigma**2) + sigma * dW)
        prices.append(S_new)
    return np.array(prices)

class MarketMaker:
    def __init__(self, spread=0.2, max_inventory=20):
        self.spread = spread
        self.inventory = 0
        self.cash = 0.0
        self.max_inventory = max_inventory
    def quote(self, price):
        inventory_skew = abs(self.inventory) / self.max_inventory
        dynamic_spread = self.spread * (1 + inventory_skew)
        bid = price - dynamic_spread / 2
        ask = price + dynamic_spread / 2
        return bid, ask
    def execute_trade(self, price, side):
        if side == "buy":
            self.inventory -= 1
            self.cash += price
        elif side == "sell":
            self.inventory += 1
            self.cash -= price

    def pnl(self, current_price):
        return self.cash + self.inventory * current_price

def run_simulation(steps=1000, spread=0.2, arrival_prob=0.8):
    prices = simulate_price(steps=steps)
    mm = MarketMaker(spread=spread)
    pnl_series = []
    inventory_series = []
    spread_series = []
    for price in prices:
        bid, ask = mm.quote(price)
        if np.random.rand() < arrival_prob:
            order = np.random.choice(["buy", "sell"])
            if order == "buy":
                mm.execute_trade(ask, "buy")
            else:
                mm.execute_trade(bid, "sell")
        pnl_series.append(mm.pnl(price))
        inventory_series.append(mm.inventory)
        spread_series.append(ask - bid)
    return {
        "prices":prices,
        "pnl":np.array(pnl_series),
        "inventory":np.array(inventory_series),
        "spread":np.array(spread_series),
        "final_pnl":pnl_series[-1]
    }

def monte_carlo(n=500, steps=1000, spread=0.2):
    final_pnls = []
    max_drawdowns = []
    for _ in range(n):
        res = run_simulation(steps=steps, spread=spread)
        final_pnls.append(res["final_pnl"])
        pnl = res["pnl"]
        peak = np.maximum.accumulate(pnl)
        drawdown = peak - pnl
        max_drawdowns.append(np.max(drawdown))

    return np.array(final_pnls), np.array(max_drawdowns)

sim = run_simulation(steps=1000)

plt.figure(figsize=(10, 4))
plt.plot(sim["prices"], color='steelblue', linewidth=0.8)
plt.title("Simulated Stock Price Path (GBM)")
plt.xlabel("Time Steps")
plt.ylabel("Price ($)")
plt.tight_layout()
plt.savefig("output_plots/1_price_path.png", dpi=150)
plt.close()

plt.figure(figsize=(10, 4))
plt.plot(sim["pnl"], color='mediumseagreen', linewidth=0.8)
plt.axhline(0, color='red', linestyle='--', linewidth=0.8)
plt.title("Market Maker PnL Over Time")
plt.xlabel("Time Steps")
plt.ylabel("PnL ($)")
plt.tight_layout()
plt.savefig("output_plots/2_pnl_over_time.png", dpi=150)
plt.close()

plt.figure(figsize=(10, 4))
plt.plot(sim["inventory"], color='coral', linewidth=0.8)
plt.axhline(0, color='black', linestyle='--', linewidth=0.8)
plt.title("Market Maker Inventory Over Time")
plt.xlabel("Time Steps")
plt.ylabel("Inventory (shares)")
plt.tight_layout()
plt.savefig("output_plots/3_inventory.png", dpi=150)
plt.close()

final_pnls, max_drawdowns = monte_carlo(n=500)

mean_pnl = np.mean(final_pnls)
std_pnl = np.std(final_pnls)
pct_profitable = (final_pnls > 0).mean() * 100

print(f" Mean Final PnL: ${mean_pnl:.2f}")
print(f"Std Dev of PnL: ${std_pnl:.2f}")
print(f"% Profitable Runs: {pct_profitable:.1f}%")
print(f"Sharpe-like ratio: {mean_pnl / std_pnl:.3f}")
print(f"Mean Max Drawdown: ${np.mean(max_drawdowns):.2f}")

plt.figure(figsize=(9, 5))
plt.hist(final_pnls, bins=50, color='steelblue', edgecolor='black', alpha=0.8)
plt.axvline(mean_pnl, color='red', linestyle='--', linewidth=1.5,label=f"Mean = ${mean_pnl:.1f}")
plt.axvline(0,color='black', linestyle=':',  linewidth=1.2,label="Break-even")
plt.title("PnL Distribution – Monte Carlo Simulation (500 Runs)")
plt.xlabel("Final PnL ($)")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()
plt.savefig("output_plots/4_pnl_distribution.png", dpi=150)
plt.close()

spreads= [0.05, 0.10, 0.20, 0.40, 0.80]
mean_pnls_by_spread = []
for sp in spreads:
    pnls, _ = monte_carlo(n=200, spread=sp)
    mean_pnls_by_spread.append(np.mean(pnls))

plt.figure(figsize=(8, 4))
plt.plot(spreads, mean_pnls_by_spread, marker='o', color='mediumseagreen')
plt.title("Mean PnL vs Bid-Ask Spread Size")
plt.xlabel("Spread ($)")
plt.ylabel("Mean Final PnL ($)")
plt.tight_layout()
plt.savefig("output_plots/5_spread_vs_pnl.png", dpi=150)
plt.close()

plt.figure(figsize=(9, 4))
plt.hist(max_drawdowns, bins=50, color='coral', edgecolor='black', alpha=0.8)
plt.axvline(np.mean(max_drawdowns), color='darkred', linestyle='--',label=f"Mean = ${np.mean(max_drawdowns):.1f}")
plt.title("Max Drawdown Distribution – Monte Carlo")
plt.xlabel("Max Drawdown ($)")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()
plt.savefig("output_plots/6_max_drawdown.png", dpi=150)
plt.close()
