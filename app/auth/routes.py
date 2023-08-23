from flask import render_template, redirect, url_for, flash, request, session,jsonify
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_babel import _
from app import  db, login,get_debug_template,settings
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import Users
#from app.auth.email import send_password_reset_email
from datetime import datetime
#from uuid import uuid4
import traceback

@login.user_loader
def load_user(id):
    #print(get_debug_template()[0].format(get_debug_template()[1](get_debug_template()[2]()).filename, get_debug_template()[1](get_debug_template()[2]()).lineno,
    #                   'load_user', "id: {}".format(session['current_user'].__dict__['_data']['id']))) 
    id = session['current_user'].__dict__['_data']['id']  if id is None or (id and str(id).lower()=='none') else id
    #print(get_debug_template()[0].format(get_debug_template()[1](get_debug_template()[2]()).filename, get_debug_template()[1](get_debug_template()[2]()).lineno,
    #                   'load_user', "id: {}".format(id))) 
    user =Users().get({'id':id})
    session['current_user'] = user if user else  session['current_user']
    return user if user else None 

@bp.route('/auth/login', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('current_user'):
        if session['current_user'].is_authenticated and not session['current_user'].locked:
           return redirect(url_for('main.index'))
    form = LoginForm()

    if request.method  == 'POST':
        user= Users().get({"username":form.username.data.lower()})
        if not bool(user)  or  not user.check_password(form.password.data):
            print('Invalid user account')
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        #print("session user info: {}".format(user.__dict__))
        login_user(user, remember =form.remember_me.data)
        next_page                 =  request.args.get('next')
        user.connectionStatus     = True
        login_count               = int(user.loginCount)
        user.loginCount           = login_count+1
        template                  = get_debug_template()[0]
        template_info             = get_debug_template()[1](get_debug_template()[2]())
        print(template.format(template_info.filename,int(template_info.lineno)+1,'login', f"initial revision and ID:{user.id},{user.id}"))
        user.save()
        session['current_user'] = user
        print(get_debug_template()[0].format(get_debug_template()[1](get_debug_template()[2]()).filename, get_debug_template()[1](get_debug_template()[2]()).lineno,
                'login', f"User ID :{user.id}"))
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        print('Logged in successfully.')
        return redirect(next_page)
    else:
        print('form is not valid')
        print(form.errors)
    opts                = {} 

    
    opts['logo']        =   "/static/logo_mini.png"
    opts['startTime']   =  datetime.utcnow()
    opts['timeOut']     =  None
    opts['siteName']    =  settings['SITE_ID']
    opts['userName']    =  None
    opts['previousDest']=  None
    opts['currentTime'] =  datetime.utcnow()
    opts['siteTitle']   =  settings['SITE_NAME']
    opts['user_count']  =  Users().get_record_count()
    print("user_count:  {}  ".format(opts['user_count']))
    message             = 'Sign In: Authorized Personnel Only'
    config              = jsonify({"dummy_data":1})
    defaultProperties   = jsonify({"dummy_data":1})
    return render_template('auth/login.html', title=_('Sign In'), pageID='login', options=opts, year='2023', form=form,message=message)


@bp.route('/logout')
def logout():
    if  session and 'current_user' in  session:
        session['current_user'].connectionStatus  = False
        session['current_user'].save()
        logout_user()
        session['current_user']= None
    return redirect(url_for('auth.login'))

@bp.route('/auth/register', methods=['GET', 'POST'])
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    print(request.form)
    if request.method.lower() == 'post' and request.form['email'] is not None and request.form['surname'] is not None and request.form['firstName'] is not None and request.form['username'] is not None and request.form['password'] is not None:
        #user = Users(request.form['text'], email=form.email.data)
        user  = Users(id=(Users().get_record_count()+1), firstName =request.form['firstName'].lower(),surname  =request.form['surname'].lower(),username  =request.form['username'].lower(),
                    email        = request.form['email'].lower(),
                    creationDate = datetime.utcnow(),
                    locked       = False ,
                    role         = 'admin',
                    connectionStatus = True ,
                    active =  True ,
                    reset = False ,
                    lastModifiedDate =datetime.utcnow(),
                    loginCount =0
        )
        user.set_password(form.password.data)
        user.save()
        flash(_('Registration Successful!'))
        return redirect(url_for('auth.login'))
    else:
        print('form is not valid')
    opts ={} 
    opts['logo']        =  "/static/logo_mini.png"
    opts['startTime']   =  datetime.utcnow()
    opts['timeOut']     =  None
    opts['siteName']    =  settings['SITE_ID']
    opts['userName']    =  None
    opts['previousDest']=  None
    opts['currentTime'] =  datetime.utcnow()
    opts['siteTitle']   =   settings['SITE_NAME']
    return render_template('auth/register.html',pageID='register', options=opts, title=_('Add User'),form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Users.objects(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',title=_('Reset Password'), form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = Users.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
