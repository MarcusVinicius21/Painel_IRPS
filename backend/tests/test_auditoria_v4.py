"""Regressões independentes do executor; todos os dados são fictícios."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from irps_core import *

I=Item('teste','Item fictício','un','consumo',specification_version='v1')
def physical(**kwargs):
 return replace(QuantityInput('1000001',I,'2027','pessoas',D(10),D(2),'origem fictícia','taxa fictícia'),**kwargs)

class AuditRegressions(unittest.TestCase):
 def test_largest_remainders_uses_original_round_quotas(self):
  cs=[AllocationCandidate(f'100000{i}',D(i),D(0),D(100),'critério fictício') for i in (1,2,3)]
  self.assertEqual(allocate_total(5,cs).assigned,{'1000001':D(1),'1000002':D(2),'1000003':D(2)})
 def test_fractional_largest_remainders(self):
  cs=[AllocationCandidate(f'100000{i}',D(i),D(0),D(10),'critério fictício') for i in (1,2,3)]
  self.assertEqual(allocate_total(D('.5'),cs,D('.1')).assigned,{'1000001':D('.1'),'1000002':D('.2'),'1000003':D('.2')})
 def test_break_even_price_does_not_round_below_cost(self):
  q=QuoteInput(3,D(1),D(2),fixed_expenses=D('.01'))
  equilibrium=calculate_quote(q).break_even_unit_price
  self.assertEqual(equilibrium,D('1.01'))
  self.assertGreaterEqual(calculate_quote(replace(q,intended_sale_price_unit=equilibrium)).contribution_profit,0)
 def test_non_numeric_ibge_rejected(self):
  with self.assertRaises(ValidationError):calculate_need(physical(municipality_ibge='abcdefg'))
 def test_non_finite_floor_rejected_with_domain_error(self):
  with self.assertRaises(ValidationError):calculate_need(physical(floor=D('NaN')))
 def test_infinite_ceiling_rejected(self):
  with self.assertRaises(ValidationError):calculate_need(physical(ceiling=D('Infinity')))
 def test_nan_evidence_quantity_domain_error(self):
  with self.assertRaises(ValidationError):Evidence('e','1000001','teste','v1','un',FactKind.CONTRACTED,2025,D('NaN'),D(1),'https://example.invalid','doc','2026-10-18')
 def test_nan_evidence_amount_domain_error(self):
  with self.assertRaises(ValidationError):Evidence('e','1000001','teste','v1','un',FactKind.CONTRACTED,2025,D(1),D('NaN'),'https://example.invalid','doc','2026-10-18')
 def test_invalid_history_minimum_rejected(self):
  with self.assertRaises(ValidationError):forecast_from_history([],'teste','1000001','un',FactKind.CONTRACTED,0)
 def test_negative_need_cannot_be_consolidated(self):
  n=NeedResult('1000001','teste','2027',D(-1),'un',Status.READY_FOR_REVIEW,'ensaio')
  with self.assertRaises(ValidationError):allocate_independent([n],{'1000001'})
 def test_allocation_invalid_ibge_rejected(self):
  with self.assertRaises(ValidationError):allocate_total(1,[AllocationCandidate('x',D(1),D(0),D(5),'critério')])
 def test_nan_weight_domain_error(self):
  with self.assertRaises(ValidationError):allocate_total(1,[AllocationCandidate('1000001',D('NaN'),D(0),D(5),'critério')])
 def test_non_finite_quote_quantity_domain_error(self):
  with self.assertRaises(ValidationError):calculate_quote(QuoteInput(D('NaN'),D(1),D(2)))
 def test_tender_invalid_municipality_rejected(self):
  p=ReferencePrice('teste','v1','un',D(1),'https://example.invalid','2026-10-18',True)
  with self.assertRaises(ValidationError):calculate_tender_value([TenderLine('x','teste','v1','un',D(1),p)])
 def test_tender_invalid_reference_date_rejected(self):
  p=ReferencePrice('teste','v1','un',D(1),'https://example.invalid','ontem',True)
  with self.assertRaises(ValidationError):calculate_tender_value([TenderLine('1000001','teste','v1','un',D(1),p)])
 def test_bounded_allocation_invariants_200_cases(self):
  import random
  rng=random.Random(20261018)
  for case in range(200):
   cs=[]
   for i in range(1,rng.randint(2,20)):
    floor=rng.randint(0,10);cap=floor+rng.randint(1,30)
    cs.append(AllocationCandidate(f'{1000000+i:07d}',D(rng.randint(1,9)),D(floor),D(cap),'critério fictício'))
   target=rng.randint(int(sum(c.floor for c in cs)),int(sum(c.ceiling for c in cs)))
   with self.subTest(case=case):
    r=allocate_total(target,cs);self.assertEqual(sum(r.assigned.values()),target)
    self.assertEqual(r.assigned,allocate_total(target,list(reversed(cs))).assigned)
    for c in cs:self.assertTrue(c.floor<=r.assigned[c.ibge]<=c.ceiling)
 def test_selection_3_10_20_preserves_local_needs(self):
  needs=[calculate_need(physical(municipality_ibge=f'{1000000+i:07d}',driver_count=D(100+i),available_stock=D(i))) for i in range(1,21)]
  twenty=allocate_independent(needs,{n.municipality_ibge for n in needs})
  for n in [3,10]:
   chosen={x.municipality_ibge for x in needs[:n]};subset=allocate_independent(needs,chosen)
   self.assertEqual(subset.assigned,{k:v for k,v in twenty.assigned.items() if k in chosen})

if __name__=='__main__':unittest.main()
