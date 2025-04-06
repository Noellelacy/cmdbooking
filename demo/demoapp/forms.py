from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import (
    MultimediaEquipment, EquipmentCategory, UserProfile,
    MaintenanceRecord, EquipmentUsage
)
from django.utils import timezone

class SignUpForm(UserCreationForm):    
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    username = forms.CharField(
        max_length=150, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    number = forms.CharField(
        max_length=20, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student ID Number'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        help_text='Your password must contain at least 8 characters.'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    user_type = forms.CharField(widget=forms.HiddenInput(), initial='student')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'number', 'password1', 'password2', 'user_type')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def clean_number(self):
        number = self.cleaned_data.get('number')
        if UserProfile.objects.filter(number=number).exists():
            raise forms.ValidationError('This Student ID is already registered.')
        return number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Profile creation is now handled in the view
        return user

class CategoryForm(forms.ModelForm):
    """Form for creating and editing equipment categories."""
    class Meta:
        model = EquipmentCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class MultimediaEquipmentForm(forms.ModelForm):
    class Meta:
        model = MultimediaEquipment
        fields = ['name', 'equipment_type', 'category', 'serial_number', 'inventory_number', 
                 'location', 'description', 'condition', 'requires_training', 'notes',
                 'total_quantity', 'available_quantity', 'min_alert_threshold', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'equipment_type': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'category': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'condition': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'requires_training': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'total_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'required': True}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'required': True}),
            'min_alert_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'required': True}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = EquipmentCategory.objects.all().order_by('name')

class MaintenanceRecordForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = ['equipment', 'issue_description', 'resolution_notes', 'resolved_date']
        widgets = {
            'issue_description': forms.Textarea(attrs={'rows': 3}),
            'resolution_notes': forms.Textarea(attrs={'rows': 3}),
            'resolved_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['equipment'].queryset = MultimediaEquipment.objects.all().order_by('name')

class ReservationApprovalForm(forms.ModelForm):
    class Meta:
        model = EquipmentUsage
        fields = ['approval_notes']
        widgets = {
            'approval_notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def save(self, commit=True, approved_by=None):
        instance = super().save(commit=False)
        if approved_by:
            instance.approved_by = approved_by
            instance.approved_at = timezone.now()
        if commit:
            instance.save()
        return instance

class EquipmentPhotoUploadForm(forms.ModelForm):
    photo_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Add any notes about the equipment condition'}),
        required=False
    )
    
    class Meta:
        model = EquipmentUsage
        fields = ['equipment_photo', 'photo_notes']
        widgets = {
            'equipment_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.status = 'photo_submitted'
        instance.photo_uploaded_at = timezone.now()
        if commit:
            instance.save()
        return instance
