from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Min, Max

from .models import Customer
from .models import AppointmentType
from .models import AppointmentSeries
from .models import Appointment
from .models import LastAppointmentImport


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "alt_name", "contact_id")


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0


@admin.register(AppointmentSeries)
class AppointmentSeriesAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer', 'start_date', 'end_date',
        'number_of_appointments', 'already_synchronized_display'
    )
    inlines = [AppointmentInline]

    def already_synchronized_display(self, obj):
        if obj.already_synchronized:
            return format_html('<span style="color: #006b1b;">&#10004;</span>')  # Grønt hak
        return format_html('<span style="color: red;">&#10008;</span>')  # Rødt kryds
    already_synchronized_display.short_description = 'Synchronized'

    def number_of_appointments(self, obj):
        return obj.appointments.count()

    def start_date(self, obj):
        return obj.appointments.aggregate(Min('start'))['start__min']

    def end_date(self, obj):
        return obj.appointments.aggregate(Max('end'))['end__max']
    

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('type', 'get_customer_name', 'get_customer_alt_name', 'start', 'end')

    def get_customer_name(self, obj):
        return obj.series.customer.name
    get_customer_name.short_description = 'customer name'

    def get_customer_alt_name(self, obj):
        return obj.series.customer.alt_name
    get_customer_alt_name.short_description = 'alt. name'


@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'name')


@admin.register(LastAppointmentImport)
class LastAppointmentImportAdmin(admin.ModelAdmin):
    pass
