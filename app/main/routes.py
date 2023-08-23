from datetime import datetime, timedelta
import flask
from flask import render_template, flash, redirect, request, url_for, g, jsonify, current_app,abort, send_from_directory,session
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from flask_babel import _, get_locale
#from guess_language import guess_language
from app import db,settings,get_debug_template #,socketio

from app.main.forms import LoginForm #, EditProfileForm, EmptyForm, PostForm, SearchForm, MessageForm
from app.models import Roles,Users,Jobs,AuditTrail,SiteSettings,Alerts,Tasks,Schedules,Schedulers, ReportUploads, ReportMetadata
#from app.translate import translate
from app.main import bp
import traceback, json
from app.main.serializer import Serializer
import os
#from PIL import Image,ImageEnhance
from inspect import getmembers, isfunction
import time
import re


def  repair_references(ref_string):
    return re.sub('href="(\w*)"', 'href="/\1"',re.sub('"[./]*[.]*plugins', '"/static/plugins',re.sub('"[./]*[.]*dist', '"/static/dist', ref_string)))   


#@bp.before_app_request
#def before_request():
#    if current_user.is_authenticated:
#        current_user.last_seen = datetime.utcnow()
#        db.session.commit()
##        g.search_form = SearchForm()
#    g.locale = str(get_locale())


#from uuid import UUID

#def is_uuid(data):
#    isUUID =False
#    try:
#        UUID(data)
#        isUUID = True
#    except Exception as e:
#        print(str(e))
#    return isUUID

#class CustomJSONDecoder(json.JSONDecoder):
#      def default(self, obj):
#        if is_uuid(obj):
#           return str(obj)
#        return json.JSONDecoder.default(self, obj)

@bp.before_request
def make_session_permanent():
    session.permanent = True
    bp.permanent_session_lifetime = timedelta(minutes=current_app.config["TIME_OUT_MINUTES"])


def get_task_names():
    return getmembers(tasks, isfunction) 



def get_items(records):
    record_items = []
    if isinstance(records,list):
        for record in records:
            record_items.append(record.__dict__['_data'])
    else:
        record_items.append(records.__dict__['_data'])
    return record_items

def finder(model_type, fields=None, sort_hash_list=None):
    mango = None
    if fields:
        mango = {'selector': {'type': model_type},'fields': fields,'sort_list':sort_hash_list} if sort_hash_list  else {'selector': {'type': model_type},'fields': fields}
    else:
        mango = {'selector': {'type': model_type},'sort_list':sort_hash_list}      if sort_hash_list  else {'selector': {'type': model_type}}  
    return  db.find(mango)                               
def data_retriever(model,action,display_format,query_fields):
    response  =  None
    model      = model.capitalize()
    if model   =='Servers':
        model  = 'VMs'
    elif model == 'Sitesettings':
        model  =  'SiteSettings'
    elif model == 'Audittrail':
        model  =  'AuditTrail'
    model_class = eval(model)
    print('model_class: {}'.format(model_class))

    if action=='sel' and display_format=='form':
        if 'id' in query_fields:
            query_fields['id']= int(query_fields['id'])
        query_fields['doc_type']= model_class().doc_type
        print(f'query_fields: {query_fields}')
        records           = model_class().fetch(db,query_fields) if  query_fields is not None else []
        print(records)
        all_records = []
        if records:
            for record in records:
                entry = {}
                if hasattr(record, '__dict__'):
                    for field in record.__dict__['_data'][field]:
                        entry[field] = record.__dict__['_data'][field]
                else:
                    entry[record] = records[record]
                if entry:
                    all_records.append(entry)
        response =  {'columns':(model_class.get_schema())[model.lower()],'tabData':all_records,'dataCount':1 }
    elif action=='sel' and display_format=='table':
        records = get_items(model_class().get())
        all_records = []
        for record in records:
            entry = {}
            if hasattr(record, '__dict__'):
                for field in record.__dict__['_data'][field]:
                    entry[field] = record.__dict__['_data'][field]
            else:
                 for field in record:
                     entry[field] = record[field]
            if entry:
                all_records.append(entry)
            
        response = {'columns':(model_class.get_schema())[model.lower()],'tabData':all_records,'dataCount':(model_class().get_record_count())}
    return response


