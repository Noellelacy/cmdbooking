from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from djreservation.views import ProductReservationView
from .models import MultimediaEquipment, EquipmentUsage, MaintenanceRecord, UserProfile, EquipmentCategory, CartItem
from .forms import SignUpForm, EquipmentCategoryForm, MultimediaEquipmentForm, MaintenanceRecordForm, ReservationApprovalForm, CategoryForm
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from django.template.context_processors import csrf
from django.db.models import Count
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import timedelta
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django import forms
import datetime
from django.http import JsonResponse
from django.db import transaction

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    success_url = reverse_lazy('home')  # Default redirect for students
    
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
    """Student login view"""
    # If user is already logged in
    if request.user.is_authenticated:
        try:
            if request.user.userprofile.is_faculty():
                return redirect('faculty_dashboard')
            return redirect('dashboard')
        except:
            pass

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is faculty
            try:
                if user.userprofile.is_faculty():
                    messages.error(request, 'Please use the faculty login page.')
                    return redirect('faculty_login')
            except:
                pass
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            
            # Redirect to next URL if provided and safe
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html', {'next': next_url})

@ensure_csrf_cookie
def faculty_login(request):
    """Faculty login view"""
    if request.user.is_authenticated:
        try:
            if request.user.userprofile.is_faculty():
                return redirect('faculty_dashboard')
            messages.error(request, 'You do not have faculty privileges.')
            return redirect('login')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('faculty_login')

    context = {
        'next': request.GET.get('next', '')
    }
    context.update(csrf(request))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'auth/faculty_login.html', context)

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            try:
                profile = user.userprofile
                if not profile.is_faculty():
                    messages.error(request, 'You do not have faculty privileges. Please use the student login.')
                    return redirect('login')
                
                login(request, user)
                messages.success(request, f'Welcome back, Professor {user.get_full_name() or user.username}!')
                next_url = request.POST.get('next', '')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('faculty_dashboard')  # Redirect to faculty_dashboard
            except UserProfile.DoesNotExist:
                messages.error(request, 'Faculty profile not found. Please contact the administrator.')
                return render(request, 'auth/faculty_login.html', context)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/faculty_login.html', context)

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

