import datetime

from django.shortcuts import render, redirect
from django.db.models import Max

from core.billy import export_invoice
from core.google_calendar import get_unsynchronized_events
from core.models import convert_calendar_event_to_appointment, LastAppointmentImport
from core.models import Appointment, AppointmentSeries
from core.models import LastInvoiceLinesEksport
from core.models import import_customers, import_appointment_types


def display_events(request):
    not_yet_imported = [
        event for event in
        get_unsynchronized_events()
        if event["id"] not in Appointment.objects.values_list("cal_id", flat=True)
    ]
    return render(request, "import_events.html", {"events": not_yet_imported})


def import_events(request):
    for calendar_event in get_unsynchronized_events():
        appointment = convert_calendar_event_to_appointment(calendar_event)

    # Log tidsstemplet for importen
    LastAppointmentImport.objects.create(timestamp=datetime.datetime.utcnow())
    return redirect('display_events')


def display_invoices(request):
    ready_for_export = (
        AppointmentSeries.objects
        .annotate(latest_end=Max('appointments__end'))
        .filter(
            already_synchronized=False,
            latest_end__lte=datetime.date.today() - datetime.timedelta(days=1),
        )
    )
    
    return render(request, "export_invoices.html", {"ready_for_export": ready_for_export})


def export_invoices(request):
    ids = request.POST.getlist("id")
    for series_id in ids:
        appointment_series = AppointmentSeries.objects.get(id=series_id)
        export_invoice(appointment_series)
    
    LastInvoiceLinesEksport.objects.create(timestamp=datetime.datetime.utcnow())
    return redirect('display_invoices')


def display_system(request):
    return render(request, "system.html")


def import_and_update_products(request):
    system = request.POST.get("system")
    import_appointment_types(system)
    return redirect("display_system")


def import_and_update_customers(request):
    system = request.POST.get("system")
    import_customers(system)
    return redirect("display_system")

def display_frontpage(request):
    return render(request, "frontpage.html")