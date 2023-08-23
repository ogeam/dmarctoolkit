from flask import render_template, flash, redirect, request, url_for, g, jsonify, current_app,abort, send_from_directory,session
from werkzeug.utils import secure_filename
from app.models  import ReportUploads, ReportMetadata, IMAPAccounts,GMailAccounts,Schedules,Jobs,DmarcRecords
import app.models  as models
from datetime import datetime
from redis import Redis
import traceback, json, time, re, json, rq,os,re
from flask_login import current_user, login_required
from flask_babel import _, get_locale
#from guess_language import guess_language
from app import db,settings,get_debug_template,csrf,cache #,socketio
#from app.translate import translate
from app.api import bp
from app.main.serializer import Serializer
from rq.job import Job
from app.gmailbox import GmailHelper
import checkdmarc

def format_data(data):

    if str(type(data)) =='datetime.datetime':
        return data.strftime("%Y%m%d_%H%M%S")
    elif  str(type(data)) =='bson.objectid.ObjectId':
        return str(data)
    elif type(data) is dict:
        return json.dumps(data)
    elif type(data) is int:
        return  int(data)
    else:
        return str(data)
def get_collection_data(data):
    table_data  =[]
    for row in data:
        temp_data = {}
        for k,v in  row.items():
            if k== 'records':
               temp_data[k]= get_collection_data(v)
            else:     
                temp_data[k]=format_data(v)
        table_data.append(temp_data) 
    return table_data

@csrf.exempt
@bp.route('/api/dashboard/<start_date>/<end_date>/',methods = ['GET'])
@bp.route('/api/dashboard/<start_date>/<end_date>/<domain>',methods = ['GET'])
#@cache.cached()
@login_required
def get_stats_info(start_date,end_date,domain='.'):
    start_date= datetime.strptime(start_date, '%Y-%m-%d')
    end_date= datetime.strptime(end_date, '%Y-%m-%d')

    report_data = ReportMetadata.objects().aggregate( [ 
            { 
                    "$match":{  "report_metadata_begin_date": {"$gte": start_date,"$lte": end_date}   }
            }
            , { "$lookup": {
                            "from": "report_records",
                            "localField": "report_id",
                            "foreignField": "report_id",
                            "as": "records"
                        }
                },{

                    "$match":{
            "$or": [
            { 
                
                "policy_published_domain": {"$regex":  domain}
            }
          
            ]
            }
            } ] )
    """
            ,{ 
                
                "identifiers_header_from": {"$regex":  domain}
            },{ 
                
                "identifiers_envelope_from":{"$regex":  domain}
            },{ 
                
                "spf_domain": {"$regex":  domain}
            }
    """ 
    temp_data = list(report_data)
    results = get_collection_data(temp_data) if len(temp_data) >0   else []
    #print(results)
    return jsonify(results)

@csrf.exempt
@bp.route('/api/report/upload',methods = ['POST'])
@login_required
def handle_report_upload():
    """
    print('args')
    print(request.args)
    print('form')
    print(request.form)
    print('values')
    print(request.values)
    print('files')
    print(request.files)
    """
    report_name     = None
    report_type     = None
    report_org      = None

    report_file = request.files.get('report_file')
    report_name = request.form.get('report_name')
    report_type = request.form.get('report_type')
    report_org  = request.form.get('report_org')


    filename = secure_filename(report_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1].replace('.','')
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
            print('File extension is not valid: '+file_ext)
            abort(400)
        raw_report_file = os.path.join(current_app.config['UPLOAD_PATH'],filename) #.replace("\\","\\\\"))
        report_check    = ReportUploads.get({"raw_report_file":raw_report_file})
        
        report_check = True if  report_check  else False
        if not report_check:
            user_id             = 1
            report_file.save(os.path.join(current_app.config['UPLOAD_PATH'], filename))
            report_id           = ReportUploads.get_record_count()+1
            report_file_name    = os.path.join(current_app.config['UPLOAD_PATH'], filename)
            uploaded_report     = ReportUploads(report_id=report_id,report_name=report_name,report_type=report_type,report_organization=report_org,raw_report_file=report_file_name,created_datetime=datetime.now())
            uploaded_report.save()
            queue               = rq.Queue(current_app.config['REDIS_QUEUE_NAME'], connection=current_app.redis)
            source              = 'upload'
            queue.enqueue('app.tasks.process_uploaded_report', args=[report_file_name,report_name,report_id, user_id, source], job_timeout=current_app.config['SYNC_INTERVAL'])
            return  jsonify({"message":"Report uploaded successfully."})


