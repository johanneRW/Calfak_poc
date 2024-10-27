import datetime

from django.test import TestCase
from django.utils import timezone

from core.models import Appointment, AppointmentSeries, AppointmentType, Customer
from core.models import add_appointment, convert_calendar_event_to_appointment


class AddAppointmentTest(TestCase):
    """Test the 'add_appointment' function"""

    def setUp(self):
        self.customer = Customer.objects.create(name="Test customer")
        self.type = AppointmentType.objects.create(name="Test type")

    def test_new_series(self):
        # Test hvad der sker, hvis vi tilføjer en aftale uden at der findes nogen
        # foregående aftaler, eller serier.
        # Så skal der automatisk oprettes en ny serie.
        appointment = add_appointment(
            self.customer,
            self.type,
            self._get_datetime(2020, 1, 1, 12),
            self._get_datetime(2020, 1, 1, 14),
        )
        self.assertIsNotNone(appointment.series)
        self.assertIsNotNone(appointment.series.id)
        self.assertEqual(appointment.series.customer, self.customer)
    
    def test_add_to_existing_series(self):
        # Test hvad der sker, hvis aftale A og B ligger mindre end et døgn fra hinanden.
        # Så skal aftale B lægges i samme serie som A.
        appointment_a = add_appointment(
            self.customer,
            self.type,
            self._get_datetime(2020, 1, 1, 12),
            self._get_datetime(2020, 1, 1, 14),
        )
        appointment_b = add_appointment(
            self.customer,
            self.type,
            self._get_datetime(2020, 1, 2, 12),
            self._get_datetime(2020, 1, 2, 14),
        )
        self.assertEqual(appointment_a.series, appointment_b.series)

    def test_start_new_series_if_too_distant(self):
        # Test hvad der sker, hvis aftale A og B ligger mere end et døgn fra hinanden.
        # Så skal aftale B starte sin egen serie.
        appointment_a = add_appointment(
            self.customer,
            self.type,
            self._get_datetime(2020, 1, 1, 12),
            self._get_datetime(2020, 1, 1, 14),
        )
        appointment_b = add_appointment(
            self.customer,
            self.type,
            self._get_datetime(2020, 1, 3, 12),
            self._get_datetime(2020, 1, 3, 14),
        )
        self.assertNotEqual(appointment_a.series, appointment_b.series)
        self.assertEqual(appointment_a.series.id, 1)
        self.assertEqual(appointment_b.series.id, 2)

    def _get_datetime(self, year, month, day, hour):
        return datetime.datetime(year, month, day, hour, tzinfo=timezone.utc)


class ConvertCalendarEventToAppointmentTest(TestCase):
    """Test the 'convert_calendar_to_appointment' function"""

    def setUp(self):
        self.customer = Customer.objects.create(name="Test customer")
        self.type = AppointmentType.objects.create(name="Test type")
    
    def test_good_match(self):
        # Test hvad der sker, hvis vi har en kalender-event, der matcher præcis
        # een kunde og een aftale-type. Så skal funktionen returnere en aftale.
        
        # Simuler en kalender-event uden at hente den fra fx Google Calendar
        calendar_event = {
            "summary": "Noget der matcher Test customer",
            "description": "Noget der matcher Test type og/eller Test customer",
            "start": {"date": "2023-12-13T01:30:00+01:00"},
            "end": {"date": "2023-12-13T02:30:00+01:00"},
            "id": "3dj2sa3evd926mgqpk3n4ui9ng",
        }
        
        appointment = convert_calendar_event_to_appointment(calendar_event)

        expected_tz = datetime.timezone(datetime.timedelta(seconds=3600))

        self.assertEqual(appointment.series.customer, self.customer)
        self.assertEqual(appointment.type, self.type)
        self.assertEqual(appointment.start, datetime.datetime(2023, 12, 13, 1, 30, tzinfo=expected_tz))
        self.assertEqual(appointment.end, datetime.datetime(2023, 12, 13, 2, 30, tzinfo=expected_tz))
        self.assertEqual(appointment.cal_id, calendar_event["id"])
