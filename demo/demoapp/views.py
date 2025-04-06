from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.db.models import Count, Avg, F, Sum, Max, Min, ExpressionWrapper, DurationField

# Custom decorators and mixins for role-based access control
def faculty_required(function):
    """Decorator to ensure only faculty members can access a view"""
    actual_decorator = user_passes_test(
        lambda u: hasattr(u, 'userprofile') and u.userprofile.is_faculty()
    )
    return actual_decorator(function)

def student_required(function):
    """Decorator to ensure only students can access a view"""
    actual_decorator = user_passes_test(
        lambda u: hasattr(u, 'userprofile') and not u.userprofile.is_faculty()
    )
    return actual_decorator(function)

class FacultyRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only faculty members can access a class-based view"""
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.is_faculty()

class StudentRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only students can access a class-based view"""
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and not self.request.user.userprofile.is_faculty()

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import ListView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction
from django.db.models import Q, Count
from djreservation.views import ProductReservationView
from .models import MultimediaEquipment, EquipmentUsage, MaintenanceRecord, UserProfile, EquipmentCategory, CartItem, BlacklistedStudent, create_user_profile, save_user_profile
from .forms import SignUpForm, MultimediaEquipmentForm, MaintenanceRecordForm, ReservationApprovalForm, CategoryForm, EquipmentPhotoUploadForm
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.template.context_processors import csrf
from django.db.models import Count
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import datetime, timedelta, date
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django import forms
import datetime
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.functions import ExtractHour, ExtractWeekDay
from django.db.models import Avg, ExpressionWrapper, F, DurationField
import json
from django.db.models.functions import TruncDate
from django.core.serializers.json import DjangoJSONEncoder

import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.db.models import Q, Count, Sum, F, ExpressionWrapper, fields
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

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
    context = {'next': next_url}
    
    # Add CSRF token explicitly to context
    context.update(csrf(request))

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
            return redirect('home')  # Redirect to home page after login
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html', context)

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
@faculty_required
def faculty_dashboard(request):
    """Dashboard view for faculty members."""
    # Get current date for comparisons
    current_date = timezone.now()

    # Get recent reservations
    recent_reservations = EquipmentUsage.objects.filter(
        Q(status='pending') |
        Q(status='approved') |
        Q(status='pending_photo') |
        Q(status='photo_submitted') |
        Q(status='checked_out')
    ).select_related('user', 'equipment').order_by('-checkout_time')[:5]

    # Get equipment status counts
    total_equipment = MultimediaEquipment.objects.count()
    available_equipment = MultimediaEquipment.objects.filter(is_available=True).count()
    maintenance_needed = MultimediaEquipment.objects.filter(condition='needs_repair').count()

    # Get reservation statistics
    active_reservations = EquipmentUsage.objects.filter(
        Q(status='approved') | Q(status='pending_photo') | Q(status='photo_submitted') | Q(status='checked_out')
    ).count()
    pending_reservations = EquipmentUsage.objects.filter(status='pending').count()
    pending_photos = EquipmentUsage.objects.filter(status='photo_submitted').count()

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
        'pending_photos': pending_photos,
        'recent_reservations': recent_reservations,
        'maintenance_alerts': maintenance_alerts,
        'all_equipment': all_equipment,
    }

    return render(request, 'faculty/dashboard.html', context)

@login_required
def home(request):
    return render(request, 'index.html')

@login_required
@student_required
def my_reservations(request):
    """View student's equipment reservations."""
    # Check if user is faculty - if so, redirect them
    if hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty():
        messages.error(request, 'Faculty members should use the faculty dashboard to view all reservations.')
        return redirect('faculty_dashboard')
    
    # Get the student's reservations
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
@student_required
def equipment_return(request, usage_id):
    usage = get_object_or_404(EquipmentUsage, id=usage_id, user=request.user)
    if request.method == 'POST':
        usage.return_equipment()
        messages.success(request, 'Equipment returned successfully!')
        return redirect('my_reservations')
    return render(request, 'equipment_return.html', {'usage': usage})

@login_required
@student_required
def dashboard(request):
    """Student dashboard view showing reserved equipment and other student info"""
    # Check if user is blacklisted
    is_blacklisted, blacklist_record = is_student_blacklisted(request.user)
    
    # Get all of the student's reservations
    all_reservations = EquipmentUsage.objects.filter(
        user=request.user
    ).select_related('equipment', 'equipment__category')
    
    # Get student's current active reservations
    active_reservations = all_reservations.filter(
        status__in=['pending', 'approved', 'checked_out']
    )
    
    # Count various statistics for the student
    pending_count = active_reservations.filter(status='pending').count()
    approved_count = active_reservations.filter(status='approved').count()
    checked_out_count = active_reservations.filter(status='checked_out').count()
    
    # Get total, active, and past bookings counts
    total_bookings = all_reservations.count()
    active_bookings_count = active_reservations.count()
    past_bookings_count = all_reservations.filter(status='returned').count()
    
    # Get recent activity - most recent 5 bookings
    recent_activity = all_reservations.order_by('-checkout_time')[:5]
    
    # Get category usage statistics
    category_stats = list(all_reservations.values('equipment__equipment_type').annotate(count=Count('id')))
    
    # Convert category_stats to a JSON-serializable format
    for stat in category_stats:
        if 'equipment__equipment_type' in stat and stat['equipment__equipment_type'] is None:
            stat['equipment__equipment_type'] = 'Unknown'
    
    # Get equipment type usage statistics
    equipment_type_stats = list(all_reservations.values('equipment__equipment_type').annotate(count=Count('id')))
    
    context = {
        'reservations': active_reservations,
        'pending_count': pending_count,
        'approved_count': approved_count, 
        'checked_out_count': checked_out_count,
        'total_bookings': total_bookings,
        'active_bookings_count': active_bookings_count,
        'past_bookings_count': past_bookings_count,
        'recent_activity': recent_activity,
        'category_stats': equipment_type_stats,
        'user_details': request.user,
        'is_blacklisted': is_blacklisted,
        'blacklist_record': blacklist_record,
    }
    
    return render(request, 'student/dashboard.html', context)

@login_required
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