@bp.route('/main/dataselect', methods=['GET'])
@bp.route('/contents',methods=['GET'] )
@login_required
def contents():
    return  render_template('main/contents.html')
    
@bp.route('/main/dataselect', methods=['GET'])
@bp.route('/dataselect',methods=['GET'] )
@login_required
def get_data_for_select():
    model              =  request.args.get('c').lower()  if request.args.get('c') else None
    key_field          =  request.args.get('k').lower()  if request.args.get('k') else None
    value_field        =  request.args.get('v').lower()	 if request.args.get('v') else None
    action             =  request.args.get('qt')         if request.args.get('qt') else None
    display_format     =  request.args.get('df')         if request.args.get('df') else None
    query_fields       =  request.args.get('qf')         if request.args.get('qf') else None
    table_data         =  {}
    all_records        =  []
    data_count         =  0 
    if model == 'tasknames':
        records = get_task_names()
        all_records = []
        for record in records:
            if record[0] not in ['get_current_job','render_template','create_app']:
                temp ={}
                temp['name'] = record[0]
                temp['taskname'] = 'app.tasks.{r}'.format(r=record[0])
                all_records.append(temp)
            data_count = len(all_records)
        print(all_records)
        return  jsonify({'tabData':all_records,'dataCount':data_count}) 
    elif  ',' not in model:
        print('model: {}'.format(model))
        print('key_field: {}'.format(key_field))
        print('value_field: {}'.format(value_field))
        print('model: '+model)
        model = model.capitalize()
        if model=='Servers':
            model = 'VMs'
        elif model == 'Sitesettings':
            model  =  'SiteSettings'
        elif model == 'Audittrail':
            model  =  'AuditTrail'
        model_class = eval(model)
        raw_records = model_class().get()
        #print('raw records')
        #print(raw_records)
        all_records = []
        for record in raw_records:
            entry = {}
            if hasattr(record, '__dict__'):
                for field in [key_field,value_field]:
                    entry[field] = record.__dict__['_data'][field]
            else:
                 if record in [key_field,value_field]:
                     entry[record] = raw_records[record]
            if entry:
                all_records.append(entry)
        #print(all_records)      
        data_count  = (model_class().get_record_count())
        return jsonify({'tabData':all_records,'dataCount':data_count}) 
    else:
        tables = model.split(',')
        for table in tables:
            table = table.lower()
            table_data[table] = data_retriever(table,action,display_format,query_fields)
        return jsonify(table_data) 

