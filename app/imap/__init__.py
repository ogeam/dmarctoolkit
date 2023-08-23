import imaplib
import email
from email.header import decode_header
import os
import traceback
import re
import ssl
from datetime import datetime
import rq 
from flask import current_app
from app.models import ReportEmails

class ImapEmailHelper():

    def __init__(self,server, username, password, port, folder, security='ssl'):
        self.username         = username
        self.password         = password
        self.imap_server      = server
        self.port             = port
        self.security         = security
        self.imap             = None
        self.folder           = folder
        self.report_email      = {}
        self.connect()

    def clean(self,text):
        new_text = "".join(c if c.isalnum() else "_" for c in text)
        ext      = new_text.split('_')[-1]
        ext_len  = -1 *(len(ext)+1)
        new_text = new_text[0:ext_len]+'.'+ext
        return new_text
               
    def parse_list_response(self, line):
        list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')
        flags, delimiter, mailbox_name = list_response_pattern.match(line).groups()
        mailbox_name = mailbox_name.strip('"')
        return (flags, delimiter, mailbox_name)

    def connect(self): 
        if self.security.lower()=='ssl':
            self.imap = imaplib.IMAP4_SSL(self.imap_server, self.port)
            self.imap.login(self.username, self.password)
        elif self.security.lower()=='tls':
            tls_context = ssl.create_default_context()
            self.imap = imaplib.IMAP4(self.imap_server, self.port)
            self.imap.starttls(ssl_context=tls_context)
            self.imap.login(self.username, self.password)
             
    def show_mailboxes(self):
        self.imap.list()

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
        
    def get_mailbox_messages(self, mailbox, schedule_id):
        _, messages = self.imap.select(mailbox)
        messages = int(messages[0])
        for i in range(messages,0, -1):
            res, msg = self.imap.fetch(str(i), "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding)
                    From, encoding = decode_header(msg.get("From"))[0]
                    
                    if isinstance(From, bytes):
                        From = From.decode(encoding)
                        print('From: '+From)
                        print('Subject: '+subject)              
                    if msg.is_multipart():
                        for part in msg.walk():
                            #content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            try:
                               if "attachment" in content_disposition:
                                    filename,encoding = decode_header(part.get_filename())[0]
                                    original_attached_filename = None
                                    if(encoding ):
                                       original_attached_filename = filename.decode(encoding)
                                       self.report_email['original_report_name']= original_attached_filename
                                    else: 
                                       original_attached_filename = filename
                                       print(filename)
                                       self.report_email['original_report_name']= original_attached_filename
                                    if original_attached_filename:
                                        new_attached_filename = self.clean(original_attached_filename)
                                        self.report_email['saved_filename']=  new_attached_filename
                                        if not os.path.isdir(self.folder):
                                            os.mkdir(self.folder)
                                        filepath = os.path.join(self.folder, new_attached_filename)
                                        print(f'Saving report attachment to {filepath}')
                                        open(filepath, "wb").write(part.get_payload(decode=True))
                                        file_stats = os.stat(filepath)
                                        file_size = file_stats.st_size
                                        self.report_email['file_size']= self.get_size_format(file_size)
                                        report_check = ReportEmails.get({"original_report_name":self.report_email['original_report_name']})
                                        if not report_check:
                                            report_id  = ReportEmails.get_record_count()+1
                                            self.report_email['created_datetime']=datetime.now()
                                            self.report_email['report_id']=report_id
                                            processed_report_file = os.path.abspath(os.path.dirname(os.path.dirname(filepath)))+os.sep+"processed"+os.sep+os.path.basename(filepath)
                                            self.report_email['processed_report_file']=processed_report_file
                                            report_email = ReportEmails(**self.report_email)
                                            report_email.save()
                                            queue = rq.Queue(current_app.config['REDIS_QUEUE_NAME'], connection= current_app.redis)
                                            source='email'
                                            queue.enqueue('app.tasks.process_uploaded_report',args=[filepath,  self.report_email['saved_filename'],report_id, 0,source,schedule_id], job_timeout=current_app.config['SYNC_INTERVAL'])
                                        self.imap.store(str(i), "+FLAGS", "\\Deleted")
                                        self.imap.expunge()
                            except:
                                traceback.print_exc()
                        print("="*100)
            
    def search_alt(self, search_string):
        try:
            typ, mailbox_data = self.show_mailboxes()
            for line in mailbox_data:
                flags, delimiter, mailbox_name = self.parse_list_response(line)
                self.imap.select(mailbox_name, readonly=True)
                typ, msg_ids = self.imap.search(None, search_string) 
                print (mailbox_name, typ, msg_ids )      
        except:
            traceback.print_exc()
            

    def search(self, search_string):
        try:
            self.imap.search(None, search_string) #https://gist.github.com/martinrusev/6121028
        except:
            traceback.print_exc()
            
            
        def delete(self, filter_string):
            _,messages = self.search(filter_string)
            messages = messages[0].split(b' ')
            for mail in messages:
                _, msg = self.imap.fetch(mail, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    print("Deleting", subject)
            self.imap.store(mail, "+FLAGS", "\\Deleted")
            self.imap.expunge()

    def close_connection(self):
        self.imap.close()
        self.imap.logout()
        
        
    
