from django.db import transaction

from tripAppBE.models import Cost, Splited
from django.db.models import Q, Sum, F, Exists, OuterRef
from decimal import Decimal, ROUND_HALF_UP


def add_cost(trip_id, title, payer_id, overall_value, split_object_list):
    try:
        with transaction.atomic():
            payment_flag = (
                len(split_object_list) == 1
                and split_object_list[0].user_id == payer_id
            )

            cost = Cost.objects.create(
                trip_id=trip_id,
                cost_name=title,
                overall_value=overall_value,
                payment=payment_flag
            )

            splits = [
                Splited(
                    cost=cost,
                    user_id=obj.user_id,
                    payer_id=payer_id,
                    payment=(payer_id == obj.user_id),
                    split_value=obj.split_value,
                    pay_back_value=(obj.split_value if payer_id == obj.user_id else 0),
                    to_pay_back_value=(0 if payer_id == obj.user_id else obj.split_value)
                )
                for obj in split_object_list
            ]
            Splited.objects.bulk_create(splits)

            return {"ok": True, "cost": cost, "splits": splits, "message": "Cost successfully created"}

    except Exception as e:
        return {"ok": False, "cost": None, "splits": None, "message": str(e)}


def update_cost(cost_id, **fields):
    try:
        updated = Cost.objects.filter(cost_id=cost_id).update(**fields)

        if not updated:
            return {"ok": False, "message": "Cost not found"}

        return {"ok": True, "message": "Cost updated"}

    except Exception as e:
        return {"ok": False, "message": str(e)}


def update_payment(cost_id, user_id, pay_back_value):
    pay_back_value = Decimal(pay_back_value)
    with transaction.atomic():
        try:
            split_obj = Splited.objects.select_for_update().get(cost_id=cost_id, user_id=user_id)

            to_pay_back = split_obj.split_value - pay_back_value
            if abs(to_pay_back) < 1:
                to_pay_back = 0

            split_obj.pay_back_value = pay_back_value
            split_obj.to_pay_back_value = to_pay_back
            split_obj.payment = abs(split_obj.split_value - pay_back_value) < 0.99
            split_obj.save(update_fields=['pay_back_value', 'to_pay_back_value', 'payment'])

            all_paid = not Splited.objects.filter(cost_id=cost_id, payment=False).exists()
            Cost.objects.filter(cost_id=cost_id).update(payment=all_paid)

            return {"ok": True, "message": "Payment updated"}

        except Splited.DoesNotExist:
            return {"ok": False, "message": "Split not found"}
        except Exception as e:
            return {"ok": False, "message": str(e)}


def delete_cost(cost_id):
    try:
        deleted, _ = Cost.objects.filter(cost_id=cost_id).delete()

        if not deleted:
            return {"ok": False, "message": "Cost dont deleted"}

        return {"ok": True, "message": "Cost deleted"}

    except Exception as e:
        return {"ok": False, "message": str(e)}


def delete_split_by_user(cost_id, user_id):
    try:
        deleted, _ = Splited.objects.filter(cost__cost_id=cost_id, user_id=user_id).delete()

        if not deleted:
            return {"ok": False, "message": "User is not assigned to this cost"}

        return {"ok": True, "message": "User removed from cost"}

    except Exception as e:
        return {"ok": False, "message": str(e)}


def get_cost_sum_for_user_per_trip(user, trip_id):
    try:
        total = (Splited.objects.filter(user=user, cost__trip_id=trip_id)
                 .aggregate(total_split=Sum('split_value')))

        return total["total_split"].quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

    except Exception as e:
        return {"total": None, "Message": e}


def get_all_cost_for_user_per_trip(user, trip_id):
    try:
        costs = (Cost.objects.filter(trip_id=trip_id)
                 .filter(Q(splited__user=user) | Q(splited__payer=user))
                 .order_by("-created_at")
                 )

        seen = set()
        unique_costs = []
        for c in costs:
            if c.cost_id not in seen:
                unique_costs.append(c)
                seen.add(c.cost_id)

        return unique_costs

    except Exception as e:
        return {"Message": str(e)}


def get_split_info_per_cost(cost_id):
    try:
        return Splited.objects.filter(cost__cost_id=cost_id)

    except Exception as e:
        return {"Message": e}



def get_payback_user_relation_per_trip(trip_id, user_id):
    list1 = (
        Splited.objects.filter(cost__trip__trip_id=trip_id, payment=False, payer_id=user_id)
        .exclude(user_id=user_id)
        .select_related('user')
        .values('user_id', 'user__username')
        .annotate(total=Sum('split_value'))
    )

    list2 = (
        Splited.objects.filter(cost__trip__trip_id=trip_id, payment=False, user_id=user_id)
        .exclude(payer_id=user_id)
        .select_related('payer')
        .values('payer_id', 'payer__username')
        .annotate(total=Sum('split_value'))
    )

    list2_dict = {item['payer_id']: item for item in list2}

    result = []

    for item in list1:
        uid = item['user_id']
        value = item['total']
        if uid in list2_dict:
            value -= list2_dict[uid]['total']
            del list2_dict[uid]
        value = Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        result.append({
            'user': {
                'id': uid,
                'username': item['user__username']
            },
            'value': value
        })

    for uid, item in list2_dict.items():
        value = Decimal(-item['total']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        result.append({
            'user': {
                'id': uid,
                'username': item['payer__username']
            },
            'value': value
        })

    return result


def fully_settlement_with_user(trip_id, user_id, settlement_user_id):
    with transaction.atomic():
        try:
            splits_qs = Splited.objects.filter(
                cost__trip__trip_id=trip_id,
                payment=False
            ).filter(
                Q(payer_id=user_id, user_id=settlement_user_id) |
                Q(payer_id=settlement_user_id, user_id=user_id)
            )

            cost_ids = list(
                splits_qs.values_list("cost_id", flat=True).distinct()
            )

            splits_qs.update(
                payment=True,
                to_pay_back_value=Decimal("0.00"),
                pay_back_value=F("split_value")
            )

            unpaid_cost_ids = set(
                Splited.objects.filter(
                    cost_id__in=cost_ids,
                    payment=False
                ).values_list("cost_id", flat=True)
            )

            Cost.objects.filter(cost_id__in=cost_ids).update(payment=True)
            Cost.objects.filter(cost_id__in=unpaid_cost_ids).update(payment=False)

            return {"ok": True, "message": "Fully settlement successful"}

        except Exception as e:
            return {"ok": False, "message": str(e)}