@bp.route('/main/images', methods=['GET', 'POST'])
@bp.route('/images', methods=['GET', 'POST'])
@login_required
def process_image_request():
    response     = {}
    path_sep     = os.path.sep
    record_index = 0
    print(request)
    for i in request.form.keys():
       print('key:{k} => value:{v}'.format(k=i,v=request.form[i]))
    for i in request.files.keys():
       print('file keys:{k} => value:{v}'.format(k=i,v=request.files[i]))
    try:
        if session['current_user'].is_authenticated:
          method                 =  request.method.lower()      
          action                 =  request.form['action'] if request.form['action'] else None
          action                 =  request.form['qt']     if None== action and request.form['qt'] else action
          action                 =  request.form['t']      if None== action and request.form['t'] else action
          query_fields           =  request.form['qf']     if request.form['qf'] else None
          query_fields           =  request.form['f']      if request.form['f'] else query_fields
          display_format         =  request.form['df']     if request.form['df'] else 'table'
          if method              == 'post':
            if action            == 'add':
                image_path       =  ''
                uploaded_file    = request.files['image_file']
                filename         = request.form['filename']
                fileFormat       = request.form['fileformat']
                fileSize         = request.form['filesize']
                lastModifiedDate = request.form['lastmodifieddate']
                imageCategory    = request.form['imagecategory']
                dimensions       = json.loads(request.form['dimensions'])
                if filename != '':
                    filename = secure_filename(filename)
                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in current_app.config['IMAGE_UPLOAD_EXTENSIONS']: #or file_ext != validate_image(uploaded_file.stream):
                        abort(400)
                image_folder = current_app.config['IMAGE_UPLOAD_DIRECTORY']+path_sep+imageCategory
                if not os.path.exists(image_folder):
                    os.mkdir(image_folder)
                uploaded_file_path = os.path.join(image_folder, filename)
                record_index     =  Images().get_last_record_id() +1
                image            =  Images().init_attributes(
                            {'id': record_index,
                            'fileName':  filename,
                            'fileFormat':  fileFormat,
                            'fileURL':  os.path.sep+uploaded_file_path.split(os.path.sep)[-4]+os.path.sep+uploaded_file_path.split(os.path.sep)[-3]+os.path.sep+uploaded_file_path.split(os.path.sep)[-2]+os.path.sep+uploaded_file_path.split(os.path.sep)[-1],
                            'fileSize':  fileSize,
                            'dimension':  request.form['dimensions'],
                            'sourceURL':  request.form['sourceUrl'] ,
                            'lastModifiedDate':  lastModifiedDate
                            }
                    ).save()
                uploaded_file.save(uploaded_file_path)
                image_path             =  os.path.sep+uploaded_file_path.split(os.path.sep)[-4]+os.path.sep+uploaded_file_path.split(os.path.sep)[-3]+os.path.sep+uploaded_file_path.split(os.path.sep)[-2]+os.path.sep+uploaded_file_path.split(os.path.sep)[-1]
                model                  =  'Images'
                trailIndex             =  AuditTrail().get_last_record_id() +1
                query_fields           =  {'id':record_index}
                description_info       =  'Addition of new record to {m}'.format(m=model)  
                change_type            =  'INSERT'
                oldData				   =   {}
                newData 			   =   image.__dict__
                AuditTrail().init_attributes({
                'id':trailIndex,'description':description_info,'oldData':oldData,'newData':newData,'affectedTable':model,'changeTime':str(datetime.utcnow()),'changeType':change_type,'userName':current_user.username,'userID':current_user.id,'recordIdentifier':query_fields
                }).save()
                image                     = Image.open(uploaded_file_path)
                resized_image             = image.resize((dimensions['width'], dimensions['height']))
                sharp_image               = ImageEnhance.Sharpness(resized_image)
                sharp_image.enhance(1.85).save(uploaded_file_path)
                response['uploadPath']    = image_path
                response['imageCategory'] = imageCategory
                response['isSuccessful']  = True
                response['model']         = 'Images'
                response['header']        = 'New Image Record'
                response['error']         = None
                response['record_index']  = record_index
                return jsonify(response)
            elif  action == 'del':
                model                    =  'Images'
                action                   =  'del'
                trailIndex               =  AuditTrail().get_last_record_id() +1
                newData				     =   {}
                description_info         =  'Removal of {m} record with details: {d} '.format(m=model,d=query_fields)
                change_type              =  'DELETE'
                oldData              	 =  image.__dict__
                auditTrail               =  AuditTrail().init_attributes ( {
                            'id':trailIndex,'description':description_info,'oldData':oldData,'newData':newData,'affectedTable':model,'changeTime':str(datetime.utcnow()),'changeType':change_type,'userName':session['current_user'].username,'userID':session['current_user'].id,'recordIdentifier':query_fields
                } ).save()
                if 'id' in query_fields:
                    query_fields['id']= int(query_fields['id'])
                query_fields['doc_type']= model_class().doc_type
                image					 = Images().fetch(db,query_fields).delete(db)
                response['message']      = 'Images with  ID \'{}\' has been successfully removed'.format(record_index)
                response['isSuccessful'] = True
                response['model']        = 'Images'
                response['header']       = 'Images Record Removal'
                response['error']        = None
                response['record_index'] = query_fields['_id']
                return jsonify(response)
         
    except Exception as e:
        traceback.print_exc()
        response['message']      = 'There was an error uploading the image'
        response['isSuccessful'] = False
        response['model']        = 'Images'
        response['error']        = str(e)
        response['header']       = "Image Upload Error"
        return jsonify(response)
        
