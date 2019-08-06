from .. import db
import re

class EditableHTML(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    editor_name = db.Column(db.String(100), unique=True)
    value = db.Column(db.Text)

    @staticmethod
    def get_editable_html(editor_name):
        editable_html_obj = EditableHTML.query.filter_by(
            editor_name=editor_name).first()

        if editable_html_obj is None:
            editable_html_obj = EditableHTML(editor_name=editor_name, value='')
        return editable_html_obj


# will fix URL in user forms so that they are clickable if http/https not included
# you can always add http because it will get bumped up to https if available, 
# but you can't bump down from https to http
def fix_url(url):
    match = re.search('^https?:\/\/', url)
    if not match:
        url = 'http://' + url
    return url