@login_required
def faculty_dashboard(request):
    """Dashboard view for faculty members."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')

    # Get current date for comparisons
    current_date = timezone.now()

    # Get recent reservations
    recent_reservations = EquipmentUsage.objects.filter(
        Q(status='pending') |
        Q(status='approved') |
        Q(status='checked_out')
    ).select_related('user', 'equipment').order_by('-checkout_time')[:5]

    # Get equipment status counts
    total_equipment = MultimediaEquipment.objects.count()
    available_equipment = MultimediaEquipment.objects.filter(is_available=True).count()
    maintenance_needed = MultimediaEquipment.objects.filter(condition='needs_repair').count()

    # Get reservation statistics
    active_reservations = EquipmentUsage.objects.filter(
        Q(status='approved') | Q(status='checked_out')
    ).count()
    pending_reservations = EquipmentUsage.objects.filter(status='pending').count()

    # Get equipment needing maintenance
    maintenance_alerts = MultimediaEquipment.objects.filter(
        condition='needs_repair'
    ).select_related('category')[:5]

    # Get all equipment for maintenance modal
    all_equipment = MultimediaEquipment.objects.all()

    context = {
        'total_equipment': total_equipment,
        'available_equipment': available_equipment,
        'maintenance_needed': maintenance_needed,
        'active_reservations': active_reservations,
        'pending_reservations': pending_reservations,
        'recent_reservations': recent_reservations,
        'maintenance_alerts': maintenance_alerts,
        'all_equipment': all_equipment,
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
    """View student's equipment reservations."""
    reservations = EquipmentUsage.objects.filter(
        user=request.user
    ).select_related(
        'equipment',
        'equipment__category'
    ).order_by('-checkout_time')
    
    return render(request, 'student/reservations/list.html', {
        'reservations': reservations,
        'active_tab': 'reservations'
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

@login_required
@user_passes_test(lambda u: hasattr(u, 'userprofile') and u.userprofile.is_faculty())
def equipment_create(request):
    """View for faculty to create new equipment"""
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

@login_required
@user_passes_test(lambda u: hasattr(u, 'userprofile') and u.userprofile.is_faculty())
def equipment_edit(request, pk):
    """View for faculty to edit equipment"""
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

@login_required
@user_passes_test(lambda u: hasattr(u, 'userprofile') and u.userprofile.is_faculty())
def equipment_delete(request, pk):
    """View for faculty to delete equipment"""
    equipment = get_object_or_404(MultimediaEquipment, pk=pk)
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, 'Equipment deleted successfully!')
        return redirect('equipment_list_manage')
    return render(request, 'faculty/equipment_confirm_delete.html', {'equipment': equipment})

@login_required
def category_list(request):
    """Display list of equipment categories."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')
    
    categories = EquipmentCategory.objects.all().order_by('name')
    return render(request, 'faculty/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    """Create a new equipment category."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            messages.success(request, 'Category created successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'faculty/category_form.html', {'form': form, 'action': 'Create'})

@login_required
def category_edit(request, pk):
    """Edit an existing equipment category."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')
    
    category = get_object_or_404(EquipmentCategory, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'faculty/category_form.html', {'form': form, 'action': 'Edit'})

@login_required
def category_delete(request, pk):
    """Delete an equipment category."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')
    
    category = get_object_or_404(EquipmentCategory, pk=pk)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('category_list')
    
    return render(request, 'faculty/category_confirm_delete.html', {'category': category})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                # Save the user first - the signal should create the profile
                user = form.save()
                
                # Ensure the profile exists before updating it
                with transaction.atomic():
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    profile.number = form.cleaned_data.get('number')
                    profile.user_type = 'student'
                    profile.save()

                messages.success(request, 'Account created successfully! Please log in with your credentials.')
                return redirect('login')
            except forms.ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {str(e)}")
                print(f"Signup error: {str(e)}")  # Debugging
                if user and user.pk:
                    user.delete()  # Cleanup if user creation failed
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, f"{field.label}: {error}")
    else:
        form = SignUpForm()

    return render(request, 'auth/signup.html', {'form': form})

