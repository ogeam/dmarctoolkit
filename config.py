import json
from os import environ, path
from os.path import exists
from dotenv import load_dotenv
import json, os
configuration     =  None
components        =  None

basedir           =  path.abspath(path.dirname(__file__))
file_path         =  path.join(basedir, 'settings/configuration.json')
config_path       =  path.join(basedir, 'settings/component_defaults.json')

if exists(file_path):
   with open(file_path, 'r') as configuration_file:
       configuration = json.load(configuration_file)

if exists(config_path):
   with open(config_path, 'r') as components_file:
       components = json.load(components_file)
       
def get_configured_value(prop_name, default_value=None ):
    return   configuration[prop_name] or ( environ.get(prop_name) if   environ.get(prop_name)  else  default_value)
    
class Config(object):
    SITE_NAME         = get_configured_value('SITE_NAME', configuration['SITE_NAME'])
    SITE_ID           = get_configured_value('SITE_ID', configuration['SITE_ID'])
    MONGODB_DB        = get_configured_value('MONGODB_DB', configuration['MONGODB_DB'])
    MONGODB_HOST      = get_configured_value('MONGODB_HOST', configuration['MONGODB_HOST'])
    MONGODB_PORT      = get_configured_value('MONGODB_PORT', configuration['MONGODB_PORT'])
    MONGODB_USERNAME  = get_configured_value('MONGODB_USERNAME', configuration['MONGODB_USERNAME'])
    MONGODB_PASSWORD  = get_configured_value('MONGODB_PASSWORD', configuration['MONGODB_PASSWORD'])
    MONGODB_CONNECT   = get_configured_value('MONGODB_CONNECT', configuration['MONGODB_CONNECT'])

    SECRET_KEY        = get_configured_value('SECRET_KEY', configuration['SECRET_KEY'])
    SESSION_TYPE      = get_configured_value('SESSION_TYPE', configuration['SESSION_TYPE']) #,'redis')  filesystem
    REDIS_URL         = get_configured_value('REDIS_URL',  configuration['REDIS_URL'])# 'redis://' or  "redis://dmrctkt-redis-server:6379"
    #SESSION_REDIS     = redis.from_url(REDIS_URL)

    LOG_TO_STDOUT           = get_configured_value('LOG_TO_STDOUT',configuration['MONGODB_CONNECT'])
    MAIL_SERVER             = get_configured_value('MAIL_SERVER',configuration['MONGODB_CONNECT'])
    MAIL_PORT               = int(get_configured_value('MAIL_PORT',configuration['MAIL_PORT']))
    MAIL_USE_TLS            = get_configured_value('MAIL_USE_TLS', configuration['MAIL_USE_TLS']) 
    MAIL_USERNAME           = get_configured_value('MAIL_USERNAME', configuration['MAIL_USERNAME']) 
    MAIL_PASSWORD           = get_configured_value('MAIL_PASSWORD', configuration['MAIL_PASSWORD']) 
    ADMINS                  = get_configured_value('ADMINS', configuration['MAIL_PASSWORD']) 
    LANGUAGES               = get_configured_value( 'LANGUAGES' , configuration['LANGUAGES'])  #,['en', 'es'])
    MS_TRANSLATOR_KEY       = get_configured_value('MS_TRANSLATOR_KEY', configuration['MS_TRANSLATOR_KEY']) 
    RECORDS_PER_PAGE        = get_configured_value('RECORDS_PER_PAGE', configuration['MS_TRANSLATOR_KEY']) 
    #MAX_CONTENT_LENGTH      = get_configured_value('MAX_CONTENT_LENGTH', configuration['MS_TRANSLATOR_KEY']) #    # , 8 * 1024 *1024)
    #IMAGE_UPLOAD_EXTENSIONS = get_configured_value('IMAGE_UPLOAD_EXTENSIONS',  configuration['IMAGE_UPLOAD_EXTENSIONS'])  # ['.jpg', '.png', '.gif','.tiff','.bmp','.ico'])
    #IMAGE_UPLOAD_DIRECTORY  = get_configured_value('IMAGE_UPLOAD_DIRECTORY',path.dirname(path.realpath(__file__))+path.sep+'app'+path.sep+'static'+path.sep+'images')
    STARTUP_MESSAGE         = get_configured_value('STARTUP_MESSAGE', configuration['STARTUP_MESSAGE']) #    # , 8 * 1024 *1024)
    REDIS_QUEUE_NAME        = get_configured_value('REDIS_QUEUE_NAME', configuration['REDIS_QUEUE_NAME'])
    MONGODB_DB                     = get_configured_value('MONGODB_DB', configuration['MONGODB_DB'])
    MONGODB_HOST                   = get_configured_value('MONGODB_HOST', configuration['MONGODB_HOST'])
    MONGODB_PORT                   = get_configured_value('MONGODB_PORT', configuration['MONGODB_PORT'])
    MONGODB_USERNAME               = get_configured_value('MONGODB_USERNAME', configuration['MONGODB_USERNAME'])
    MONGODB_PASSWORD               = get_configured_value('MONGODB_PASSWORD', configuration['MONGODB_PASSWORD'])
    MONGODB_CONNECT                = get_configured_value('MONGODB_CONNECT', configuration['MONGODB_CONNECT'])
    MONGODB_REPLICASET             = get_configured_value('MONGODB_REPLICASET', configuration['MONGODB_REPLICASET'])
    MONGODB_DIRECT_CONNECTION      = get_configured_value('MONGODB_DIRECT_CONNECTION', configuration['MONGODB_DIRECT_CONNECTION'])
    MONGODB_AUTH_MECHANISM         = get_configured_value('MONGODB_AUTH_MECHANISM', configuration['MONGODB_AUTH_MECHANISM'])
    MONGODB_URL                    = get_configured_value('MONGODB_URL', configuration['MONGODB_URL'])
    UPLOAD_EXTENSIONS              =  configuration["UPLOAD_EXTENSIONS"]
    TIME_OUT_MINUTES               =  configuration["TIME_OUT_MINUTES"]
    UPLOAD_PATH                    = basedir+os.sep+"app"+os.sep+"static"+os.sep+"uploads"+os.sep+"new"
    EMAIL_PATH                     = basedir+os.sep+"app"+os.sep+"static"+os.sep+"uploads"+os.sep+"emails"
    KEY_PATH                       = basedir+os.sep+"app"+os.sep+"static"+os.sep+"uploads"+os.sep+"keystore"
    CIPHER_COUNT                   = get_configured_value('CIPHER_COUNT', configuration['CIPHER_COUNT'])
    DEBUG                          =  True
    CACHE_TYPE                     =  "SimpleCache"
    mongodb_url_settings           = {"db":MONGODB_DB, "host": MONGODB_URL,"alias":"default",'connect': MONGODB_CONNECT}
    mongo_repl_settings            = {
                                        'db': MONGODB_DB,
                                        'host': MONGODB_HOST,                                   
                                        'username':MONGODB_USERNAME,
                                        'password':MONGODB_PASSWORD,
                                        'directConnection': MONGODB_DIRECT_CONNECTION,
                                        'connect': MONGODB_CONNECT,
                                        'port': MONGODB_PORT,
                                        'replicaSet': MONGODB_REPLICASET,
                                        'authMechanism': MONGODB_AUTH_MECHANISM
                                        ,"alias":"default"
                                    }
    MONGODB_SETTINGS               = mongodb_url_settings if MONGODB_URL!="" else mongo_repl_settings
    DEFAULT_CONNECTION_NAME       = "default"
    COMPONENTS                    = components
    COMPONENT_CONFIG = {}
    COMPONENT_CONFIG["mongoBridgeURL"]  = configuration["MONGO_BRIDGE_URL"]
    COMPONENT_CONFIG["pouchDBPort"]     = configuration["POUCHDB_PORT"]
    COMPONENT_CONFIG["pouchDBUsername"] = configuration["POUCHDB_USERNAME"]
    COMPONENT_CONFIG["pouchDBPassword"] = configuration["POUCHDB_PASSWORD"]
    COMPONENT_CONFIG["pouchDBDatabase"] = configuration["POUCHDB_DATABASE"]
    COMPONENT_CONFIG["pouchDBServer"]   = configuration["POUCHDB_SERVER"]
    SYNC_INTERVAL                       = configuration["SYNC_INTERVAL"]
    COMPONENT_CONFIG["syncInterval"]    = SYNC_INTERVAL
    COMPONENT_CONFIG["syncInfo"]        =  configuration["SYNC_INFO"]
    COMPONENT_CONFIG["syncMode"]        =  configuration["SYNC_MODE"]
    COMPONENT_CONFIG["UPLOAD_EXTENSIONS"]  = UPLOAD_EXTENSIONS
    CACHE_DEFAULT_TIMEOUT               =  SYNC_INTERVAL
    
    
