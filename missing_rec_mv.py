import os
import sys
from flexydial import settings
from callcenter.models import DiallerEventLog
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime, timedelta
from django.core.files import File
from os import listdir
ENABLE = False

job_defaults = {
	'coalesce': True,
	'max_instances': 15
}
sched = BlockingScheduler()
sched.configure(job_defaults=job_defaults)

def recording_file_transfer():
		"""
		this function to insert recording file into bucket
		"""
		#if settings.AWS_STORAGE_BUCKET_NAME or settings.GS_BUCKET_NAME:
		try:
			push_rec_status = settings.R_SERVER.get("push_rec_status")
			if not push_rec_status or push_rec_status.decode('utf-8') == 'False':
				dialereventlog_emty_rec = DiallerEventLog.objects.filter(recording_file="",created__date__gte='2022-08-01',callserver=settings.FS_INTERNAL_IP)
				if dialereventlog_emty_rec:
					settings.R_SERVER.set("push_rec_status", True)
					for dialereventlog in dialereventlog_emty_rec:
						if dialereventlog.session_uuid:
							file_path=settings.RECORDING_ROOT+"/"+datetime.strptime(str(dialereventlog.ring_time),"%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y-%H-%M")+"_"+str(dialereventlog.customer_cid)+"_"+str(dialereventlog.session_uuid)+".mp3"
							onlyfiles = [f for f in listdir(settings.RECORDING_ROOT+"/")]
							ele = "_"+str(dialereventlog.customer_cid)+"_"+str(dialereventlog.session_uuid)+".mp3"
							print('ele', ele)
							all_rec_files = "~".join(onlyfiles)
							if os.path.isfile(file_path):
								save_recordings(dialereventlog,file_path)
							elif ele in all_rec_files:
								ind = all_rec_files.index(ele)
								start = ind - 16 #len("11-04-2022-17-45")
								end = ind+len(ele)
								file_path = settings.RECORDING_ROOT+"/"+all_rec_files[start:end]
								save_recordings(dialereventlog,file_path)
							else:
								print('File not exists ::',file_path)
					settings.R_SERVER.set("push_rec_status", False)	
				print("Recordings Moved to Bucket")
		except Exception as e:

			settings.R_SERVER.set("push_rec_status", False)	
			print("Exception occures from recording_file_transfer",e)
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print(exc_type, fname, exc_tb.tb_lineno)
def save_recordings(dialereventlog,file_path):
	# if (dialereventlog.connect_time or dialereventlog.dialed_status=='Connected'):
	f = open(file_path, 'rb')
	dialereventlog.recording_file.save(os.path.basename(f.name), File(f), save=True)
	dialereventlog.save()
	f.close()

def missing_recording_transfer():
	"""
	Start APSchedular for autodialing.
	"""
	global ENABLE
	sched.add_jobstore(MemoryJobStore(), 'list')
	execution_time = datetime.now() + timedelta(minutes=0.1)
	sched.add_job(recording_file_transfer,'interval',seconds=3600, start_date=execution_time,
						   id='autodial', jobstore='list')
	if sched.state == 0:
		sched.start()
if __name__ == '__main__':
	missing_recording_transfer()
