from argparse import SUPPRESS
import base64
from datetime import datetime, timedelta
from email.policy import default
from hashlib import md5
import json 
import os
from time import time
from flask import current_app, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import redis
import rq
from app import db #,  login, get_debug_template
#from app.search import add_to_index, remove_from_index, query_index
#from flask_mongoengine.wtf import model_form
import  json
from uuid import uuid4

from flask_login import UserMixin
    
class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = cls.query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.objects(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                cls.add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                cls.add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                cls.remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            cls.add_to_index(cls.__tablename__, obj)
    @classmethod
    def get_json(self):
        return  current_app.json_enconder(self, exclude_none=True)
#db.objects.listen(db.session, 'before_commit', SearchableMixin.before_commit)
#db.objects.listen(db.session, 'after_commit', SearchableMixin.after_commit)
class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                              **kwargs) if resources.has_prev else None
            }
        }
        return data
    

class ReportUploads(SearchableMixin,PaginatedAPIMixin,db.Document):

    report_id             =   db.IntField(unique=True)
    report_name           =   db.StringField(unique=True)
    report_type           =   db.StringField()
    report_organization   =   db.StringField() 
    raw_report_file       =   db.StringField() 
    processed_report_file =   db.StringField() 
    status                =   db.IntField(default = 0)
    created_datetime      =   db.DateTimeField( default=datetime.utcnow)
    last_modified_date    =   db.DateTimeField( default=datetime.utcnow)
    meta                  = { "db_alias":"default", 'collection':'report_uploads',  "indexes":  [("report_id", "report_name", "report_type", "report_organization", "raw_report_file","processed_report_file", "created_datetime","last_modified_date")]}
    @staticmethod  
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = ReportUploads.objects(**find_params).first()
        return data
    
    @staticmethod  
    def find(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = ReportUploads.objects(**find_params)
        return data
    
    
    @staticmethod
    def get_schema():
      schema_data = {
			"titleField": "ReportName",
			"idField": "report_id",
			"reportuploads": {
				"report_id": "Report ID",
				"report_name": "Report Name",
				"report_type": "Report Type",
				"report_organization": "Report Organization",
				"raw_report_file": "Report File",
                "processed_report_file": "Report File",
                "status": "Status",
                "last_modified_date": "Last Modified Date",
				"created_datetime": "Created Datetime"
			},
			"sc": 0,
			"order": ["id", "report_name", "report_type", "report_organization", "raw_report_file","process_report_file","status", "created_datetime","last_modified_date"]
		}
      return schema_data

    def __repr__(self):
        return '<ReportUpload {}>'.format(self.report_name)
    @staticmethod
    def get_record_count():
        return ReportUploads.objects().all().count()

class GMailAccounts(SearchableMixin,PaginatedAPIMixin,db.Document):

    account_id            =   db.IntField(unique=True)
    account_name          =   db.StringField(unique=True)
    email_address         =   db.StringField()
    api_key               =   db.StringField()
    servers               =   db.StringField()
    credential_file       =   db.StringField() 
    token_file            =   db.StringField() 
    report_filter         =   db.StringField() 
    report_schedule       =   db.StringField() 
    created_datetime      =   db.DateTimeField( default=datetime.utcnow)
    last_modified_date    =   db.DateTimeField( default=datetime.utcnow)
    meta                  =   {"db_alias":"default", 'collection':'gmail_accounts',  "indexes":  [("account_id", "account_name", "email_address", "api_key","servers","report_schedule",  "created_datetime","last_modified_date")]}
    
    @staticmethod  
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = GMailAccounts.objects(**find_params).first()
        return data
    
    @staticmethod  
    def find(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = GMailAccounts.objects(**find_params)
        return data
       
    @staticmethod
    def get_schema():
      schema_data = {
			"titleField": "account_name",
			"idField": "account_id",
			"GMailSettings": {
				"account_id": "Account ID",
				"account_name": "Account Name",
				"servers": "Servers",
                "credential_file": "Credentials File",
				"token_file": "Token File",
				"report_filter": "Report Filter",
                "last_modified_date": "Last Modified Date",
				"created_datetime": "Created Datetime"
			},
			"sc": 0,
			"order": ["account_id", "account_name", "email_address", "api_key", "servers", "credential_file","token_file","report_filter", "created_datetime","last_modified_date"]
		}
      return schema_data

    def __repr__(self):
        return '<GMailAccounts {}>'.format(self.account_name)
    @staticmethod
    def get_record_count():
        return GMailAccounts.objects().all().count()
    
class IMAPAccounts(SearchableMixin,PaginatedAPIMixin,db.Document):

    account_id            =   db.IntField(unique=True)
    imap_server_address   =   db.StringField(unique=True)
    imap_username         =   db.StringField()
    imap_password         =   db.StringField()
    imap_security         =   db.StringField()
    imap_report_schedule  =   db.StringField() 
    imap_port             =   db.IntField()
    created_datetime      =   db.DateTimeField( default=datetime.utcnow)
    last_modified_date    =   db.DateTimeField( default=datetime.utcnow)
    meta                  =  {"db_alias":"default", 'collection':'i_m_a_p_accounts',  "indexes":  [("account_id", "imap_server_address", "imap_username","imap_port", "imap_security","imap_report_schedule",  "created_datetime","last_modified_date")]}
    
    @staticmethod  
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = IMAPAccounts.objects(**find_params).first()
        return data
    
    @staticmethod  
    def find(find_params=None):
        find_params = {} if find_params==None else find_params
        data        = IMAPAccounts.objects(**find_params)
        return data
       
    @staticmethod
    def get_schema():
      schema_data = {
			"titleField": "account_name",
			"idField": "account_id",
			"IMAPAccounts": {
				"account_id": "Account ID",
				"account_name": "Account Name",
				"servers": "Servers",
                "credential_file": "Credentials File",
				"token_file": "Token File",
				"report_filter": "Report Filter",
                "last_modified_date": "Last Modified Date",
				"created_datetime": "Created Datetime"
			},
			"sc": 0,
			"order": ["account_id", "imap_server_address", "imap_username", "imap_password","imap_port", "imap_security","imap_report_schedule",  "created_datetime","last_modified_date"]
		}
      return schema_data

    def __repr__(self):
        return '<IMAPAccounts {}>'.format(self.imap_server_address)
    @staticmethod
    def get_record_count():
        return IMAPAccounts.objects().all().count()
    
class ReportMetadata (SearchableMixin,PaginatedAPIMixin,db.Document):
    report_id                	       = db.IntField(unique=True)
    report_name         	 	       = db.StringField()	
    report_type         	 	       = db.StringField()		
    report_xml_schema		           = db.StringField()			
    report_metadata_org_name 	       = db.StringField()			
    report_metadata_org_email	       = db.StringField()		
    report_metadata_org_extra_contact_info = db.StringField()		
    report_metadata_report_id	       = db.StringField(unique=True)		
    report_metadata_begin_date	       = db.DateTimeField()	
    report_metadata_end_date	       = db.DateTimeField()	
    report_metadata_errors		       = db.ListField()
    policy_published_domain		       = db.StringField()	
    policy_published_adkim		       = db.StringField()		
    policy_published_aspf		       = db.StringField()	
    policy_published_p		           = db.StringField()
    policy_published_sp		           = db.StringField()		
    policy_published_pct		       = db.StringField()		
    policy_published_fo		           = db.StringField()
    created_datetime		           = db.DateTimeField(default=datetime.utcnow)	
    meta                               = { "db_alias":"default", 'collection':'report_metadata',  "indexes":  [("report_id", "report_name","report_type", "report_metadata_begin_date", "report_metadata_end_date","report_metadata_org_name", "report_metadata_org_email", "report_metadata_report_id","policy_published_domain", "created_datetime")]}

    @staticmethod  
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = ReportMetadata.objects(**find_params).first()
        return data
    
    @staticmethod  
    def find(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = ReportMetadata.objects(**find_params)
        return data
    
    @staticmethod
    def get_schema():
      schema_data = {
			"titleField": "ReportName",
			"idField": "report_id",
			"reportuploads": {
				"report_id": "Report ID",
				"report_name": "Report Name",
				"report_type": "Report Type",
				"report_organization": "Report Organization",
				"raw_report_file": "Report File",
                "processed_report_file": "Report File",
                "status": "Status",
                "last_modified_date": "Last Modified Date",
				"created_datetime": "Created Datetime"
			},
			"sc": 0,
			"order": ["id", "report_name", "report_type", "report_organization", "raw_report_file","process_report_file","status", "created_datetime","last_modified_date"]
		}
      return schema_data

    def __repr__(self):
        return '<ReportMetadata {}>'.format(self.report_name)
    @staticmethod
    def get_record_count():
        return ReportMetadata.objects().all().count()
    
class ReportRecords (SearchableMixin,PaginatedAPIMixin,db.Document):	
    report_id                	    = db.IntField()
    report_name         	  	    = db.StringField()	
    report_type         	 	    = db.StringField()
    report_record_id                = db.IntField(unique=True)
    source_ip_address		        = db.StringField()							
    source_country			        = db.StringField()								
    source_reverse_dns		        = db.StringField()								
    source_base_domain		        = db.StringField()								
    count				            = db.IntField()							
    alignment_spf			        = db.BooleanField()							
    alignment_dkim			        = db.BooleanField()							
    alignment_dmarc			        = db.BooleanField()							
    policy_evaluated_disposition	= db.StringField()							
    policy_evaluated_dkim		    = db.StringField()							
    policy_evaluated_spf		    = db.StringField()							
    identifiers_header_from		    = db.StringField()							
    identifiers_envelope_from	    = db.StringField()							
    identifiers_envelope_to		    = db.StringField()
    policy_override_reasons_comment = db.StringField()
    policy_override_reasons_type    = db.StringField()

    dkim_domain			            = db.StringField()							
    dkim_selector			        = db.StringField()							
    dkim_result			            = db.StringField()							
    spf_domain			            = db.StringField()							
    spf_scope			            = db.StringField()							
    spf_result			            = db.StringField()
    source_ip_hostname              = db.StringField()                             
    source_ip_city                  = db.StringField()                     
    source_ip_region                = db.StringField()                         
    source_ip_country               = db.StringField()                       
    source_ip_location              = db.StringField()                        
    source_ip_organization          = db.StringField()                         
    source_ip_postal                = db.StringField()                     
    source_ip_timezone              = db.StringField()                       
    created_datetime		        = db.DateTimeField(default=datetime.utcnow)
    meta                            = { "db_alias":"default", 'collection':'report_records',  "indexes":  [("report_id", "report_name","report_type","report_record_id", "source_ip_address", "source_country", "source_reverse_dns","source_base_domain","identifiers_header_from",  "identifiers_envelope_from", "identifiers_envelope_to", "dkim_domain", "spf_domain", "created_datetime")]}

    @staticmethod  
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = ReportRecords.objects(**find_params).first()
        return data

    @staticmethod  
    def find(find_params=None):
        find_params = {} if find_params==None else find_params
        data        = ReportRecords.objects(**find_params)
        return data

    @staticmethod
    def get_schema():
        schema_data = {
                "titleField": "ReportName",
                "idField": "report_id",
                "reportuploads": {
                    "report_id": "Report ID",
                    "report_name": "Report Name",
                    "report_type": "Report Type",
                    "report_organization": "Report Organization",
                    "raw_report_file": "Report File",
            "processed_report_file": "Report File",
            "status": "Status",
            "last_modified_date": "Last Modified Date",
                    "created_datetime": "Created Datetime"
                },
                "sc": 0,
                "order": ["id", "report_name", "report_type", "report_organization", "raw_report_file","process_report_file","status", "created_datetime","last_modified_date"]
            }
        return schema_data

    def __repr__(self):
        return '<ReportRecord {}>'.format(self.report_name)
    @staticmethod
    def get_record_count():
        return ReportRecords.objects().all().count()
    

class ReportEmails(SearchableMixin,PaginatedAPIMixin,db.Document):

    report_id             =   db.IntField(unique=True)
    original_report_name  =   db.StringField(unique=True) 
    frm                   =   db.StringField()
    to                    =   db.StringField() 
    subject               =   db.StringField() 
    date                  =   db.StringField() 
    saved_filename        =   db.StringField() 
    file_size             =   db.StringField() 
    processed_report_file =   db.StringField()
    status                =   db.IntField(default = 0)
    created_datetime      =   db.DateTimeField( default=datetime.utcnow)
    last_modified_date    =   db.DateTimeField( default=datetime.utcnow)
    meta                  =   { "db_alias":"default", 'collection':'report_emails',  "indexes":  [("report_id", "original_report_name" , "frm", "to",  "subject","date","saved_filename","processed_report_file", "status", "created_datetime","last_modified_date")]}
   
    @staticmethod  
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        data        = ReportEmails.objects(**find_params).first()
        return data
    
    @staticmethod  
    def find(find_params=None):
        find_params = {} if find_params==None else find_params
        data        = ReportEmails.objects(**find_params)
        return data
    
    @staticmethod
    def get_schema():
      schema_data = {
			"titleField": "ReportName",
			"idField": "report_id",
			"ReportEmails": {
				"report_id": "Report ID",
				"original_report_name": "Original Name",
				"frm": "From",
				"to": "To",
                "subject": "Subject",
                "date": "Date",
                "saved_filename": "Saved File Name",
                "file_size": "File Size",
                "processed_report_file": "Processed Report File",
                "status": "Status",
                "created_datetime": "Created Datetime",
                "last_modified_date": "Last Modified Date"
			},
			"sc": 0,
			"order": ["report_id","original_report_name", "frm", "to","subject", "date" ,"saved_filename", "file_size","processed_report_file", "status", "created_datetime","last_modified_date"]
		}
      return schema_data

    def __repr__(self):
        return '<ReportEmails {}>'.format(self.report_name)
    @staticmethod
    def get_record_count():
        return ReportEmails.objects().all().count()
        
class DmarcRecords (SearchableMixin,PaginatedAPIMixin,db.Document):
    record_id        = db.IntField(unique=True)
    domain_name      = db.StringField()	
    p         	     = db.StringField()		
    rua		         = db.StringField()			
    ruf 	         = db.StringField()			
    sp	             = db.StringField()		
    ri 				 = db.StringField()	
    dmarc_text	     = db.StringField()	
    created_datetime = db.DateTimeField(default=datetime.utcnow)	
    meta                               = { "db_alias":"default", 'collection':'dmarc_records',  "indexes":  [("record_id", "domain_name","p","ruf", "sp", "ri", "created_datetime")]}

    @staticmethod  
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = DmarcRecords.objects(**find_params).first()
        return data
    
    @staticmethod  
    def find(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = DmarcRecords.objects(**find_params)
        return data
    
    @staticmethod
    def get_schema():
      schema_data = {
			"titleField": "ReportName",
			"idField": "record_id",
			"reportuploads": {
				"record_id": "Report ID",
				"domain_name": "Report Name",
				"p": "Report Type",
				"report_organization": "Report Organization",
				"raw_report_file": "Report File",
                "processed_report_file": "Report File",
                "status": "Status",
                "last_modified_date": "Last Modified Date",
				"created_datetime": "Created Datetime"
			},
			"sc": 0,
			"order": ["id", "domain_name", "p", "report_organization", "raw_report_file","process_report_file","status", "created_datetime","last_modified_date"]
		}
      return schema_data

    def __repr__(self):
        return '<DmarcRecords {}>'.format(self.domain_name)
    @staticmethod
    def get_record_count():
        return DmarcRecords.objects().all().count()
    
class Roles(SearchableMixin,PaginatedAPIMixin,db.Document):
    id                  =  db.IntField()
    roleName            =  db.StringField()
    roleDescription     =  db.StringField()
    creationDate        = db.DateTimeField( default=datetime.utcnow)
    lastModifiedDate    = db.DateTimeField( default=datetime.utcnow)

    @staticmethod
    def get_schema():
      schema_data =  {'titleField':'Role Name','idField':'id','roles':{'id':'id','roleName':'Role Name','roleDescription':'Role Description','creationDate':'Creation Date','lastModifiedDate':'Last Modified Date'},'sc':0, 'order': ['id','roleName','roleDescription','creationDate','lastModifiedDate']}
      return schema_data

    def save(self):
        additional_fields     =  []
        self.lastModifiedDate = datetime.utcnow()
        self.store(db, additional_fields)      

    def get(field=None, value=None, find_params=None):
        find_params = {} if find_params==None else  find_params
        field  =   "doc_type" if field is None else  field
        value  =   self.doc_type if  value is None else  value
        data = self.load(db,field=field, value=value,find_params= find_params) 
        return data
    @staticmethod
    def get_record_count(self):
        return Roles.objects().all().count()

class Users(UserMixin, PaginatedAPIMixin, db.Document):
    id                  = db.IntField(primary_key=True)
    firstName           = db.StringField(max_length = (255), index=True )
    surname             = db.StringField(max_length = (255), index=True )
    username            = db.StringField(max_length = (64),  index=True, unique=True)
    email               = db.StringField(max_length = (120), index=True, unique=True)
    passwordHash        = db.StringField(max_length = (255))
    creationDate        = db.DateTimeField(index=True, default=datetime.utcnow)
    locked              = db.BooleanField(default=False)
    role                = db.ReferenceField(Roles)
    connectionStatus    = db.BooleanField(default=False)
    active              = db.BooleanField( default=False)
    loginCount          = db.IntField( default=0)
    reset               = db.BooleanField(default=False)
    lastModifiedDate    = db.DateTimeField(index=True, default=datetime.utcnow)
    token               = db.StringField(max_length = (32), index=True, unique=True)
    tokenExpiration     = db.DateTimeField()
    meta                = {"db_alias":"default", 'collection':'users', 'indexes':[('id','firstName','surname','email','passwordHash','creationDate','lastModifiedDate','token')]}

    @staticmethod
    def get_schema():
      schema_data = {'idField':'_id','Users':{'_id':'id','firstName':'First Name','surname':'Surname','username':'Username','email':'Email','creationDate':'Creation Date','locked':'Locked','team': 'Team','role' : 'Role', 'connectionStatus':'Connection Status', 'active':'Active', 'loginCount':'Login Count',  'lastModifiedDate':'Last Modified Date', 'tokenExpiration':'Token Expiration'},'sc':3,'order': ['_id','firstName','surname','username','email','creationDate','locked','team','role','connectionStatus','tokenExpiration']}
      return schema_data

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.passwordHash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passwordHash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def get_record_count():
        return Users.objects().all().count()

    @staticmethod
    def get_serial_index():
        return 3
           
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],algorithms=['HS256'])['reset_password']
        except:
            return
        return Users.objects(id=id).first()

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id,*args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.objects(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.objects(name=name, user=self,complete=False).first()

    def to_dict(self, include_email=False):
        data = {      
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = Users.objects(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user
    
    def is_authenticated(self):
        return self.connectionStatus    
    @staticmethod
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        data        = Users.objects(**find_params).first()
        return data

#@login.user_loader
#def load_user(id):
#    return Users.objects(id=int(id)).first()
class Jobs(SearchableMixin ,db.Document):
    job_id      = db.StringField(unique=True)
    name        = db.StringField( )
    parameters  = db.StringField( )
    report_id   = db.IntField( )
    description = db.StringField()
    user_id     = db.IntField( )
    complete    = db.BooleanField(default=False)
    startTime   = db.DateTimeField(default=datetime.utcnow)
    endTime     = db.DateTimeField()
    progress    = db.IntField()
    jobStatus   = db.IntField()
    info        = db.ListField()
    schedule    = db.StringField()
    errors      = db.ListField()
    last_modified_date = db.DateTimeField(default=datetime.utcnow)
    RUNNING     = 1
    SUCCEEDED   = 2
    FAILED      = 3
    QUEUED      = 0
    meta        = {"db_alias":"default", 'collection':'jobs', 'indexes':[('job_id','name','user_id', 'report_id', 'startTime','endTime','jobStatus','info','schedule','last_modified_date')]}

    @staticmethod
    def get_schema():
      schema_data = {'titleField':'Name','idField':'_id','jobs':{'_id':'_id','job_id':'Job ID','name':'Name','report_id':'Report ID', 'parameters':'Parameters', 'description':'Description','user_id':'User ID','complete':'Complete','startTime':'Start Time','endTime':'End Time', 'progress':'Progress', 'jobStatus': 'Job Status','info': 'Info','schedule':'Schedule','errors':'Errors','last_modified_date':'Last Modified Date'}, 'sc':0, 'order': ['job_id','name','parameters','description','user_id','report_id', 'complete','startTime','endTime','progress','jobStatus', 'info','schedule','errors']}
      return schema_data 
 
    @staticmethod  
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        data        = Jobs.objects(**find_params).first()
        return data
    
    @staticmethod  
    def find(find_params=None):
        find_params = {} if find_params==None else find_params
        data        = Jobs.objects(**find_params)
        return data
    

    def get_record_count(self):
        return Jobs.objects().all().count() 

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
    
    def get_info(self):
        job = self.get_rq_job()
        return job.meta.get('info', '') if job is not None else ''
    



class Schedules(PaginatedAPIMixin,db.Document):
    schedule_id                   =  db.IntField()
    name                 =  db.StringField()
    startTime            =  db.DateTimeField( default=datetime.utcnow)
    description          =  db.StringField()
    repeat               =  db.IntField()
    months	             =  db.IntField(default=0 )
    weeks	         =  db.IntField(default=0 )
    days            	 =  db.IntField(default=0 )
    hours     		 =  db.IntField(default=0)
    minutes              =  db.IntField(default=0)
    seconds   		 =  db.IntField(default=0)
    scheduleStatus	 =  db.IntField(default=0 )
    DISABLED             =  0
    ACTIVE               =  1
    last_modified_date     =  db.DateTimeField()
    created_datetime	   =  db.DateTimeField( default=datetime.utcnow)
	
    @staticmethod
    def get_schema():
      schema_data =  {"db_alias":"default", 'collection':'scheduless', 'titleField':'id','idField':'_id','schedules':{'_id':'_id','id':'ID','name': 'Name','createdtime': 'Created Time','startTime': 'Start Time','description': 'Description','repeat':'Repeat','months':'Months','weeks':'Weeks','days':'Days','hours':'Hours','minutes':'Minutes','seconds':'Seconds','scheduleStatus':'Schedule Status','last_modified_date':'Last Modified Date'},'sc':0,'order': ['id','name','createdtime','startTime','description','repeat','months','weeks','days','hours','minutes','seconds','scheduleStatus','last_modified_date']}
      return schema_data
      
    @staticmethod  
    def find(find_params=None):
        find_params = {} if find_params==None else find_params
        
        data        = Schedules.objects(**find_params)
        return data

    @staticmethod  
    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        data        = Schedules.objects(**find_params).first()
        return data

    def __repr__(self):
        return '<ReportRecord {}>'.format(self.report_name)
    @staticmethod
    def get_record_count():
        return Schedules.objects().all().count()

    def get_interval(self):
        return int(self.months)+int(self.weeks)+int(self.days)+int(self.hours)+int(self.minutes)+int(self.seconds)
        
class AuditTrail(SearchableMixin,PaginatedAPIMixin,db.Document):
    doc_type            =  'audittrail'
    id                  =  db.IntField()
    description         =  db.StringField()
    oldData    			=  db.DictField()
    newData    			=  db.DictField()
    changeTime          =  db.DateTimeField( default=datetime.utcnow)
    changeType          =  db.StringField()
    affectedTable       =  db.StringField()
    username            =  db.StringField()
    userID              =  db.IntField()
    recordIdentifier    =  db.DictField()
    meta                = {'indexes':[('id','description','oldData','newData','changeTime','changeType','affectedTable','username')]}

    @staticmethod
    def get_schema():
      schema_data =  {'idField':'_id','audittrail':{'_id':'_id','id':'id','description':'Description','oldData':'Old Data','newData':'New Data','changeTime':'Change Time','changeType':'Change Type','userName':'UserName','userID':'userID','recordIdentifier':'Record Identifier'},'sc':0,'order': ['id','description','oldData','newData','changeTime','changeType','affectedTable','userName','userID','recordIdentifier']}
      return schema_data

    def save(self):
        additional_fields     =  []
        self.lastModifiedDate = datetime.utcnow()
        self.store(db, additional_fields)      

    def get(find_params=None):    
        find_params = {} if find_params==None else find_params
        data        = AuditTrail.objects(**find_params).first()
        return data

    def get_record_count(self):
        return AuditTrail.objects().all().count()

class SiteSettings(SearchableMixin,PaginatedAPIMixin,db.Document):
    id                  =  db.IntField()
    siteName            =  db.StringField()
    siteTitle    	    =  db.StringField()
    siteLogo   	        =  db.StringField()
    ldapServer          =  db.StringField()
    ldapUser            =  db.StringField()
    ldapPassword        =  db.StringField()
    emailServer 	    =  db.StringField()
    emailUser           =  db.StringField()
    emailPassword       =  db.StringField()
    tableLiveFetch      =  db.BooleanField(default=False)
    formLiveFetch       =  db.BooleanField(default=False)
    lastModifiedDate    =  db.DateTimeField( default=datetime.utcnow)

    @staticmethod
    def get_schema():
      schema_data =  {'titleField':'Site Name','idField':'_id','sitesettings':{'_id':'_id','id':'id','siteName':'Site Name','siteTitle':'Site Title','siteLogo':'Site Logo','ldapServer':'LDAP Server','ldapUser':'LDAP User','ldapPassword':'LDAP Password','emailServer':'Email Server','emailUser':'Email User','emailPassword':'Email Password', 'lastModifiedDate':'Last Modified Date','tableLiveFetch':'Table Live Fetch','formLiveFetch':'Form Live Fetch'},'sc':2,'order': ['id','siteName','siteTitle','siteLogo','ldapServer','ldapUser','ldapPassword','emailServer','emailPassword','emailUser','emailPassword','lastModifiedDate', 'tableLiveFetch','formLiveFetch']}
      return schema_data

    @staticmethod
    def get_record_count():
        return 0
    @staticmethod
    def get_last_record_id():
        return  0

    def save(self):
        additional_fields     =  []
        self.lastModifiedDate = datetime.utcnow()
        self.store(db, additional_fields)      

    def get(find_params=None):
        find_params = {} if find_params==None else find_params
        data        = SiteSettings.objects(**find_params).first()
        return data
    
class Alerts(SearchableMixin,PaginatedAPIMixin,db.Document):
    doc_type            =  'alerts'
    id                  =  db.IntField()
    taskName            =  db.IntField()
    userID		        =  db.IntField()
    name                =  db.StringField()
    description         =  db.StringField()
    startTime           =  db.DateTimeField( default=datetime.utcnow)
    lastModifiedTime    =  db.DateTimeField( default=datetime.utcnow)
    alertInterval       =  db.IntField()
    lastRunResult       =  db.StringField()
    repeat              =  db.IntField(default=0)
    mailingList         =  db.StringField()
    meta                 = {'indexes':[('id','name','taskName','userID','description','startTime','lastModifiedTime','lastRunResult','repeat','mailingList')]}
	
   
    @staticmethod
    def get_schema():
      schema_data =  {'titleField':'Name','idField':'_id','alerts':{'_id':'_id','id':'id','taskName':'Task Name','userID':'User ID','name':'Name','startTime':'startTime','repeat':'Repeat','LastModifiedTime':'Last Modified Time','alertInterval':'Alert Interval','lastRunResult':'last Run Results', 'description':'Decription', 'mailingList':'Mailing List'},'sc':0,'order': ['id','taskName','userID','name','startTime','repeat','LastModifiedTime','alertInterval','lastRunResult','description', 'mailingList']}
      return schema_data

    def save(self):
        additional_fields     =  []
        self.lastModifiedDate = datetime.utcnow()
        self.store(db, additional_fields)      

    def get(field=None, value=None, find_params=None):
        find_params = {} if find_params==None else  find_params
        field  =   "doc_type" if field is None else  field
        value  =   self.doc_type if  value is None else  value
        data = self.load(db,field=field, value=value,find_params= find_params) 
        return data

    def get_record_count(self):
        return Alerts.objects().all().count()


class Tasks(SearchableMixin,PaginatedAPIMixin,db.Document):
    id                  =  db.IntField()
    name                =  db.StringField()
    description         =  db.StringField()
    taskName            =  db.StringField()
    taskBody            =  db.StringField()
    taskFileName        =  db.StringField()
    taskType            =  db.IntField()
    parameterValueMap   =  db.StringField()
    runCount            =  db.IntField(default=0)
    creationTime        =  db.DateTimeField( default=datetime.utcnow)
    SYSTEM_TYPE         =  0
    USER_TYPE           =  1
    CUSTOM_TYPE         =  2
    meta                = {'indexes':[('id','description','name','taskName','taskBody','taskFileName','creationTime')]}
   
    @staticmethod
    def get_schema():
      schema_data =  {'titleField':'Name','idField':'_id','tasks':{'_id':'_id','id':'id','name':'Name','description':'Descrition','taskName':'Task Name','taskBody':'Task Body','taskFileName':'Task Filename','taskType':'Task Type','parameterValueMap':'Parameter Value Map','creationTime':'Creation Time','runCount':'Run Count'},'sc':0,'order': ['id','name','description','taskName', 'taskBody','taskFileName','taskType','parameterValueMap','creationTime','runCount']}
      return schema_data

    def save(self):
        additional_fields     =  []
        self.lastModifiedDate = datetime.utcnow()
        self.store(db, additional_fields)      

    def get(field=None, value=None, find_params=None):
        find_params = {} if find_params==None else  find_params
        field  =   "doc_type" if field is None else  field
        value  =   self.doc_type if  value is None else  value
        data = self.load(db,field=field, value=value,find_params= find_params) 
        return data

    def get_record_count(self):
        return Tasks.objects().all().count()
    
        

class Schedulers(SearchableMixin,PaginatedAPIMixin,db.Document):
    doc_type             =  'schedulers'
    id                   =  db.IntField()
    name                 =  db.StringField()
    createdtime		     =  db.DateTimeField( default=datetime.utcnow)
    scheduleTaskName     =  db.StringField()
    scheduleName         =  db.StringField()
    description          =  db.StringField()
    onwerName  			 =  db.StringField()
    schedulerStatus      =  db.IntField()
    SYSTEM_TYPE          =  0
    USER_TYPE            =  1
    DISABLED             =  2
    ACTIVE               =  1
    DORMANT              =  0
    scheduleType         =  db.IntField()
    alertid              =  db.IntField()
    lastModifiedDate     =  db.DateTimeField()

    meta                 = {'indexes':[('id','name','scheduleTaskName','scheduleName','createdtime','scheduleName','onwerName','scheduleType','lastModifiedDate','alertid','schedulerStatus')]}
	
    @staticmethod
    def get_schema():
      schema_data =  {'titleField':'id','idField':'_id','schedulers':{'_id':'_id','id':'ID','name': 'Name','createdtime': 'Created Time','scheduleTaskName': 'Schedule Task Name','scheduleName': 'Schedule Name','description':'Description','onwerName':'Onwer Name','schedulerStatus':'Scheduler Status','scheduleType':'Schedule Type','alertid':'Alert ID','minutes':'Minutes','seconds':'Seconds','lastModifiedDate':'Last Modified Date','lastModifiedDate':'Last Modified Date'},'sc':0,'order': ['id','name','createdtime','scheduleTaskName','scheduleName','description','onwerName','schedulerStatus','scheduleType','alertid','lastModifiedDate']}
      return schema_data

    def save(self):
        additional_fields     =  []
        self.lastModifiedDate = datetime.utcnow()
        self.store(db, additional_fields)      

    def get(field=None, value=None, find_params=None):
        find_params = {} if find_params==None else  find_params
        field  =   "doc_type" if field is None else  field
        value  =   self.doc_type if  value is None else  value
        data = self.load(db,field=field, value=value,find_params= find_params) 
        return data

    def get_record_count(self):
        return Schedulers.objects().all().count()

    def schedule_task(self):
        task            = None
        alert_info 		= None
        task_info  		= None
        schedule_info	= None
		
        if self.scheduleType != Schedulers.SYSTEM_TYPE:
            alert_info       = Alerts.get('id', self.alertid)
        task_info            = Tasks.get('id',self.taskid)
        if task_info: 
            schedule_info    = Schedules.get('id',self.scheduleid)
            schedule_start   = alert_info.startTime  if alert_info and alert_info.startTime else schedule_info.startTime 
            taskname         = task_info.taskname
            param_value_map  = json.loads(task_info.parameter_value_map) if task_info.parameter_value_map else None
            interval         = schedule_info.get_interval()
            repeat           = alert_info.repeat if alert_info.repeat else schedule_info.repeat
            description      = alert_info.description if alert_info.description else task_info.repeat
            name             = self.name+'-'+alert_info.name+'-'+task_info.name if alert_info else self.name+'-'+schedule_info.name+'-'+task_info.name 
            rq_job           = current_app.scheduler.schedule( scheduled_time=schedule_start,func=taskname,    args=param_value_map.values(), kwargs=param_value_map,  interval=interval,  repeat=repeat, meta={'info': '','progress':0 }   )
            Jobs().init_attributes(id=rq_job.get_id(), name=name, description=description,userID=self.id, startTime   = datetime.utcnow(), endTime     = None,progress    = 0, jobStatus = Tasks.QUEUED, info        = '').save()
            task = rq_job
            self.schedulerStatus  = Schedulers.ACTIVE
            self.save()
        return task