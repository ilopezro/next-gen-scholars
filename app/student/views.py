import datetime
from flask import (abort, flash, redirect, render_template, url_for, request,
                   jsonify)
from flask_login import current_user, login_required
from ..models import TestScore, RecommendationLetter, Essay, College, Major, StudentProfile
from .. import db, csrf
from . import student
from .forms import (
    AddTestScoreForm, AddRecommendationLetterForm, AddSupplementalEssayForm,
    EditCollegeForm, EditSupplementalEssayForm, EditTestScoreForm,
    EditCommonAppEssayForm, AddChecklistItemForm, EditChecklistItemForm,
    EditStudentProfile, AddMajorForm, AddCollegeForm,
    EditRecommendationLetterForm, AddCommonAppEssayForm)
from ..models import (User, College, Essay, TestScore, ChecklistItem,
                      RecommendationLetter, TestName, Notification)
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRETS_FILE = 'client_secret.json'
import flask
import requests
import os 
import httplib2
import datetime
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


@student.route('/profile')
@login_required
def view_user_profile():
    sat = '––'
    act = '––'
    student_profile = current_user.student_profile
    if student_profile is not None:
        test_scores = student_profile.test_scores
        for t in test_scores:
            print (t.name)
            if t.name == 'SAT':
                sat = max(sat, t.score) if sat != '––' else t.score
            if t.name == 'ACT':
                act = max(act, t.score) if act != '––' else t.score
        return render_template(
            'student/student_profile.html',
            user=current_user,
            sat=sat,
            act=act)


@student.route('/calendar')
@login_required
def calendar():
    if current_user.student_profile.cal_token:
        return render_template('student/calendar.html', authenticated=True)
    else:
        return render_template('student/calendar.html', authenticated=False)


