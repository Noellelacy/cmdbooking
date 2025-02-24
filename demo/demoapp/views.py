from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from djreservation.views import ProductReservationView
from .models import MultimediaEquipment, EquipmentUsage, MaintenanceRecord, UserProfile, EquipmentCategory
from .forms import SignUpForm, EquipmentCategoryForm, MultimediaEquipmentForm, MaintenanceRecordForm
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from django.template.context_processors import csrf

class EquipmentReservation(ProductReservationView):
    base_model = MultimediaEquipment
    amount_field = 'quantity_available'
    extra_display_field = ['equipment_type', 'location', 'description']

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    success_url = reverse_lazy('index')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        
        # Check if user is faculty
        try:
            if hasattr(user, 'userprofile') and user.userprofile.is_faculty():
                messages.success(self.request, f'Welcome back, Professor {user.get_full_name() or user.username}!')
                return redirect('faculty_dashboard')
        except:
            pass
            
        messages.success(self.request, f'Welcome back, {user.username}!')
        return response

@ensure_csrf_cookie
def login_view(request):
    # If user is already logged in
    if request.user.is_authenticated:
        try:
            if request.user.userprofile.is_faculty():
                return redirect('faculty_dashboard')
            return redirect('home')
        except:
            pass

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and hasattr(user, 'userprofile') and not user.userprofile.is_faculty():
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html', {'next': request.GET.get('next', '')})

@login_required
@require_http_methods(["POST"])
def logout_view(request):
    # Check if user is faculty or student and store the result before logout
    try:
        is_faculty = hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty()
    except:
        is_faculty = False
    
    # Now logout the user
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    
    # Redirect based on stored user type
    if is_faculty:
        return redirect('faculty_login')
    return redirect('login')

@login_required
@require_http_methods(["POST"])
def faculty_logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('faculty_login')

@ensure_csrf_cookie
def faculty_login(request):
    # If user is already logged in and is faculty, redirect to dashboard
    if request.user.is_authenticated:
        try:
            if request.user.userprofile.is_faculty():
                return redirect('faculty_dashboard')
        except:
            pass

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and hasattr(user, 'userprofile') and user.userprofile.is_faculty():
            login(request, user)
            messages.success(request, f'Welcome back, Professor {user.get_full_name() or user.username}!')
            return redirect('faculty_dashboard')
        else:
            messages.error(request, 'Invalid faculty credentials.')
    
    return render(request, 'faculty/faculty_login.html', {'next': request.GET.get('next', '')})

def faculty_dashboard(request):
    # Check if user is faculty
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Please login as faculty first.')
        return redirect('faculty_login')
        
    context = {
        'total_equipment': MultimediaEquipment.objects.count(),
        'available_equipment': MultimediaEquipment.objects.filter(is_available=True).count(),
        'maintenance_needed': MultimediaEquipment.objects.filter(condition='needs_repair').count(),
    }
    return render(request, 'faculty/dashboard.html', context)

@login_required
def home(request):
    return render(request, 'index.html')

@login_required
def equipment_list(request):
    equipment = MultimediaEquipment.objects.all().select_related(
        'category', 'added_by', 'last_modified_by'
    ).order_by('-created_at')
    
    context = {
        'equipment_list': equipment,
        'is_faculty': request.user.userprofile.is_faculty(),
    }
    return render(request, 'equipment/equipment_list.html', context)

@login_required
def my_reservations(request):
    reservations = EquipmentUsage.objects.filter(user=request.user).order_by('-checkout_time')
    return render(request, 'my_reservations.html', {
        'reservations': reservations
    })

@login_required
def equipment_return(request, usage_id):
    usage = get_object_or_404(EquipmentUsage, id=usage_id, user=request.user)
    if request.method == 'POST':
        usage.return_equipment()
        messages.success(request, 'Equipment returned successfully!')
        return redirect('my_reservations')
    return render(request, 'equipment_return.html', {'usage': usage})

def dashboard(request):
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('login')
    
    total_equipment = MultimediaEquipment.objects.count()
    available_equipment = MultimediaEquipment.objects.filter(is_available=True).count()
    maintenance_needed = MultimediaEquipment.objects.filter(condition='needs_repair').count()
    
    context = {
        'total_equipment': total_equipment,
        'available_equipment': available_equipment,
        'maintenance_needed': maintenance_needed,
    }
    return render(request, 'faculty/dashboard.html', context)