@ensure_csrf_cookie
def signup(request):
    """
    User registration view with ensure_csrf_cookie to make sure
    the CSRF token is always set in the response cookies.
    """
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                # Temporarily disconnect the signal 
                post_save.disconnect(create_user_profile, sender=User)
                post_save.disconnect(save_user_profile, sender=User)
                
                # Use transaction to ensure all operations succeed or fail together
                with transaction.atomic():
                    # Save the user
                    user = form.save()
                    print(f"User created: {user.username}")
                    
                    # Create the profile
                    profile = UserProfile.objects.create(
                        user=user,
                        number=form.cleaned_data.get('number'),
                        user_type='student'
                    )
                    print(f"Profile created: {user.username}, ID: {profile.id}")

                # Reconnect the signals
                post_save.connect(create_user_profile, sender=User)
                post_save.connect(save_user_profile, sender=User)

                messages.success(request, 'Account created successfully! Please log in with your credentials.')
                return redirect('login')
            except forms.ValidationError as e:
                messages.error(request, str(e))
                print(f"Validation error: {str(e)}")
            except Exception as e:
                error_message = str(e)
                print(f"Complete error: {error_message}")  # Print the full error
                
                if 'UNIQUE constraint failed' in error_message:
                    if 'auth_user.username' in error_message:
                        messages.error(request, 'A user with this username already exists. Please try a different username.')
                    elif 'auth_user.email' in error_message:
                        messages.error(request, 'A user with this email already exists. Please use a different email address.')
                    elif 'demoapp_userprofile.user_id' in error_message:
                        messages.error(request, 'There was a problem creating your profile. Please try again with a different username.')
                    else:
                        messages.error(request, f'Account creation failed due to a duplicate value: {error_message}')
                else:
                    messages.error(request, f"An unexpected error occurred: {error_message}")
                
                # Cleanup if user creation failed but profile creation didn't
                if 'user' in locals() and user and user.pk:
                    try:
                        print(f"Cleaning up user: {user.username}")
                        user.delete()
                    except Exception as cleanup_error:
                        print(f"Error during cleanup: {str(cleanup_error)}")
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
    """View for faculty to manage all equipment reservations."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can manage reservations.')
        return redirect('faculty_login')
    
    # Get filter parameters
    status = request.GET.get('status', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    reservations = EquipmentUsage.objects.select_related(
        'user', 'equipment', 'equipment__category'
    ).order_by('-checkout_time')
    
    # Apply filters
    if status:
        reservations = reservations.filter(status=status)
    
    # Add filter for pending photo reviews if requested
    if request.GET.get('photo_review', '') == 'true':
        reservations = reservations.filter(status='photo_submitted')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            reservations = reservations.filter(checkout_time__date__gte=start_date)
        except (ValueError, TypeError):
            start_date = None
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            reservations = reservations.filter(checkout_time__date__lte=end_date)
        except (ValueError, TypeError):
            end_date = None
    
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
            # Check if there's enough quantity available
            equipment = reservation.equipment
            if reservation.quantity > equipment.available_quantity:
                messages.error(request, f'Cannot approve reservation. Only {equipment.available_quantity} units of {equipment.name} are available.')
                return redirect('manage_reservations')
                
            # Process the approval
            reservation = form.save(commit=False)
            reservation.status = 'pending_photo'  # Change to pending_photo instead of approved
            reservation.approved_by = request.user
            reservation.approved_at = timezone.now()
            reservation.save()
            
            # Update equipment availability
            equipment.available_quantity -= reservation.quantity
            equipment.save()
            
            # Send email notification to student
            subject = 'Equipment Reservation Approved'
            message = f'''Your reservation for {reservation.quantity} x {reservation.equipment.name} has been approved.
            
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
            
            # Restore the equipment quantity since the reservation was rejected
            equipment = reservation.equipment
            equipment.available_quantity += reservation.quantity
            equipment.save()
            
            # Send email notification to student
            subject = 'Equipment Reservation Rejected'
            message = f'''Your reservation for {reservation.quantity} x {reservation.equipment.name} has been rejected.
            
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
    
    return JsonResponse({'success': True, 'message': f'Successfully checked out {reservation.quantity} x {reservation.equipment.name}'})

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
    
    try:
        with transaction.atomic():
            reservation.status = 'returned'
            reservation.actual_return_time = timezone.now()
            reservation.save()
            
            # Restore the equipment quantity
            equipment = reservation.equipment
            equipment.available_quantity += reservation.quantity
            equipment.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully returned {reservation.quantity} x {reservation.equipment.name}'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error returning equipment: {str(e)}'
        })

class StudentEquipmentListView(LoginRequiredMixin, ListView):
    model = MultimediaEquipment
    template_name = 'student/equipment_list.html'
    context_object_name = 'equipment_list'
    paginate_by = 9  # Show 9 items per page (3x3 grid)
    
    def dispatch(self, request, *args, **kwargs):
        # Check if the user is faculty - if so, redirect them
        if hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty():
            messages.error(request, 'The equipment browsing page is for students only.')
            return redirect('faculty_dashboard')
        return super().dispatch(request, *args, **kwargs)

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
        context['is_faculty'] = self.request.user.userprofile.is_faculty()
        return context

@login_required
@student_required
def browse_equipment(request):
    """View for students to browse available equipment for reservations"""
    categories = EquipmentCategory.objects.all()
    equipment_list = MultimediaEquipment.objects.filter(is_available=True).order_by('name')
    
    context = {
        'categories': categories,
        'equipment_list': equipment_list,
    }
    return render(request, 'student/equipment_list.html', context)

def refresh_csrf(request):
    """
    View to refresh CSRF token - returns a new token to be used in forms.
    This helps with CSRF validation failures after session timeouts.
    """
    return HttpResponse(get_token(request))

## Blacklist utility function
def is_student_blacklisted(user):
    """Check if a student is blacklisted and return the blacklist record if they are.
    
    Args:
        user: The user to check
        
    Returns:
        tuple: (is_blacklisted, blacklist_record)
            - is_blacklisted (bool): True if the user is blacklisted
            - blacklist_record (BlacklistedStudent): The blacklist record if found, None otherwise
    """
    if user.is_anonymous:
        return False, None
        
    blacklist_record = BlacklistedStudent.objects.filter(student=user, is_active=True).first()
    return blacklist_record is not None, blacklist_record

def has_active_reservation(user, equipment_id):
    """Check if a user already has an active reservation for specified equipment.
    
    Args:
        user: The user to check
        equipment_id: ID of the equipment to check
        
    Returns:
        bool: True if user has an active reservation, False otherwise
    """
    active_statuses = ['pending', 'approved', 'pending_photo', 'photo_submitted', 'checked_out']
    
    # Check for active reservations with the standard statuses
    existing_active_reservations = EquipmentUsage.objects.filter(
        user=user,
        equipment_id=equipment_id,
        status__in=active_statuses
    ).count()
    
    # Also check for any overdue reservations that haven't been marked as returned
    now = timezone.now()
    overdue_reservations = EquipmentUsage.objects.filter(
        user=user,
        equipment_id=equipment_id,
        expected_return_time__lt=now,
        status='checked_out'  # Only checked out items can be overdue
    ).count()
    
    return existing_active_reservations > 0 or overdue_reservations > 0

def has_any_overdue_items(user):
    """Check if a user has any overdue items across all equipment.
    
    Args:
        user: The user to check
        
    Returns:
        tuple: (has_overdue, overdue_reservation) - whether user has overdue items and the first overdue reservation
    """
    now = timezone.now()
    overdue_reservation = EquipmentUsage.objects.filter(
        user=user,
        expected_return_time__lt=now,
        status='checked_out'
    ).first()
    
    return (overdue_reservation is not None, overdue_reservation)

@login_required
@student_required
def view_cart(request):
    """View the current user's reservation cart."""
    cart_items = CartItem.objects.filter(user=request.user).select_related('equipment')
    
    context = {
        'cart_items': cart_items,
        'total_items': cart_items.count()
    }
    return render(request, 'student/cart.html', context)

