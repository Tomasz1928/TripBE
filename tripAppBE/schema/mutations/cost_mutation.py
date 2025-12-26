import graphene
from graphql import GraphQLError

from tripAppBE.schema.types.cost_type import SplitInput
from tripAppBE.services.cost_service import (
    add_cost,
    update_cost,
    update_payment,
    delete_cost,
    delete_split_by_user,
    fully_settlement_with_participant
)
from tripAppBE.models import TripParticipant


# --- Helper to get current participant in a trip ---
def get_current_participant(user, trip_id):
    try:
        return TripParticipant.objects.get(trip_id=trip_id, user=user)
    except TripParticipant.DoesNotExist:
        raise GraphQLError("User is not a participant in this trip.")


# -------------------- Mutations --------------------

class CreateCost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        payer_id = graphene.ID(required=True)
        trip_id = graphene.ID(required=True)
        value = graphene.Decimal(required=True)
        currency = graphene.String(required=True)
        description = graphene.String(required=False)
        split_object_list = graphene.List(SplitInput, required=True)

    ok = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    cost_id = graphene.ID(required=True)

    def mutate(self, info, title, payer_id, trip_id, value, currency, split_object_list, description=""):
        result = add_cost(
            trip_id=trip_id,
            title=title,
            payer_participant_id=payer_id,
            overall_value=value,
            split_object_list=split_object_list,
            currency=currency,
            description=description
        )
        return CreateCost(
            ok=result["ok"],
            message=result.get("message"),
            cost_id=result["cost"].cost_id if result["ok"] else None
        )


class UpdateCost(graphene.Mutation):
    class Arguments:
        cost_id = graphene.ID(required=True)
        title = graphene.String()
        value = graphene.Decimal()
        payer_id = graphene.ID()  # participant ID

    ok = graphene.Boolean(required=True)
    message = graphene.String(required=True)

    def mutate(self, info, cost_id, title=None, value=None, payer_id=None):
        fields = {}
        if title is not None:
            fields["cost_name"] = title
        if value is not None:
            fields["overall_value"] = value
        if payer_id is not None:
            fields["payer_id"] = payer_id

        result = update_cost(cost_id, **fields)
        return UpdateCost(ok=result["ok"], message=result["message"])


class UpdatePayment(graphene.Mutation):
    class Arguments:
        cost_id = graphene.ID(required=True)
        participant_id = graphene.ID(required=True)
        pay_back_value = graphene.Float(required=False)
        currency = graphene.String(required=True)

    ok = graphene.Boolean(required=True)
    message = graphene.String(required=True)

    def mutate(self, info, cost_id, participant_id, currency, pay_back_value=None):
        result = update_payment(cost_id, participant_id, pay_back_value, currency)
        return UpdatePayment(ok=result["ok"], message=result["message"])


class DeleteCost(graphene.Mutation):
    class Arguments:
        cost_id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)
    message = graphene.String(required=True)

    def mutate(self, info, cost_id):
        result = delete_cost(cost_id)
        return DeleteCost(ok=result["ok"], message=result["message"])


class DeleteParticipantSplits(graphene.Mutation):
    class Arguments:
        cost_id = graphene.ID(required=True)
        participant_id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)
    message = graphene.String(required=True)

    def mutate(self, info, cost_id, participant_id):
        result = delete_split_by_user(cost_id, participant_id)
        return DeleteParticipantSplits(ok=result["ok"], message=result["message"])


class FullySettlement(graphene.Mutation):
    class Arguments:
        trip_id = graphene.ID(required=True)
        settlement_participant_id = graphene.ID(required=True)
        currency = graphene.String(required=False)

    ok = graphene.Boolean(required=True)
    message = graphene.String(required=True)

    def mutate(self, info, trip_id, settlement_participant_id, currency=None):
        user = info.context.user
        participant = get_current_participant(user, trip_id)

        result = fully_settlement_with_participant(
            trip_id=trip_id,
            participant_id=participant.id,
            settlement_participant_id=settlement_participant_id,
            currency=currency
        )
        return FullySettlement(ok=result["ok"], message=result["message"])
