import csv
import unittest
from decimal import Decimal as D
from pathlib import Path
from irps_core import (
    Item, QuantityInput, Status, calculate_need, allocate_independent,
    AllocationCandidate, allocate_total, Evidence, FactKind, Sharing,
    summarize_history, forecast_from_history, QuoteInput, calculate_quote,
    ValidationError, may_read, Role, ReferencePrice, TenderLine, calculate_tender_value,
)

ITEM = Item('camiseta-modelo-A', 'Camiseta escolar - modelo A', 'unidade', 'uniformes', specification_version='A')
ID_A, ID_B, ID_C = '1000001', '1000002', '1000003' # CHAVES FICTÍCIAS (não códigos válidos de municípios reais)

def inp(ibge, pupils, rate='2', stock='0', incoming='0', floor=None, ceiling=None):
    return QuantityInput(ibge, ITEM,'2027', 'alunos_atendidos', D(pupils) if pupils is not None else None,
        D(rate) if rate is not None else None,'fonte_de_ensaio','politica_da_rede',D('0'),D(stock),D(incoming),floor,ceiling)

def evt(eid, ibge=ID_A, kind=FactKind.CONTRACTED, qty='100', money='3000', year=2024, spec='A', sharing=Sharing.PUBLIC):
    return Evidence(eid,ibge,ITEM.key,spec,'unidade',kind,year,D(qty) if qty is not None else None,
        D(money) if money is not None else None,'https://example.invalid/fonte','doc_'+eid,'2026-10-18',sharing)

class NeedTests(unittest.TestCase):
    def test_need_and_stock(self):
        n=calculate_need(inp(ID_A,'1200',stock='400'))
        self.assertEqual((n.quantity,n.status),(2000,Status.READY_FOR_REVIEW))
    def test_missing_driver_not_zero(self):
        n=calculate_need(inp(ID_A,None))
        self.assertIsNone(n.quantity)
        self.assertEqual(n.status,Status.INSUFFICIENT_DATA)
    def test_zero_is_valid(self):
        n=calculate_need(inp(ID_A,'0'))
        self.assertEqual(n.quantity,0)
    def test_over_ceiling_blocks_not_clips(self):
        n=calculate_need(inp(ID_A,'1200',ceiling=2000))
        self.assertEqual(n.quantity,2400)
        self.assertEqual(n.status,Status.BLOCKED)
    def test_below_floor_blocks_not_inflates(self):
        n=calculate_need(inp(ID_A,'2',floor=20))
        self.assertEqual(n.quantity,4)
        self.assertEqual(n.status,Status.BLOCKED)
    def test_floor_greater_than_ceiling(self):
        self.assertEqual(calculate_need(inp(ID_A,'10',floor=100,ceiling=5)).status,Status.BLOCKED)
    def test_bad_negative_stock(self):
        with self.assertRaises(ValidationError): calculate_need(inp(ID_A,'10',stock='-1'))
    def test_invalid_reserve(self):
        a=inp(ID_A,'10')
        from dataclasses import replace
        with self.assertRaises(ValidationError): calculate_need(replace(a,safety_rate=D('1.3')))
    def test_incoming_reduces_not_negative(self):
        self.assertEqual(calculate_need(inp(ID_A,'10',incoming='500')).quantity,0)

class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.needs=[calculate_need(inp(ID_A,'200')),calculate_need(inp(ID_B,'400')),calculate_need(inp(ID_C,'600'))]
    def test_bottom_up_selection_no_inflation(self):
        a=allocate_independent(self.needs,{ID_A,ID_B,ID_C})
        b=allocate_independent(self.needs,{ID_A,ID_B})
        self.assertEqual(a.total,2400)
        self.assertEqual(b.total,1200)
        self.assertEqual(b.assigned[ID_A],a.assigned[ID_A])
    def test_bottom_up_mixed_specification_blocked(self):
        from dataclasses import replace
        other=replace(self.needs[1],specification_version='B')
        with self.assertRaises(ValidationError): allocate_independent([self.needs[0],other],{ID_A,ID_B})
    def test_bottom_up_missing_city(self):
        with self.assertRaises(ValidationError): allocate_independent(self.needs,{'9999999'})
    def test_bottom_up_mixed_product_blocked(self):
        from dataclasses import replace
        other=replace(self.needs[1],item_key='pneu')
        with self.assertRaises(ValidationError): allocate_independent([self.needs[0],other],{ID_A,ID_B})
    def test_top_down_with_documented_caps(self):
        c=[AllocationCandidate(ID_A,D('1'),10,100,'fonte A'),AllocationCandidate(ID_B,D('3'),5,100,'fonte B')]
        r=allocate_total(80,c)
        self.assertEqual(sum(r.assigned.values()),80)
        self.assertLessEqual(r.assigned[ID_A],100)
        self.assertGreater(r.assigned[ID_B],r.assigned[ID_A])
    def test_top_down_cap_saturation(self):
        c=[AllocationCandidate(ID_A,D('5'),0,10,'fonte A'),AllocationCandidate(ID_B,D('1'),0,100,'fonte B')]
        r=allocate_total(80,c)
        self.assertEqual(r.assigned[ID_A],10)
        self.assertEqual(r.assigned[ID_B],70)
    def test_top_down_infeasible(self):
        with self.assertRaises(ValidationError): allocate_total(100,[AllocationCandidate(ID_A,D('1'),5,20,'fonte')])
    def test_top_down_without_source(self):
        with self.assertRaises(ValidationError): allocate_total(10,[AllocationCandidate(ID_A,D('1'),0,20,'')])

