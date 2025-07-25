from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, name, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, phone_number=phone_number, **extra_fields)
        user.set_password(password)  # Hashes the main password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, name, phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_email_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=128, blank=True, null=True)  # Increased max_length for hashed OTP
    otp_created_at = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=False)  # Changed to False until verified
    is_staff = models.BooleanField(default=False)
    ROLE_CHOICES = [
        ('company_admin', 'Company Admin'),
        ('client', 'Client'),
        ('staff', 'Staff'),
        ('driver', 'Driver'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='driver')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone_number']

    objects = UserManager()

    def __str__(self):
        return self.email

    def set_otp(self, raw_otp):
        """Set the OTP with hashing."""
        self.otp = make_password(raw_otp)
        self.otp_created_at = timezone.now()

    def check_otp(self, raw_otp):
        """Check the OTP against the stored hashed value."""
        return check_password(raw_otp, self.otp) if self.otp else False