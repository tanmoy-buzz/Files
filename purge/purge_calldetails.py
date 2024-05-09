from django.core.management.base import BaseCommand
from crm.models import *
from callcenter.models import *
import datetime

class Command(BaseCommand):
    def handle(self, **options):
        try:
            # campaign_names = [
            #     'test'
            # ]
            # start_date = datetime.datetime(2023, 5, 1, 8, 00, 47, 537695)
            # print('strdate',start_date,type(start_date))
            end_date= datetime.datetime(2022, 11, 1, 8, 00, 47, 537695)
            print("en",end_date)
            # for campaign_name in campaign_names:
            #     campaign = Campaign.objects.filter(name=campaign_name).first()
            #     print("campaign",campaign)
            #     if campaign:
            CallDetail.objects.filter(Q(created__lte=end_date)).delete()
                    # print("@@@@@@@",cdr_rp)
                    # cdr_rp.delete()
            print("###########")

        except Exception as e:
            print('Exception in delete selected campaign', e)
