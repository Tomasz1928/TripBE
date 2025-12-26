from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class SplitDTO:
    participant_id: int
    split_value: Decimal
    split_value_main_current: Optional[Decimal] = None