@csrf.exempt
@bp.route('/api/data/<table>',methods = ['GET'])
#@cache.cached()
@login_required
def get_data(table):
    """
    print('args')
    print(request.args)
    print('form')
    print(request.form)
    print('values')
    print(request.values)
    """
    tables = []
    results = {}
    if '+' in table:
        tables = table.split('+')
    else:
        tables.append(table)
    for tab in tables:
        results[tab.lower()]=[]  
        collection =  models.__dict__[tab]
        query = request.args.get(tab.lower())
        if query == '{}':
            query ={}
        elif query != 'none':
            query= json.loads(query)

        if query =='none':
            break
        data= collection.find(query)
        data = data.to_json() 
        if len(data)>0:
            for row in json.loads(data):
                temp_data= {}
                for k,v in row.items():
                    if 'password' in k:
                        temp_data[k]='*'*12
                    elif 'date' in k or 'time' in k: 
                        temp_data[k]= (datetime.fromtimestamp(v['$date']/1000.0)).strftime("%Y-%m-%d %H:%M:%S") if '$date' in v else  v
                    elif k != '_id':
                        temp_data[k]=v
                results[tab.lower()].append(temp_data) 
        #print(results)
    return jsonify(results)

@csrf.exempt
@bp.route('/api/sync/<table>',methods = ['GET'])
@bp.route('/api/sync/<table>/<max_id>',methods = ['GET'])
#@cache.cached()
@login_required
def get_table_data(table, max_id=None):
    
    data = []
    results = []
    collection =  models.__dict__[table] if table in list(models.__dict__.keys()) else None
    if collection:
        sync_info  = [ info for info in current_app.config["COMPONENT_CONFIG"]["syncInfo"] if info["collectionName"]==table]
        if len(sync_info)>0:
            selector   = sync_info[0]['selector']
            if len(selector.keys()) >0:
                data = collection.find(selector)
            else:
                if max_id:
                    temp_data = {}
                    id_field = sync_info[0]['idField']
                    max_id = int(max_id)
                    id_field = f'{id_field}__gt'
                    temp_data[id_field]= max_id
                    data = collection.find(temp_data)
                    data = [entry.to_json() for entry in data]
                    
                else:
                    data= collection.find()
                    if len(data) >0:
                      data = [entry.to_json() for entry in data]
                for entry in data:
                    temp_data = {}
                    data_info = json.loads(entry) #if  type(entry) is str else entry
                    for k,v in data_info.items():
                        if k == '_id':
                            temp_data[k]=str(v['$oid']) if '$oid' in v else v
                        elif 'date' in k or 'time' in k: 
                            temp_data[k]= (datetime.fromtimestamp(v['$date']/1000.0)).strftime("%Y-%m-%d %H:%M:%S") if '$date' in v else  v
                        else:
                            temp_data[k]=v
                    results.append(temp_data)
        else:
            results=[]
    else:
            results=[]
    #if table in ['ReportMetadata','ReportRecords']:
    #    print(results)
    return jsonify(results)

