from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Q, Sum, F, Case, When, Value, BooleanField


from tripAppBE.models import Cost, Splited


# ======================================================
# COST MANAGEMENT
# ======================================================

def add_cost(trip_id, title, payer_participant_id, overall_value, split_object_list):
    """
    Dodaje koszt + splity (bulk)
    """
    payment_flag = (
        len(split_object_list) == 1
        and split_object_list[0].participant_id == payer_participant_id
    )

    with transaction.atomic():
        cost = Cost.objects.create(
            trip_id=trip_id,
            cost_name=title,
            overall_value=overall_value,
            payment=payment_flag
        )

        splits = [
            Splited(
                cost_id=cost.cost_id,
                participant_id=obj.participant_id,
                payer_id=payer_participant_id,
                payment=(payer_participant_id == obj.participant_id),
                split_value=obj.split_value,
                pay_back_value=(
                    obj.split_value if payer_participant_id == obj.participant_id else Decimal("0.00")
                ),
                to_pay_back_value=(
                    Decimal("0.00") if payer_participant_id == obj.participant_id else obj.split_value
                )
            )
            for obj in split_object_list
        ]

        Splited.objects.bulk_create(splits)

        return {"ok": True, "cost": cost}


def update_cost(cost_id, **fields):
    """
    Aktualizacja kosztu (bez SELECT)
    """
    updated = Cost.objects.filter(cost_id=cost_id).update(**fields)

    if not updated:
        return {"ok": False, "message": "Cost not found"}

    return {"ok": True, "message": "Cost updated"}


def update_payment(cost_id, participant_id, pay_back_value):
    """
    Aktualizacja płatności splitu + status kosztu
    """
    pay_back_value = Decimal(pay_back_value)

    with transaction.atomic():
        updated = (
            Splited.objects
            .filter(cost_id=cost_id, participant_id=participant_id)
            .update(
                pay_back_value=pay_back_value,
                to_pay_back_value=F("split_value") - pay_back_value,
                payment=Case(
                    When(
                        split_value__lte=pay_back_value,
                        then=Value(True)
                    ),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )
        )

        if not updated:
            return {"ok": False, "message": "Split not found"}

        unpaid_exists = Splited.objects.filter(
            cost_id=cost_id,
            payment=False
        ).exists()

        Cost.objects.filter(cost_id=cost_id).update(payment=not unpaid_exists)

        return {"ok": True, "message": "Payments update"}


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

def get_cost_sum_for_participant_per_trip(participant_id, trip_id):
    total = (
        Splited.objects
        .filter(cost__trip_id=trip_id, participant_id=participant_id)
        .aggregate(total=Sum("split_value"))
        ["total"]
    )

    return (total or Decimal("0.00")).quantize(
        Decimal("0.00"),
        rounding=ROUND_HALF_UP
    )


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


def get_split_info_per_cost(cost_id):
    return Splited.objects.filter(cost_id=cost_id)


# ======================================================
# PAYBACK / SETTLEMENT
# ======================================================

def get_payback_participant_relation_per_trip(trip_id, participant_id):
    """
    Oblicza relacje kto komu ile jest winien
    """
    they_owe_me = (
        Splited.objects
        .filter(cost__trip_id=trip_id, payment=False, payer_id=participant_id)
        .exclude(participant_id=participant_id)
        .values(
            "participant_id",
            "participant__nickname",
            "participant__user_id"
        )
        .annotate(total=Sum("split_value"))
    )

    i_owe_them = (
        Splited.objects
        .filter(cost__trip_id=trip_id, payment=False, participant_id=participant_id)
        .exclude(payer_id=participant_id)
        .values(
            "payer_id",
            "payer__nickname",
            "payer__user_id"
        )
        .annotate(total=Sum("split_value"))
    )

    owe_dict = {item["payer_id"]: item for item in i_owe_them}
    result = []

    for item in they_owe_me:
        pid = item["participant_id"]
        value = item["total"]

        if pid in owe_dict:
            value -= owe_dict[pid]["total"]
            del owe_dict[pid]

        value = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if value != 0:
            result.append({
                "participant": {
                    "id": pid,
                    "nickname": item["participant__nickname"],
                    "user_id": item["participant__user_id"]
                },
                "value": value
            })

    for pid, item in owe_dict.items():
        value = Decimal(-item["total"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if value != 0:
            result.append({
                "participant": {
                    "id": pid,
                    "nickname": item["payer__nickname"],
                    "user_id": item["payer__user_id"]
                },
                "value": value
            })

    return result


def fully_settlement_with_participant(trip_id, participant_id, settlement_participant_id):
    """
    Pełne rozliczenie pomiędzy dwoma participantami
    """
    with transaction.atomic():
        splits_qs = Splited.objects.filter(
            cost__trip_id=trip_id,
            payment=False
        ).filter(
            Q(payer_id=participant_id, participant_id=settlement_participant_id) |
            Q(payer_id=settlement_participant_id, participant_id=participant_id)
        )

        cost_ids = list(
            splits_qs.values_list("cost_id", flat=True).distinct()
        )

        splits_qs.update(
            payment=True,
            to_pay_back_value=Decimal("0.00"),
            pay_back_value=F("split_value")
        )

        unpaid_cost_ids = (
            Splited.objects
            .filter(cost_id__in=cost_ids, payment=False)
            .values_list("cost_id", flat=True)
        )

        Cost.objects.filter(cost_id__in=cost_ids).update(payment=True)
        Cost.objects.filter(cost_id__in=unpaid_cost_ids).update(payment=False)

        return {"ok": True, "message": "Fully settlement successful"}
