from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Q, Sum, F, Case, When, Value, BooleanField, ExpressionWrapper, DecimalField
from django.db.models.functions import Round

from tripAppBE.models import Cost, Splited, Trip
from tripAppBE.services.convert_currency_service import fetch_currency_rates, \
    update_description, convert_currency
from tripAppBE.services.dto.cost_dto import SplitDTO


def calculate_split_values(obj, is_payer, payment_flag):
    """
    Helper do obliczania wartości pay_back i to_pay_back.
    """
    split_value_main = obj.split_value_main_current

    if payment_flag:
        # Jeden uczestnik płaci → to_pay_back = 0, pay_back = cały split
        return {
            "pay_back_value": obj.split_value,
            "pay_back_value_main_current": split_value_main,
            "to_pay_back_value": Decimal("0.00"),
            "to_pay_back_value_main_current": Decimal("0.00"),
        }

    # Standardowa logika
    return {
        "pay_back_value": obj.split_value if is_payer else Decimal("0.00"),
        "pay_back_value_main_current": split_value_main if is_payer else Decimal("0.00"),
        "to_pay_back_value": Decimal("0.00") if is_payer else obj.split_value,
        "to_pay_back_value_main_current": Decimal("0.00") if is_payer else split_value_main,
    }


# ======================================================
# COST MANAGEMENT
# ======================================================


def add_cost(
    trip_id,
    title,
    payer_participant_id,
    overall_value,
    split_object_list,
    currency,
    description,
):
    """
    Dodaje koszt + splity (bulk)
    """

    trip = Trip.objects.filter(trip_id=trip_id).first()
    if not trip:
        return {"ok": False, "message": "Trip not found"}

    # ===== KONWERSJA Graphene Input → DTO =====
    split_dtos = [
        SplitDTO(
            participant_id=int(obj.participant_id),
            split_value=obj.split_value,
        )
        for obj in split_object_list
    ]

    # ===== DOMYŚLNE WARTOŚCI (waluta główna) =====
    overall_value_main_currency = overall_value
    rate = 1.0

    for obj in split_dtos:
        obj.split_value_main_current = obj.split_value

    # ===== PRZELICZANIE WALUT =====
    if currency != trip.default_currency:
        rate_dict = fetch_currency_rates(currency)
        rate = rate_dict.get(trip.default_currency.lower())

        overall_value_main_currency = convert_currency( overall_value, currency, trip.default_currency, rate_dict)

        description = update_description(description, overall_value, overall_value_main_currency, currency, trip.default_currency, rate_dict)

        for obj in split_dtos:
            obj.split_value_main_current = convert_currency(obj.split_value, currency, trip.default_currency, rate_dict)

    # ===== FLAGA PŁATNOŚCI =====
    payment_flag = (
        len(split_object_list) == 1
        and str(split_object_list[0].participant_id) == str(payer_participant_id)
    )

    # ===== ZAPIS DO BAZY =====
    with transaction.atomic():
        cost = Cost.objects.create(
            trip=trip, cost_name=title, overall_value=overall_value,
            overall_value_main_currency=overall_value_main_currency, payed_currency=currency,
            payment=payment_flag, description=description,
        )

        splits = []

        for obj in split_dtos:
            is_payer = str(payer_participant_id) == str(obj.participant_id)
            values = calculate_split_values(obj, is_payer, payment_flag)

            splits.append(
                Splited(
                    cost_id=cost.cost_id, participant_id=obj.participant_id,
                    payer_id=payer_participant_id, payment=is_payer,
                    split_value=obj.split_value, split_value_main_current=obj.split_value_main_current,
                    rate=rate,
                    **values
                )
            )

        Splited.objects.bulk_create(splits)

    return { "ok": True, "message": "New cost added", "cost": cost,}


def update_cost(cost_id, **fields):
    """
    Aktualizacja kosztu (bez SELECT)
    """
    updated = Cost.objects.filter(cost_id=cost_id).update(**fields)

    if not updated:
        return {"ok": False, "message": "Cost not found"}

    return {"ok": True, "message": "Cost updated"}


