import graphene

from tripAppBE.schema.types.cost_type import CostType, SplitType, CostSumType, ParticipantPaybackType, \
    SplitValueType, CurrencyType
from tripAppBE.services.cost_service import (
    get_all_cost_for_participant_per_trip,
     get_cost_sum_for_participant_per_trip_bulk,
    get_payback_participant_relation_per_trip_bulk
)
from tripAppBE.models import TripParticipant, Splited
from graphql import GraphQLError


# --- Helper to get current participant in a trip ---
def get_current_participant(user, trip_id):
    try:
        return TripParticipant.objects.get(trip_id=trip_id, user=user)
    except TripParticipant.DoesNotExist:
        raise GraphQLError("User is not a participant in this trip.")


# -------------------- Queries --------------------

class GetCostsSumPerTrip(graphene.ObjectType):
    cost_sum = graphene.Field(
        CostSumType,
        trip_id=graphene.ID(required=True),
        required=True
    )

    def resolve_cost_sum(self, info, trip_id):
        participant = get_current_participant(info.context.user, trip_id)
        result = get_cost_sum_for_participant_per_trip_bulk(participant, trip_id)

        overview = CurrencyType(
            currency=result["overviewSum"]["currency"],
            value=result["overviewSum"]["value"]
        )

        splits = [
            CurrencyType(currency=item["currency"], value=item["value"])
            for item in result["splitsByCurrency"]
        ]

        return CostSumType(
            overviewSum=overview,
            splitsByCurrency=splits
        )


class GetCostsPerTrip(graphene.ObjectType):
    costs_list = graphene.List(
        CostType,
        trip_id=graphene.ID(required=True),
        required=True
    )

    def resolve_costs_list(self, info, trip_id):
        participant = get_current_participant(info.context.user, trip_id)
        return get_all_cost_for_participant_per_trip(participant.id, trip_id)


class GetSplitsInfo(graphene.ObjectType):
    splits = graphene.List(
        SplitType,
        cost_id=graphene.ID(required=True),
        required=True
    )

    def resolve_splits(self, info, cost_id):
        splits = Splited.objects.select_related("participant", "payer", "cost__trip").filter(cost_id=cost_id)

        result = []
        for s in splits:
            same_currency = s.cost.payed_currency == s.cost.trip.default_currency

            split_value = SplitValueType(value=s.split_value, currency=s.cost.payed_currency)
            to_pay_back_value = SplitValueType(value=s.to_pay_back_value, currency=s.cost.payed_currency)
            pay_back_value = SplitValueType(value=s.pay_back_value, currency=s.cost.payed_currency)

            split_value_main = SplitValueType(value=s.split_value_main_current, currency=s.cost.trip.default_currency)
            to_pay_back_value_main = SplitValueType(value=s.to_pay_back_value_main_current, currency=s.cost.trip.default_currency)
            pay_back_value_main = SplitValueType(value=s.pay_back_value_main_current, currency=s.cost.trip.default_currency)

            result.append(
                SplitType(
                    participant_id=s.participant.id,
                    participant_nickname=s.participant.nickname,
                    payer_id=s.payer.id,
                    payer_nickname=s.payer.nickname,
                    payment=s.payment,

                    split_value=split_value,
                    to_pay_back_value=to_pay_back_value,
                    pay_back_value=pay_back_value,

                    split_value_main=split_value_main,
                    to_pay_back_value_main=to_pay_back_value_main,
                    pay_back_value_main=pay_back_value_main,
                )
            )
        return result


class GetPayback(graphene.ObjectType):
    payback_per_trip = graphene.List(
        ParticipantPaybackType,
        trip_id=graphene.ID(required=True),
        required=True
    )

    def resolve_payback_per_trip(self, info, trip_id):
        participant = get_current_participant(info.context.user, trip_id)
        paybacks = get_payback_participant_relation_per_trip_bulk(trip_id, participant.id)

        result = []
        for pb in paybacks:
            value_main = CurrencyType(
                currency=pb["trip_currency"],
                value=pb["total_main"]
            )
            values_by_currency = [
                CurrencyType(currency=c, value=v)
                for c, v in pb["totals_by_currency"].items()
            ]

            result.append(
                ParticipantPaybackType(
                    participant_id=pb["participant"]["id"],
                    nickname=pb["participant"]["nickname"],
                    value_main=value_main,
                    values_by_currency=values_by_currency
                )
            )
        return result
