from django.contrib.auth.models import User
from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    MinimumLengthValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
)
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import UserProfile

PASSWORD_VALIDATORS = [

    UserAttributeSimilarityValidator(
        user_attributes=['username', 'email', 'first_name', 'last_name'],
        max_similarity=0.7
    ),
    MinimumLengthValidator(min_length=8),
    CommonPasswordValidator(),
    NumericPasswordValidator()
]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'website', 'reputation', 'created_at', 'updated_at']
        read_only_fields = ['reputation', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'profile', 'date_joined', 'is_active'
        ]   
        read_only_fields = ['date_joined', 'is_active']


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'profile', 'date_joined', 'is_active'
        ]
        read_only_fields = ['id', 'username', 'email', 'date_joined', 'is_active']
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Update User fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        
        # Update Profile fields
        if profile_data:
            profile = instance.profile
            profile.bio = profile_data.get('bio', profile.bio)
            profile.website = profile_data.get('website', profile.website)
            
            # Handle profile picture if provided
            if 'profile_picture' in profile_data:
                profile.profile_picture = profile_data.get('profile_picture')
            
            profile.save()
            
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Manual password validation
        password = attrs['password']
        
        # Create a test user for validation
        user = User(
            username=attrs.get('username', ''),
            email=attrs.get('email', ''),
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', '')
        )
        
        # For email similarity, do an explicit check
        if attrs.get('email'):
            email_parts = attrs['email'].split('@')[0]  # Get username part of email
            if email_parts in password:
                raise serializers.ValidationError({
                    "password": ["Password too similar to email address."]
                })
        
        # Run all validators
        errors = []
        for validator in PASSWORD_VALIDATORS:
            try:
                validator.validate(password, user)
            except ValidationError as e:
                errors.extend(e.messages)
        
        if errors:
            raise serializers.ValidationError({"password": errors})
            
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'website']