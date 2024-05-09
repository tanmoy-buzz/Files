from django.core.management.base import BaseCommand
from django.db.models import Q
import datetime
from crm.models import Contact

def delete_contact_data():
    end_date= datetime.datetime(2023, 7, 31, 8, 00, 47, 537695)
    Contact.objects.filter(Q(created_date__lte=end_date)).delete()
    print("===done=========")
           

if __name__ == "__main__":
    delete_contact_data()
    print(f"entries deleted successfully.")