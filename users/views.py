from django.conf import settings
from rest_framework.views import APIView
from .serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import User
import jwt, datetime
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated


class CustomAuthentication(BasicAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get("jwt")

        if not token:
            raise AuthenticationFailed("Unauthenticated")

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated")

        user = User.objects.filter(id=payload["id"]).first()
        if user is None:
            raise AuthenticationFailed("Unauthenticated")

        if datetime.datetime.utcnow() > datetime.datetime.fromtimestamp(
            int(payload["exp"])
        ):
            raise AuthenticationFailed("Token expired")

        return (user, None)


# Create your views here.
class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class LoginView(APIView):
    def post(self, request):
        email = request.data["email"]
        password = request.data["password"]

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed("User not forund!")

        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect Password")

        payload = {
            "id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
            "iat": datetime.datetime.utcnow(),
        }

        token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

        response = Response()

        response.set_cookie(key="jwt", value=token, httponly=True, samesite="None")

        response.data = {"jwt": token}

        return response


class UserView(APIView):
    authentication_classes = [SessionAuthentication, CustomAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response(serializer.data)


class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie("jwt", samesite="None")
        response.data = {"message": "success"}

        return response
