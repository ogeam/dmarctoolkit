from app import create_app, db, cli,login,mail,bootstrap,moment,babel
from app.models import Roles,Users,Jobs,AuditTrail,SiteSettings,Alerts#,Tasks



app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
   return {'create_app':create_app, 'db':db,'cli':cli,'login':login,'mail':mail,'bootstrap':bootstrap,'moment':moment,'babel':babel,'session':session,'roles': Roles,'users': Users,'auditTrail':AuditTrail,'siteSettings':SiteSettings,'settings':app.config} #,'tasks':Tasks}
# 
