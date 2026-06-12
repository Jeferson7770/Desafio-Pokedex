from django.core.cache import cache
from django.utils import timezone


def _prev_month(year, month):
    return (year - 1, 12) if month == 1 else (year, month - 1)


def invalidar_cache_financeiro(firm_id):
    """
    Invalida todo cache financeiro do firm.
    Com Redis: usa delete_pattern para cobrir qualquer combinação de params (year/month, start_date/end_date).
    Fallback para LocMemCache (desenvolvimento local): apaga chaves do mês atual e anterior.
    """
    prefixes = ["dashboard", "yearly_summary", "honorarios", "outras_entradas",
                "financial_report", "cash_flow_summary"]
    try:
        for p in prefixes:
            cache.delete_pattern(f"{p}:{firm_id}:*")
    except AttributeError:
        today = timezone.localdate()
        y, m = today.year, today.month
        py, pm = _prev_month(y, m)
        keys = (
            [f"{p}:{firm_id}:{y}:{m}" for p in prefixes]
            + [f"{p}:{firm_id}:{py}:{pm}" for p in prefixes]
        )
        cache.delete_many(keys)


def invalidar_cache_motor(firm_id):
    try:
        cache.delete_pattern(f"motor_prioridade:{firm_id}:*")
    except AttributeError:
        today = timezone.localdate()
        cache.delete(f"motor_prioridade:{firm_id}:{today.year}:{today.month}")


def invalidar_cache_prolabore(user_id):
    cache.delete_many([
        f"prolabore_history:{user_id}:3",
        f"prolabore_history:{user_id}:6",
        f"prolabore_history:{user_id}:12",
        f"prolabore_history:{user_id}:36",
    ])
