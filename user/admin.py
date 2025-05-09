# user/admin.py
from django.contrib import admin
from .models import User, Room, House, Contact, Booking

# Customizing User model in admin
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'city', 'state', 'number', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'name', 'city')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'city', 'state')  # Use the actual fields here
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'location', 'city', 'state', 'number')}),
        ('Permissions', {'fields': ('active', 'staff', 'is_superuser')}),  # Use the actual fields
    )

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

# Register the admin
admin.site.register(User, CustomUserAdmin)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'user_email', 'location', 'city', 'cost', 'bedrooms', 'AC', 'date')
    list_filter = ('city', 'state', 'bedrooms', 'AC', 'kitchen', 'hall', 'balcany')
    search_fields = ('location', 'city', 'desc', 'user_email__email')
    date_hierarchy = 'date'
    raw_id_fields = ('user_email',) # Good for ForeignKey fields with many instances


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('house_id', 'user_email', 'location', 'city', 'cost', 'bedrooms', 'floor', 'AC', 'date')
    list_filter = ('city', 'state', 'bedrooms', 'floor', 'AC', 'kitchen', 'hall', 'balcany')
    search_fields = ('location', 'city', 'desc', 'user_email__email')
    date_hierarchy = 'date'
    raw_id_fields = ('user_email',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('contact_id', 'subject', 'email', 'body')
    list_filter = ('subject',)
    search_fields = ('subject', 'email', 'body')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'property_type', 'get_property_display', 'check_in', 'check_out', 'status', 'booking_date', 'get_total_price')
    list_filter = ('status', 'property_type', 'check_in', 'check_out')
    search_fields = ('user__email', 'room__location', 'house__location', 'notes')
    date_hierarchy = 'booking_date'
    raw_id_fields = ('user', 'room', 'house')
    actions = ['approve_bookings', 'reject_bookings']

    def get_property_display(self, obj):
        return obj.get_property()
    get_property_display.short_description = 'Property'

    def approve_bookings(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} bookings were successfully approved.", level=admin.messages.SUCCESS)
    approve_bookings.short_description = "Mark selected bookings as Approved"

    def reject_bookings(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} bookings were successfully rejected.", level=admin.messages.ERROR)
    reject_bookings.short_description = "Mark selected bookings as Rejected"

    # Custom logic to prevent editing room/house directly if they are linked to a booking
    # Not essential for basic functionality, but good for data integrity
    # def get_readonly_fields(self, request, obj=None):
    #     if obj: # obj is not None, so it's an edit
    #         return self.readonly_fields + ('room', 'house', 'property_type')
    #     return self.readonly_fields