@login_required
@require_http_methods(["POST"])
def report_maintenance(request):
    """Handle maintenance issue reports from faculty."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can report maintenance issues.')
        return redirect('faculty_login')
    
    equipment_id = request.POST.get('equipment')
    issue_description = request.POST.get('issue_description')
    
    try:
        equipment = MultimediaEquipment.objects.get(id=equipment_id)
        
        # Create maintenance record
        MaintenanceRecord.objects.create(
            equipment=equipment,
            reported_by=request.user,
            issue_description=issue_description
        )
        
        # Update equipment condition
        equipment.condition = 'needs_repair'
        equipment.save()
        
        messages.success(request, 'Maintenance issue reported successfully.')
    except MultimediaEquipment.DoesNotExist:
        messages.error(request, 'Equipment not found.')
    except Exception as e:
        messages.error(request, f'Error reporting maintenance issue: {str(e)}')
    
    return redirect('faculty_dashboard')

@login_required
def manage_reservations(request):
    """View for faculty to manage equipment reservations."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')
    
    # Get filter parameters
    status = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    reservations = EquipmentUsage.objects.all().order_by('-checkout_time')
    
    # Apply filters
    if status:
        reservations = reservations.filter(status=status)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            reservations = reservations.filter(checkout_time__date__gte=start_date)
        except ValueError:
            messages.warning(request, 'Invalid start date format.')
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            reservations = reservations.filter(checkout_time__date__lte=end_date)
        except ValueError:
            messages.warning(request, 'Invalid end date format.')
    
    if search_query:
        reservations = reservations.filter(
            Q(equipment__name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(course_code__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(reservations, 10)
    page = request.GET.get('page')
    try:
        reservations = paginator.page(page)
    except PageNotAnInteger:
        reservations = paginator.page(1)
    except EmptyPage:
        reservations = paginator.page(paginator.num_pages)
    
    context = {
        'reservations': reservations,
        'status_choices': EquipmentUsage.STATUS_CHOICES,
        'current_status': status,
        'start_date': start_date,
        'end_date': end_date,
        'search_query': search_query
    }
    
    return render(request, 'faculty/manage_reservations.html', context)

@login_required
def approve_reservation(request, reservation_id):
    """Approve a reservation request."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can approve reservations.')
        return redirect('faculty_login')
    
    reservation = get_object_or_404(EquipmentUsage, id=reservation_id)
    
    if request.method == 'POST':
        form = ReservationApprovalForm(request.POST, instance=reservation)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.status = 'approved'
            reservation.save()
            
            # Send email notification to student
            subject = 'Equipment Reservation Approved'
            message = f'''Your reservation for {reservation.equipment.name} has been approved.
            
            Checkout Time: {reservation.checkout_time}
            Expected Return Time: {reservation.expected_return_time}
            
            Notes: {reservation.approval_notes}
            
            Please pick up the equipment at the specified time.'''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [reservation.user.email],
                fail_silently=True,
            )
            
            messages.success(request, 'Reservation approved successfully.')
            return redirect('manage_reservations')
    else:
        form = ReservationApprovalForm(instance=reservation)
    
    return render(request, 'faculty/approve_reservation.html', {
        'form': form,
        'reservation': reservation
    })

@login_required
def reject_reservation(request, reservation_id):
    """Reject a reservation request."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can reject reservations.')
        return redirect('faculty_login')
    
    reservation = get_object_or_404(EquipmentUsage, id=reservation_id)
    
    if request.method == 'POST':
        form = ReservationApprovalForm(request.POST, instance=reservation)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.status = 'rejected'
            reservation.save()
            
            # Send email notification to student
            subject = 'Equipment Reservation Rejected'
            message = f'''Your reservation for {reservation.equipment.name} has been rejected.
            
            Reason: {reservation.approval_notes}
            
            Please contact your faculty advisor if you have any questions.'''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [reservation.user.email],
                fail_silently=True,
            )
            
            messages.success(request, 'Reservation rejected successfully.')
            return redirect('manage_reservations')
    else:
        form = ReservationApprovalForm(instance=reservation)
    
    return render(request, 'faculty/reject_reservation.html', {
        'form': form,
        'reservation': reservation
    })

@login_required
def mark_checked_out(request, reservation_id):
    """Mark a reservation as checked out."""
    if not request.user.userprofile.is_faculty():
        return JsonResponse({'success': False, 'error': 'Only faculty members can mark reservations as checked out.'})
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
    reservation = get_object_or_404(EquipmentUsage, id=reservation_id)
    
    if reservation.status != 'approved':
        return JsonResponse({'success': False, 'error': 'Only approved reservations can be marked as checked out.'})
    
    reservation.status = 'checked_out'
    reservation.save()
    
    # Update equipment availability
    equipment = reservation.equipment
    equipment.is_available = False
    equipment.save()
    
    return JsonResponse({'success': True})

@login_required
def mark_returned(request, reservation_id):
    """Mark a reservation as returned."""
    if not request.user.userprofile.is_faculty():
        return JsonResponse({'success': False, 'error': 'Only faculty members can mark reservations as returned.'})
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
    reservation = get_object_or_404(EquipmentUsage, id=reservation_id)
    
    if reservation.status not in ['checked_out', 'overdue']:
        return JsonResponse({'success': False, 'error': 'Only checked out or overdue reservations can be marked as returned.'})
    
    reservation.status = 'returned'
    reservation.actual_return_time = timezone.now()
    reservation.save()
    
    # Update equipment availability
    equipment = reservation.equipment
    equipment.is_available = True
    equipment.save()
    
    return JsonResponse({'success': True})

class StudentEquipmentListView(LoginRequiredMixin, ListView):
    model = MultimediaEquipment
    template_name = 'equipment/student_equipment_list.html'
    context_object_name = 'equipment_list'
    paginate_by = 9  # Show 9 items per page (3x3 grid)

    def get_queryset(self):
        queryset = MultimediaEquipment.objects.all()
        
        # Apply search filter
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        # Apply category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Apply equipment type filter
        equipment_type = self.request.GET.get('type')
        if equipment_type:
            queryset = queryset.filter(equipment_type=equipment_type)
        
        return queryset.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = EquipmentCategory.objects.all()
        context['equipment_types'] = MultimediaEquipment.EQUIPMENT_TYPES
        return context

@ensure_csrf_cookie
def refresh_csrf(request):
    """View to refresh CSRF token"""
    return JsonResponse({'csrf_token': request.META["CSRF_COOKIE"]})

@login_required
def add_to_cart(request, equipment_id):
    """Add an equipment item to the user's reservation cart."""
    if request.method == 'POST':
        equipment = get_object_or_404(MultimediaEquipment, pk=equipment_id)
        
        # Check if equipment is available
        if not equipment.is_available:
            messages.error(request, 'This equipment is not available for reservation.')
            return redirect('equipment_list')
        
        # Check if user already has this equipment in cart
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            equipment=equipment
        )
        
        if created:
            messages.success(request, f'{equipment.name} added to your reservation cart.')
        else:
            messages.info(request, f'{equipment.name} is already in your reservation cart.')
            
        return redirect('view_cart')
    
    return redirect('equipment_list')

@login_required
def view_cart(request):
    """View the current user's reservation cart."""
    cart_items = CartItem.objects.filter(user=request.user).select_related('equipment')
    
    context = {
        'cart_items': cart_items,
        'total_items': cart_items.count()
    }
    return render(request, 'student/cart.html', context)

@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the user's reservation cart."""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=item_id, user=request.user)
        equipment_name = cart_item.equipment.name
        cart_item.delete()
        messages.success(request, f'{equipment_name} removed from your reservation cart.')
    
    return redirect('view_cart')

@login_required
def update_cart_item(request, item_id):
    """Update reservation details for a cart item."""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=item_id, user=request.user)
        try:
            cart_item.start_time = request.POST.get('start_time')
            cart_item.end_time = request.POST.get('end_time')
            cart_item.purpose = request.POST.get('purpose')
            cart_item.save()
            messages.success(request, 'Reservation details updated.')
        except Exception as e:
            messages.error(request, f'Error updating reservation details: {str(e)}')
    
    return redirect('view_cart')

@login_required
def checkout_cart(request):
    """Process the final reservation for all items in cart."""
    cart_items = CartItem.objects.filter(user=request.user).select_related('equipment')
    
    if not cart_items.exists():
        messages.error(request, 'Your reservation cart is empty.')
        return redirect('view_cart')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                for item in cart_items:
                    if not (item.start_time and item.end_time and item.purpose):
                        raise ValueError(f'Please provide all required details for {item.equipment.name}')
                        
                    # Create reservation using EquipmentUsage
                    usage = EquipmentUsage.objects.create(
                        user=request.user,
                        equipment=item.equipment,
                        checkout_time=item.start_time,
                        expected_return_time=item.end_time,
                        purpose=item.purpose,
                        status='pending'
                    )
                
                # Clear the cart after successful checkout
                cart_items.delete()
                
                messages.success(request, 'Your reservation requests have been submitted and are pending approval.')
                return redirect('my_reservations')
                
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('view_cart')
        except Exception as e:
            messages.error(request, f'Error processing your reservation: {str(e)}')
            return redirect('view_cart')
    
    context = {
        'cart_items': cart_items,
        'total_items': cart_items.count()
    }
    return render(request, 'student/checkout.html', context)
