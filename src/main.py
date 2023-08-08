from flask import Flask
from utils import *
import config 
import time
from models import db


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = config.db_url
app.config["SQLALCHEMY_ECHO"] = config.log_sql
db.init_app(app)

@app.route('/')
def index_view():
    routes = [
        {'path': r.rule, 'methods': list(r.methods)} 
        for r in app.url_map.iter_rules()
    ]
    return ok(routes)


@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()
    if isinstance(e, BizException):
        return fail(e.args[0], e.args[1])
    return fail(msg=str(e))

if __name__ == '__main__':
    kill_proc_by_port(config.port)
    time.sleep(1)
    app.run(
        host=config.host, 
        port=config.port, 
        debug=config.debug,
        threaded=True,
    )