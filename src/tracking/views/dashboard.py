import pandas as pd
from django.shortcuts import render
from django.db.models import Q
from tracking.models import Order, Carrier, State, Customer

def view_dashboard(request):
    # 1. Verificar se existem dados no banco
    if not Order.objects.exists():
        return render(request, "tracking/dashboard.html", {
            "empty_state": True,
            "states": [],
            "carriers": []
        })

    # 2. Obter dados de filtros para preencher os selects
    all_states = State.objects.all().order_by('id')
    all_carriers = Carrier.objects.all().order_by('name')
    
    # 3. Pegar os parâmetros de filtro da requisição GET
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    uf_filtro = request.GET.get("uf", "")
    carrier_filtro = request.GET.get("carrier", "")
    status_filtro = request.GET.get("status", "")

    # 4. Construir a query filtrada
    query = Q()
    if data_inicio:
        query &= Q(order_date__gte=data_inicio)
    if data_fim:
        query &= Q(order_date__lte=data_fim)
    if uf_filtro:
        query &= Q(customer__city__state_id=uf_filtro)
    if carrier_filtro:
        query &= Q(carrier_id=carrier_filtro)
    if status_filtro:
        query &= Q(status=status_filtro)

    filtered_orders = Order.objects.filter(query).select_related(
        'customer__city__state', 'carrier'
    ).order_by('-order_date')

    # Se a busca filtrada não retornar nada
    if not filtered_orders.exists():
        return render(request, "tracking/dashboard.html", {
            "no_filtered_data": True,
            "empty_state": False,
            "states": all_states,
            "carriers": all_carriers,
            "filters": {
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "uf": uf_filtro,
                "carrier": carrier_filtro,
                "status": status_filtro,
            }
        })

    # 5. Converter queryset em Pandas DataFrame para processamento analítico
    orders_data = list(filtered_orders.values(
        'nfe', 'order_date', 'collection_date', 'delivery_date', 'status',
        'carrier__name', 'customer__city__state_id', 'customer__name'
    ))
    
    df = pd.DataFrame(orders_data)
    
    # Converter datas para datetime
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['collection_date'] = pd.to_datetime(df['collection_date'])
    df['delivery_date'] = pd.to_datetime(df['delivery_date'])

    # Calcular colunas auxiliares de tempos
    df['lead_time'] = (df['delivery_date'] - df['order_date']).dt.days
    df['transit_time'] = (df['delivery_date'] - df['collection_date']).dt.days

    # 6. Calcular KPIs Principais
    total_orders = len(df)
    
    status_counts = df['status'].value_counts()
    
    entregues_count = int(status_counts.get('ENTREGUE', 0))
    transito_count = int(status_counts.get('TRANSITO', 0))
    pendentes_count = int(status_counts.get('PENDENTE', 0))
    
    entregues_pct = round((entregues_count / total_orders) * 100, 1) if total_orders > 0 else 0
    transito_pct = round((transito_count / total_orders) * 100, 1) if total_orders > 0 else 0
    pendentes_pct = round((pendentes_count / total_orders) * 100, 1) if total_orders > 0 else 0

    # Tempo médio de Entrega (Pedido até a Entrega)
    avg_lead_time = df['lead_time'].mean()
    avg_lead_time = round(avg_lead_time, 1) if pd.notna(avg_lead_time) else "N/A"

    # Tempo médio de Trânsito (Coleta até a Entrega)
    avg_transit_time = df['transit_time'].mean()
    avg_transit_time = round(avg_transit_time, 1) if pd.notna(avg_transit_time) else "N/A"

    # 7. Agrupamento para Gráficos
    
    # A) Evolução Temporal de Envios (Agrupado por data de pedido)
    timeline_df = df.groupby(df['order_date'].dt.date).size().reset_index(name='count').sort_values('order_date')
    timeline_labels = timeline_df['order_date'].apply(lambda x: x.strftime('%d/%m/%Y')).tolist()
    timeline_data = timeline_df['count'].tolist()

    # B) Distribuição por Estado de Destino (UF)
    state_df = df.groupby('customer__city__state_id').size().reset_index(name='count').sort_values('count', ascending=False)
    state_labels = state_df['customer__city__state_id'].tolist()
    state_data = state_df['count'].tolist()

    # C) Desempenho de Transportadoras (Volume e Transit Time)
    carrier_df = df.groupby('carrier__name').agg(
        count=('nfe', 'count'),
        avg_transit=('transit_time', 'mean')
    ).reset_index().sort_values('count', ascending=False)
    
    carrier_df['avg_transit'] = carrier_df['avg_transit'].fillna(0).round(1)
    carrier_labels = carrier_df['carrier__name'].tolist()
    carrier_counts = carrier_df['count'].tolist()
    carrier_transits = carrier_df['avg_transit'].tolist()

    # D) Distribuição de Status (Donut Chart)
    status_labels = ['Pendente', 'Em Trânsito', 'Entregue']
    status_data = [pendentes_count, transito_count, entregues_count]

    # 8. Listar Pedidos Recentes Filtrados (limitar a 20 para visualização rápida)
    recent_orders = filtered_orders[:20]

    context = {
        "empty_state": False,
        "no_filtered_data": False,
        "states": all_states,
        "carriers": all_carriers,
        "filters": {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "uf": uf_filtro,
            "carrier": carrier_filtro,
            "status": status_filtro,
        },
        "kpis": {
            "total_orders": total_orders,
            "entregues_count": entregues_count,
            "entregues_pct": entregues_pct,
            "transito_count": transito_count,
            "transito_pct": transito_pct,
            "pendentes_count": pendentes_count,
            "pendentes_pct": pendentes_pct,
            "avg_lead_time": avg_lead_time,
            "avg_transit_time": avg_transit_time,
        },
        "charts": {
            "timeline_labels": timeline_labels,
            "timeline_data": timeline_data,
            "state_labels": state_labels,
            "state_data": state_data,
            "carrier_labels": carrier_labels,
            "carrier_counts": carrier_counts,
            "carrier_transits": carrier_transits,
            "status_labels": status_labels,
            "status_data": status_data,
        },
        "recent_orders": recent_orders
    }

    return render(request, "tracking/dashboard.html", context)