def update_payment(cost_id, participant_id, pay_back_value, current_currency=None):
    """
    Aktualizacja płatności splitu + status kosztu z uwzględnieniem waluty bieżącej.

    - Jeśli current_currency != trip.default_currency → standardowa konwersja na main currency
    - Jeśli current_currency == trip.default_currency → pay_back_value traktowane jako main currency,
      split_value przeliczany odwrotnie przez rate
    """
    pay_back_value = Decimal(pay_back_value)

    with transaction.atomic():
        # Pobierz split i powiązany trip
        split_qs = Splited.objects.select_related('cost__trip').filter(cost_id=cost_id, participant_id=participant_id)
        if not split_qs.exists():
            return {"ok": False, "message": "Split not found"}

        split = split_qs.first()
        trip = split.cost.trip
        rate = split.rate if split.rate else Decimal("1.0")

        if current_currency and current_currency == trip.default_currency:
            # pay_back_value traktujemy jako main currency → przeliczamy split_value
            split_value_calc = pay_back_value / rate
            to_pay_back_value_calc = split.split_value - split_value_calc

            # Bulk update dla jednego splitu
            split_qs.update(
                split_value=F("split_value"),  # pozostaje bez zmian
                pay_back_value=split_value_calc,
                to_pay_back_value=to_pay_back_value_calc,
                payment=Case(
                    When(split_value__lte=split_value_calc, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                ),
                pay_back_value_main_current=pay_back_value,
                to_pay_back_value_main_current=split.split_value_main_current - pay_back_value
            )
        else:
            # standardowa logika: pay_back_value w walucie transakcji
            split_qs.update(
                pay_back_value=pay_back_value,
                to_pay_back_value=F("split_value") - pay_back_value,
                payment=Case(
                    When(split_value__lte=pay_back_value, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )

            # Bulk update main currency z zaokrągleniem
            Splited.objects.filter(cost_id=cost_id).update(
                pay_back_value_main_current=Round(F("pay_back_value") * F("rate"), precision=2),
                to_pay_back_value_main_current=Round(F("to_pay_back_value") * F("rate"), precision=2)
            )

        # ===== Aktualizacja statusu kosztu =====
        unpaid_exists = Splited.objects.filter(cost_id=cost_id, payment=False).exists()
        Cost.objects.filter(cost_id=cost_id).update(payment=not unpaid_exists)

    return {"ok": True, "message": "Payments updated"}


def delete_cost(cost_id):
    """
    Usuwa koszt (cascade splity)
    """
    deleted, _ = Cost.objects.filter(cost_id=cost_id).delete()

    if not deleted:
        return {"ok": False, "message": "Cost not deleted"}

    return {"ok": True, "message": "Cost deleted"}


def delete_split_by_user(cost_id, participant_id):
    """
    Usuwa split użytkownika z kosztu
    """
    deleted, _ = Splited.objects.filter(
        cost_id=cost_id,
        participant_id=participant_id
    ).delete()

    if not deleted:
        return {"ok": False, "message": "Participant is not assigned to this cost"}

    return {"ok": True, "message": "Participant removed from cost"}


# ======================================================
# COST QUERIES
# ======================================================

def get_cost_sum_for_participant_per_trip_bulk(participant_id, trip_id):
    """
    Zwraca sumę kosztów uczestnika dla danego tripu w formacie:
    {
        overviewSum: {"currency": trip.default_currency, "value": total_main_currency},
        splitsByCurrency: [{"currency": "USD", "value": 123.45}, ...]
    }
    Wersja BULK, bez pętli po splitach.
    """
    # Pobranie tripu
    trip = Trip.objects.filter(trip_id=trip_id).first()
    if not trip:
        return {
            "overviewSum": {"currency": None, "value": Decimal("0.00")},
            "splitsByCurrency": []
        }

    # ===== Suma w walucie głównej =====
    total_main = (
        Splited.objects
        .filter(cost__trip_id=trip_id, participant_id=participant_id)
        .aggregate(total=Sum("split_value_main_current"))["total"]
    )
    total_main = (total_main or Decimal("0.00")).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    overviewSum = {"currency": trip.default_currency, "value": total_main}

    # ===== Suma według każdej waluty (BULK) =====
    from django.db.models import DecimalField
    totals_by_currency_qs = (
        Splited.objects
        .filter(cost__trip_id=trip_id, participant_id=participant_id)
        .values(currency=F("cost__payed_currency"))
        .annotate(total=Sum("split_value", output_field=DecimalField(max_digits=20, decimal_places=2)))
    )

    splitsByCurrency = [
        {"currency": item["currency"], "value": item["total"].quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)}
        for item in totals_by_currency_qs
    ]

    return {
        "overviewSum": overviewSum,
        "splitsByCurrency": splitsByCurrency
    }


def get_all_cost_for_participant_per_trip(participant_id, trip_id):
    return (
        Cost.objects
        .filter(trip_id=trip_id)
        .filter(
            Q(splited__participant_id=participant_id) |
            Q(splited__payer_id=participant_id)
        )
        .distinct()
        .order_by("-created_at")
    )


# ======================================================
# PAYBACK / SETTLEMENT
# ======================================================

def get_payback_participant_relation_per_trip_bulk(trip_id, participant_id):
    """
    Oblicza kto komu ile jest winien w walucie głównej i per walutę.
    """
    splits = Splited.objects.filter(
        cost__trip_id=trip_id
    ).select_related("participant", "payer", "cost__trip", "cost")

    # jeśli nie ma splitów, zwróć pustą listę
    if not splits.exists():
        return []

    trip_currency = splits[0].cost.trip.default_currency

    totals = {}
    for s in splits:
        if s.payment:
            continue

        if s.payer.id == participant_id and s.participant.id != participant_id:
            pid = s.participant.id
            sign = 1  # oni mi są winni
        elif s.participant.id == participant_id and s.payer.id != participant_id:
            pid = s.payer.id
            sign = -1  # ja jestem im winien
        else:
            continue

        if pid not in totals:
            totals[pid] = {
                "participant": {
                    "id": pid,
                    "nickname": s.participant.nickname if sign > 0 else s.payer.nickname,
                    "user_id": s.participant.user_id if sign > 0 else s.payer.user_id,
                },
                "total_main": Decimal("0.00"),
                "totals_by_currency": {}
            }

        totals[pid]["total_main"] += sign * (s.to_pay_back_value_main_current or Decimal("0.00"))
        totals[pid]["totals_by_currency"].setdefault(s.cost.payed_currency, Decimal("0.00"))
        totals[pid]["totals_by_currency"][s.cost.payed_currency] += sign * s.to_pay_back_value

    # Zaokrąglanie
    for pid, data in totals.items():
        data["total_main"] = data["total_main"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        for c, v in data["totals_by_currency"].items():
            data["totals_by_currency"][c] = v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # dodajemy walutę tripu dla value_main
        data["trip_currency"] = trip_currency

    return list(totals.values())


def fully_settlement_with_participant(trip_id, participant_id, settlement_participant_id, currency=None):
    """
    Pełne rozliczenie pomiędzy dwoma participantami.
    Jeśli currency=None → rozliczenie po wszystkich kosztach (full settlement)
    Jeśli currency='USD' → rozliczenie tylko dla kosztów w podanej walucie
    """
    with transaction.atomic():
        splits_qs = Splited.objects.filter(
            cost__trip_id=trip_id,
            payment=False
        ).filter(
            Q(payer_id=participant_id, participant_id=settlement_participant_id) |
            Q(payer_id=settlement_participant_id, participant_id=participant_id)
        )

        if currency:
            splits_qs = splits_qs.filter(cost__payed_currency=currency)

        cost_ids = list(splits_qs.values_list("cost_id", flat=True).distinct())

        # ===== Aktualizacja splitów =====
        splits_qs.update(
            to_pay_back_value=Decimal("0.00"),
            to_pay_back_value_main_current=Decimal("0.00"),
            pay_back_value=F("split_value"),
            pay_back_value_main_current=F("split_value_main_current"),
            payment=True
        )

        # ===== Sprawdzenie statusu kosztów =====
        for cost_id in cost_ids:
            all_paid = not Splited.objects.filter(cost_id=cost_id, payment=False).exists()
            Cost.objects.filter(cost_id=cost_id).update(payment=all_paid)

        return {
            "ok": True,
            "message": f"Fully settlement successful {'for currency ' + currency if currency else 'in main currency'}"
        }
