from datetime import timedelta
import rq 
from rq import get_current_job
#from app import app as current_app, db
from app.dmarcparser  import DmarcReport
from app.models import Jobs, ReportEmails,ReportMetadata, ReportRecords, ReportUploads,Schedules,GMailAccounts, IMAPAccounts
import os
import traceback
import shutil
from datetime import datetime
from flask import current_app
#import  app as current_app
from app.gmailbox import GmailHelper
from app.imap import ImapEmailHelper
from app.main.serializer import Serializer
import urllib.request
import json

def process_uploaded_report(report_file,report_name, report_id,user_id=1,source='upload',schedule_id=0):
    running_job      =  None
    source_report_id =  report_id
    try:
        redis_job    = get_current_job()
        job_name     = 'app.tasks.process_uploaded_report'
        parameters   = f'{report_file},{report_name},{source_report_id},{user_id}'
        running_job  = Jobs.get({"name":job_name,"parameters": parameters,"report_id":source_report_id})
        job_id = redis_job.get_id()
        description = f'{job_name} with parameters {parameters}'
        job = Jobs(job_id=job_id, name=job_name,report_id=source_report_id, parameters=parameters, description=description,user_id=user_id,jobStatus=0, schedule=str(schedule_id),info=[f'Job queued in Redis with ID: {redis_job.id}'])
        job.save()
        report_file                          = report_file.replace('\\','/').replace('C:','/mnt/c')
        dmarc_report                         = DmarcReport(report_file)
        report_metadata                      = {}
        meta_report_id                       = ReportMetadata.get_record_count()+1
        report_metadata['report_id']         = meta_report_id
        report_metadata['report_name']       = report_name
        report_metadata['report_xml_schema'] = dmarc_report.xml_schema
        report_metadata['report_type']       = dmarc_report.report_type

        if  hasattr(dmarc_report,'report_metadata') and  dmarc_report.report_metadata:
            for k,v  in dmarc_report.report_metadata.items():
                report_metadata[k]=v
        if  hasattr(dmarc_report,'policy_published') and dmarc_report.policy_published:
            for k,v  in dmarc_report.policy_published.items():
                report_metadata[k]=v
        ReportMetadata(**report_metadata).save()

        record_count      = len(dmarc_report.records) if dmarc_report.records else 0
        report_record     = {}
        index             = ReportRecords.get_record_count()
        index             = index +1 if index else 1
        ip_dict           = {}
        access_token      = '1f081d29076cdc'

        for record in dmarc_report.records:
            report_record = {}
            report_record['report_id']         = meta_report_id
            report_record['report_name']       = report_name
            report_record['report_type']       = dmarc_report.report_type
            report_record['report_record_id']  = index
            redis_job.meta['progress']         = 100.0 * index / record_count
            redis_job.save_meta()
            for k,v in record.items():
                key= k.replace('-','_') 
                report_record[key]=v
                if key =='source_ip_address':
                    if v not in list(ip_dict.keys()):
                        with urllib.request.urlopen(f'https://ipinfo.io/{v}?token={access_token}') as response:
                           ip_dict[v]= json.loads(response.read())
                    report_record['source_ip_hostname']=ip_dict[v]['hostname']  if 'hostname' in ip_dict[v] else ''
                    report_record['source_ip_city']=ip_dict[v]['city']  if 'city' in ip_dict[v] else ''
                    report_record['source_ip_region']=ip_dict[v]['region']  if 'region' in ip_dict[v] else ''
                    report_record['source_ip_country']=ip_dict[v]['country']  if 'country' in ip_dict[v] else ''
                    report_record['source_ip_location']=ip_dict[v]['loc']  if 'loc' in ip_dict[v] else ''
                    report_record['source_ip_organization']=ip_dict[v]['org']  if 'org' in ip_dict[v] else ''
                    report_record['source_ip_postal']=  ip_dict[v]['postal'] if 'postal' in ip_dict[v] else ''
                    report_record['source_ip_timezone']=ip_dict[v]['org']     if 'org' in ip_dict[v] else ''         
            ReportRecords(**report_record).save()
            index+=1
        new_report_file = os.path.abspath(os.path.dirname(os.path.dirname(report_file)))+os.sep+"processed"+os.sep+os.path.basename(report_file)
        shutil.move(report_file, new_report_file)
        if source== 'upload':
            report_upload = ReportUploads.get({'report_id':source_report_id })
            if report_upload:
                report_upload['status']                = 1
                report_upload['processed_report_file'] = new_report_file
                report_upload['last_modified_date']    = datetime.now()
                report_upload.save()
        elif source=='email':
            report_mail = ReportEmails.get({'report_id':source_report_id })
            if  report_mail:
                report_mail['status']                = 1
                report_mail['processed_report_file'] = new_report_file
                report_mail['last_modified_date']    = datetime.now()
                report_mail.save()
        running_job = Jobs.get({"job_id":job_id})
        running_job.complete  = True
        running_job.endTime   = datetime.now()
        running_job.info      = running_job.info +[f'Job complete successfully at {running_job.endTime}. The uploaded file has been renamed from {report_file} to {new_report_file} ']
        running_job.jobStatus = Jobs.SUCCEEDED
        running_job.progress  = 100.0
        running_job.save()
    except Exception as e:
        traceback.print_exc()
        running_job = Jobs.get({"job_id":job_id})
        if running_job:
            running_job.complete    = False
            running_job.info        = running_job.info +[f'An error occured while processing the report ']
            running_job.errors      = running_job.errors.append(datetime.now().strftime("%Y%m%d_%H%M%S")+": "+str(e))
            running_job.jobStatus   = Jobs.FAILED
            running_job.save()