@bp.route('/main/schema', methods=['GET'])
@bp.route('/schema',methods=['GET'] )
@login_required
def get_schema():
    model =  request.args.get('qf').replace(' ','').capitalize()
    if model=='Servers':
        model = 'VMs'
    elif model == 'Sitesettings':
        model  =  'SiteSettings'
    elif model == 'Audit':
        model  =  'AuditTrail'

    model_class = eval(model)
    print('model_class: {}'.format(model_class))
    return jsonify(model_class.get_schema())


@bp.route('/main/data', methods=['GET', 'POST'])
@bp.route('/data', methods=['GET', 'POST'])
@login_required
def process_data_request():
    try:
        response = {}
        for i in request.form.keys():
            if 'password' in i:      
                print('key:{k} => value:{v}'.format(k=i,v=Serializer().multiDemystify(request.form[i],3)))
            else:
                print('key:{k} => value:{v}'.format(k=i,v=request.form[i]))
            print('request method: {}'.format(flask.request.method))
        is_valid       =  None
        model          =  None
        query_fields   =  None
        display_format =  None
        action         =  None
        newData        =  {}
        oldData        =  None
        model_class    =  None

        if current_user.is_authenticated:
            method       =  flask.request.method.lower()      
            if method == 'post':
                for  key in  request.form.keys():
                    print('post key: '+key)
                    if key =='is_form_data_valid':
                        is_valid     =  request.form[key].lower()
                    elif key =='data_item' or key == 'c':
                        model     =  request.form[key].lower()
                    elif key =='f' or key =='qf':
                        query_fields    =  request.form[key].lower()
                    elif key =='t'  or key =='qt':
                        action    =  request.form[key].lower()
                    if  'pl' in key:
                       formatted_key = key.replace('pl[','').replace(']','')
                       newData[formatted_key] = request.form[key]          
                print('action: '+action)
                print('query_fields: '+query_fields)
            elif   method  == 'get':
                model            =  request.args.get('c').lower() if request.args.get('c') else None
                action           =  request.args.get('qt') if request.args.get('qt') else 'sel'
                display_format   =  request.args.get('df') if request.args.get('df') else None
                query_fields     =  json.loads(request.args.get('qf')) if request.args.get('qf') != None  else None
            print('action: '+action)
            print('model: '+model)
            model = model.capitalize()
            if model=='Servers':
                model = 'VMs'
            elif model == 'Sitesettings':
                model  =  'SiteSettings'
            elif model == 'Audittrail':
                model  =  'AuditTrail'
            model_class = eval(model)
            
            if action  in ['add','udt', 'del']:
                trailIndex           =  AuditTrail().get_last_record_id() +1
                if action            !='add':                   
                  if '_id' in query_fields:
                      query_fields = query_fields.strip()
                      query_fields = ''.join([ query_fields[x] for  x in  range(2, len(query_fields)-2)])
                      new_fields = {}
                      for field in query_fields.split(','):
                          item  = field.strip().split(':')
                          item[0] = item[0].replace('"','').replace('\'','')
                          new_fields[item[0]] = item[1].replace('"','').replace('\'','')
                      query_fields = new_fields
                  else:
                      query_fields = json.loads(query_fields)
                  query_fields['doc_type']= model_class().doc_type
                  print(query_fields)
                  oldData            = model_class().fetch(db,query_fields)
                else:
                    query_fields     = {}
                description_info     = None
                change_type          = None
                if action            == 'add':
                    description_info  =  'Addition of new record to {m}'.format(m=model)  
                    change_type       =  'INSERT'
                elif action          == 'udt':
                    description_info  =  'Modification of {m} record with details: {d} '.format(m=model,d=query_fields)
                    change_type       =  'UPDATE'
                elif action          == 'del':
                    description_info  =  'Removal of {m} record with details: {d} '.format(m=model,d=query_fields)
                    change_type       =  'DELETE'
                print('logging change...')
                #oldData=  oldData.to_mongo() if oldData else {}
                #oldData=  oldData.__dict__ if oldData else {}
                oldData =   oldData.get_json() if oldData else {}
                AuditTrail().init_attributes({'id':trailIndex,'description': description_info,' oldData':oldData,' newData':newData,'affectedTable':model,'changeTime':str(datetime.utcnow()),'changeType':change_type,'userName':session['current_user'].username,'userID':session['current_user'].id,'recordIdentifier':query_fields} ).save()               
            if method == 'post':
                is_form_valid =  True if is_valid =='yes' else False
                if is_form_valid:
                    if action == 'add':
                        print('last record id: '+str(model_class().get_last_record_id()))
                        record_index     =  model_class().get_last_record_id() +1
                        print('record index: {}'.format(record_index))
                       
                        columns= model_class.get_schema()['order']
                        columns_value_map = {}
                        columns_value_map['id'] = record_index
                            
                        for column in columns:
                           value_index  = 'pl[{c}]'.format(c=column.lower())
                           field_value  =  request.form[value_index] if value_index in request.form else None
                           if column == 'active':
                              field_value = True if field_value.lower()== 'yes' else False 
                           if column not in [ '_id','id'] or (column == '_id' and  None !=field_value):
                               columns_value_map[column]= field_value
                     
                        model_class().init_attributes(columns_value_map).save()
                        response['message']      = 'A new record  has been successfully added to '+model
                        response['isSuccessful'] = True
                        response['model']        = model.capitalize()
                        response['header']       = 'New Record Added to {t}'.format(t=model.capitalize())
                        response['error']        = None
                        response['record_index'] = record_index
                        response_info ={}
                        response_info['message']      = 'A new record  has been successfully added to '+model
                        response_info['isSuccessful'] = True
                        response_info['model']        = model.capitalize()
                        response_info['header']       = 'New Record Added to {t}'.format(t=model.capitalize())
                        response_info['error']        = None
                        response_info['record_index'] = record_index
                    
                        if response['error'] == None:
                            response_data = json.dumps(response_info)
                        return  jsonify(response)
                    elif action ==  'udt':
                        print('updating record')
                        columns= model_class.get_schema()['order']
                        columns_value_map = {}
                        if 'id' in query_fields:
                            query_fields['id']= int(query_fields['id'])
                        query_fields['doc_type']= model_class().doc_type
                        record = model_class().fetch(db,query_fields)
                        for column in columns:
                           value_index  = 'pl[{c}]'.format(c=column.lower())
                           field_value  = request.form[value_index] if request.form[value_index]  else record[column]
                           if column == 'active':
                              field_value = True if field_value.lower()== 'yes' else False 
                           columns_value_map[column] = field_value
                        columns_value_map['_id'] = record['_id']
                        columns_value_map['_rev'] = record['_rev']  
                        model_class().init_attributes(columns_value_map).save()
                
                        response['message']      = 'The details of record {} of {}  have been successfully updated'.format(request.form['pl[id]'],model)
                        response['isSuccessful'] = True
                        response['model']        = model.capitalize()
                        response['header']       = '{t}: Record Update'.format(t=model.capitalize())
                        response['error']        = None
                        response['record_index'] = query_fields['_id']
                        response_info = {}
                        response_info['message']      = 'The details of record {} of {}  have been successfully updated'.format(request.form['pl[id]'],model)
                        response_info['isSuccessful'] = True
                        response_info['model']        = model.capitalize()
                        response_info['header']       = '{t}: Record Update'.format(t=model.capitalize())
                        response_info['error']        = None
                        response_info['record_index'] = query_fields['_id']

                        if response['error'] == None:
                            response_data = json.dumps(response_info)
                          #  socketio.emit('datachangecommitted', response_data, broadcast=True)
                        return  jsonify(response)
                    elif action ==  'del':
                        print('deleting record...')
                        record_index = query_fields['_id']
                        if 'id' in query_fields:
                            query_fields['id']= int(query_fields['id'])
                        query_fields['doc_type']= model_class().doc_type
                        model_class().fetch(db,query_fields).delete(db)
                        response['message']      = 'Record with  ID \'{}\' has been successfully removed'.format(record_index)
                        response['isSuccessful'] = True
                        response['model']        =  model.capitalize()
                        response['header']       = '{t}: Record Removal'.format(t=model.capitalize())
                        response['error']        = None
                        response['record_index'] = record_index  
                        response_info= {}
                        response_info['message']      = 'Record with  ID \'{}\' has been successfully removed'.format(record_index)
                        response_info['isSuccessful'] = True
                        response_info['model']        =  model.capitalize()
                        response_info['header']       = '{t}: Record Removal'.format(t=model.capitalize())
                        response_info['error']        = None

                        return  jsonify(response)
            elif method  == 'get':
                print("model: {}".format(model))
                print("action: {}".format(action))
                print("query_fields: {}".format(query_fields))
                print("display_format: {}".format(display_format))
                response = data_retriever(model, action, display_format,query_fields)
                #print(get_debug_template()[0].format(get_debug_template()[1](get_debug_template()[2]()).filename, get_debug_template()[1](get_debug_template()[2]()).lineno,
                #'login', "response:{} ".format(response)))
                return  jsonify(response)
        else:
            response['message']      = 'form is not valid'
            response['isSuccessful'] = False
            response['model']        = 'Events'
    except Exception as e:
        traceback.print_exc()
        response['message']      = 'There was an error during the data update. Please contact your administrator'
        response['isSuccessful'] = False
        response['model']        = model
        response['error']        = str(e)
        response['header']       = "Error Updating {m} Information: ".format(m=model)
    return  jsonify(response)


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/main/index', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
 
    opts ={} 
    opts['logo']        =   "/static/logo_mini.png"
    opts['startTime']   =  datetime.utcnow()
    opts['timeOut']     =  None
    opts['siteName']    =  settings['SITE_ID']
    opts['userName']    =  None
    opts['previousDest']=  None
    opts['currentUser'] =  session['current_user'].username
    opts['currentTime'] =  datetime.utcnow()
    opts['siteTitle']   = settings['SITE_NAME']
    
    tdelta = timedelta(  days=1, seconds=0, microseconds=0)
    end_date = datetime.now()+tdelta if current_app.config['COMPONENTS']["contentHeader"]["contentWrapper"]["dashboardReportRange"]["reportEnd"]=="" else current_app.config['COMPONENTS']["contentHeader"]["contentWrapper"]["dashboardReportRange"]["reportEnd"]
    if current_app.config['COMPONENTS']["contentHeader"]["contentWrapper"]["dashboardReportRange"]["reportEnd"]=="":
       current_app.config['COMPONENTS']["contentHeader"]["contentWrapper"]["dashboardReportRange"]["reportEnd"]=end_date.strftime('%Y-%m-%d %H:%M:%S')
    tdelta = timedelta(  days=365, seconds=0, microseconds=0)
    start_date = current_app.config['COMPONENTS']["contentHeader"]["contentWrapper"]["dashboardReportRange"]["reportStart"] if current_app.config['COMPONENTS']["contentHeader"]["contentWrapper"]["dashboardReportRange"]["reportStart"] else '2012-01-01 00:00:00'
    start_date =  datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')#end_date -tdelta 
    dashboard_data  =  get_stats_info(start_date,end_date )   
    current_app.config['COMPONENTS']['dashboardData'] = dashboard_data
    data_config         = json.dumps(current_app.config['COMPONENT_CONFIG'])
    default_properties  = json.dumps(current_app.config['COMPONENTS'])
    version             =  round(time.time()*1000)

    return render_template('main/index.html', title='Dashboard',pageID='dashboard',options=opts, dataConfig=data_config,defaultComponents=default_properties, version=version)

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

def get_stats_info(start_date,end_date, domain="."):

    report_data = ReportMetadata.objects().aggregate( [ 
        { 
             "$match":{  "report_metadata_begin_date": {"$gte": start_date,"$lte":  end_date}  }
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
		},{ 
		  
		  "identifiers_header_from": {"$regex":  domain}
		},{ 
		  
		  "identifiers_envelope_from":{"$regex":  domain}
		},{ 
		  
		  "spf_domain": {"$regex":  domain}
		}
]
}
            } ] )
    temp_data = list(report_data)
    results = get_collection_data(temp_data) if len(temp_data) >0   else []
    
    return results
"""
@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
"""