@student.route('/calendar_data', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def calendar_data():
    if not current_user.student_profile.cal_token:
        return jsonify(data=[])
    #Load credentials from the session.
    credentials_json = {
            'token': current_user.student_profile.cal_token,
            'refresh_token': current_user.student_profile.cal_refresh_token,
            'token_uri': current_user.student_profile.cal_token_uri,
            'client_id': current_user.student_profile.cal_client_id,
            'client_secret': current_user.student_profile.cal_client_secret,
            'scopes': current_user.student_profile.cal_scopes
    }
    credentials = google.oauth2.credentials.Credentials(**credentials_json)
    service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    event_data = []
    page_token = None
    while True:
      events = service.events().list(calendarId='primary', pageToken=page_token, timeMin=now).execute()
      for event in events['items']:
        event_data.append({'title':event['summary'], 'start':event['start']['dateTime'], 'end':event['end']['dateTime']})
      page_token = events.get('nextPageToken')
      if not page_token:
        break

    current_user.student_profile.cal_token = credentials.token
    current_user.student_profile.cal_refresh_token = credentials.refresh_token
    current_user.student_profile.cal_token_uri = credentials.token_uri
    current_user.student_profile.cal_client_id = credentials.client_id
    current_user.student_profile.cal_client_secret = credentials.client_secret
    current_user.student_profile.cal_scopes = credentials.scopes
    db.session.add(current_user)
    db.session.commit()
    return jsonify(data=event_data)


@student.route('/authorize_calendar')
@login_required
def authorize_calendar():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = url_for('student.oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        prompt='consent',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    #flask.session['state'] = state
    current_user.student_profile.cal_state = state
    db.session.add(current_user)
    db.session.commit()
    return flask.redirect(authorization_url)


@student.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = current_user.student_profile.cal_state

  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
  flow.redirect_uri = flask.url_for('student.oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in database
  credentials = flow.credentials
  current_user.student_profile.cal_token = credentials.token
  current_user.student_profile.cal_refresh_token = credentials.refresh_token
  current_user.student_profile.cal_token_uri = credentials.token_uri
  current_user.student_profile.cal_client_id = credentials.client_id
  current_user.student_profile.cal_client_secret = credentials.client_secret
  current_user.student_profile.cal_scopes = credentials.scopes
  current_user.student_profile.cal_state = state
  db.session.add(current_user)
  db.session.commit()

  return flask.redirect(flask.url_for('student.calendar'))



@student.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Allow user to update basic profile information.
    student_profile = current_user.student_profile
    if student_profile:
        form = EditStudentProfile(
            grade=student_profile.grade,
            high_school=student_profile.high_school,
            graduation_year=student_profile.graduation_year,
            district=student_profile.district,
            city=student_profile.city,
            state=student_profile.state,
            fafsa_status=student_profile.fafsa_status,
            gpa=student_profile.gpa,
            early_deadline=bool_to_string(student_profile.early_deadline))
        if form.validate_on_submit():
            # Update user profile information.
            student_profile.grade = form.grade.data
            student_profile.high_school = form.high_school.data
            student_profile.graduation_year = form.graduation_year.data
            student_profile.district = form.district.data
            student_profile.city = form.city.data
            student_profile.state = form.state.data
            student_profile.fafsa_status = form.fafsa_status.data
            student_profile.gpa = form.gpa.data
            student_profile.early_deadline = string_to_bool(
                form.early_deadline.data)
            db.session.add(student_profile)
            db.session.commit()
            return redirect(url_for('student.view_user_profile'))
        return render_template('student/update_profile.html', form=form)
    flash('Profile could not be updated.', 'error')
    return redirect(url_for('student.view_user_profile'))


# test score methods


@student.route('/profile/add_test_score', methods=['GET', 'POST'])
@login_required
def add_test_score():
    form = AddTestScoreForm()
    if form.validate_on_submit():
        # create new test score from form data
        new_item = TestScore(
            student_profile_id=current_user.student_profile_id,
            name=form.test_name.data.name,
            month=form.month.data,
            year=form.year.data,
            score=form.score.data)
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('student.view_user_profile'))
    return render_template(
        'student/add_academic_info.html', form=form, header="Add Test Score")


@student.route(
    '/profile/test_score/delete/<int:item_id>', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def delete_test_score(item_id):
    test_score = TestScore.query.filter_by(id=item_id).first()
    if test_score:
        db.session.delete(test_score)
        db.session.commit()
        return jsonify({"success": "True"})
    return jsonify({"success": "False"})


@student.route(
    '/profile/test_score/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_test_score(item_id):
    test_score = TestScore.query.filter_by(id=item_id).first()
    if test_score:
        form = EditTestScoreForm(
            test_name=TestName.query.filter_by(name=test_score.name).first(),
            month=test_score.month,
            year=test_score.year,
            score=test_score.score)
        if form.validate_on_submit():
            test_score.name = form.test_name.data.name
            test_score.month = form.month.data
            test_score.year = form.year.data
            test_score.score = form.score.data
            db.session.add(test_score)
            db.session.commit()
            return redirect(url_for('student.view_user_profile'))
        return render_template(
            'student/edit_academic_info.html',
            form=form,
            header="Edit Test Score")
    flash('Item could not be updated', 'error')
    return redirect(url_for('student.view_user_profile'))


# recommendation letter methods


@student.route('/profile/add_recommendation_letter', methods=['GET', 'POST'])
@login_required
def add_recommendation_letter():
    form = AddRecommendationLetterForm()
    if form.validate_on_submit():
        new_item = RecommendationLetter(
            student_profile_id=current_user.student_profile_id,
            name=form.name.data,
            category=form.category.data,
            status=form.status.data)
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('student.view_user_profile'))

    return render_template(
        'student/add_academic_info.html',
        form=form,
        header="Add Recommendation Letter")


@student.route(
    '/profile/recommendation_letter/edit/<int:item_id>',
    methods=['GET', 'POST'])
@login_required
def edit_recommendation_letter(item_id):
    letter = RecommendationLetter.query.filter_by(id=item_id).first()
    if letter:
        form = EditRecommendationLetterForm(
            name=letter.name, category=letter.category, status=letter.status)
        if form.validate_on_submit():
            letter.name = form.name.data
            letter.category = form.category.data
            letter.status = form.status.data
            db.session.add(letter)
            db.session.commit()
            return redirect(url_for('student.view_user_profile'))
        return render_template(
            'student/edit_academic_info.html',
            form=form,
            header="Edit Recommendation Letter")
    flash('Item could not be updated', 'error')
    return redirect(url_for('student.view_user_profile'))


@student.route(
    '/profile/recommendation_letter/delete/<int:item_id>',
    methods=['GET', 'POST'])
@login_required
@csrf.exempt
def delete_recommendation_letter(item_id):
    letter = RecommendationLetter.query.filter_by(id=item_id).first()
    if letter:
        db.session.delete(letter)
        db.session.commit()
        db.session.commit()
        return jsonify({"success": "True"})
    return jsonify({"success": "False"})


# college methods


@student.route('/profile/add_college', methods=['GET', 'POST'])
@login_required
def add_college():
    # Add a college student is interested in.
    form = AddCollegeForm()
    student_profile = current_user.student_profile
    if form.validate_on_submit():
        if form.name.data not in student_profile.colleges:
            # Only check to add college if not already in their list.
            college_name = College.query.filter_by(name=form.name.data).first()
            if college_name is not None:
                # College already exists in database.
                student_profile.colleges.append(college_name)
            else:
                student_profile.colleges.append(College(name=form.name.data))
            db.session.add(student_profile)
            db.session.commit()
            return redirect(url_for('student.view_user_profile'))

    return render_template(
        'student/add_academic_info.html', form=form, header="Add College")

@student.route('/colleges')
@login_required
def colleges():
    """View all colleges."""
    colleges = College.query.all()
    return render_template(
        'student/colleges.html', colleges=colleges)

@student.route('/profile/college/delete/<int:item_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_college(item_id):
    college = College.query.filter_by(id=item_id).first()
    if college:
        db.session.delete(college)
        db.session.commit()
        return jsonify({"success": "True"})
    return jsonify({"success": "False"})


@student.route('/profile/college/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_college(item_id):
    college = College.query.filter_by(id=item_id).first()
    if college:
        form = EditCollegeForm(college_name=college.name)
        if form.validate_on_submit():
            college.name = form.college_name.data
            db.session.add(college)
            db.session.commit()
            return redirect(url_for('student.view_user_profile'))
        return render_template(
            'student/edit_academic_info.html',
            form=form,
            header="Edit College")
    flash('Item could not be updated', 'error')
    return redirect(url_for('student.view_user_profile'))


# common app essay methods


@student.route('/profile/add_common_app_essay', methods=['GET', 'POST'])
@login_required
def add_common_app_essay():
    form = AddCommonAppEssayForm()
    if form.validate_on_submit():
        current_user.student_profile.common_app_essay = form.link.data
        current_user.student_profile.common_app_essay_status = form.status.data
        db.session.add(current_user)
        db.session.commit()
        return redirect(url_for('student.view_user_profile'))

    return render_template(
        'student/add_academic_info.html',
        form=form,
        header="Add Supplemental Essay")


@student.route('/profile/common_app_essay/edit', methods=['GET', 'POST'])
@login_required
def edit_common_app_essay():
    form = EditCommonAppEssayForm(
        link=current_user.student_profile.common_app_essay)
    if form.validate_on_submit():
        current_user.student_profile.common_app_essay = form.link.data
        current_user.student_profile.common_app_essay_status = form.status.data
        db.session.add(current_user)
        db.session.commit()
        return redirect(url_for('student.view_user_profile'))
    return render_template(
        'student/edit_academic_info.html',
        form=form,
        header="Edit Common App Essay")


@student.route('/profile/common_app_essay/delete', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def delete_common_app_essay():
    current_user.student_profile.common_app_essay = ''
    db.session.add(current_user)
    db.session.commit()
    return redirect(url_for('student.view_user_profile'))


# supplemental essay methods


@student.route('/profile/add_supplemental_essay', methods=['GET', 'POST'])
@login_required
def add_supplemental_essay():
    form = AddSupplementalEssayForm()
    if form.validate_on_submit():
        # create new essay from form data
        new_item = Essay(
            student_profile_id=current_user.student_profile_id,
            name=form.name.data,
            link=form.link.data,
            status=form.status.data)
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('student.view_user_profile'))

    return render_template(
        'student/add_academic_info.html',
        form=form,
        header="Add Supplemental Essay")


@student.route(
    '/profile/supplemental_essay/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_supplemental_essay(item_id):
    essay = Essay.query.filter_by(id=item_id).first()
    if essay:
        form = EditSupplementalEssayForm(
            essay_name=essay.name, link=essay.link)
        if form.validate_on_submit():
            essay.name = form.essay_name.data
            essay.link = form.link.data
            essay.status = form.status.data
            db.session.add(essay)
            db.session.commit()
            return redirect(url_for('student.view_user_profile'))
        return render_template(
            'student/edit_academic_info.html',
            form=form,
            header="Edit Supplemental Essay")
    flash('Item could not be updated', 'error')
    return redirect(url_for('student.view_user_profile'))


@student.route(
    '/profile/supplemental_essay/delete/<int:item_id>',
    methods=['GET', 'POST'])
@login_required
@csrf.exempt
def delete_supplemental_essay(item_id):
    essay = Essay.query.filter_by(id=item_id).first()
    if essay:
        db.session.delete(essay)
        db.session.commit()
        return jsonify({"success": "True"})
    return jsonify({"success": "False"})


# major methods


@student.route('/profile/add_major', methods=['GET', 'POST'])
@login_required
def add_major():
    # Add a major student is interested in.
    form = AddMajorForm()
    student_profile = current_user.student_profile
    if form.validate_on_submit():
        if form.major.data not in student_profile.majors:
            # Only check to add major if not already in their list.
            major_name = Major.query.filter_by(name=form.major.data).first()
            if major_name is not None:
                # Major already exists in database.
                student_profile.majors.append(major_name)
            else:
                student_profile.majors.append(Major(name=form.major.data))
            db.session.add(student_profile)
            db.session.commit()
            return redirect(url_for('student.view_user_profile'))

    return render_template(
        'student/add_academic_info.html', form=form, header="Add Major")


@student.route('/profile/major/delete/<int:item_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_major(item_id):
    major = Major.query.filter_by(id=item_id).first()
    if major:
        db.session.delete(major)
        db.session.commit()
        return jsonify({"success": "True"})
    return jsonify({"success": "False"})


# checklist methods


@student.route('/checklist')
@login_required
def checklist_default():
    # get the logged-in user's profile id
    if current_user.student_profile_id:
        return redirect(url_for('student.checklist',
                    student_profile_id=current_user.student_profile_id))
    else:
        return redirect(url_for('main.index'))

@student.route('/checklist/<int:student_profile_id>', methods=['GET', 'POST'])
@login_required
def checklist(student_profile_id):
    # only allows the student or counselors/admins to see a student's profile
    if student_profile_id == current_user.student_profile_id or current_user.role_id != 1:
        checklist_items = ChecklistItem.query.filter_by(
            assignee_id=student_profile_id)
        completed_items = [item for item in checklist_items if item.is_checked]
        checklist_items = [
            item for item in checklist_items if not item.is_checked
        ]
        #### form to add checklist item ###
        form = AddChecklistItemForm()
        if form.validate_on_submit():
            event_id = add_to_cal(student_profile_id, form.item_text.data, form.date.data)
            # add new checklist item to user's account
            checklist_item = ChecklistItem(
                assignee_id=student_profile_id,
                text=form.item_text.data,
                is_deletable=True,
                deadline=form.date.data,
                cal_event_id=event_id)
            ### if counselor is adding checklist item, send a notification
            if current_user.role_id != 1:
                notif_text = '{} {} added "{}" to your checklist'.format(
                    current_user.first_name, current_user.last_name, checklist_item.text)
                notification = Notification(text=notif_text, student_profile_id=student_profile_id)
                db.session.add(notification)
            db.session.add(checklist_item)
            db.session.commit()
            return redirect(
                url_for(
                    'student.checklist',
                    student_profile_id=student_profile_id))
        ### pull student notifications ###
        current_notifs = []
        if current_user.role_id == 1:
            now = datetime.datetime.utcnow()
            all_notifs = Notification.get_user_notifications(
                student_profile_id=current_user.student_profile_id)
            for n in all_notifs:
                time_diff = now - n.created_at
                if time_diff.days > 14 and n.seen:
                    db.session.delete(n)
                else:
                    ago_str = ''
                    if time_diff.days > 0:
                        ago_str = '{} days ago'.format(time_diff.days)
                    elif time_diff.seconds >= 3600:
                        hours = time_diff.seconds // 3600
                        ago_str = '1 hour ago' if hours == 1 else '{} hours ago'.format(
                            hours)
                    elif time_diff.seconds >= 60:
                        mins = time_diff.seconds // 60
                        ago_str = '1 minute ago' if mins == 1 else '{} minutes ago'.format(
                            mins)
                    else:
                        ago_str = '1 second ago' if time_diff.seconds == 1 else '{} seconds ago'.format(
                            time_diff.seconds)
                    current_notifs += [(n, ago_str)]
                    n.seen = True
            db.session.commit()
        if len(current_notifs) == 0:
            current_notifs = None
        ### return student dashboard checklist ###
        return render_template(
            'student/checklist.html',
            form=form,
            checklist=checklist_items,
            notifications=current_notifs,
            completed=completed_items,
            student_profile_id=student_profile_id)
    flash('You do not have access to this page', 'error')
    return redirect(url_for('main.index'))


def add_to_cal(student_profile_id, text, deadline):
    if deadline is None:
        return ''
    token= current_user.student_profile.cal_token
    refresh_token= current_user.student_profile.cal_refresh_token
    token_uri= current_user.student_profile.cal_token_uri
    client_id= current_user.student_profile.cal_client_id
    client_secret= current_user.student_profile.cal_client_secret
    scopes= current_user.student_profile.cal_scopes
    credentials_json = {
            'token': token,
            'refresh_token': refresh_token,
            'token_uri': token_uri,
            'client_id': client_id,
            'client_secret': client_secret,
            'scopes': scopes
    }

    credentials = google.oauth2.credentials.Credentials(**credentials_json)
    service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
    student_profile = StudentProfile.query.filter_by(id=student_profile_id).first()
    y = deadline.year
    m = deadline.month
    d = deadline.day
    event_body = {
        'summary': text,
        'start': {
            'dateTime': datetime.datetime(y, m, d).isoformat('T'),
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': datetime.datetime(y, m, d).isoformat('T'),
            'timeZone': 'America/Los_Angeles',
        },
    }

    event = service.events().insert(calendarId='primary', body=event_body).execute()
    current_user.student_profile.cal_token = credentials.token
    current_user.student_profile.cal_refresh_token = credentials.refresh_token
    current_user.student_profile.cal_token_uri = credentials.token_uri
    current_user.student_profile.cal_client_id = credentials.client_id
    current_user.student_profile.cal_client_secret = credentials.client_secret
    current_user.student_profile.cal_scopes = credentials.scopes
    db.session.add(current_user)
    db.session.commit()
    return event.get('id')


@student.route('/checklist/delete/<int:item_id>', methods=['GET', 'POST'])
@login_required
def delete_checklist_item(item_id):
    checklist_item = ChecklistItem.query.filter_by(id=item_id).first()
    if checklist_item:
        if checklist_item.deadline is not None:
            delete_event(checklist_item.cal_event_id)
        db.session.delete(checklist_item)
        db.session.commit()
        return redirect(
            url_for(
                'student.checklist',
                student_profile_id=checklist_item.assignee_id))
    flash('Item could not be deleted', 'error')
    return redirect(url_for('main.index'))


def delete_event(event_id):
    token= current_user.student_profile.cal_token
    refresh_token= current_user.student_profile.cal_refresh_token
    token_uri= current_user.student_profile.cal_token_uri
    client_id= current_user.student_profile.cal_client_id
    client_secret= current_user.student_profile.cal_client_secret
    scopes= current_user.student_profile.cal_scopes
    credentials_json = {
            'token': token,
            'refresh_token': refresh_token,
            'token_uri': token_uri,
            'client_id': client_id,
            'client_secret': client_secret,
            'scopes': scopes
    }

    credentials = google.oauth2.credentials.Credentials(**credentials_json)
    service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
    service.events().delete(calendarId='primary', eventId=event_id).execute()

    current_user.student_profile.cal_token = credentials.token
    current_user.student_profile.cal_refresh_token = credentials.refresh_token
    current_user.student_profile.cal_token_uri = credentials.token_uri
    current_user.student_profile.cal_client_id = credentials.client_id
    current_user.student_profile.cal_client_secret = credentials.client_secret
    current_user.student_profile.cal_scopes = credentials.scopes
    db.session.add(current_user)
    db.session.commit()


def update_event(event_id, new_text, new_deadline):
    token= current_user.student_profile.cal_token
    refresh_token= current_user.student_profile.cal_refresh_token
    token_uri= current_user.student_profile.cal_token_uri
    client_id= current_user.student_profile.cal_client_id
    client_secret= current_user.student_profile.cal_client_secret
    scopes= current_user.student_profile.cal_scopes
    credentials_json = {
            'token': token,
            'refresh_token': refresh_token,
            'token_uri': token_uri,
            'client_id': client_id,
            'client_secret': client_secret,
            'scopes': scopes
    }

    credentials = google.oauth2.credentials.Credentials(**credentials_json)
    service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    event['summary'] = new_text
    y = new_deadline.year
    m = new_deadline.month
    d = new_deadline.day
    event['start'] = {
        'dateTime': datetime.datetime(y, m, d).isoformat('T'),
        'timeZone': 'America/Los_Angeles',
    }
    event['end'] = {
        'dateTime': datetime.datetime(y, m, d).isoformat('T'),
        'timeZone': 'America/Los_Angeles',
    }
    updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()

    current_user.student_profile.cal_token = credentials.token
    current_user.student_profile.cal_refresh_token = credentials.refresh_token
    current_user.student_profile.cal_token_uri = credentials.token_uri
    current_user.student_profile.cal_client_id = credentials.client_id
    current_user.student_profile.cal_client_secret = credentials.client_secret
    current_user.student_profile.cal_scopes = credentials.scopes
    db.session.add(current_user)
    db.session.commit()


@student.route('/checklist/complete/<int:item_id>', methods=['GET', 'POST'])
@login_required
def complete_checklist_item(item_id):
    checklist_item = ChecklistItem.query.filter_by(id=item_id).first()
    if checklist_item:
        checklist_item.is_checked = True
        db.session.add(checklist_item)
        db.session.commit()
        return redirect(
            url_for(
                'student.checklist',
                student_profile_id=checklist_item.assignee_id))
    flash('Item could not be completed', 'error')
    return redirect(url_for('main.index'))


@student.route('/checklist/undo/<int:item_id>', methods=['GET', 'POST'])
@login_required
def undo_checklist_item(item_id):
    checklist_item = ChecklistItem.query.filter_by(id=item_id).first()
    if checklist_item:
        checklist_item.is_checked = False
        db.session.add(checklist_item)
        db.session.commit()
        return redirect(
            url_for(
                'student.checklist',
                student_profile_id=checklist_item.assignee_id))
    flash('Item could not be undone', 'error')
    return redirect(url_for('main.index'))


@student.route('/checklist/update/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_checklist_item(item_id):
    item = ChecklistItem.query.filter_by(id=item_id).first()
    if item:
        form = EditChecklistItemForm(item_text=item.text, date=item.deadline)
        if form.validate_on_submit():
            if form.item_text.data is not None:
                update_event(item.cal_event_id, form.item_text.data, form.date.data)
            item.text = form.item_text.data
            item.deadline = form.date.data
            db.session.add(item)
            db.session.commit()
            return redirect(
                url_for(
                    'student.checklist', student_profile_id=item.assignee_id))
        return render_template(
            'student/update_checklist.html',
            form=form,
            student_profile_id=item.assignee_id)
    flash('Item could not be updated', 'error')
    return redirect(url_for('main.index'))


@student.route('/college_profile/<int:college_id>')
@login_required
def view_college_profile(college_id):
    current_college = College.query.filter_by(id=college_id).first()
    return render_template('main/college_profile.html', college=current_college)


def string_to_bool(str):
    if str == 'True':
        return True
    if str == 'False':
        return False


def bool_to_string(bool):
    if bool:
        return 'True'
    else:
        return 'False'