class EvidenceTests(unittest.TestCase):
    def test_contract_vs_paid_separate(self):
        events=[evt('a',kind=FactKind.CONTRACTED),evt('b',kind=FactKind.PAID,money='600')]
        s=summarize_history(events,kind=FactKind.CONTRACTED,item_key=ITEM.key,unit='unidade',years={2024},municipalities={ID_A},specification_version='A')
        self.assertEqual((s.summed_quantity,s.summed_amount_brl),(D('100'),D('3000')))
    def test_missing_amount_not_zero(self):
        s=summarize_history([evt('a',money=None)],kind=FactKind.CONTRACTED,item_key=ITEM.key,unit='unidade',years={2024},municipalities={ID_A},specification_version='A')
        self.assertIsNone(s.summed_amount_brl)
    def test_distinct_municipalities(self):
        s=summarize_history([evt('a'),evt('b'),evt('c',ibge=ID_B)],kind=FactKind.CONTRACTED,item_key=ITEM.key,unit='unidade',years={2024},municipalities={ID_A,ID_B},specification_version='A')
        self.assertEqual(s.municipalities_count,2)
    def test_exact_duplicate_not_double_count(self):
        a=evt('same')
        s=summarize_history([a,a],kind=FactKind.CONTRACTED,item_key=ITEM.key,unit='unidade',years={2024},municipalities={ID_A},specification_version='A')
        self.assertEqual(s.records_count,1)
    def test_paid_does_not_suggest_consumed_quantity(self):
        s=summarize_history([evt('pay',kind=FactKind.PAID)],kind=FactKind.PAID,item_key=ITEM.key,unit='unidade',years={2024},municipalities={ID_A},specification_version='A')
        self.assertIsNone(s.summed_quantity)
        self.assertEqual(s.summed_amount_brl,D('3000'))
    def test_specification_isolated(self):
        s=summarize_history([evt('a',spec='A'),evt('b',spec='B')],kind=FactKind.CONTRACTED,item_key=ITEM.key,unit='unidade',years={2024},municipalities={ID_A},specification_version='A')
        self.assertEqual(s.records_count,1)
    def test_public_not_private(self):
        s=summarize_history([evt('a',sharing=Sharing.BUSINESS_PRIVATE)],kind=FactKind.CONTRACTED,item_key=ITEM.key,unit='unidade',years={2024},municipalities={ID_A},specification_version='A')
        self.assertEqual(s.records_count,0)
    def test_three_years_history_needed(self):
        data=[evt('a',year=2023,qty='100'),evt('b',year=2024,qty='200')]
        val,warnings=forecast_from_history(data,ITEM.key,ID_A,'unidade',FactKind.CONTRACTED)
        self.assertIsNone(val)
        self.assertIn('insuficiente',warnings[0])
    def test_history_median(self):
        data=[evt('a',year=2023,qty='100'),evt('b',year=2024,qty='200'),evt('c',year=2025,qty='900')]
        val,_=forecast_from_history(data,ITEM.key,ID_A,'unidade',FactKind.CONTRACTED)
        self.assertEqual(val,D('200'))
    def test_paid_cannot_forecast_consumption(self):
        val,_=forecast_from_history([evt('x',kind=FactKind.PAID)],ITEM.key,ID_A,'unidade',FactKind.PAID)
        self.assertIsNone(val)

class FinanceTests(unittest.TestCase):
    def test_quote_example(self):
        q=calculate_quote(QuoteInput(100,D('70'),D('110'),D('500'),D('200'),D('0'),D('0.08')))
        self.assertEqual(q.gross_revenue,D('11000.00'))
        self.assertEqual(q.total_costs,D('8580.00'))
        self.assertEqual(q.contribution_profit,D('2420.00'))
        self.assertEqual(q.margin_percent,D('22.00'))
    def test_margin_vs_markup(self):
        q=calculate_quote(QuoteInput(1,D('80'),D('100')))
        self.assertEqual(q.margin_percent,D('20.00'))
        self.assertEqual(q.markup_percent,D('25.00'))
    def test_zero_quantity_has_no_undefined_margin(self):
        q=calculate_quote(QuoteInput(0,D('80'),D('100')))
        self.assertIsNone(q.margin_percent)
        self.assertIsNone(q.break_even_unit_price)
    def test_invalid_tax_rate(self):
        with self.assertRaises(ValidationError): calculate_quote(QuoteInput(10,D('1'),D('2'),sales_tax_rate=D('1')))
    def test_non_finite(self):
        with self.assertRaises(ValidationError): calculate_quote(QuoteInput(1,D('NaN'),D('2')))


