from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired(message="Search query cannot be empty")])
    submit = SubmitField("Submit")