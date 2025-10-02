# src/spec_schema.py
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict

class IndicatorDef(BaseModel):
    name: Literal["SMA","EMA","RSI","ATR","MACD","QuarterGrid","Session"]
    params: Dict[str, float] | Dict[str, int]
    alias: str   # e.g. "RSI_14"

class EntryRule(BaseModel):
    side: Literal["LONG","SHORT"]
    condition: str               # e.g. "(RSI_14 < 30) and (QG == 'Q1')"
    session: Optional[Literal["Asia","London","NY"]] = None

class ExitRule(BaseModel):
    type: Literal["TP_SL","IndicatorCross","Time"]
    params: Dict[str, float|int|str]

class RiskRule(BaseModel):
    fixed_fraction: float = 0.01
    max_positions: int = 1

class StrategySpec(BaseModel):
    name: str
    timeframe: Literal["M5","M15","H1","H4","D1"]
    instruments: List[str]
    indicators: List[IndicatorDef]
    entries: List[EntryRule]
    exits: List[ExitRule]
    risk: RiskRule
