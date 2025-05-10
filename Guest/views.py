from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
# from .forms import SignUpForm
from django.template import loader
from user.models import *
from datetime import *
import re
import os
from django.contrib import messages
from django.db.models import Q


def index(request):
    template = loader.get_template('index.html')
    context = {}

    room = Room.objects.all()
    if bool(room):
        n = len(room)
        nslide = n // 3 + (n % 3 > 0)
        rooms = [room, range(1, nslide), n]
        context.update({'room': rooms})
    house = House.objects.all()
    if bool(house):
        n = len(house)
        nslide = n // 3 + (n % 3 > 0)
        houses = [house, range(1, nslide), n]
        context.update({'house': houses})
    return HttpResponse(template.render(context, request))


def home(request):
    template = loader.get_template('home.html')
    context = {}
    context.update({'result': ''})
    context.update({'msg': 'Search your query'})
    return HttpResponse(template.render(context, request))


def search(request):
    # Use render shortcut instead of loader
    # template = loader.get_template('home.html')
    context = {}

    if request.method == 'GET':
        # --- Get all potential filter parameters ---
        typ = request.GET.get('type', '') # House or Apartment
        q = request.GET.get('q', '').strip() # Location query (city, location, state)
        keywords = request.GET.get('keywords', '').strip()
        min_cost = request.GET.get('min_cost', '')
        max_cost = request.GET.get('max_cost', '')
        bedrooms = request.GET.get('bedrooms', '')
        # Amenities - treat presence of param as 'yes' if using checkboxes without value="yes"
        # Or check value if using value="yes" e.g., request.GET.get('ac') == 'yes'
        ac = request.GET.get('ac', '') # Expecting 'yes' if checked
        kitchen = request.GET.get('kitchen', '') # Expecting 'yes'
        hall = request.GET.get('hall', '') # Expecting 'yes'
        balcony = request.GET.get('balcony', '') # Expecting 'yes' (Note: model field is 'balcany')
        sort_by = request.GET.get('sort_by', '') # e.g., 'price_asc', 'price_desc', 'date_new'

        # --- Pass parameters back to context for form repopulation ---
        context.update({
            'type': typ,
            'q': q,
            'keywords': keywords,
            'min_cost': min_cost,
            'max_cost': max_cost,
            'bedrooms': bedrooms,
            'ac': ac,
            'kitchen': kitchen,
            'hall': hall,
            'balcony': balcony,
            'sort_by': sort_by,
        })

        results_queryset = None

        # --- Apply filters based on type ---
        if typ == 'House':
            results_queryset = House.objects.all()
            model_name = "House"

            # Location Filter (City, Location, State) - Case Insensitive Contains
            if q:
                results_queryset = results_queryset.filter(
                    Q(location__icontains=q) |
                    Q(city__icontains=q) |
                    Q(state__icontains=q)
                )

            # Keyword Filter (Description) - Case Insensitive Contains
            if keywords:
                results_queryset = results_queryset.filter(desc__icontains=keywords)

            # Price Filter
            try:
                if min_cost:
                    results_queryset = results_queryset.filter(cost__gte=int(min_cost))
                if max_cost:
                    results_queryset = results_queryset.filter(cost__lte=int(max_cost))
            except ValueError:
                messages.error(request, "Invalid price value entered.")
                # Decide if you want to stop or continue without price filter
                # results_queryset = House.objects.none() # Option: show no results on bad input

            # Bedroom Filter (Minimum number)
            try:
                if bedrooms:
                    results_queryset = results_queryset.filter(bedrooms__gte=int(bedrooms))
            except ValueError:
                 messages.error(request, "Invalid bedroom value entered.")
                 # results_queryset = House.objects.none()

            # Amenity Filters (Case Insensitive Exact Match for 'yes'/'no' fields)
            if ac == 'yes':
                 # Assuming your model stores 'yes' or 'no'. Adjust if different.
                results_queryset = results_queryset.filter(AC__iexact='yes')
            if kitchen == 'yes':
                 # Assuming your model stores an integer for kitchens in House? If so:
                 # results_queryset = results_queryset.filter(kitchen__gte=1)
                 # If it's CharField 'yes'/'no' like Room:
                 messages.warning(request, "Kitchen filter might behave unexpectedly for Houses based on model definition (IntegerField).")
                 # Adjust logic based on how you store House kitchen info. Let's assume CharField for now:
                 results_queryset = results_queryset.filter(kitchen__iexact='yes') # MODIFY IF NEEDED
            if hall == 'yes':
                results_queryset = results_queryset.filter(hall__iexact='yes')
            if balcony == 'yes':
                # Use the actual field name from your model
                results_queryset = results_queryset.filter(balcany__iexact='yes') # Field name is 'balcany'

        elif typ == 'Apartment': # Corresponds to Room model
            results_queryset = Room.objects.all()
            model_name = "Apartment"

            # Location Filter (City, Location, State)
            if q:
                results_queryset = results_queryset.filter(
                    Q(location__icontains=q) |
                    Q(city__icontains=q) |
                    Q(state__icontains=q)
                )

            # Keyword Filter (Description)
            if keywords:
                results_queryset = results_queryset.filter(desc__icontains=keywords)

            # Price Filter
            try:
                if min_cost:
                    results_queryset = results_queryset.filter(cost__gte=int(min_cost))
                if max_cost:
                    results_queryset = results_queryset.filter(cost__lte=int(max_cost))
            except ValueError:
                messages.error(request, "Invalid price value entered.")
                # results_queryset = Room.objects.none()

            # Bedroom Filter
            try:
                if bedrooms:
                    results_queryset = results_queryset.filter(bedrooms__gte=int(bedrooms))
            except ValueError:
                 messages.error(request, "Invalid bedroom value entered.")
                 # results_queryset = Room.objects.none()

            # Amenity Filters
            if ac == 'yes':
                results_queryset = results_queryset.filter(AC__iexact='yes')
            if kitchen == 'yes':
                results_queryset = results_queryset.filter(kitchen__iexact='yes')
            if hall == 'yes':
                results_queryset = results_queryset.filter(hall__iexact='yes')
            if balcony == 'yes':
                # Use the actual field name from your model
                results_queryset = results_queryset.filter(balcany__iexact='yes') # Field name is 'balcany'

        else:
             # No valid type selected, or initial search page load without type
             if typ: # Only show error if a type was actually submitted
                 messages.error(request, "Please select a valid property type (House or Apartment).")
             results_queryset = None # Show no results unless a type is selected


        # --- Apply Sorting ---
        if results_queryset is not None:
            if sort_by == 'price_asc':
                results_queryset = results_queryset.order_by('cost')
            elif sort_by == 'price_desc':
                results_queryset = results_queryset.order_by('-cost')
            elif sort_by == 'date_new':
                results_queryset = results_queryset.order_by('-date')
            else:
                 # Default sort (maybe newest first?)
                 results_queryset = results_queryset.order_by('-date') # Example default

        # --- Prepare results for template ---
        final_results = []
        if results_queryset is not None:
            final_results = list(results_queryset) # Evaluate queryset
            if not final_results and (q or keywords or min_cost or max_cost or bedrooms or ac or kitchen or hall or balcony):
                # Only show 'no results' if filters were actually applied
                 messages.info(request, f"No matching {model_name}s found for your criteria.")
        elif typ: # If a type was selected but no results_queryset was created (e.g. invalid type)
            pass # Error message already handled


        result_list = [final_results, len(final_results)]
        context.update({'result': result_list})

    # If not GET, or initial load before search
    else:
         context.update({'result': [[], 0]}) # Empty result list
         # Optional: Add a default message for the initial page load if desired
         # context.update({'msg': 'Search for properties using the filters.'})


    # Use the render shortcut
    return render(request, 'home.html', context)