def linuxize_file(file_path):
    return file_path.replace('C:\\','/mnt/c/').replace('\\','/')

def process_gmail_reports(account_id):
    
    gmail_account = GMailAccounts.get({"account_id":account_id})
    gmailHelper = GmailHelper(gmail_account.servers,gmail_account.email_address,linuxize_file(gmail_account.credential_file),linuxize_file(gmail_account.token_file))
    service = gmailHelper.gmail_authenticate()
    results = gmailHelper.search_messages(service, gmail_account.report_filter)
    schedule = Schedules.get({"schedule_id":gmail_account.report_schedule})
    for msg in results:
        gmailHelper.read_dmarc_message(service, msg, current_app.config['EMAIL_PATH'],schedule.schedule_id)
    queue = rq.Queue(current_app.config['REDIS_QUEUE_NAME'], connection=current_app.redis)
    if schedule.repeat !=0:
        schedule_repeat      = schedule.repeat
        queue.enqueue_in(timedelta(seconds=schedule_repeat), 'app.tasks.process_gmail_reports', args=[account_id], job_timeout=current_app.config['SYNC_INTERVAL'])
        
    elif schedule.repeat is None or str(schedule.repeat).trim() == '' or schedule.repeat == 0:
         months_in_seconds   = schedule.months * 3600 *24 * 30
         weeks_in_seconds    = schedule.weeks  * 3600 *24 * 7
         days_in_seconds     = schedule.days * 3600 * 24 
         hours_in_seconds    = schedule.hours * 3600
         minutes_in_seconds  = schedule.months * 60
         seconds             = schedule.seconds
         schedule_repeat     = months_in_seconds+weeks_in_seconds+days_in_seconds+hours_in_seconds+minutes_in_seconds+seconds
         queue.enqueue_in(timedelta(seconds=schedule_repeat), 'app.tasks.process_gmail_reports', args= [account_id], job_timeout=current_app.config['SYNC_INTERVAL'])     
    #else:
    #    queue.enqueue('app.tasks.process_gmail_reports', args=[account_id], job_timeout=current_app.config['SYNC_INTERVAL'])
        
def process_imap_reports(account_id):
    imap_account  = IMAPAccounts.get({"account_id":account_id})
    email_address = imap_account.imap_username       
    imap_server   = imap_account.imap_server_address 
    password      = imap_account.imap_password
    key_maker     = Serializer()
    count         = current_app.config['CIPHER_COUNT']
    password      = key_maker.multiDemystify(password,count)
    port          = imap_account.imap_port
    security      = str(imap_account.imap_security).lower()
    imapHelper    = ImapEmailHelper(imap_server,email_address, password,  port,current_app.config['EMAIL_PATH'], security)
    imapHelper.get_mailbox_messages('INBOX',imap_account.imap_report_schedule)
    imapHelper.close_connection()
    schedule = Schedules.get({"schedule_id":imap_account.imap_report_schedule}) if imap_account.imap_report_schedule!= 'none' else 0
    queue = rq.Queue(current_app.config['REDIS_QUEUE_NAME'], connection=current_app.redis)

    if schedule.repeat       !=0:
        schedule_repeat      = schedule.repeat
        queue.enqueue_in(timedelta(seconds=schedule_repeat), 'app.tasks.process_imap_reports', args=[account_id], job_timeout=current_app.config['SYNC_INTERVAL'])  
    elif schedule.repeat is None or str(schedule.repeat).trim() == '' or schedule.repeat == 0:
         months_in_seconds   = schedule.months * 3600 *24 * 30
         weeks_in_seconds    = schedule.weeks  * 3600 *24 * 7
         days_in_seconds     = schedule.days * 3600 * 24 
         hours_in_seconds    = schedule.hours * 3600
         minutes_in_seconds  = schedule.months * 60
         seconds             = schedule.seconds
         schedule_repeat     = months_in_seconds+weeks_in_seconds+days_in_seconds+hours_in_seconds+minutes_in_seconds+seconds
         queue.enqueue_in(timedelta(seconds=schedule_repeat), 'app.tasks.process_imap_reports', args= [account_id], job_timeout=current_app.config['SYNC_INTERVAL'])
    #else:
    #    queue.enqueue('app.tasks.process_imap_reports', args=[account_id], job_timeout=current_app.config['SYNC_INTERVAL'])