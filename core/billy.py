import datetime
from itertools import groupby
from django.conf import settings 

import requests

# Reusable class for sending requests to the Billy API
# Source: https://www.billy.dk/api/

class BillyClient:
    def __init__(self, apiToken):
        self.apiToken = apiToken

    def request(self, method, url, body):
        baseUrl = 'https://api.billysbilling.com/v2'
        try:
            response = {
                'GET': requests.get(
                    baseUrl + url,
                    headers={'X-Access-Token': self.apiToken}
                ),
                'POST': requests.post(
                    baseUrl + url,
                    json=body,
                    headers={'X-Access-Token': self.apiToken}
                ),
            }[method]
            status_code = response.status_code
            raw_body = response.text
            if status_code >= 400:
                raise requests.exceptions.RequestException(
                    '{}: {} failed with {:d} - {}'
                    .format(method, url, status_code, raw_body)
                )
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            raise e


# Get id of organization associated with the API token.
def getOrganizationId(client):
    response = client.request('GET', '/organization', None)
    return response['organization']['id']


def export_invoice(appointment_series):
    if appointment_series.already_synchronized:
        return

    client = BillyClient(settings.API_TOKEN)
    organization_id = getOrganizationId(client)

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
                "productId": items[0].type.product_id,
                "quantity": len(items),
                "unitPrice": items[0].type.price,
                "description": ", ".join(app.start.strftime("%d-%m-%y %H:%M") for app in items)
            }
        )

    invoice = {
        'organizationId': organization_id,
        'entryDate': datetime.date.today().isoformat(),
        'contactId': contact_id,
        'lines': lines
    }

    response = client.request('POST', '/invoices', {'invoice': invoice})
    invoice_id = response['invoices'][0]['id']

    appointment_series.already_synchronized = True
    appointment_series.save()

    return invoice_id

def get_products():
    result = []
    client = BillyClient(settings.API_TOKEN)
    response = client.request('GET', '/products', None)
    for product in response["products"]:
        prices = client.request('GET', '/productPrices?productId=%s' % product["id"], None)
        result.append(
            {
                "id": product["id"],
                "name": product["name"],
                "unitPrice": prices["productPrices"][0]["unitPrice"],
            }
        )
    return result


def get_customers():
    result = []
    client = BillyClient(settings.API_TOKEN)
    response = client.request('GET', '/contacts', None)
    for contact in response["contacts"]:
        result.append(
            {
                "id": contact["id"],
                "name": contact["name"],
            }
        )
    return result
