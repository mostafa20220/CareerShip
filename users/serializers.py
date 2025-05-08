from users.models import User
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['first_name','last_name','email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }



class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
            token.blacklist()  # Blacklist the refresh token
        except Exception as e:
            raise serializers.ValidationError("Invalid or expired refresh token.")

        return value

    def create(self, validated_data):
        return validated_data

class RetrieveProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [ 'id' , 'first_name','last_name','email','user_type','is_premium','phone','avatar']

class UpdateProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['first_name','last_name','phone','avatar', ]

class RemoveUserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    
    def validate(self, data):
        user = User.objects.filter(email=data.get('email'),id=data.get("id")).first()
        if not user:
            raise serializers.ValidationError("User with this email and id does not exist.")
        data['user'] = user
        return data

    def create(self, validated_data):
        user = validated_data.get('user')
        user.is_active = False
        user.save()
        return user
