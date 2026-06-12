from django.core.cache import cache
from django.utils import timezone


def _prev_month(year, month):
    return (year - 1, 12) if month == 1 else (year, month - 1)


def invalidar_cache_financeiro(firm_id):
    """Dashboard, yearly-summary, honorarios, outras-entradas, relatorios e cash-flow do mês atual e anterior."""
    today = timezone.localdate()
    y, m = today.year, today.month
    py, pm = _prev_month(y, m)

    prefixes = ["dashboard", "yearly_summary", "honorarios", "outras_entradas",
                "financial_report", "cash_flow_summary"]
    keys = [
        f"{p}:{firm_id}:{y}:{m}" for p in prefixes
    ] + [
        f"{p}:{firm_id}:{py}:{pm}" for p in prefixes
    ]
    cache.delete_many(keys)


def invalidar_cache_motor(firm_id):
    today = timezone.localdate()
    cache.delete(f"motor_prioridade:{firm_id}:{today.year}:{today.month}")


def invalidar_cache_prolabore(user_id):
    cache.delete_many([
        f"prolabore_history:{user_id}:3",
        f"prolabore_history:{user_id}:6",
        f"prolabore_history:{user_id}:12",
        f"prolabore_history:{user_id}:36",
    ])