def about(request):
    template = loader.get_template('about.html')
    context = {}

    room = Room.objects.all()
    if bool(room):
        context.update({'room': room})
    house = House.objects.all()
    if bool(house):
        context.update({'house': house})
    return HttpResponse(template.render(context, request))


def contact(request):
    template = loader.get_template('contact.html')
    context = {}

    if request.method == 'POST':
        subject = request.POST['subject']
        email = request.POST['email']
        body = request.POST['body']
        regex = r'^[a-z0-9]+[\\._]?[a-z0-9]+[@]\\w+[.]\\w{2,3}$'
        if re.search(regex, email):
            pass
        else:
            template = loader.get_template('register.html')
            context.update({'msg': 'invalid email'})
            return HttpResponse(template.render(context, request))
        contact = Contact(subject=subject, email=email, body=body)
        contact.save()
        context.update({'msg': 'msg send to admin'})
        return HttpResponse(template.render(context, request))
    else:
        context.update({'msg': ''})
        return HttpResponse(template.render(context, request))


def descr(request):
    template = loader.get_template('desc.html')
    context = {}
    if request.method == 'GET':
        id = request.GET['id']
        try:
            room = Room.objects.get(room_id=id)
            context.update({'val': room})
            context.update({'type': 'Apartment'})
            user = User.objects.get(email=room.user_email)
        except:
            house = House.objects.get(house_id=id)
            context.update({'val': house})
            context.update({'type': 'House'})
            user = User.objects.get(email=house.user_email)
    context.update({'user': user})
    return HttpResponse(template.render(context, request))


# def loginpage(request):
#     return render(request, 'login.html', {'msg': ''})


# Guest/views.py

