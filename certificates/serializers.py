from rest_framework import serializers
from .models import Certificate

class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['id', 'project', 'user', 'no', 'created_at']
        read_only_fields = ['id', 'no', 'created_at']

