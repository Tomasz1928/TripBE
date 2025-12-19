import graphene

from tripAppBE.services.auth_service import register_user, login_user, logout


class RegisterUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    user_id = graphene.Int()

    def mutate(self, info, username, password):
        user = register_user(username, password)
        if user is None:
            return RegisterUser(ok=False, user_id=None)

        return RegisterUser(ok=True, user_id=user.id)

class LoginUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, username, password):
        login_user(info.context, username, password)
        return LoginUser(ok=True)


class LogoutUser(graphene.Mutation):
    ok = graphene.Boolean()

    def mutate(self, info):
        request = info.context
        logout(request)
        return LogoutUser(ok=True)
