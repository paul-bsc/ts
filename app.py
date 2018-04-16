# import the Flask class from the flask module
from flask import Flask, render_template, url_for, request, redirect, session
import requests

# create the application object
app = Flask(__name__)


# use decorators to link the function to a url
@app.route('/')
def home():
    error = None
    if 'token' in session.keys():
        return "Place holder"  # return a string
    else:
        return redirect(url_for('login'))


@app.route('/welcome')
def welcome():
    return render_template('welcome.html')  # render a template


# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log a user in to the microsite

    Returns:
        html-page: Returns the login page
    """
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        (valid, response) = get_token(username, password)
        if valid is True:
            session['username'] = username
            session['password'] = password
            session['token'] = response
            return redirect(url_for('home'))
        else:
            error = response
    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """Log a user out of the microsite

    Returns:
        html-page: Returns the login page
    """
    error = None
    session.clear()
    return redirect(url_for('login'))


def get_token(username, password):
    """Get the sign-in token

    Args:
        username (string): Provided username.
        password (string): Provided password.

    Returns:
        bool: True if successful, otherwise false
        response (string): Returns the token or the returned error message
    """

    url = "http://staging.tangent.tngnt.co/api-token-auth/"

    payload = "------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; " \
              "name=\"username\"\r\n\r\n{}\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent" \
              "-Disposition: form-data; " \
              "name=\"password\"\r\n\r\n{}\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW-- ".format(username, password)
    headers = {
        'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        'cache-control': "no-cache"
    }

    response = requests.request("POST", url, data=payload, headers=headers).json()
    # print(response)

    if 'token' in response.keys():
        return True, response['token']
    elif 'non_field_errors' in response.keys():
        return False, response['non_field_errors']
    else:
        return False, None


def get_user(token):
    url = "http://staging.tangent.tngnt.co/api/user/me/"

    headers = {
        'authorization': "Token {}".format(token),
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers)

    return response.json()[0]


def get_user_full(token):
    url = "http://staging.tangent.tngnt.co/api/employee/me/"

    headers = {
        'authorization': "Token {}".format(token),
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers)

    return response.json()[0]


def get_employee(token, race=None, position=None, start_date=None, user=None, gender=None, birth_date=None, email=None):
    url = "http://staging.tangent.tngnt.co/api/employee/"

    headers = {
        'authorization': "Token {}".format(token),
        'race': race,
        'position': position,
        'start_date': start_date,
        'user': user,
        'gender': gender,
        'birth_date': birth_date,
        'email': email,
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers)

    return response.json()


def birthday_coming_up(employees, days):
    birthdays_coming_up = []
    for employee in employees:
        if employee['days_to_birthday'] - days <= 0:
            birthdays_coming_up.append(employee['user']['id'])


# start the server with the 'run()' method
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.run(debug=True)