@login_required
@student_required
def remove_from_cart(request, item_id):
    """Remove an item from the user's reservation cart."""
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        cart_item.delete()
        messages.success(request, f'{cart_item.equipment.name} removed from your cart.')
    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found in your cart.')
    
    return redirect('view_cart')

@login_required
@student_required
def add_to_cart(request, equipment_id):
    """Add an equipment item to the user's reservation cart."""
    # Check if student is blacklisted
    is_blacklisted, blacklist_record = is_student_blacklisted(request.user)
    if is_blacklisted:
        messages.error(request, f'You cannot make reservations because you are blacklisted. Reason: {blacklist_record.reason}')
        return redirect('equipment_list')
    
    # First check if the student has ANY overdue items (regardless of equipment type)
    has_overdue, overdue_item = has_any_overdue_items(request.user)
    if has_overdue:
        equipment_name = overdue_item.equipment.name if overdue_item.equipment else "Unknown equipment"
        messages.error(request, 
            f'You have an overdue item ({equipment_name}, due {overdue_item.expected_return_time.strftime("%Y-%m-%d %H:%M")}). '
            f'Please return all overdue items before making new reservations.'
        )
        return redirect('equipment_list')
    
    # Then check if user already has an active reservation for this specific equipment
    if has_active_reservation(request.user, equipment_id):
        # Check specifically for overdue items
        now = timezone.now()
        overdue_reservation = EquipmentUsage.objects.filter(
            user=request.user,
            equipment_id=equipment_id,
            expected_return_time__lt=now,
            status='checked_out'
        ).first()
        
        if overdue_reservation:
            messages.error(request, f'You have an overdue reservation for this equipment (due {overdue_reservation.expected_return_time.strftime("%Y-%m-%d %H:%M")}). Please return it before making a new reservation.')
        else:
            messages.error(request, 'You already have an active reservation for this equipment. You cannot reserve the same item again until your current reservation is completed.')
        return redirect('equipment_list')
        
    equipment = get_object_or_404(MultimediaEquipment, id=equipment_id, is_available=True)
    
    # Check if already in cart
    if CartItem.objects.filter(user=request.user, equipment=equipment).exists():
        messages.info(request, f'{equipment.name} is already in your cart.')
    else:
        CartItem.objects.create(user=request.user, equipment=equipment)
        messages.success(request, f'{equipment.name} added to your cart.')
    
    return redirect('view_cart')

@login_required
@student_required
def update_cart_item(request, item_id):
    """Update reservation details for a cart item."""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=item_id, user=request.user)
        try:
            # Get quantity from form with validation
            try:
                quantity = int(request.POST.get('quantity', 1))
                quantity = max(1, quantity)  # Ensure at least 1
            except ValueError:
                quantity = cart_item.quantity  # Keep existing quantity on error
                
            # Check if requested quantity is available
            equipment = cart_item.equipment
            if quantity > equipment.available_quantity:
                messages.warning(request, f'Only {equipment.available_quantity} units of {equipment.name} are available. Adjusting quantity.')
                quantity = equipment.available_quantity
            
            # Get reservation times
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            
            if start_time_str and end_time_str:
                # Handle both datetime objects and strings
                if isinstance(start_time_str, datetime.datetime) and isinstance(end_time_str, datetime.datetime):
                    start_time = start_time_str
                    end_time = end_time_str
                else:
                    # Ensure values are strings before parsing
                    if not isinstance(start_time_str, str) or not isinstance(end_time_str, str):
                        messages.error(request, 'Invalid date format. Please try again.')
                        return redirect('view_cart')
                        
                    start_time = datetime.datetime.fromisoformat(start_time_str)
                    end_time = datetime.datetime.fromisoformat(end_time_str)
                
                # Calculate time difference in hours
                time_diff = (end_time - start_time).total_seconds() / 3600
                
                # Check if reservation exceeds 24 hours
                if time_diff > 24:
                    messages.error(request, f'Reservation for {cart_item.equipment.name} cannot exceed 24 hours. Your requested duration: {time_diff:.1f} hours.')
                    return redirect('view_cart')
                
                # Check if start time is in the past - make timezone-aware comparison
                now = datetime.datetime.now()
                
                if start_time.tzinfo is not None:
                    # If start_time is timezone-aware, make now timezone-aware too
                    now = timezone.make_aware(now)
                
                if start_time < now:
                    messages.error(request, 'Start time cannot be in the past.')
                    return redirect('view_cart')
                
                # Check if end time is before start time
                if end_time <= start_time:
                    messages.error(request, 'End time must be after start time.')
                    return redirect('view_cart')
            
            # Update cart item details
            cart_item.quantity = quantity
            cart_item.start_time = start_time_str
            cart_item.end_time = end_time_str
            cart_item.purpose = request.POST.get('purpose')
            cart_item.save()
            messages.success(request, 'Reservation details updated.')
        except Exception as e:
            messages.error(request, f'Error updating reservation details: {str(e)}')
    
    return redirect('view_cart')

