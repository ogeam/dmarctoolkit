import os
from google.oauth2.credentials import Credentials
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type
from datetime import datetime
import rq 
from flask import current_app
from app.models import ReportEmails
#import traceback


class GmailHelper():

    def __init__(self, mail_servers,email_address, credentials_file,token_file):

        self.mailServers          = []
        self.mailServers.append(mail_servers)
        self.email_address        = email_address
        self.credentials_file     = credentials_file
        self.token_file           = token_file
        self.report_email         = {}

    def gmail_authenticate(self):
        creds = None
        if os.path.exists(self.token_file ):
            creds = Credentials.from_authorized_user_file(self.token_file , self.mailServers)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.mailServers)
                creds = flow.run_local_server(port=0)
            with open(self.token_file , 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)
    
    def token_authenticate(self):
        creds = None
        if os.path.exists(self.token_file ):
            creds = Credentials.from_authorized_user_file(self.token_file , self.mailServers)
        if  creds and creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.mailServers)
            creds = flow.run_local_server(port=0)
            with open(self.token_file , 'w') as token:
                token.write(creds.to_json())
        return build('gmail', 'v1', credentials=creds)
    
    def add_attachment(self,message, filename):
        content_type, encoding = guess_mime_type(filename)
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(filename, 'rb')
            msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(filename, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(filename, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(filename, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(filename)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

    def build_message(self,destination, obj, body, attachments=[]):
        if not attachments: # no attachments given
            message = MIMEText(body)
            message['to'] = destination
            message['from'] = self.email_address
            message['subject'] = obj
        else:
            message = MIMEMultipart()
            message['to'] = destination
            message['from'] = self.email_address
            message['subject'] = obj
            message.attach(MIMEText(body))
            for filename in attachments:
                self.add_attachment(message, filename)
        return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self,service, destination, obj, body, attachments=[]):
        return service.users().messages().send( userId="me", body=self.build_message(destination, obj, body, attachments)).execute()

    def search_messages(self,service, query):
        result = service.users().messages().list(userId='me',q=query).execute()
        messages = [ ]
        if 'messages' in result:
            messages.extend(result['messages'])
        while 'nextPageToken' in result:
            page_token = result['nextPageToken']
            result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
            if 'messages' in result:
                messages.extend(result['messages'])
        return messages

    def get_size_format(self,b, factor=1024, suffix="B"):
        """
        Scale bytes to its proper byte format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.2f}{unit}{suffix}"
            b /= factor
        return f"{b:.2f}Y{suffix}"

    def clean(self,text):
        new_text = "".join(c if c.isalnum() else "_" for c in text)
        ext      = new_text.split('_')[-1]
        ext_len  = -1 *(len(ext)+1)
        new_text = new_text[0:ext_len]+'.'+ext
        return new_text
    
    def parse_parts(self,service, parts, folder_name, message):
        if parts:
            for part in parts:
                filename = part.get("filename")
                mimeType = part.get("mimeType")
                body = part.get("body")
                data = body.get("data")
                file_size = body.get("size")
                part_headers = part.get("headers")
                if part.get("parts"):
                    self.parse_parts(service, part.get("parts"), folder_name, message)
                if mimeType == "text/plain":
                    if data:
                        text = urlsafe_b64decode(data).decode()
                        print(text)
                elif mimeType == "text/html":
                    if not filename:
                        filename = "index.html"
                    filepath = os.path.join(folder_name, filename)
                    print("Saving HTML to", filepath)
                    with open(filepath, "wb") as f:
                        f.write(urlsafe_b64decode(data))
                else:
                   
                    for part_header in part_headers:
                        part_header_name = part_header.get("name")
                        part_header_value = part_header.get("value")
                        if part_header_name == "Content-Disposition":
                            if "attachment" in part_header_value:
                                print("Saving the file:", filename, "size:", self.get_size_format(file_size))
                                attachment_id = body.get("attachmentId")
                                attachment = service.users().messages().attachments().get(id=attachment_id, userId='me', messageId=message['id']).execute()
                                data = attachment.get("data")
                                filepath = os.path.join(folder_name, filename)
                                if data:
                                    with open(filepath, "wb") as f:
                                        f.write(urlsafe_b64decode(data))

    def read_message(self,service, message, mail_folder):

        msg            = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        payload        = msg['payload']
        headers        = payload.get("headers")
        parts          = payload.get("parts")
        folder_name    = mail_folder
        has_subject    = False
        if headers:
            for header in headers:
                name   = header.get("name")
                value  = header.get("value")
                if name.lower() == 'from':
                    print("From:", value)
                if name.lower() == "to":
                    print("To:", value)
                if name.lower() == "subject":
                    has_subject = True                 
                    folder_name = self.clean(value)
                    folder_counter = 0
                    while os.path.isdir(folder_name):
                        folder_counter += 1
                        if folder_name[-1].isdigit() and folder_name[-2] == "_":
                            folder_name = f"{folder_name[:-2]}_{folder_counter}"
                        elif folder_name[-2:].isdigit() and folder_name[-3] == "_":
                            folder_name = f"{folder_name[:-3]}_{folder_counter}"
                        else:
                            folder_name = f"{folder_name}_{folder_counter}"
                    folder_name = mail_folder+os.sep+folder_name
                    if not os.path.exists(folder_name):
                        os.mkdir(folder_name)
                    print("Subject:", value)
                if name.lower() == "date":
                    print("Date:", value)
        if not has_subject:
            folder_name = mail_folder+os.sep+folder_name
            if not os.path.isdir(folder_name):
                os.mkdir(folder_name)
                
        self.parse_parts(service, parts, folder_name, message)
        print("="*50)


    def mark_as_read(self,service, query):
        messages_to_mark = self.search_messages(service, query)
        print(f"Matched emails: {len(messages_to_mark)}")
        return service.users().messages().batchModify(
        userId='me',
        body={
            'ids': [ msg['id'] for msg in messages_to_mark ],
            'removeLabelIds': ['UNREAD']
        }
        ).execute()
    

    def read_dmarc_message(self,service, message,folder_name, schedule_id):

        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        payload = msg['payload']
        headers = payload.get("headers")
        parts = payload.get("parts")
        if headers:
            for header in headers:
                name = header.get("name")
                value = header.get("value")
                if name.lower() == 'from':
                    self.report_email['frm']= value
                if name.lower() == "to":
                   self.report_email['to']= value
                if name.lower() == "subject":
                    self.report_email['subject']= value
                    print("Subject:", value)
                if name.lower() == "date":
                   self.report_email['date']= value        
        if not os.path.exists(folder_name):
           try:
              os.mkdir(folder_name)
           except:
              pass  
        self.parse_dmarc_parts(service, parts, folder_name, message,schedule_id)
        print("="*50)
        
    def parse_dmarc_parts(self,service, parts, folder_name, message,schedule_id):
        if parts:
            for part in parts:
                filename        = part.get("filename")
                self.report_email['original_report_name']= filename
                filename        = self.clean(filename)
                self.report_email['saved_filename']=  filename
                mimeType        = part.get("mimeType")
                body            = part.get("body")
                data            = body.get("data")
                file_size       = body.get("size")
                self.report_email['file_size']= self.get_size_format(file_size)
                part_headers    = part.get("headers")
                if part.get("parts"):
                    self.parse_dmarc_parts(service, part.get("parts"), folder_name, message)
                if mimeType  not in ["text/html", "text/plain"]:
                   for part_header in part_headers:
                        part_header_name = part_header.get("name")
                        part_header_value = part_header.get("value")
                        if part_header_name == "Content-Disposition":
                            if "attachment" in part_header_value:
                                # we get the attachment ID 
                                if not filename.endswith('html'):
                                    print("Saving report:", filename, "size:", self.get_size_format(file_size))
                                    attachment_id = body.get("attachmentId")
                                    attachment = service.users().messages().attachments().get(id=attachment_id, userId='me', messageId=message['id']).execute()
                                    data = attachment.get("data")
                                    filepath = os.path.join(folder_name, filename)
                                    if data:
                                        with open(filepath, "wb") as f:
                                            f.write(urlsafe_b64decode(data))
                                        report_check = ReportEmails.get({"original_report_name":self.report_email['original_report_name']})
                                        if not report_check:
                                            report_id  = ReportEmails.get_record_count()+1
                                            self.report_email['created_datetime']=datetime.now()
                                            self.report_email['report_id']=report_id
                                            report_file = None
                                            report_file =  os.path.join(current_app.config['EMAIL_PATH'], filename) 
                                            processed_report_file = os.path.abspath(os.path.dirname(os.path.dirname(report_file)))+os.sep+"processed"+os.sep+os.path.basename(report_file)
                                            self.report_email['processed_report_file']=processed_report_file
                                            report_email = ReportEmails(**self.report_email)
                                            report_email.save()
                                            queue = rq.Queue(current_app.config['REDIS_QUEUE_NAME'], connection= current_app.redis)
                                            source='email'
                                            queue.enqueue('app.tasks.process_uploaded_report',args=[report_file,  self.report_email['saved_filename'],report_id, 0,source,schedule_id], job_timeout=current_app.config['SYNC_INTERVAL'])
            messages_to_mark = []
            messages_to_mark.append(message)
            service.users().messages().trash( userId='me',id=message['id']).execute()
                            


                            