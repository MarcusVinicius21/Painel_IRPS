"""IRPS V4: núcleo de domínio de referência, somente com dados fictícios nos exemplos.

Não substitui ETP/TR/IRP, validação de preços, aprovação da autoridade ou fontes oficiais.
"""
from .domain import Evidence, FactKind, Item, Municipality, QuantityInput, NeedResult, Status, Sharing, ValidationError
from .forecast import calculate_need, forecast_from_history
from .allocate import AllocationCandidate, allocate_total, allocate_independent, AllocationResult
from .market import summarize_history, MarketSummary
from .finance import QuoteInput, QuoteResult, calculate_quote
from .permissions import Role, may_read
from .tender import ReferencePrice, TenderLine, TenderSummary, calculate_tender_value

__all__ = ['Evidence','FactKind','Item','Municipality','QuantityInput','NeedResult','Status','Sharing','ValidationError','calculate_need','forecast_from_history','AllocationCandidate','AllocationResult','allocate_total','allocate_independent','summarize_history','MarketSummary','QuoteInput','QuoteResult','calculate_quote','Role','may_read','ReferencePrice','TenderLine','TenderSummary','calculate_tender_value']