@csrf.exempt
@bp.route('/api/add/<data_type>',methods = ['POST'])
@login_required
def add_record (data_type):
    """
    print('args')
    print(request.args)
    print('form')
    print(request.form)
    print('values')
    print(request.values)
    print('files')
    print(request.files)
    """
    count = current_app.config['CIPHER_COUNT']
    mode= request.form.get('mode')
    key_maker = Serializer()
    #print(mode)
    #print(data_type)
    if mode == 'new': 
        if data_type == 'imap':
            imap_server_address  = request.form.get('imap_server_address')
            imap_username        = request.form.get('imap_username')
            imap_password        = request.form.get('imap_password')
            imap_security        = request.form.get('imap_security')
            imap_report_schedule = request.form.get('imap_report_schedule')
            imap_port            = request.form.get('imap_port')
            imap_account_check   = IMAPAccounts.get({"imap_server_address":imap_server_address})
            
            is_existing_account = True if  imap_account_check  else False
            if not is_existing_account:
                account_id   = IMAPAccounts.get_record_count()+1
                imap_account = IMAPAccounts(account_id=account_id
                                            ,imap_server_address=imap_server_address
                                            ,imap_username=imap_username
                                            ,imap_password=key_maker.multiCrypt(imap_password,count)
                                            ,imap_security=imap_security
                                            ,imap_port= imap_port
                                            ,imap_report_schedule=imap_report_schedule
                                            ,created_datetime=datetime.now()
                                            )
                imap_account.save()
                queue = rq.Queue(current_app.config['REDIS_QUEUE_NAME'], connection=current_app.redis)
                queue.enqueue( 'app.tasks.process_imap_reports', args=[account_id], job_timeout=current_app.config['SYNC_INTERVAL'])
                return  jsonify({"message":"Account successfully added."})
            else:
                return  jsonify({"message":"Account already exists"})
        elif data_type == 'schedule':
            name  = request.form.get('schedule_name')
            description        = request.form.get('schedule_description')
            startTime          = request.form.get('startTime')
            status             = request.form.get('scheduleStatus')
            repeat             = request.form.get('schedule_repeat')
            months             = request.form.get('months')
            weeks              = request.form.get('weeks')
            hours              = request.form.get('hours')
            minutes            = request.form.get('minutes')
            seconds            = request.form.get('seconds')
            repeat             =  0 if repeat.lower()=='none' else repeat

            status      = Schedules.ACTIVE if str(status).lower() =='active' else  Schedules.DISABLED 
            if str(repeat).lower() == 'yearly':
                repeat = 3600 *24 *30*12
            elif str(repeat).lower() == 'quarterly':
                repeat = 3600 *24 *30*3
            elif str(repeat).lower() == 'monthly':
                repeat = 3600 *24 *30
            elif str(repeat).lower() == 'weekly':
                repeat = 3600*24 *7
            elif str(repeat).lower() == 'bi-weekly':
                repeat = 3600*24 *7*2
            elif str(repeat).lower() == 'daily':
                repeat = 3600*24
            elif str(repeat).lower() == 'hourly':
                repeat = 3600
            elif str(repeat).lower() == 'none':
                repeat = 9999999999
            schedule_check   = Schedules.get({"name":name})
            is_existing_account = True if  schedule_check  else False
            if not is_existing_account:
                id   = Schedules.get_record_count()+1
                schedule = Schedules(schedule_id=id
                                    ,name=name
                                    ,description=description
                                    ,startTime=startTime
                                    ,scheduleStatus=status
                                    ,repeat=repeat
                                    ,months=months
                                    ,weeks=weeks
                                    ,hours=hours
                                    ,minutes=minutes
                                    ,seconds=seconds
                                    )
                schedule.save()
                return  jsonify({"message":"Schedule created successfully."})
            else:
                return  jsonify({"message":"Schedule already exists"})
        elif data_type == 'gmail':
            credentials_file = request.files.get('crendentials')
            email_address    = request.form.get('gmail_email_address')
            gmail_servers    = request.form.get('gmail_server_address')
            api_key          = request.form.get('gmail_api_key')
            account_name     = request.form.get('gmail_account_name')
            report_schedule  = request.form.get('report_schedule')
            report_filter    = request.form.get('gmail_report_filter')
            
            filename          = secure_filename(credentials_file.filename)
            if filename       != '':
                cred_path     = os.path.join(current_app.config['KEY_PATH'], filename)
                tok_path      = cred_path+'.token.pickle'
                account_check = GMailAccounts.get({"credential_file":cred_path})
                account_check = True if  account_check  else False

                if not account_check:
                  
                    credentials_file.save(cred_path)
                    gmailHelper = GmailHelper(gmail_servers,email_address,cred_path,tok_path)
                    gmailHelper.gmail_authenticate()
                    id   = GMailAccounts.get_record_count()+1
                    gmailAccount = GMailAccounts(
                            account_id              =   id
                            , account_name          =   account_name
                            , email_address         =   email_address
                            , api_key               =   api_key
                            , servers               =   gmail_servers
                            , credential_file       =   cred_path
                            ,token_file             =   tok_path
                            , report_filter         =   report_filter
                            , report_schedule       =   report_schedule
                            ,created_datetime       =   datetime.utcnow()
                    )
                    gmailAccount.save()
                    queue = rq.Queue(current_app.config['REDIS_QUEUE_NAME'], connection=current_app.redis)
                    queue.enqueue( 'app.tasks.process_gmail_reports', args=[id], job_timeout=current_app.config['SYNC_INTERVAL'])
                    return  jsonify({"message":"Account successfully added."})
                else:
                    return  jsonify({"message":"Account already exists."})
        elif data_type == 'dmarc':
                domain_name 	   = request.form.get('domain_name')
                p       		   = request.form.get('p')
                rua         	   = request.form.get('rua')
                ruf                = request.form.get('ruf')
                sp                 = request.form.get('sp')
                ri                 = request.form.get('ri')
                dmarc_txt          = request.form.get('dmarc_txt')
                created_datetime   = datetime.now()


                dmarc_record_check   = DmarcRecords.get({"domain_name":domain_name})
                is_existing_account  = True if  dmarc_record_check  else False
                if not is_existing_account:
                    id               = DmarcRecords.get_record_count()+1
                    dmarc_record     = DmarcRecords(record_id=id
                                        ,domain_name=domain_name
                                        ,p=p
                                        ,rua=rua
                                        ,ruf=ruf
                                        ,sp=sp
                                        ,ri=ri
                                        ,dmarc_text=dmarc_txt
                                        ,created_datetime=created_datetime
                                        
                                        )
                    dmarc_record.save()
                    return  jsonify({"message":"DMARC Record saved successfully."})
                else:
                    return  jsonify({"message":"DMARC Record already exists"})     
    elif mode=='edit':
        if data_type == 'imap':
            imap_server_address  = request.form.get('imap_server_address')
            imap_username        = request.form.get('imap_username')
            #imap_password        = request.form.get('imap_password')
            imap_security        = request.form.get('imap_security')
            imap_report_schedule = request.form.get('imap_report_schedule')
            imap_port            = request.form.get('imap_port')
            account_id           = request.form.get('account_id')
            imap_account         = IMAPAccounts.get({"account_id":account_id})
            imap_account.imap_server_address=imap_server_address
            imap_account.imap_username=imap_username
            #imap_account.imap_password=key_maker.multiCrypt(imap_password,count)
            imap_account.imap_security=imap_security
            imap_account.imap_port= imap_port
            imap_account.imap_report_schedule=imap_report_schedule
            imap_account.last_modified_date=datetime.now()
            imap_account_check   = IMAPAccounts.get({"imap_server_address":imap_server_address})
            is_editable = True if  not imap_account_check or imap_account_check.account_id == imap_account.account_id  else False

            if is_editable:				
                try:
                    imap_account.save()
                    queue = rq.Queue(current_app.config['REDIS_QUEUE_NAME'], connection=current_app.redis)
                    #job = Jobs.get({'schedule':imap_report_schedule}).first()
                    #print(job)
                    #job = Job.fetch(job.job_id, connection=current_app.redis)
                    #print(job)
                    #if job and job.job_id:
                    #    job.cancel()
                    #else: 
                    #    print("Job not found")
                    queue.enqueue( 'app.tasks.process_imap_reports', args=[account_id], job_timeout=current_app.config['SYNC_INTERVAL'])
                    return  jsonify({"message":"Account updated successfully."})
                except:
                    return  jsonify({"message":"Account could not be  updated"})
        elif data_type         == 'schedule':
            name  			   = request.form.get('schedule_name')
            description        = request.form.get('schedule_description')
            startTime          = request.form.get('startTime')
            status             = request.form.get('scheduleStatus')
            repeat             = request.form.get('schedule_repeat')
            months             = request.form.get('months')
            weeks              = request.form.get('weeks')
            hours              = request.form.get('hours')
            minutes            = request.form.get('minutes')
            seconds            = request.form.get('seconds')
            schedule_id		   = request.form.get('schedule_id')
            repeat             =  0 if repeat.lower()=='none' else repeat

            status      = Schedules.ACTIVE if str(status).lower() =='active' else  Schedules.DISABLED 
            if str(repeat).lower() == 'yearly':
                repeat = 3600 *24 *30*12
            elif str(repeat).lower() == 'quarterly':
                repeat = 3600 *24 *30*3
            elif str(repeat).lower() == 'monthly':
                repeat = 3600 *24 *30
            elif str(repeat).lower() == 'weekly':
                repeat = 3600*24 *7
            elif str(repeat).lower() == 'bi-weekly':
                repeat = 3600*24 *7*2
            elif str(repeat).lower() == 'daily':
                repeat = 3600*24
            elif str(repeat).lower() == 'hourly':
                repeat = 3600
            elif str(repeat).lower() == 'none':
                repeat = 9999999999
                
            schedule_check   = Schedules.get({"name":name})
            schedule	     = Schedules.get({"schedule_id":schedule_id})
            is_editable = True if  not schedule_check or schedule_check.schedule_id == schedule.schedule_id  else False
            #print(is_editable)
            if is_editable:
                schedule.name=name
                schedule.description=description
                schedule.startTime=startTime
                schedule.scheduleStatus=status
                schedule.repeat=repeat
                schedule.months=months
                schedule.weeks=weeks
                schedule.hours=hours
                schedule.minutes=minutes
                schedule.seconds=seconds
                schedule.last_modified_date=datetime.now()
                try:
                    schedule.save()
                    return  jsonify({"message":"Schedule updated successfully."})
                except:
                    return  jsonify({"message":"Schedule could not be  updated"})
        elif data_type        == 'gmail':
            credentials_file  = request.files.get('crendentials')
            email_address     = request.form.get('gmail_email_address')
            gmail_servers     = request.form.get('gmail_server_address')
            api_key           = request.form.get('gmail_api_key')
            account_name      = request.form.get('gmail_account_name')
            report_schedule   = request.form.get('report_schedule')
            report_filter     = request.form.get('gmail_report_filter')
            account_id        = request.form.get('acount_id')
            filename          = secure_filename(credentials_file.filename)
            if filename       != '':
                cred_path     = os.path.join(current_app.config['KEY_PATH'], filename)
                tok_path      = cred_path+'.token.pickle'
                account_check = GMailAccounts.get({"credential_file":cred_path})
                gmail_account = GMailAccounts.get({"account_id":account_id})
                is_editable = True if  not account_check or account_check.account_id == account_check.account_id  else False

                if  is_editable:
                    credentials_file.save(cred_path)
                    gmailHelper = GmailHelper(gmail_servers,email_address,cred_path,tok_path)
                    gmailHelper.gmail_authenticate()
                    gmail_account.account_name          =   account_name
                    gmail_account.email_address         =   email_address
                    gmail_account.api_key               =   api_key
                    gmail_account.servers               =   gmail_servers
                    gmail_account.credential_file       =   cred_path
                    gmail_account.token_file            =   tok_path
                    gmail_account.report_filter         =   report_filter
                    gmail_account.report_schedule       =   report_schedule
                    gmail_account.last_modified_date    =   datetime.utcnow()
                    gmail_account.save()
                    queue = rq.Queue(current_app.config['REDIS_QUEUE_NAME'], connection=current_app.redis)
                    job = Jobs.get({'schedule':report_schedule}).first()
                    job = Job.fetch(job.job_id, connection=current_app.redis)
                    if job:
                        job.cancel()
                    queue.enqueue( 'app.tasks.process_gmail_reports', args=[account_id], job_timeout=current_app.config['SYNC_INTERVAL'])
                    return  jsonify({"message":"Account updated successfully."})
                else:
                    return  jsonify({"message":"Account could not be updated."})