from django.contrib.auth import login
from django.shortcuts import render, redirect
from user.models import User
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        try:
            # Get all form data
            email = request.POST.get('email')
            name = request.POST.get('name')
            password = request.POST.get('password')
            number = request.POST.get('number')
            location = request.POST.get('location')
            city = request.POST.get('city')
            state = request.POST.get('state')
            is_owner = request.POST.get('is_owner') == 'on'  # Checkbox handling

            # Create user using your custom UserManager
            user = User.objects.create_user(
                email=email,
                name=name,
                password=password,
                number=number,
                location=location,
                city=city,
                state=state,
                is_owner=is_owner
            )

            # Log the user in
            login(request, user)
            return redirect('/profile/')

        except Exception as e:
            # Show error message if registration fails
            return render(request, 'register.html', {
                'msg': str(e),
                'form_data': request.POST  # Pass back form data to repopulate fields
            })

    # GET request - show empty form
    return render(request, 'register.html', {'msg': ''})

# Guest/views.py

@login_required()
def profile(request):
    report = Contact.objects.filter(email=request.user.email)
    context = {
        'user': request.user,
        'report': report,
        'reportno': report.count(),
    }

    if request.user.is_owner:
        room = Room.objects.filter(user_email=request.user)
        house = House.objects.filter(user_email=request.user)
        context.update({
            'roomno': room.count(),
            'houseno': house.count(),
        })
        if room.exists():
            n = len(room)
            nslide = n // 3 + (n % 3 > 0)
            context.update({'room': [room, range(1, nslide), n]})
        if house.exists():
            n = len(house)
            nslide = n // 3 + (n % 3 > 0)
            context.update({'house': [house, range(1, nslide), n]})
        return render(request, 'profile.html', context=context) # Create a separate template for owners
    else:
        bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
        context.update({'bookings': bookings})
        return render(request, 'profile.html', context=context) # Create a separate template for customers

# Guest/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from user.models import User, Room
from django.contrib import messages

@login_required(login_url='/login')
def post(request):
    if not request.user.is_owner:
        messages.error(request, "Only property owners can post rooms.")
        return redirect('profile') # Redirect to profile or another appropriate page

    if request.method == "GET":
        context = {'user': request.user}
        return render(request, 'post.html', context)
    elif request.method == "POST":
        try:
            dimention = request.POST.get('dimention', '').strip()
            location = request.POST.get('location', '').lower().strip()
            city = request.POST.get('city', '').lower().strip()
            state = request.POST.get('state', '').lower().strip()
            cost_str = request.POST.get('cost', '').strip()
            hall = request.POST.get('hall', '').lower().strip()
            kitchen = request.POST.get('kitchen', '').lower().strip()
            balcany = request.POST.get('balcany', '').lower().strip()
            bedroom_str = request.POST.get('bedroom', '').strip()
            ac = request.POST.get('AC', '').lower().strip()
            desc = request.POST.get('desc', '').upper().strip()
            img = request.FILES.get('img')

            # Validate required fields
            if not all([dimention, location, city, state, cost_str, bedroom_str, img]):
                messages.error(request, "Please fill in all required fields.")
                return render(request, 'post.html', {'user': request.user, 'form_data': request.POST})

            try:
                bedroom = int(bedroom_str)
                cost = int(cost_str)
                if bedroom <= 0 or cost <= 0:
                    messages.error(request, "Bedroom and cost must be positive numbers.")
                    return render(request, 'post.html', {'user': request.user, 'form_data': request.POST})
            except ValueError:
                messages.error(request, "Invalid value for bedroom or cost. Please enter numbers.")
                return render(request, 'post.html', {'user': request.user, 'form_data': request.POST})

            user_obj = request.user
            room = Room.objects.create(
                user_email=user_obj,
                dimention=dimention,
                location=location,
                city=city,
                state=state,
                cost=cost,
                hall=hall,
                kitchen=kitchen,
                balcany=balcany,
                bedrooms=bedroom,
                AC=ac,
                desc=desc,
                img=img,
            )
            messages.success(request, 'Apartment/Room details submitted successfully.')
            return redirect('/profile/') # Redirect to the user's profile page
        except Exception as e:
            messages.error(request, f"An error occurred while submitting: {e}")
            return render(request, 'post.html', {'user': request.user, 'form_data': request.POST})

    # If it's a GET request and the user is an owner, display the form
    return render(request, 'post.html', {'user': request.user})

