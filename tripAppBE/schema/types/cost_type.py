import graphene

# Jeśli używasz jeszcze UserType dla istniejących użytkowników
from tripAppBE.schema.types.user_type import UserType


# -------------------- Cost / Split Types --------------------

class CostType(graphene.ObjectType):
    cost_id = graphene.ID()
    cost_name = graphene.String()
    overall_value = graphene.Decimal()
    payment = graphene.Boolean()


class SplitType(graphene.ObjectType):
    payment = graphene.Boolean()
    split_value = graphene.Decimal()
    to_pay_back_value = graphene.Decimal()
    pay_back_value = graphene.Decimal()

    # Participant zamiast User
    participant_id = graphene.ID()
    participant_nickname = graphene.String()

    payer_id = graphene.ID()
    payer_nickname = graphene.String()


class CostSumType(graphene.ObjectType):
    cost_sum = graphene.Decimal()


# -------------------- Input Types --------------------

class SplitInput(graphene.InputObjectType):
    participant_id = graphene.ID(required=True)
    split_value = graphene.Decimal(required=True)


# -------------------- Payback / Balance Types --------------------

class ParticipantPaybackType(graphene.ObjectType):
    participant_id = graphene.ID()
    nickname = graphene.String()
    value = graphene.Decimal()
