from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fill:
    date: str
    side: str
    quantity: float
    price: float
    commission: float
    slippage: float


class PortfolioLedger:
    """Deterministic long-only ledger for historical paper trading."""

    def __init__(self, initial_cash: float = 100_000.0, fee_bps: float = 5.0, slippage_bps: float = 5.0):
        if initial_cash <= 0 or fee_bps < 0 or slippage_bps < 0:
            raise ValueError("initial cash must be positive and costs nonnegative")
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.quantity = 0.0
        self.average_cost = 0.0
        self.realized_pnl = 0.0
        self.fees = 0.0
        self.slippage_cost = 0.0
        self.fills: list[Fill] = []
        self.fee_bps = float(fee_bps)
        self.slippage_bps = float(slippage_bps)

    def execute(self, date: str, side: str, quantity: float, price: float) -> Fill:
        side = side.lower()
        quantity, price = float(quantity), float(price)
        if side not in {"buy", "sell"} or quantity <= 0 or price <= 0:
            raise ValueError("side must be buy/sell and quantity/price must be positive")
        if side == "sell" and quantity > self.quantity + 1e-12:
            raise ValueError("cannot sell more shares than held")
        notional = quantity * price
        commission = notional * self.fee_bps / 10_000
        slip = notional * self.slippage_bps / 10_000
        if side == "buy":
            total = notional + commission + slip
            if total > self.cash + 1e-9:
                raise ValueError("insufficient cash")
            new_quantity = self.quantity + quantity
            self.average_cost = ((self.average_cost * self.quantity) + total) / new_quantity
            self.quantity = new_quantity
            self.cash -= total
        else:
            proceeds = notional - commission - slip
            self.realized_pnl += proceeds - (self.average_cost * quantity)
            self.quantity -= quantity
            self.cash += proceeds
            if self.quantity < 1e-12:
                self.quantity, self.average_cost = 0.0, 0.0
        self.fees += commission
        self.slippage_cost += slip
        fill = Fill(date, side, quantity, price, commission, slip)
        self.fills.append(fill)
        return fill

    def mark(self, price: float) -> dict:
        price = float(price)
        if price <= 0:
            raise ValueError("mark price must be positive")
        equity = self.cash + self.quantity * price
        return {"cash": self.cash, "quantity": self.quantity, "price": price,
                "market_value": self.quantity * price, "equity": equity,
                "unrealized_pnl": (price - self.average_cost) * self.quantity,
                "realized_pnl": self.realized_pnl, "fees": self.fees,
                "slippage_cost": self.slippage_cost}

