from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from tracking.models import Country, State, City, Customer, Carrier, Order

class DashboardTestCase(TestCase):
    def setUp(self):
        # Create default client
        self.client = Client()
        
    def test_dashboard_empty_state(self):
        response = self.client.get(reverse('tracking:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['empty_state'])
        self.assertContains(response, "Nenhum dado importado")

    def test_dashboard_with_data(self):
        # Setup mock entities
        country = Country.objects.create(name="BRASIL")
        state_sp = State.objects.create(id="SP", name="SÃO PAULO", country=country)
        state_rj = State.objects.create(id="RJ", name="RIO DE JANEIRO", country=country)
        
        city_sp = City.objects.create(name="SÃO PAULO", state=state_sp)
        city_rj = City.objects.create(name="RIO DE JANEIRO", state=state_rj)
        
        customer_a = Customer.objects.create(name="Cliente A", cnpj="12345678901234", city=city_sp)
        customer_b = Customer.objects.create(name="Cliente B", cnpj="98765432109876", city=city_rj)
        
        carrier_x = Carrier.objects.create(name="TransX", cnpj="11111111111111", city=city_sp)
        carrier_y = Carrier.objects.create(name="TransY", cnpj="22222222222222", city=city_rj)
        
        # Create orders
        # Order 1: Delivered
        Order.objects.create(
            nfe="001",
            order_date=date(2026, 7, 1),
            collection_date=date(2026, 7, 2),
            delivery_date=date(2026, 7, 5),
            status="ENTREGUE",
            customer=customer_a,
            carrier=carrier_x
        )
        
        # Order 2: In transit
        Order.objects.create(
            nfe="002",
            order_date=date(2026, 7, 5),
            collection_date=date(2026, 7, 6),
            delivery_date=None,
            status="TRANSITO",
            customer=customer_b,
            carrier=carrier_y
        )
        
        # Order 3: Pending
        Order.objects.create(
            nfe="003",
            order_date=date(2026, 7, 10),
            collection_date=None,
            delivery_date=None,
            status="PENDENTE",
            customer=customer_a,
            carrier=carrier_x
        )
        
        # Request dashboard
        response = self.client.get(reverse('tracking:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['empty_state'])
        self.assertFalse(response.context['no_filtered_data'])
        
        # Check KPIs
        kpis = response.context['kpis']
        self.assertEqual(kpis['total_orders'], 3)
        self.assertEqual(kpis['entregues_count'], 1)
        self.assertEqual(kpis['transito_count'], 1)
        self.assertEqual(kpis['pendentes_count'], 1)
        # Lead time: (2026-07-05 - 2026-07-01) = 4 days
        self.assertEqual(kpis['avg_lead_time'], 4.0)
        # Transit time: (2026-07-05 - 2026-07-02) = 3 days
        self.assertEqual(kpis['avg_transit_time'], 3.0)
        
        # Test filters
        # 1. Filter by State (SP)
        response_sp = self.client.get(reverse('tracking:dashboard'), {'uf': 'SP'})
        self.assertEqual(response_sp.context['kpis']['total_orders'], 2) # Order 1 & 3 are SP
        
        # 2. Filter by Carrier (carrier_y)
        response_carrier = self.client.get(reverse('tracking:dashboard'), {'carrier': carrier_y.id})
        self.assertEqual(response_carrier.context['kpis']['total_orders'], 1) # Order 2
        
        # 3. Filter by Date range
        response_date = self.client.get(reverse('tracking:dashboard'), {
            'data_inicio': '2026-07-01',
            'data_fim': '2026-07-04'
        })
        self.assertEqual(response_date.context['kpis']['total_orders'], 1) # Only Order 1
        
        # 4. Filter that yields empty results
        response_empty = self.client.get(reverse('tracking:dashboard'), {'uf': 'DF'})
        self.assertTrue(response_empty.context['no_filtered_data'])
        self.assertContains(response_empty, "Nenhum pedido filtrado")