@login_required
@student_required
def checkout_cart(request):
    """Process the final reservation for all items in cart."""
    # Check if user is blacklisted before proceeding
    is_blacklisted, blacklist_record = is_student_blacklisted(request.user)
    if is_blacklisted:
        messages.error(
            request, 
            f'You are currently blacklisted and cannot make reservations. Reason: {blacklist_record.reason}. '
            f'Please contact a faculty member for assistance.'
        )
        return redirect('view_cart')
    
    # Check if the student has ANY overdue items (regardless of equipment type)
    has_overdue, overdue_item = has_any_overdue_items(request.user)
    if has_overdue:
        equipment_name = overdue_item.equipment.name if overdue_item.equipment else "Unknown equipment"
        messages.error(request, 
            f'You have an overdue item ({equipment_name}, due {overdue_item.expected_return_time.strftime("%Y-%m-%d %H:%M")}). '
            f'Please return all overdue items before making new reservations.'
        )
        return redirect('view_cart')
    
    cart_items = CartItem.objects.filter(user=request.user).select_related('equipment')
    
    if not cart_items:
        messages.warning(request, 'Your cart is empty. Please add items before checking out.')
        return redirect('equipment_list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                for item in cart_items:
                    if not (item.start_time and item.end_time and item.purpose):
                        raise ValueError(f'Please provide all required details for {item.equipment.name}')
                    
                    # Check reservation time frame (cannot exceed 24 hours)
                    try:
                        # Handle the case when item.start_time and item.end_time are already datetime objects
                        if isinstance(item.start_time, datetime.datetime) and isinstance(item.end_time, datetime.datetime):
                            start_time = item.start_time
                            end_time = item.end_time
                        else:
                            # Ensure start_time and end_time are strings before parsing
                            if not isinstance(item.start_time, str) or not isinstance(item.end_time, str):
                                messages.error(request, 'Invalid date format. Please try again.')
                                return redirect('view_cart')
                                
                            start_time = datetime.datetime.fromisoformat(item.start_time)
                            end_time = datetime.datetime.fromisoformat(item.end_time)
                        
                        # Calculate time difference in hours
                        time_diff = (end_time - start_time).total_seconds() / 3600
                        
                        # Check if reservation exceeds 24 hours
                        if time_diff > 24:
                            raise ValueError(f'Reservation for {item.equipment.name} cannot exceed 24 hours. Your requested duration: {time_diff:.1f} hours.')
                        
                        # Check if start time is in the past - make timezone-aware comparison
                        now = datetime.datetime.now()
                        
                        if start_time.tzinfo is not None:
                            # If start_time is timezone-aware, make now timezone-aware too
                            now = timezone.make_aware(now)
                        
                        if start_time < now:
                            raise ValueError(f'Start time for {item.equipment.name} cannot be in the past.')
                        
                        # Check if end time is before start time
                        if end_time <= start_time:
                            raise ValueError(f'End time for {item.equipment.name} must be after start time.')
                            
                    except ValueError as e:
                        if 'fromisoformat' in str(e):
                            raise ValueError(f'Invalid date format for {item.equipment.name}. Please use the datetime picker.')
                        else:
                            raise e
                    
                    # Verify quantity is still available
                    equipment = item.equipment
                    if item.quantity > equipment.available_quantity:
                        raise ValueError(f'Only {equipment.available_quantity} units of {equipment.name} are available.')
                        
                    # Check if user already has an active reservation for this equipment
                    if has_active_reservation(request.user, equipment.id):
                        # Check specifically for overdue items
                        now = timezone.now()
                        overdue_reservation = EquipmentUsage.objects.filter(
                            user=request.user,
                            equipment_id=equipment.id,
                            expected_return_time__lt=now,
                            status='checked_out'
                        ).first()
                        
                        if overdue_reservation:
                            raise ValueError(f'You have an overdue reservation for {equipment.name} (due {overdue_reservation.expected_return_time.strftime("%Y-%m-%d %H:%M")}). Please return it before making a new reservation.')
                        else:
                            raise ValueError(f'You already have an active reservation for {equipment.name}. You cannot reserve the same item again until your current reservation is completed.')
                        
                    # Create reservation using EquipmentUsage with quantity
                    usage = EquipmentUsage.objects.create(
                        user=request.user,
                        equipment=item.equipment,
                        checkout_time=item.start_time,
                        expected_return_time=item.end_time,
                        purpose=item.purpose,
                        status='pending',
                        quantity=item.quantity
                    )
                    
                    # Update equipment availability
                    equipment.available_quantity -= item.quantity
                    equipment.save()
                
                # Clear the cart after successful checkout
                cart_items.delete()
                
                messages.success(request, 'Your reservation requests have been submitted and are pending approval.')
                return redirect('my_reservations')
                
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('view_cart')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('view_cart')
    
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'student/cart.html', context)

