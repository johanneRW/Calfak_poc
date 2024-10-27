import datetime

from django.db import models
from rapidfuzz import fuzz
from django.db.models import Min, Max


class Customer(models.Model):
    name = models.TextField()
    alt_name = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    contact_id = models.CharField(max_length=200, unique=True)  # Contact ID in external system (Billy)

    def __str__(self):
        if self.alt_name:
            return f"{self.name} ({self.alt_name})"
        return f"{self.name}"


class AppointmentType(models.Model):
    name = models.TextField()
    alt_name = models.TextField(null=True, blank=True)
    product_id = models.CharField(max_length=200, unique=True)  # Product ID in external system (Billy)
    price = models.FloatField()

    def __str__(self):
        return f"{self.name} ({self.product_id})"


class AppointmentSeries(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    already_synchronized = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.customer}, {self.already_synchronized}"
    
    def start_date(self):
        return self.appointments.aggregate(Min('start'))['start__min']
    
    def end_date(self):
        return self.appointments.aggregate(Max('end'))['end__max']


class Appointment(models.Model):
    series = models.ForeignKey(AppointmentSeries, related_name='appointments', on_delete=models.DO_NOTHING)
    type = models.ForeignKey(AppointmentType, on_delete=models.DO_NOTHING)
    start = models.DateTimeField()
    end = models.DateTimeField()
    cal_id = models.TextField(null=True)  # Event ID in external system (Google Calendar)
    system_note = models.TextField(null=True, blank=True)  # Anvendes hvis aftalen ikke matcher nogen kunde eller varenummer

    def __str__(self):
        return f"{self.start} - {self.end}, {self.type}"


def add_appointment(customer, type, start, end, system_note):
    # Find serier for samme kunde, hvor der findes aftaler enten på samme dag eller dagen før
    existing_series = AppointmentSeries.objects.filter(
        customer=customer,
        appointments__start__date__gte=start.date() - datetime.timedelta(days=1),
        appointments__start__date__lte=start.date()
    )

    if existing_series.exists():
        # Brug den eksisterende serie
        series = existing_series.first()
    else:
        # Opret en ny serie, hvis der ikke findes nogen
        series = AppointmentSeries.objects.create(customer=customer)
    
    # Opret den nye aftale
    appointment = Appointment.objects.create(
        series=series, 
        type=type,
        start=start,
        end=end,
        system_note=system_note,
    )

    return appointment


def find_customer(summary):
    best_match = None
    highest_score = 0
    customers = Customer.objects.all()

    for customer in customers:
        for name in (customer.name, customer.alt_name):
            score = fuzz.partial_ratio(name, summary)
            print("Leder efter %r i %r - score=%r" % (name, summary, score))
            if score > highest_score:
                best_match = customer
                highest_score = score

    if highest_score > 85:  # Denne tærskel kan justeres efter behov
        return best_match, None
    else:
        default_customer = Customer.objects.get(name="Default")
        return default_customer, "Kunne ikke matche kunden (input var %r)" % summary


def find_type(summary, description):
    best_match = None
    highest_score = 0
    types = AppointmentType.objects.all()

    for type in types:
        for name in (type.name, type.alt_name):
            for input_text in (summary, description):
                score = fuzz.partial_ratio(name, input_text)
                if score > highest_score:
                    best_match = type
                    highest_score = score

    if highest_score > 85:  # Juster denne tærskel efter behov
        return best_match, None
    else:
        default_type = AppointmentType.objects.get(name="Default")
        return default_type, "Kunne ikke matche aftaletype (input var %r)" % description
        

def parse_calendar_date(calendar_date):
    val = calendar_date.get("dateTime", calendar_date.get("date"))
    return datetime.datetime.fromisoformat(val)


def convert_calendar_event_to_appointment(calendar_event):
    customer, system_note_a = find_customer(calendar_event["summary"])
    type, system_note_b = find_type(calendar_event["summary"], calendar_event.get("description"))
    start = parse_calendar_date(calendar_event["start"])
    end = parse_calendar_date(calendar_event["end"])

    if system_note_a or system_note_b:
        system_note = "%r - %r" % (system_note_a, system_note_b)
    else:
        system_note = None

    # Tjek om vi allerede har gemt kalender-eventen som en Appointment
    appointments = Appointment.objects.filter(cal_id=calendar_event["id"])
    if appointments.exists():
        # TODO: opdater en eksisterende Appointment (?)
        return 
    else:
        appointment = add_appointment(customer, type, start, end, system_note)
        appointment.cal_id = calendar_event["id"]
        appointment.save() 
        return appointment


# gem timpestamp for sidste import så det kan bruges når der skal hentes nye appointments ind
class LastAppointmentImport(models.Model):
    timestamp = models.DateTimeField()


# gem timpestamp for sidste ekspot så det kan bruges når der skal eksporteres kontolinjer
class LastInvoiceLinesEksport(models.Model):
    timestamp = models.DateTimeField()  


def import_appointment_types(system):
    if system == "economic":
        from core.economic import get_products
    elif system == "billy":
        from core.billy import get_products
    else:
        raise Exception("No support for system=%s" % system)

    objs = [
        AppointmentType(
            name=product["name"], product_id=product["id"], price=product["unitPrice"]
        )
        for product in get_products()
    ]

    # Docs: https://docs.djangoproject.com/en/4.2/ref/models/querysets/#django.db.models.query.QuerySet.bulk_create
    # Example: https://stackoverflow.com/a/74189912
    AppointmentType.objects.bulk_create(
        objs,
        update_conflicts=True,
        unique_fields=["product_id"],
        update_fields=["name", "price"],
    )


def import_customers(system):
    if system == "economic":
        from core.economic import get_customers
    elif system == "billy":
        from core.billy import get_customers
    else:
        raise Exception("No support for system=%s" % system)

    objs = [
        Customer(name=customer["name"], contact_id=customer["id"])
        for customer in get_customers()
    ]

    # Docs: https://docs.djangoproject.com/en/4.2/ref/models/querysets/#django.db.models.query.QuerySet.bulk_create
    # Example: https://stackoverflow.com/a/74189912
    Customer.objects.bulk_create(
        objs,
        update_conflicts=True,
        unique_fields=["contact_id"],
        update_fields=["name"],
    )
