from firebase_admin import auth, firestore
from flask import session, request
import requests, json, argparse, os, threading
from werkzeug.exceptions import BadRequestKeyError


class User():

    def create_user(self, uemail, upassword, uname, db, msg=None):
        try:
            doc = db.collection(u'users').document(uname).get()
            if doc.exists:
                raise auth._auth_utils.EmailAlreadyExistsError(message="The username provided already exists", cause=None, http_response=None)
            else:
                auth.get_user_by_email(uemail)
                raise auth._auth_utils.EmailAlreadyExistsError(message="The email provided already exists", cause=None, http_response=None)

        except auth._auth_utils.UserNotFoundError:
            user = auth.create_user(
                email=uemail,
                email_verified=False,
                password=upassword,
                display_name=uname,
                ) 
            session['email'] = user.email
            session['uid'] = user.uid
            session['uname'] = user.display_name

        except auth._auth_utils.EmailAlreadyExistsError:
            msg = "The username/email you entered already exists in our database."

        except ValueError:
            msg = "Your password has to be atleast 6 characters."

        return msg 

    def logout_user(self):
        session.pop('email')
        session.pop('uid')
        session.pop('uname')

        for course in ['sw', 'py', 'ee']:
            try:
                session.pop(course)
            except:
                pass
        

    def login_user(self, email, password, return_secure_token: bool = True, msg=None):
        FIREBASE_WEB_API_KEY = "AIzaSyAopjFhQL0sG7DqIZpxSOf1NyE5pgK5Y7Y" # SET AS ON ENVIRON VARIABLE
        rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

        message = {
            'INVALID_EMAIL' : 'Your have not submitted an appropriate email',
            'INVALID_PASSWORD' : 'The password you have entered is not correct',
            'EMAIL_NOT_FOUND' : 'Your email does not exist in our database'
        }   

        payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": return_secure_token})

        r = requests.post(rest_api_url,
                        params={"key": FIREBASE_WEB_API_KEY},
                        data=payload)
        user = r.json()

        if 'error' in user:
            msg = message[user['error']['message']]

        else:
            session['email'] = user['email']
            session['uid'] = user['localId']
            session['uname'] = user['displayName']

        return msg
    
    def assignmentCompleted(self, hidden_vals, uname, course, db):
        for hidden_val in hidden_vals:
            try:
                db.collection(u'users').document(uname).collection(u'courses').document(course).update({hidden_val: int(request.form[hidden_val])})
            except BadRequestKeyError:
                pass

    def setupCourse(self, username, courseName, quizNames, db):
        totalpoints = len(quizNames) * 4
        course = {
            u'totalpoints': totalpoints
        }
        for quizName in quizNames:
            course[quizName] = 0

        ref = db.collection(u'users').document(username).collection(u'courses').document(courseName)
        ref.set(course)

    def getProgress(self, doc, quizNames):
        score = 0

        for quizName in quizNames:
            score += doc[quizName]
        
        return int(float(score) / float(doc['totalpoints']) * 100)
    
    def getCourseDoc(self, username, courseName, db):
        doc_ref = db.collection(u'users').document(username).collection(u'courses').document(courseName)
        return doc_ref.get().to_dict()
    