@login_required
@faculty_required
def faculty_analytics(request):
    """Advanced analytics dashboard for faculty members."""
    # Current date for comparisons
    current_date = timezone.now()
    
    # Default date range: last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Process date range filter from form
    if 'daterange' in request.GET and request.GET.get('daterange'):
        date_range = request.GET.get('daterange').split(' - ')
        if len(date_range) == 2:
            try:
                # Date format from the picker is MM/DD/YYYY
                start_date = datetime.strptime(date_range[0], '%m/%d/%Y').date()
                end_date = datetime.strptime(date_range[1], '%m/%d/%Y').date()
            except ValueError:
                # If there's an error parsing dates, use the defaults
                pass
    
    # Convert dates to datetime for query
    start_datetime = timezone.datetime.combine(start_date, timezone.datetime.min.time())
    end_datetime = timezone.datetime.combine(end_date, timezone.datetime.max.time())
    
    # Get equipment usages within the date range
    usages = EquipmentUsage.objects.filter(
        checkout_time__gte=start_datetime,
        checkout_time__lte=end_datetime
    )
    
    # 1. Equipment Utilization Rate
    total_equipment_count = MultimediaEquipment.objects.count()
    used_equipment_ids = usages.values_list('equipment_id', flat=True).distinct()
    utilization_rate = (len(set(used_equipment_ids)) / total_equipment_count * 100) if total_equipment_count > 0 else 0
    
    # 2. Peak Usage Times by Hour
    usage_hours = usages.annotate(
        hour=ExtractHour('checkout_time')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Create a full 24-hour series (even hours with 0 usage)
    hours_data = {hour: 0 for hour in range(24)}
    for item in usage_hours:
        hours_data[item['hour']] = item['count']
    
    # 3. Peak Usage by Day of Week
    usage_by_day = usages.annotate(
        day=ExtractWeekDay('checkout_time')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Create a full 7-day series (even days with 0 usage)
    days_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    # Django's ExtractWeekDay returns 1-7 where 1=Sunday, so we need to adjust
    days_data = {i+1: {'name': day, 'count': 0} for i, day in enumerate(days_names)}
    for item in usage_by_day:
        days_data[item['day']]['count'] = item['count']
    
    # 4. Popular Equipment (Top 10)
    popular_equipment = list(usages.values(
        'equipment__id', 'equipment__name', 'equipment__equipment_type'
    ).annotate(
        usage_count=Count('id')
    ).order_by('-usage_count')[:10])
    
    # 5. Underutilized Equipment (Bottom 10)
    # First, get counts for all equipment that has been used
    equipment_usage_counts = dict(usages.values('equipment').annotate(
        count=Count('id')).values_list('equipment', 'count'))
    
    # Then identify equipment with zero or low usage
    all_equipment = MultimediaEquipment.objects.values('id', 'name', 'equipment_type')
    for item in all_equipment:
        item['usage_count'] = equipment_usage_counts.get(item['id'], 0)
    
    underutilized_equipment = sorted(all_equipment, key=lambda x: x['usage_count'])[:10]
    
    # 6. Category-wise Usage
    category_usage = list(usages.values(
        'equipment__category__id', 'equipment__category__name'
    ).annotate(
        usage_count=Count('id')
    ).order_by('-usage_count'))
    
    # 7. Reservation Duration Statistics
    durations = []
    for usage in usages:
        if usage.actual_return_time:
            duration = (usage.actual_return_time - usage.checkout_time).total_seconds() / 3600  # hours
        elif usage.expected_return_time:
            duration = (usage.expected_return_time - usage.checkout_time).total_seconds() / 3600  # hours
        else:
            duration = 0
        durations.append(duration)
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    max_duration = max(durations) if durations else 0
    
    # 8. Equipment that is frequently overbooked
    overbooked_equipment = list(usages.filter(
        status='rejected'
    ).values(
        'equipment__id', 'equipment__name'
    ).annotate(
        reject_count=Count('id')
    ).order_by('-reject_count')[:5])

    # 9. Status distribution
    status_distribution = dict(usages.values('status').annotate(
        count=Count('id')).values_list('status', 'count'))
    
    # Prepare context data
    context = {
        'utilization_rate': round(utilization_rate, 1),
        'hours_data': list(hours_data.values()),
        'days_data': [days_data[i+1]['count'] for i in range(7)],
        # Keep the original queryset version for template rendering
        'popular_equipment_display': popular_equipment,
        'underutilized_equipment_display': underutilized_equipment,
        'category_usage_display': category_usage,
        'overbooked_equipment_display': overbooked_equipment,
        # JSON versions for JavaScript
        'popular_equipment': json.dumps(popular_equipment, cls=DjangoJSONEncoder),
        'underutilized_equipment': json.dumps(underutilized_equipment, cls=DjangoJSONEncoder),
        'category_usage': json.dumps(category_usage, cls=DjangoJSONEncoder),
        'durations': json.dumps(durations, cls=DjangoJSONEncoder),
        'avg_duration': round(avg_duration, 1),
        'max_duration': round(max_duration, 1),
        'status_distribution': json.dumps(status_distribution, cls=DjangoJSONEncoder),
        'active_tab': 'analytics',
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render(request, 'faculty/analytics.html', context)

@login_required
@faculty_required
def equipment_detail_analytics(request, equipment_id):
    """View analytics for a specific equipment."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can view analytics.')
        return redirect('faculty_login')
    
    try:
        equipment = MultimediaEquipment.objects.get(id=equipment_id)
    except MultimediaEquipment.DoesNotExist:
        messages.error(request, 'Equipment not found.')
        return redirect('faculty_analytics')
    
    # Default to last 30 days if not specified
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date') and request.GET.get('end_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
        except ValueError:
            # If date parsing fails, use the defaults
            pass
    
    # Convert dates to datetime for query
    start_datetime = timezone.datetime.combine(start_date, timezone.datetime.min.time())
    end_datetime = timezone.datetime.combine(end_date, timezone.datetime.max.time())
    
    # Get all usage records for this equipment
    usages = EquipmentUsage.objects.filter(
        equipment=equipment,
        checkout_time__gte=start_datetime,
        checkout_time__lte=end_datetime
    ).select_related('user', 'user__userprofile')
    
    # Key statistics
    total_reservations = usages.count()
    unique_users = usages.values('user').distinct().count()
    
    # Calculate utilization rate (% of days the equipment was used)
    date_range = (end_date - start_date).days + 1
    
    # Get unique dates when the equipment was used
    if usages.exists():
        # For datetime objects, use .date() method
        checkout_dates = set()
        for usage in usages:
            # Check if checkout_time is already a date or a datetime
            if hasattr(usage.checkout_time, 'date'):
                checkout_dates.add(usage.checkout_time.date())
            else:
                checkout_dates.add(usage.checkout_time)
        days_used = len(checkout_dates)
    else:
        days_used = 0
    
    utilization_rate = (days_used / date_range * 100) if date_range > 0 else 0
    
    # Calculate average duration
    durations = []
    for usage in usages:
        if usage.actual_return_time:
            duration = (usage.actual_return_time - usage.checkout_time).total_seconds() / 3600  # hours
        elif usage.expected_return_time:
            duration = (usage.expected_return_time - usage.checkout_time).total_seconds() / 3600  # hours
        else:
            duration = 0
        durations.append(duration)
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Timeline data
    timeline_items = []
    
    # Add reservations to timeline
    for usage in usages:
        end_time = usage.actual_return_time or usage.expected_return_time or usage.checkout_time
        timeline_items.append({
            'id': f'reservation-{usage.id}',
            'content': f'Reserved by {usage.user.username}',
            'start': usage.checkout_time.isoformat(),
            'end': end_time.isoformat(),
            'group': 1,
            'className': 'reservation',
            'description': f'Purpose: {usage.purpose or "Not specified"}'
        })
    
    # Get all queries that might use the equipment in timeline
    # First, query raw SQL to get the correct schema
    from django.db import connection
    
    maintenance_query = "SELECT * FROM demoapp_maintenancerecord WHERE equipment_id = %s AND reported_date >= %s AND reported_date <= %s"
    with connection.cursor() as cursor:
        cursor.execute(maintenance_query, [equipment.id, start_datetime, end_datetime])
        columns = [col[0] for col in cursor.description]
        maintenance_records_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Add maintenance records from raw query
    for record in maintenance_records_data:
        # Use a 2-hour default duration for maintenance
        reported_date = record['reported_date']
        if isinstance(reported_date, str):
            reported_date = datetime.fromisoformat(reported_date.replace('Z', '+00:00'))
        
        end_time = reported_date + timedelta(hours=2)
        
        timeline_items.append({
            'id': f'maintenance-{record["id"]}',
            'content': f'Maintenance: {record["issue_description"]}',
            'start': reported_date.isoformat(),
            'end': end_time.isoformat(),
            'group': 2,
            'className': 'maintenance',
            'description': record.get('resolution_notes', 'No notes')
        })
    
    # Daily usage data
    daily_usage = usages.annotate(
        day=TruncDate('checkout_time')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    daily_labels = []
    daily_data = []
    
    # Fill in days with no usage
    current_date = start_date
    while current_date <= end_date:
        daily_labels.append(current_date.strftime('%Y-%m-%d'))
        daily_data.append(0)
        current_date += timedelta(days=1)
    
    # Update with actual usage
    for usage in daily_usage:
        day = usage['day']
        # Check if day is a datetime or already a date
        if hasattr(day, 'date'):
            day = day.date()
        
        day_index = (day - start_date).days
        if 0 <= day_index < len(daily_data):
            daily_data[day_index] = usage['count']
    
    daily_usage_data = {
        'labels': [str(entry['day']) for entry in daily_usage],
        'datasets': [{
            'label': 'Reservations',
            'data': [entry['count'] for entry in daily_usage],
            'borderColor': 'rgba(75, 192, 192, 1)',
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'fill': True
        }]
    }
    
    hourly_usage = usages.annotate(
        hour=ExtractHour('checkout_time')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    hours_data = {hour: 0 for hour in range(24)}
    for item in hourly_usage:
        hours_data[item['hour']] = item['count']
    
    hourly_usage_data = {
        'labels': [f"{hour}:00" for hour in range(24)],
        'datasets': [{
            'label': 'Reservations',
            'data': [next((entry['count'] for entry in hourly_usage if entry['hour'] == hour), 0) for hour in range(24)],
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        }]
    }
    
    # Department usage data - group by username instead of department
    user_usage = usages.values(
        'user__username'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Limit to top 10 users
    
    user_labels = [item['user__username'] for item in user_usage]
    user_usage_values = [item['count'] for item in user_usage]
    
    user_usage_data = {
        'labels': user_labels,
        'datasets': [{
            'data': user_usage_values,
            'backgroundColor': [
                'rgba(255, 99, 132, 0.5)',
                'rgba(54, 162, 235, 0.5)',
                'rgba(255, 206, 86, 0.5)',
                'rgba(75, 192, 192, 0.5)',
                'rgba(153, 102, 255, 0.5)',
                'rgba(255, 159, 64, 0.5)'
            ],
            'borderColor': [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)'
            ],
            'borderWidth': 1
        }]
    }
    
    # Rejection data
    rejection_reasons = [
        'Not Available',
        'Maintenance',
        'Reservations Full',
        'Not Authorized',
        'Other'
    ]
    
    # Simulated rejection data (replace with actual data if available)
    rejected_usages = EquipmentUsage.objects.filter(
        equipment=equipment,
        status='rejected',
        checkout_time__gte=start_datetime,
        checkout_time__lte=end_datetime
    )
    
    # Count rejections by reason (simplified)
    rejection_counts = {reason: 0 for reason in rejection_reasons}
    for usage in rejected_usages:
        reason = usage.rejection_reason if hasattr(usage, 'rejection_reason') and usage.rejection_reason else 'Other'
        if reason in rejection_counts:
            rejection_counts[reason] += 1
        else:
            rejection_counts['Other'] += 1
    
    rejection_data = {
        'labels': rejection_reasons,
        'datasets': [{
            'label': 'Rejections by Reason',
            'data': [rejection_counts[reason] for reason in rejection_reasons],
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        }]
    }
    
    # User statistics
    user_stats = usages.values(
        'user__username'
    ).annotate(
        total_reservations=Count('id'),
        avg_duration=Avg(
            ExpressionWrapper(
                F('actual_return_time') - F('checkout_time'),
                output_field=DurationField()
            )
        ),
        last_used=Max('checkout_time')
    ).order_by('-total_reservations')
    
    # Convert timeline data to JSON
    timeline_data_json = json.dumps(timeline_items, default=str)
    daily_usage_data_json = json.dumps(daily_usage_data, default=str)
    hourly_usage_data_json = json.dumps(hourly_usage_data, default=str)
    user_usage_data_json = json.dumps(user_usage_data, default=str)
    rejection_data_json = json.dumps(rejection_data, default=str)
    
    context = {
        'equipment': equipment,
        'total_reservations': total_reservations,
        'unique_users': unique_users,
        'utilization_rate': round(utilization_rate, 1),
        'avg_duration': avg_duration,
        'timeline_data': timeline_data_json,
        'daily_usage_data': daily_usage_data_json,
        'hourly_usage_data': hourly_usage_data_json,
        'user_usage_data': user_usage_data_json,
        'rejection_data': rejection_data_json,
        'user_stats': user_stats,
        'start_date': start_date,
        'end_date': end_date,
        'active_tab': 'analytics'
    }
    
    return render(request, 'faculty/equipment_detail_analytics.html', context)

@login_required
@faculty_required
def equipment_analytics(request):
    """View for faculty to see equipment analytics."""
    return render(request, 'faculty/equipment_analytics.html')

@login_required
@faculty_required
def manage_blacklist(request):
    """View to manage the blacklist of students."""
    blacklisted_students = BlacklistedStudent.objects.select_related('student', 'blacklisted_by').all()
    
    # Get all students (excluding faculty)
    students = User.objects.filter(userprofile__user_type='student')
    
    # Exclude already blacklisted students
    blacklisted_student_ids = BlacklistedStudent.objects.values_list('student_id', flat=True)
    students = students.exclude(id__in=blacklisted_student_ids)
    
    return render(request, 'faculty/blacklist/manage_blacklist.html', {
        'blacklisted_students': blacklisted_students,
        'students': students
    })

@login_required
@faculty_required
def blacklist_student(request, student_id):
    """View to blacklist a student."""
    if request.method == 'POST':
        reason = request.POST.get('reason')
        
        try:
            student = User.objects.get(id=student_id)
            
            # Check if student is already blacklisted
            if BlacklistedStudent.objects.filter(student=student).exists():
                messages.error(request, 'This student is already blacklisted.')
                return redirect('manage_blacklist')
            
            # Create blacklist record
            BlacklistedStudent.objects.create(
                student=student,
                reason=reason,
                blacklisted_by=request.user
            )
            messages.success(request, f'Student {student.username} has been blacklisted.')
            return redirect('manage_blacklist')
        except User.DoesNotExist:
            messages.error(request, 'Student not found.')
            return redirect('manage_blacklist')

    # Get student details
    try:
        student = User.objects.get(id=student_id)
        if not hasattr(student, 'userprofile') or student.userprofile.is_faculty():
            messages.error(request, 'Selected user is not a student.')
            return redirect('manage_blacklist')
    except User.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('manage_blacklist')
    
    return render(request, 'faculty/blacklist/blacklist_student.html', {'student': student})

@login_required
@faculty_required
def remove_from_blacklist(request, blacklist_id):
    """View to remove a student from the blacklist."""
    try:
        blacklist_record = BlacklistedStudent.objects.get(id=blacklist_id)
    except BlacklistedStudent.DoesNotExist:
        messages.error(request, 'Blacklist record not found.')
        return redirect('manage_blacklist')
    
    if request.method == 'POST':
        # Delete the blacklist record
        student_name = blacklist_record.student.username
        blacklist_record.delete()
        messages.success(request, f'Student {student_name} has been removed from the blacklist.')
        return redirect('manage_blacklist')
    
    return render(request, 'faculty/blacklist/remove_from_blacklist.html', {'blacklist': blacklist_record})

@login_required
def upload_equipment_photo(request, reservation_id):
    """View for students to upload equipment photos before checkout"""
    if request.user.userprofile.is_faculty():
        messages.error(request, 'Only students can upload equipment photos.')
        return redirect('home')
    
    reservation = get_object_or_404(EquipmentUsage, id=reservation_id, user=request.user)
    
    # Check if reservation is in the correct status
    if reservation.status != 'pending_photo':
        if reservation.status == 'photo_submitted':
            messages.info(request, 'Your photo has already been submitted and is awaiting review by faculty.')
        elif reservation.status == 'approved':
            messages.info(request, 'Your reservation has been approved but does not require a photo upload.')
        elif reservation.status == 'rejected':
            messages.error(request, 'This reservation has been rejected and cannot be processed further.')
        elif reservation.status == 'checked_out':
            messages.info(request, 'This equipment has already been checked out.')
        else:
            messages.error(request, 'This reservation is not in the photo upload stage.')
        return redirect('my_reservations')
    
    if request.method == 'POST':
        form = EquipmentPhotoUploadForm(request.POST, request.FILES, instance=reservation)
        if form.is_valid():
            reservation = form.save()
            messages.success(request, 'Equipment photo uploaded successfully. Your reservation is now awaiting final checkout.')
            return redirect('my_reservations')
    else:
        form = EquipmentPhotoUploadForm(instance=reservation)
        
        # Check if this is a re-upload after a rejection
        if hasattr(reservation, 'photo_uploaded_at') and reservation.photo_uploaded_at is not None:
            messages.warning(request, 'Your previous photo was rejected. Please upload a clearer photo of the equipment.')
    
    context = {
        'form': form,
        'reservation': reservation
    }
    
    return render(request, 'student/reservations/upload_photo.html', context)

@login_required
def review_equipment_photo(request, reservation_id):
    """View for faculty to review equipment photos and complete checkout process"""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can review equipment photos.')
        return redirect('home')
    
    reservation = get_object_or_404(EquipmentUsage, id=reservation_id)
    
    # Check if reservation is in the correct status
    if reservation.status != 'photo_submitted':
        messages.error(request, 'This reservation is not in the photo review stage.')
        return redirect('manage_reservations')
    
    if request.method == 'POST':
        if 'approve_photo' in request.POST:
            # Update equipment availability
            equipment = reservation.equipment
            if reservation.quantity <= equipment.available_quantity:
                equipment.available_quantity -= reservation.quantity
                equipment.save()
                
                # Complete checkout
                reservation.status = 'checked_out'
                reservation.save()
                
                messages.success(request, 'Photo approved and equipment checked out successfully.')
            else:
                messages.error(request, f'Cannot complete checkout. Only {equipment.available_quantity} units of {equipment.name} are available.')
            
            return redirect('manage_reservations')
            
        elif 'reject_photo' in request.POST:
            rejection_reason = request.POST.get('rejection_reason', '')
            if rejection_reason:
                # Store the rejection reason in the approval_notes field
                reservation.approval_notes = f"Photo rejected: {rejection_reason}"
            reservation.status = 'pending_photo'  # Reset to pending_photo for student to try again
            reservation.save()
            messages.warning(request, 'Photo rejected. Student will be asked to upload a new photo.')
            return redirect('manage_reservations')
    
    context = {
        'reservation': reservation
    }
    
    return render(request, 'faculty/equipment/review_photo.html', context)

@login_required
def maintenance_list(request):
    """Display list of maintenance records for faculty."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')
    
    # Get query parameters for filtering
    equipment_id = request.GET.get('equipment')
    status = request.GET.get('status')
    
    # Base queryset
    records = MaintenanceRecord.objects.all().order_by('-reported_date')
    
    # Apply filters
    if equipment_id:
        records = records.filter(equipment_id=equipment_id)
    
    if status == 'pending':
        records = records.filter(resolved_date__isnull=True)
    elif status == 'resolved':
        records = records.filter(resolved_date__isnull=False)
    
    # Pagination
    paginator = Paginator(records, 9)  # 9 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get list of equipment for filtering
    equipment_list = MultimediaEquipment.objects.all().order_by('name')
    
    return render(request, 'faculty/maintenance/maintenance_list.html', {
        'maintenance_records': page_obj,
        'equipment_list': equipment_list
    })

@login_required
def maintenance_create(request):
    """Create a new maintenance record by faculty."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')
    
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.reported_by = request.user
            record.save()
            
            # Update equipment condition
            equipment = record.equipment
            equipment.condition = 'needs_repair'
            equipment.save()
            
            messages.success(request, 'Maintenance issue reported successfully.')
            return redirect('maintenance_list')
    else:
        form = MaintenanceRecordForm()
        # Remove resolution fields for creation
        form.fields.pop('resolution_notes', None)
        form.fields.pop('resolved_date', None)
    
    return render(request, 'faculty/maintenance/maintenance_form.html', {
        'form': form,
        'action': 'Report'
    })

@login_required
def maintenance_detail(request, pk):
    """View details of a maintenance record."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')
    
    maintenance = get_object_or_404(MaintenanceRecord, pk=pk)
    
    return render(request, 'faculty/maintenance/maintenance_detail.html', {
        'maintenance': maintenance
    })

@login_required
def maintenance_resolve(request, pk):
    """Mark a maintenance record as resolved."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')
    
    maintenance = get_object_or_404(MaintenanceRecord, pk=pk)
    
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST, instance=maintenance)
        if form.is_valid():
            record = form.save()
            
            # Update equipment condition if needed
            equipment = record.equipment
            equipment.condition = 'good'  # Reset to good after repair
            equipment.last_maintained = timezone.now()
            equipment.save()
            
            messages.success(request, 'Maintenance record updated successfully.')
            return redirect('maintenance_list')
    else:
        form = MaintenanceRecordForm(instance=maintenance)
        # Only include resolution fields
        for field_name in list(form.fields.keys()):
            if field_name not in ['resolution_notes', 'resolved_date']:
                form.fields[field_name] = form.fields[field_name]
                form.fields[field_name].widget.attrs['readonly'] = True
        
        # Set default resolved date to now
        form.initial['resolved_date'] = timezone.now()
    
    return render(request, 'faculty/maintenance/maintenance_form.html', {
        'form': form,
        'action': 'Resolve'
    })

@login_required
def admin_student_management(request):
    """Admin view for managing all students with advanced filtering and blacklisting."""
    # Strict security check - must be staff, superuser, and not faculty
    if not request.user.is_staff or not request.user.is_superuser or hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get all users with student profiles
    students = User.objects.filter(userprofile__user_type='student')
    
    # Process search and filters
    search_query = request.GET.get('search', '')
    blacklist_status = request.GET.get('blacklist_status', '')
    active_status = request.GET.get('active_status', '')
    
    # Apply filters
    if search_query:
        students = students.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) | 
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(userprofile__number__icontains=search_query)
        )
    
    if blacklist_status:
        if blacklist_status == 'blacklisted':
            # Students who are currently blacklisted
            blacklisted_ids = BlacklistedStudent.objects.filter(is_active=True).values_list('student_id', flat=True)
            students = students.filter(id__in=blacklisted_ids)
        elif blacklist_status == 'not_blacklisted':
            # Students who are not blacklisted
            blacklisted_ids = BlacklistedStudent.objects.filter(is_active=True).values_list('student_id', flat=True)
            students = students.exclude(id__in=blacklisted_ids)
    
    if active_status:
        students = students.filter(is_active=(active_status == 'active'))
    
    # Get blacklist info for all students in one query to avoid N+1 problem
    active_blacklists = {b.student_id: b for b in BlacklistedStudent.objects.filter(is_active=True)}
    
    # Annotate students with reservation counts
    students = students.annotate(
        reservation_count=Count('equipmentusage', distinct=True),
        overdue_count=Count('equipmentusage', 
                           filter=Q(equipmentusage__status='overdue'),
                           distinct=True)
    )
    
    # Pagination
    paginator = Paginator(students, 20)  # Show 20 students per page
    page = request.GET.get('page')
    
    try:
        students_page = paginator.page(page)
    except PageNotAnInteger:
        students_page = paginator.page(1)
    except EmptyPage:
        students_page = paginator.page(paginator.num_pages)
    
    # Prepare data for template
    student_data = []
    for student in students_page:
        is_blacklisted = student.id in active_blacklists
        blacklist_reason = active_blacklists[student.id].reason if is_blacklisted else None
        
        student_data.append({
            'user': student,
            'is_blacklisted': is_blacklisted,
            'blacklist_reason': blacklist_reason,
            'reservation_count': student.reservation_count,
            'overdue_count': student.overdue_count,
        })
    
    context = {
        'student_data': student_data,
        'students_page': students_page,
        'search_query': search_query,
        'blacklist_status': blacklist_status,
        'active_status': active_status,
        'total_count': students.count(),
    }
    
    return render(request, 'admin/student_management.html', context)

@login_required
def admin_blacklist_student(request):
    """Admin view for blacklisting a student."""
    # Strict security check - must be staff, superuser, and not faculty
    if not request.user.is_staff or not request.user.is_superuser or hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        reason = request.POST.get('reason')
        
        if not student_id or not reason:
            messages.error(request, 'Student ID and reason are required.')
            return redirect('admin_student_management')
        
        try:
            student = User.objects.get(id=student_id)
            
            # Check if student is already blacklisted
            existing_blacklist = BlacklistedStudent.objects.filter(
                student=student,
                is_active=True
            ).first()
            
            if existing_blacklist:
                messages.warning(request, f'{student.username} is already blacklisted.')
            else:
                # Create new blacklist record
                BlacklistedStudent.objects.create(
                    student=student,
                    blacklisted_by=request.user,
                    reason=reason
                )
                messages.success(request, f'{student.username} has been blacklisted successfully.')
        
        except User.DoesNotExist:
            messages.error(request, 'Student not found.')
    
    # Redirect back to the referring page or the student management page
    return redirect(request.META.get('HTTP_REFERER', 'admin_student_management'))

@login_required
def admin_remove_blacklist(request):
    """Admin view for removing a student from the blacklist."""
    # Strict security check - must be staff, superuser, and not faculty
    if not request.user.is_staff or not request.user.is_superuser or hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        removal_notes = request.POST.get('removal_notes', '')
        
        if not student_id:
            messages.error(request, 'Student ID is required.')
            return redirect('admin_student_management')
        
        try:
            student = User.objects.get(id=student_id)
            
            # Find active blacklist record
            blacklist = BlacklistedStudent.objects.filter(
                student=student,
                is_active=True
            ).first()
            
            if blacklist:
                # Update blacklist record
                blacklist.is_active = False
                blacklist.removed_by = request.user
                blacklist.removed_date = timezone.now()
                blacklist.removal_notes = removal_notes
                blacklist.save()
                
                messages.success(request, f'{student.username} has been removed from the blacklist.')
            else:
                messages.warning(request, f'{student.username} is not currently blacklisted.')
        
        except User.DoesNotExist:
            messages.error(request, 'Student not found.')
    
    # Redirect back to the referring page or the student management page
    return redirect(request.META.get('HTTP_REFERER', 'admin_student_management'))

@login_required
def admin_bulk_blacklist(request):
    """Admin view for blacklisting multiple students at once."""
    # Strict security check - must be staff, superuser, and not faculty
    if not request.user.is_staff or not request.user.is_superuser or hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        reason = request.POST.get('reason')
        
        if not student_ids or not reason:
            messages.error(request, 'Please select at least one student and provide a reason.')
            return redirect('admin_student_management')
        
        blacklisted_count = 0
        already_blacklisted = 0
        
        for student_id in student_ids:
            try:
                student = User.objects.get(id=student_id)
                
                # Check if already blacklisted
                existing = BlacklistedStudent.objects.filter(
                    student=student,
                    is_active=True
                ).exists()
                
                if not existing:
                    BlacklistedStudent.objects.create(
                        student=student,
                        blacklisted_by=request.user,
                        reason=reason
                    )
                    blacklisted_count += 1
                else:
                    already_blacklisted += 1
                    
            except User.DoesNotExist:
                continue
        
        if blacklisted_count > 0:
            messages.success(request, f'Successfully blacklisted {blacklisted_count} students.')
        if already_blacklisted > 0:
            messages.info(request, f'{already_blacklisted} students were already blacklisted.')
    
    return redirect('admin_student_management')