@csrf.exempt
@bp.route('/api/delete/<table>',methods = ['POST'])
@login_required
def remove_record(table):
    """ 
    print('args')
    print(request.args)
    print('form')
    print(request.form)
    print('values')
    print(request.values)
    """
    collection =  models.__dict__[table]
    id  = 1
    if table.lower() == 'imapaccounts':
        id       = 'account_id'
    elif table.lower() == 'gmailaccounts':
        id       = 'account_id'

    id_value     = request.form.get(id)
    temp_data     = {}
    temp_data[id] = id_value
    entry_pending_removal = collection.find(temp_data)
    try:
        entry_pending_removal.delete()
        return  jsonify({"message":"Record with ID: "+id_value+"  deleted successfully."})
    except:
        traceback.print_exc()
        return  jsonify({"message":"Record with ID: "+id_value+" could not be deleted."})
    
@csrf.exempt
@bp.route('/api/checkdmarc',methods = ['POST'])
@cache.cached()
@login_required
def run_dmarc_check():
    """
    print('args')
    print(request.args)
    print('form')
    print(request.form)
    print('values')
    print(request.values)
    """
    domain_name = request.form.get('domain_name')
    if domain_name and len(domain_name)!=0:
       output = checkdmarc.check_dmarc(domain_name)
       return  jsonify({"message":output})