import graphene

# Jeśli używasz jeszcze UserType dla istniejących użytkowników
from tripAppBE.schema.types.user_type import UserType


# -------------------- Cost / Split Types --------------------

class CostType(graphene.ObjectType):
    cost_id = graphene.ID()
    cost_name = graphene.String()
    overall_value = graphene.Decimal()
    overall_value_main_currency = graphene.Decimal()
    payment = graphene.Boolean()
    payed_currency = graphene.String()
    description = graphene.String()


class SplitValueType(graphene.ObjectType):
    value = graphene.Decimal()
    currency = graphene.String()

class SplitType(graphene.ObjectType):
    participant_id = graphene.ID()
    participant_nickname = graphene.String()
    payer_id = graphene.ID()
    payer_nickname = graphene.String()
    payment = graphene.Boolean()

    split_value = graphene.Field(SplitValueType)
    to_pay_back_value = graphene.Field(SplitValueType)
    pay_back_value = graphene.Field(SplitValueType)

    split_value_main = graphene.Field(SplitValueType)
    to_pay_back_value_main = graphene.Field(SplitValueType)
    pay_back_value_main = graphene.Field(SplitValueType)


class CurrencyType(graphene.ObjectType):
    currency = graphene.String(required=True)
    value = graphene.Decimal(required=True)

class CostSumType(graphene.ObjectType):
    overviewSum = graphene.Field(CurrencyType, required=True)
    splitsByCurrency = graphene.List(CurrencyType, required=True)

# -------------------- Input Types --------------------

class SplitInput(graphene.InputObjectType):
    participant_id = graphene.ID(required=True)
    split_value = graphene.Decimal(required=True)


# -------------------- Payback / Balance Types --------------------

class ParticipantPaybackType(graphene.ObjectType):
    participant_id = graphene.ID()
    nickname = graphene.String()
    value_main = graphene.Field(CurrencyType)
    values_by_currency = graphene.List(CurrencyType)

# Resolver
class GetPayback(graphene.ObjectType):
    payback_per_trip = graphene.List(
        ParticipantPaybackType,
        trip_id=graphene.ID(required=True),
    )

