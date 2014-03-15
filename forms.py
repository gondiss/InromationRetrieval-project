from flask.ext.wtf import Form
from wtforms import TextField
from wtforms.validators import Required

class QueryForm(Form):
    queryid = TextField('queryid', validators = [Required()])
