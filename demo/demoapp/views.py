from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views import View
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.db.models import Q, Count
from djreservation.views import ProductReservationView
from .models import MultimediaEquipment, EquipmentUsage, MaintenanceRecord, UserProfile, EquipmentCategory, CartItem, create_user_profile, save_user_profile
from .forms import SignUpForm, EquipmentCategoryForm, MultimediaEquipmentForm, MaintenanceRecordForm, ReservationApprovalForm, CategoryForm
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

import datetime

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
            return redirect('home')  # Redirect to home page after login
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
def equipment_return(request, usage_id):
    usage = get_object_or_404(EquipmentUsage, id=usage_id, user=request.user)
    if request.method == 'POST':
        usage.return_equipment()
        messages.success(request, 'Equipment returned successfully!')
        return redirect('my_reservations')
    return render(request, 'equipment_return.html', {'usage': usage})

@login_required
def dashboard(request):
    """Student dashboard view showing reserved equipment and other student info"""
    # Check if user is a student
    if request.user.userprofile.is_faculty():
        messages.error(request, 'This dashboard is for students only. Faculty members should use the faculty dashboard.')
        return redirect('faculty_dashboard')
    
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
    category_stats = all_reservations.values('equipment__category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get equipment type usage statistics
    equipment_type_stats = all_reservations.values('equipment__equipment_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
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
    }
    
    return render(request, 'dashboard.html', context)

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
            # Check if there's enough quantity available
            equipment = reservation.equipment
            if reservation.quantity > equipment.available_quantity:
                messages.error(request, f'Cannot approve reservation. Only {equipment.available_quantity} units of {equipment.name} are available.')
                return redirect('manage_reservations')
                
            # Process the approval
            reservation = form.save(commit=False)
            reservation.status = 'approved'
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

def refresh_csrf(request):
    """
    View to refresh CSRF token - returns a new token to be used in forms.
    This helps with CSRF validation failures after session timeouts.
    """
    return HttpResponse(get_token(request))

@login_required
def add_to_cart(request, equipment_id):
    """Add an equipment item to the user's reservation cart."""
    # Check if user is faculty - if so, redirect them
    if hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty():
        messages.error(request, 'Faculty members cannot make equipment reservations.')
        return redirect('faculty_dashboard')
    
    if request.method == 'POST':
        equipment = get_object_or_404(MultimediaEquipment, pk=equipment_id)
        
        # Get requested quantity from form (default to 1 if not provided)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
            
        # Ensure requested quantity is at least 1
        quantity = max(1, quantity)
        
        # Check if equipment is available and has enough quantity
        if equipment.available_quantity <= 0:
            messages.error(request, f'{equipment.name} is out of stock.')
            return redirect('equipment_list')
            
        # Ensure the requested quantity doesn't exceed available quantity
        if quantity > equipment.available_quantity:
            messages.warning(request, f'Only {equipment.available_quantity} units of {equipment.name} are available. Adjusting quantity.')
            quantity = equipment.available_quantity
        
        # Check if user already has this equipment in cart
        if CartItem.objects.filter(user=request.user, equipment=equipment).exists():
            messages.warning(request, f'{equipment.name} is already in your cart. Please update quantity in the cart view instead of adding it again.')
            return redirect('view_cart')
        
        # Add the item to the cart
        cart_item = CartItem.objects.create(
            user=request.user,
            equipment=equipment,
            quantity=quantity
        )
        
        messages.success(request, f'Added {quantity} {equipment.name} to your reservation cart.')
        return redirect('view_cart')
    
    return redirect('equipment_list')

@login_required
def view_cart(request):
    """View the current user's reservation cart."""
    # Check if user is faculty - if so, redirect them
    if hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty():
        messages.error(request, 'Faculty members cannot make equipment reservations.')
        return redirect('faculty_dashboard')
    
    cart_items = CartItem.objects.filter(user=request.user).select_related('equipment')
    
    context = {
        'cart_items': cart_items,
        'total_items': cart_items.count()
    }
    return render(request, 'student/cart.html', context)

@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the user's reservation cart."""
    # Check if user is faculty - if so, redirect them
    if hasattr(request.user, 'userprofile') and request.user.userprofile.is_faculty():
        messages.error(request, 'Faculty members cannot make equipment reservations.')
        return redirect('faculty_dashboard')
    
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
                # Parse datetime strings
                try:
                    start_time = datetime.datetime.fromisoformat(start_time_str)
                    end_time = datetime.datetime.fromisoformat(end_time_str)
                    
                    # Calculate time difference in hours
                    time_diff = (end_time - start_time).total_seconds() / 3600
                    
                    # Check if reservation exceeds 24 hours
                    if time_diff > 24:
                        messages.error(request, f'Reservation duration cannot exceed 24 hours. Your requested duration: {time_diff:.1f} hours.')
                        return redirect('view_cart')
                    
                    # Check if start time is in the past
                    if start_time < datetime.datetime.now():
                        messages.error(request, 'Start time cannot be in the past.')
                        return redirect('view_cart')
                    
                    # Check if end time is before start time
                    if end_time <= start_time:
                        messages.error(request, 'End time must be after start time.')
                        return redirect('view_cart')
                    
                except ValueError:
                    messages.error(request, 'Invalid date/time format. Please use the datetime picker.')
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
                    
                    # Check reservation time frame (cannot exceed 24 hours)
                    try:
                        start_time = datetime.datetime.fromisoformat(item.start_time)
                        end_time = datetime.datetime.fromisoformat(item.end_time)
                        
                        # Calculate time difference in hours
                        time_diff = (end_time - start_time).total_seconds() / 3600
                        
                        # Check if reservation exceeds 24 hours
                        if time_diff > 24:
                            raise ValueError(f'Reservation for {item.equipment.name} cannot exceed 24 hours. Your requested duration: {time_diff:.1f} hours.')
                        
                        # Check if start time is in the past
                        if start_time < datetime.datetime.now():
                            raise ValueError(f'Start time for {item.equipment.name} cannot be in the past.')
                        
                        # Check if end time is before start time
                        if end_time <= start_time:
                            raise ValueError(f'End time for {item.equipment.name} must be after start time.')
                            
                    except ValueError as e:
                        if 'fromisoformat' in str(e):
                            raise ValueError(f'Invalid date/time format for {item.equipment.name}. Please use the datetime picker.')
                        else:
                            raise e
                    
                    # Verify quantity is still available
                    equipment = item.equipment
                    if item.quantity > equipment.available_quantity:
                        raise ValueError(f'Only {equipment.available_quantity} units of {equipment.name} are available.')
                        
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
                    
                    # Update available quantity (temporarily reduce while pending approval)
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
def faculty_analytics(request):
    """Advanced analytics dashboard for faculty members."""
    if not request.user.userprofile.is_faculty():
        messages.error(request, 'Only faculty members can access this page.')
        return redirect('faculty_login')

    # Date range filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days if no date range is specified
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Convert dates to datetime for query
    start_datetime = timezone.datetime.combine(start_date, timezone.datetime.min.time())
    end_datetime = timezone.datetime.combine(end_date, timezone.datetime.max.time())
    
    # Base querysets
    equipments = MultimediaEquipment.objects.all()
    usages = EquipmentUsage.objects.filter(
        checkout_time__gte=start_datetime,
        checkout_time__lte=end_datetime
    ).select_related('equipment', 'user', 'user__userprofile')
    
    # 1. Equipment Utilization Rate
    total_equipment_count = equipments.count()
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
    popular_equipment = usages.values(
        'equipment__id', 'equipment__name', 'equipment__equipment_type'
    ).annotate(
        usage_count=Count('id')
    ).order_by('-usage_count')[:10]
    
    # 5. Underutilized Equipment (Bottom 10)
    # First, get counts for all equipment that has been used
    equipment_usage_counts = dict(usages.values('equipment').annotate(
        count=Count('id')).values_list('equipment', 'count'))
    
    # Then identify equipment with zero or low usage
    all_equipment = equipments.values('id', 'name', 'equipment_type')
    for item in all_equipment:
        item['usage_count'] = equipment_usage_counts.get(item['id'], 0)
    
    underutilized_equipment = sorted(all_equipment, key=lambda x: x['usage_count'])[:10]
    
    # 6. Category-wise Usage
    category_usage = usages.values(
        'equipment__category__id', 'equipment__category__name'
    ).annotate(
        usage_count=Count('id')
    ).order_by('-usage_count')
    
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
    overbooked_equipment = usages.filter(
        status='rejected'
    ).values(
        'equipment__id', 'equipment__name'
    ).annotate(
        reject_count=Count('id')
    ).order_by('-reject_count')[:5]
    
    # Prepare context data
    context = {
        'utilization_rate': round(utilization_rate, 1),
        'hours_data': hours_data,
        'days_data': list(days_data.values()),
        'popular_equipment': popular_equipment,
        'underutilized_equipment': underutilized_equipment,
        'category_usage': category_usage,
        'avg_duration': round(avg_duration, 1),
        'max_duration': round(max_duration, 1),
        'overbooked_equipment': overbooked_equipment,
        'start_date': start_date,
        'end_date': end_date,
        'active_tab': 'analytics'
    }
    
    return render(request, 'faculty/analytics.html', context)
