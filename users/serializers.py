from rest_framework import serializers
from .models import User


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email and password:
            user = User.objects.filter(email=email).first()

            if user is None:
                msg = "User not found"
                raise serializers.ValidationError(msg, code="authorization")

            if not user.check_password(password):
                msg = "Incorrect Password"
                raise serializers.ValidationError(msg, code="authorization")
        else:
            msg = 'Must include "email" and "password".'
            raise serializers.ValidationError(msg, code="authorization")

        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", "")
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
