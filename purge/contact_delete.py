from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = "Describe AutoDial Commands"
    def handle(self, **options):

        from scripts import crm_contact
        crm_contact.delete_contact_data()