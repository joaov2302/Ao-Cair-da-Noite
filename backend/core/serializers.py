from rest_framework import serializers
from .rules import ATTRIBUTES, CLASSES, ARCHETYPES


class AttributesSerializer(serializers.Serializer):
    FOR = serializers.IntegerField(min_value=0, max_value=3, allow_null=True, required=False)
    AGI = serializers.IntegerField(min_value=0, max_value=3, allow_null=True, required=False)
    VIG = serializers.IntegerField(min_value=0, max_value=3, allow_null=True, required=False)
    PRE = serializers.IntegerField(min_value=0, max_value=3, allow_null=True, required=False)
    INT = serializers.IntegerField(min_value=0, max_value=3, allow_null=True, required=False)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or any(k not in ATTRIBUTES for k in data):
            raise serializers.ValidationError({'non_field_errors': ['Atributos inválidos.']})
        if any(v is not None and type(v) is not int for v in data.values()):
            raise serializers.ValidationError({'non_field_errors': ['Use valores inteiros ou null, sem conversão implícita.']})
        return super().to_internal_value(data)


class CharacterDataSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, allow_blank=True, required=False, default='')
    concept = serializers.CharField(max_length=4000, allow_blank=True, required=False, default='')
    race = serializers.CharField(max_length=120, allow_blank=True, required=False, default='')
    classId = serializers.ChoiceField(choices=[''] + [c['id'] for c in CLASSES], required=False, default='')
    archetypeId = serializers.ChoiceField(choices=[''] + [a['id'] for a in ARCHETYPES], required=False, default='')
    attributes = AttributesSerializer(required=False, default=dict)
    skills = serializers.CharField(max_length=8000, allow_blank=True, required=False, default='')
    equipment = serializers.CharField(max_length=8000, allow_blank=True, required=False, default='')
    techniques = serializers.CharField(max_length=8000, allow_blank=True, required=False, default='')
    techniqueKind = serializers.ChoiceField(choices=['', 'respiracao', 'sanguinea', 'outra'], required=False, default='')
    uniqueAbility = serializers.CharField(max_length=4000, allow_blank=True, required=False, default='')
    story = serializers.CharField(max_length=12000, allow_blank=True, required=False, default='')
    assetId = serializers.IntegerField(allow_null=True, required=False, default=None)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError({'non_field_errors': ['Há campos desconhecidos ou protegidos na ficha.']})
        return super().to_internal_value(data)