def equipment_list_manage(request):
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('login')
        
    equipment = MultimediaEquipment.objects.all().order_by('name')
    return render(request, 'faculty/equipment_list.html', {'equipment': equipment})

def equipment_create(request):
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('login')
        
    if request.method == 'POST':
        form = MultimediaEquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.save()
            messages.success(request, 'Equipment added successfully!')
            return redirect('equipment_list_manage')
    else:
        form = MultimediaEquipmentForm()
    return render(request, 'faculty/equipment_form.html', {'form': form, 'action': 'Add'})

def equipment_edit(request, pk):
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('login')
        
    equipment = get_object_or_404(MultimediaEquipment, pk=pk)
    if request.method == 'POST':
        form = MultimediaEquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipment updated successfully!')
            return redirect('equipment_list_manage')
    else:
        form = MultimediaEquipmentForm(instance=equipment)
    return render(request, 'faculty/equipment_form.html', {'form': form, 'action': 'Edit'})

def equipment_delete(request, pk):
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('login')
        
    equipment = get_object_or_404(MultimediaEquipment, pk=pk)
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, 'Equipment deleted successfully!')
        return redirect('equipment_list_manage')
    return render(request, 'faculty/equipment_confirm_delete.html', {'equipment': equipment})

def category_list(request):
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('login')
        
    categories = EquipmentCategory.objects.all().order_by('name')
    return render(request, 'faculty/category_list.html', {'categories': categories})

def category_create(request):
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('login')
        
    if request.method == 'POST':
        form = EquipmentCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.save()
            messages.success(request, 'Category added successfully!')
            return redirect('category_list')
    else:
        form = EquipmentCategoryForm()
    return render(request, 'faculty/category_form.html', {'form': form, 'action': 'Add'})

def category_edit(request, pk):
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('login')
        
    category = get_object_or_404(EquipmentCategory, pk=pk)
    if request.method == 'POST':
        form = EquipmentCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_list')
    else:
        form = EquipmentCategoryForm(instance=category)
    return render(request, 'faculty/category_form.html', {'form': form, 'action': 'Edit'})

def category_delete(request, pk):
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('login')
        
    category = get_object_or_404(EquipmentCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('category_list')
    return render(request, 'faculty/category_confirm_delete.html', {'category': category})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        try:
            if form.is_valid():
                user = form.save(commit=False)
                user.save()
                # Create UserProfile
                number = form.cleaned_data.get('number')  
                UserProfile.objects.create(
                    user=user,
                    user_type='student',
                    number=number
                )
                messages.success(request, 'Account created successfully! Please log in.')
                return redirect('login')
            else:
                # Show specific form errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            # If user was created but profile failed, delete the user
            if 'user' in locals():
                user.delete()
    else:
        form = SignUpForm()
    
    return render(request, 'signup.html', {'form': form})

@login_required
@user_passes_test(lambda u: hasattr(u, 'userprofile') and u.userprofile.is_faculty())
def equipment_create(request):
    """View for faculty to create new equipment"""
    if request.method == 'POST':
        form = MultimediaEquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.added_by = request.user
            equipment.last_modified_by = request.user
            equipment.save()
            messages.success(request, 'Equipment added successfully.')
            return redirect('equipment_list')
    else:
        form = MultimediaEquipmentForm()
    
    return render(request, 'equipment/equipment_form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(lambda u: hasattr(u, 'userprofile') and u.userprofile.is_faculty())
def equipment_edit(request, pk):
    """View for faculty to edit equipment"""
    equipment = get_object_or_404(MultimediaEquipment, pk=pk)
    
    if request.method == 'POST':
        form = MultimediaEquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.last_modified_by = request.user
            equipment.save()
            messages.success(request, 'Equipment updated successfully.')
            return redirect('equipment_list')
    else:
        form = MultimediaEquipmentForm(instance=equipment)
    
    context = {
        'form': form,
        'equipment': equipment,
        'action': 'Edit',
        'added_by': equipment.added_by,
        'last_modified_by': equipment.last_modified_by,
        'created_at': equipment.created_at,
        'updated_at': equipment.updated_at,
    }
    return render(request, 'equipment/equipment_form.html', context)

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
