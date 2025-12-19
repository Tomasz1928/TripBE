import graphene

from tripAppBE.services.auth_service import session


class SessionType(graphene.ObjectType):
    is_authenticated = graphene.Boolean()

    def resolve_is_authenticated(self, info):
        return session(info.context)


class AuthQuery(graphene.ObjectType):
    session = graphene.Field(SessionType)

    def resolve_session(self, info):
        return SessionType()
