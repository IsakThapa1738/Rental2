from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import User, Room, House
from django.contrib import messages

@login_required(login_url='/login')
def profile(request):
    # It's more standard to use request.user for logged-in users
    # Assuming 'member_id' was intended to store the user's email during login
    email = request.session.get('member_id')

    if not email:
        messages.error(request, "User information not found in session. Please log in again.")
        return redirect('login')

    try:
        # Use get() instead of filter() if you expect only one user with that email
        user = User.objects.get(email=email)
        context = {
            'user': user,
        }
        return render(request, 'user/profile.html', context)
    except User.DoesNotExist:
        messages.error(request, "User account not found.")
        return redirect('index') # Or some other appropriate page
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        return redirect('index') # Or some other appropriate error handling

def post(request):
	user = request.session['member_id']
	return render(request, 'user/post.html', {'user':user})