@login_required(login_url='/login')
def posth(request):
    if request.method == "GET":
        context = {'user': request.user}
        return render(request, 'posth.html', context)
    else:
        try:
            area = request.POST['area']
            floor = request.POST['floor']
            location = request.POST['location'].lower()
            city = request.POST['city'].lower()
            state = request.POST['state'].lower()
            cost = request.POST['cost']
            hall = request.POST['hall'].lower()
            kitchen = request.POST['kitchen'].lower()
            balcany = request.POST['balcany'].lower()
            bedroom = request.POST['bedroom']
            ac = request.POST['AC'].lower()
            desc = request.POST['desc'].upper()
            img = request.FILES['img']
            bedroom = int(bedroom)
            cost = int(cost)
            user_obj = request.user  # Use request.user directly

            house = House.objects.create(
                user_email=user_obj,
                location=location,
                city=city,
                state=state,
                cost=cost,
                hall=hall,
                kitchen=kitchen,
                balcany=balcany,
                bedrooms=bedroom,
                area=area,
                floor=floor,
                AC=ac,
                desc=desc,
                img=img,
            )
            messages.success(request, 'House details submitted successfully.')
            return redirect('/profile/')  # Redirect to the user's profile page

        except Exception as e:
            print("\nError saving house:", e, "\n")
            messages.error(request, f"An error occurred while submitting: {e}")
            return render(request, 'posth.html', {'user': request.user, 'form_data': request.POST})

def deleter(request):
    if request.method == 'GET':
        id = request.GET['id']
        instance = Room.objects.get(room_id=id)
        instance.delete()
        messages.success(request, 'Appartment details deleted successfully..')
    return redirect('/profile')


def deleteh(request):
    if request.method == 'GET':
        id = request.GET['id']
        instance = House.objects.get(house_id=id)
        instance.delete()
        messages.success(request, 'House details deleted successfully..')
    return redirect('/profile')


def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html', {'msg': ''})

    email = request.POST['email']
    password = request.POST['password']
    user = authenticate(request, email=email, password=password)

    if user is not None:
        login(request, user)
        # Check if the user is a staff member or an admin
        if user.is_staff or user.is_admin:
            # Redirect to the Django admin site
            return redirect('/admin/')
        else:
            # Redirect to the user's profile page or home page for regular users
            return redirect('/profile/') # Or '/' if you want to redirect to index for normal users
    else:
        template = loader.get_template('login.html')
        context = {
            'msg': 'Email and password, you entered, did not match.'
        }
        return HttpResponse(template.render(context, request))

from django.shortcuts import render, redirect, get_object_or_404
from user.models import Booking, Room, House
from user.forms import BookingForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def create_booking(request, property_type, property_id):
    # Get the property
    if property_type == 'room':
        property_obj = get_object_or_404(Room, pk=property_id)
        property_filter = Q(room=property_obj)
    elif property_type == 'house':
        property_obj = get_object_or_404(House, pk=property_id)
        property_filter = Q(house=property_obj)
    else:
        messages.error(request, "Invalid property type")
        return redirect('index')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.property_type = property_type
            
            # Assign the correct property based on type
            if property_type == 'room':
                booking.room = property_obj
            else:
                booking.house = property_obj
            
            # Check for date conflicts using the correct filter
            conflicting_bookings = Booking.objects.filter(
                property_filter,
                check_in__lt=booking.check_out,
                check_out__gt=booking.check_in
            ).exclude(status__in=['rejected', 'cancelled'])
            
            if conflicting_bookings.exists():
                messages.error(request, "The property is not available for the selected dates")
            else:
                booking.save()
                messages.success(request, "Booking request sent to property owner")
                return redirect('booking_history')
    else:
        form = BookingForm()

    return render(request, 'booking/create.html', {
        'property': property_obj,
        'property_type': property_type,
        'form': form
    })

@login_required
def booking_history(request):
    """Show only bookings made by the current user"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, 'booking/history.html', {
        'bookings': bookings,
        'is_owner': False  # Indicates this is the guest's view
    })

@login_required
def update_booking_status(request, booking_id, status):
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Verify permission
    if not booking.can_manage(request.user):
        messages.error(request, "You don't have permission to manage this booking")
        return redirect('booking_history')
    
    # Validate status
    if status not in ['approved', 'rejected']:
        messages.error(request, "Invalid status")
        return redirect('booking_history')
    
    # Update status
    booking.status = status
    booking.save()
    messages.success(request, f"Booking #{booking.id} has been {status}")
    
    return redirect('booking_history')



@login_required
def received_bookings(request):
    """Show only bookings for the current user's properties"""
    bookings = Booking.objects.filter(
        Q(room__user_email=request.user) | Q(house__user_email=request.user)
    ).order_by('-booking_date')
    return render(request, 'booking/received.html', {
        'bookings': bookings,
        'is_owner': True  # Indicates this is the owner's view
    })

@login_required
def update_booking_status(request, booking_id, status):
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Verify the current user owns the property
    if not (booking.room and booking.room.user_email == request.user) and \
       not (booking.house and booking.house.user_email == request.user):
        messages.error(request, "You don't have permission to manage this booking")
        return redirect('received_bookings')
    
    if status in ['approved', 'rejected']:
        booking.status = status
        booking.save()
        messages.success(request, f"Booking has been {status}")
    
    return redirect('received_bookings')