from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class UpgradeForm(FlaskForm):
    file_json = StringField("File_Json: ", validators=[DataRequired()])
    environment = StringField("Environment: ", validators=[DataRequired()])
    webhook_url = StringField("Webhook_URL: ", validators=[DataRequired()])
    kube_version_low = StringField("Kube_Version_Low: ", validators=[DataRequired()])
    kube_version_mid = StringField("Kube_Version_Mid: ", validators=[DataRequired()])
    kube_version_hi = StringField("Kube_Version_High: ", validators=[DataRequired()])
    kube_version_final = StringField("Kube_Version_Final: ", validators=[DataRequired()])
    submit = SubmitField("Submit")


class StopForm(FlaskForm):
    submit = SubmitField("Stop")