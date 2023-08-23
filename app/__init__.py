import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request #, current_app
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap5
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from config import Config
import json
from json import JSONEncoder
from flask_mongoengine import MongoEngine 
import rq
from rq_scheduler import Scheduler
from flask_session import Session
from redis import Redis
import bson
from flask_caching import Cache

from flask_wtf import  CSRFProtect

from datetime import datetime

def get_debug_template():
    from inspect import currentframe, getframeinfo
    return "\nFile \"{}\", line {}\nFunction (Method): '{}'\nMessage: {}\n",getframeinfo,currentframe

class DateTimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        elif isinstance(obj, bson.objectid.ObjectId):
            return str(bson.objectid.ObjectId(obj))

        return super(DateTimeEncoder, self).default(obj)
    


login               = LoginManager()
login.login_view    = 'auth.login'
login.login_message = _l('Please log in.')
mail                = Mail()
bootstrap           = Bootstrap5()
moment              = Moment()
babel               = Babel()
db                  = MongoEngine()
session             = Session()
settings            = None
is_running          = False
context             = None
csrf                = CSRFProtect()
cache               = None
cache                = Cache(config={'CACHE_TYPE': Config.CACHE_TYPE})


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    global settings
    settings                         = app.config
    app.config["SESSION_PERMANENT"]  = False
    app.json_encoder                 = DateTimeEncoder
    db.init_app(app)
    session.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
   
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue(app.config['REDIS_QUEUE_NAME'], connection=app.redis)
    app.scheduler  = Scheduler(queue = app.task_queue,connection=app.redis)
    from app.main import bp as main_bp
    #from app.errors import bp as errors_bp
    #from app.tasklist import bp as tasklist_bp
    from app.auth import bp as auth_bp
    from app.api import bp as api_bp
    #app.register_blueprint(errors_bp, url_prefix='/errors')
    #
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    #app.register_blueprint(tasklist_bp, url_prefix='/tasks')

        
    if not app.debug and not app.testing: #and not is_running:
        #is_running = True
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='{} Access Problem'.format(app.config['SITE_ID']),
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/{}.log'.format(app.config['SITE_ID']),maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info(app.config['STARTUP_MESSAGE'])
    return app

#@babel.localeselector
#def get_locale():
#    return request.accept_languages.best_match(current_app.config['LANGUAGES'])