class TenderTests(unittest.TestCase):
    def price(self, item='camisa', spec='A', valid=True):
        return ReferencePrice(item,spec,'unidade',D('30.50'),'https://example.invalid/preco','2026-10-18',valid)
    def test_two_cities_total(self):
        p=self.price()
        result=calculate_tender_value([TenderLine(ID_A,'camisa','A','unidade',D('100'),p), TenderLine(ID_B,'camisa','A','unidade',D('200'),p)])
        self.assertEqual(result.total_brl,D('9150.00'))
        self.assertEqual(result.by_municipality[ID_A],D('3050.00'))
    def test_mismatched_price_blocked(self):
        with self.assertRaises(ValidationError): calculate_tender_value([TenderLine(ID_A,'camisa','B','unidade',D('100'),self.price())])
    def test_not_validated_blocked(self):
        with self.assertRaises(ValidationError): calculate_tender_value([TenderLine(ID_A,'camisa','A','unidade',D('10'),self.price(valid=False))])
    def test_duplicate_line_blocked(self):
        a=TenderLine(ID_A,'camisa','A','unidade',D('10'),self.price())
        with self.assertRaises(ValidationError): calculate_tender_value([a,a])
    def test_118_cities_selection_totals(self):
        p=self.price(); lines=[TenderLine(f'{1000000+i:07d}','camisa','A','unidade',D('2'),p) for i in range(1,119)]
        r=calculate_tender_value(lines)
        self.assertEqual(len(r.by_municipality),118)
        self.assertEqual(r.total_brl,D('7198.00'))
    def test_118_selection_does_not_change_existing_needs(self):
        p=self.price(); lines=[TenderLine(f'{1000000+i:07d}','camisa','A','unidade',D(i),p) for i in range(1,119)]
        with118=calculate_tender_value(lines)
        with20=calculate_tender_value(lines[:20])
        self.assertEqual(with118.by_municipality[ID_A],with20.by_municipality[ID_A])
        self.assertGreater(with118.total_brl,with20.total_brl)

class FractionalQuantityTests(unittest.TestCase):
    def test_area_m2(self):
        item=Item('obra-pavimento','Pavimentação por m²','m2','obras',quantity_step=D('0.01'))
        n=calculate_need(QuantityInput(ID_A,item,'2027','area',D('123.451'),D('1'),'f1','f2'))
        self.assertEqual(n.quantity,D('123.46'))
    def test_allocate_fractional(self):
        c=[AllocationCandidate(ID_A,D('1'),D('0'),D('10'),'f1'),AllocationCandidate(ID_B,D('1'),D('0'),D('10'),'f2')]
        a=allocate_total(D('5.5'),c,quantity_step=D('0.5'))
        self.assertEqual(a.total,D('5.5'))
        self.assertEqual(sum(a.assigned.values()),D('5.5'))
    def test_incompatible_fractional_step(self):
        with self.assertRaises(ValidationError): allocate_total(D('1.25'),[AllocationCandidate(ID_A,D('1'),D('0'),D('10'),'f')],quantity_step=D('0.5'))

class PermissionTests(unittest.TestCase):
    def test_public(self): self.assertTrue(may_read(Role.PUBLIC_READER,Sharing.PUBLIC))
    def test_private_cross_tenant_blocked(self): self.assertFalse(may_read(Role.SUPPLIER,Sharing.BUSINESS_PRIVATE,False))
    def test_supplier_cannot_see_government_internal(self): self.assertFalse(may_read(Role.SUPPLIER,Sharing.GOVERNMENT_INTERNAL,True))
    def test_internal_is_scoped(self): self.assertTrue(may_read(Role.CONSORTIUM_ANALYST,Sharing.GOVERNMENT_INTERNAL,True))
    def test_admin_not_cross_kind(self): self.assertFalse(may_read(Role.ORG_ADMIN,Sharing.BUSINESS_PRIVATE,True,"governo"))
    def test_supplier_admin_private(self): self.assertTrue(may_read(Role.ORG_ADMIN,Sharing.BUSINESS_PRIVATE,True,"fornecedor"))

class SeedTests(unittest.TestCase):
    def test_seed_118_has_unverified_codes(self):
        p=Path(__file__).resolve().parents[2]/'dados'/'municipios_118_origem.csv'
        with p.open(encoding='utf-8-sig', newline='') as fh: rows=list(csv.DictReader(fh,delimiter=';'))
        self.assertEqual(len(rows),118)
        self.assertTrue(all(row['codigo_ibge_a_validar']=='' for row in rows))

if __name__=='__main__': unittest.main()
