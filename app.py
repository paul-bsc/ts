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
    error = None
    session.clear()
    return redirect(url_for('login'))


def get_token(username, password):
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


# start the server with the 'run()' method
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.run(debug=True)

