import datetime
from itertools import groupby
from django.conf import settings

import requests

BASE_URL = "https://restapi.e-conomic.com/"



HEADERS = {'X-AppSecretToken': settings.APP_SECRET_TOKEN, 'X-AgreementGrantToken': settings.AGREEMENT_GRANT_TOKEN,
           'Content-Type': "application/json"}


def export_invoice(appointment_series):
    if appointment_series.already_synchronized:
        return

    contact_id = appointment_series.customer.contact_id

    lines = []
    groups = groupby(
        appointment_series.appointments.order_by('type__name'),
        lambda appointment: appointment.type.name
    )

    for group_name, group in groups:
        items = list(group)
        lines.append(
            {
                "product": {
                    "productNumber": items[0].type.product_id
                },
                "quantity": len(items),
                "unitNetPrice": items[0].type.price,
                "description": ", ".join(app.start.strftime("%d-%m-%y %H:%M") for app in items)
            }
        )

    invoice = {
        "date": datetime.date.today().isoformat(),
        "currency": "DKK",
        "paymentTerms": {
            "paymentTermsNumber": 1,
        },
        "customer": {
            "customerNumber": int(contact_id),
        },
        "recipient": {
            "name": appointment_series.customer.name,
            "vatZone": {
                "vatZoneNumber": 1,
            }
        },
        "layout": {
            "layoutNumber": get_default_layout_number(),
        },
        "lines": lines
    }

    response = requests.post(BASE_URL + "invoices/drafts", json=invoice, headers=HEADERS)

    appointment_series.already_synchronized = True
    appointment_series.save()

    return response.json()


def get_default_layout_number():
    response = requests.get(BASE_URL + "layouts", headers=HEADERS)
    doc = response.json()
    return doc["collection"][0]["layoutNumber"]


def get_products():
    result = []
    response = requests.get(BASE_URL + "products", headers=HEADERS)
    doc = response.json()
    for product in doc["collection"]:
        details = requests.get(
            BASE_URL + "products/%s" % product["productNumber"], headers=HEADERS
        )
        details_doc = details.json()
        result.append(
            {
                "id": product["productNumber"],
                "name": product["name"],
                "unitPrice": details_doc["salesPrice"],
            }
        )
    return result


def get_customers():
    result = []
    response = requests.get(BASE_URL + "customers", headers=HEADERS)
    doc = response.json()
    for customer in doc["collection"]:
        result.append(
            {
                "id": customer["customerNumber"],
                "name": customer["name"],
            }
        )
    return result
