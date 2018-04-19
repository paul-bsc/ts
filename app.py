# -*- coding: utf-8 -*-
# import the Flask class from the flask module
from flask import Flask, render_template, url_for, request, redirect, session, jsonify
import requests
from pandas.io.json import json_normalize
import pandas as pd
import json

# create the application object
app = Flask(__name__)


# use decorators to link the function to a url
@app.route('/')
def home():
    error = None
    if 'token' in session.keys():
        employees = get_employee(session['token'])
        labels, bar_datasets = build_position_chart_data(employees)
        basic_table_names, basic_table_values = build_datatable_source(employees)
        birthdays = birthday_coming_up(employees, 30)
        employee_count = len(employees)  # temporary - need to make more robust
        user_fields, review_columns, review_data, next_of_kin_fields = build_user_source(get_user_full(session['token']))
        return render_template('stats.html',
                               labels=labels,
                               bar_datasets=bar_datasets,
                               birthdays=birthdays,
                               employee_count=employee_count,
                               basic_table_names=basic_table_names,
                               basic_table_values=basic_table_values,
                               user_fields=user_fields,
                               review_columns=review_columns,
                               review_data=review_data,
                               next_of_kin_fields=next_of_kin_fields)
    else:
        return redirect(url_for('login'))


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
            print(session.keys())
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

    try:
        response = requests.request("POST", url, data=payload, headers=headers).json()
        print(response)
        if 'token' in response.keys():
            return True, response['token']
        elif 'non_field_errors' in response.keys():
            return False, response['non_field_errors'][0]
        else:
            return False, None
    except requests.exceptions.Timeout:
        return False, "Request Timeout. Please try again."
    except requests.exceptions.TooManyRedirects:
        return False, "Too Many Redirects. Please try again."
    except requests.exceptions.RequestException as e:
        return False, "Error. Please try again."


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

    return response.json()


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


# the data coming from the server is incorrect, will have to change this to do a proper date calcuation
def birthday_coming_up(employees, days):
    birthdays = []
    for employee in employees:
        if employee['days_to_birthday'] < 30:
            birthdays.append([
                "{} {}".format(employee['user']['first_name'], employee['user']['last_name']),
                employee['birth_date'],
                employee['age']])
    return birthdays


@app.route("/stats")
def chart():
    employees = get_employee(session['token'])
    labels, data = build_position_chart_data(employees)
    labels = list(data.keys())
    values = list(data)
    birthdays = birthday_coming_up(employees, 30)
    employee_count = len(employees) # temporary - need to make more robust



    return render_template('stats.html', values=values, labels=labels, birthdays=birthdays, employee_count=employee_count)


def build_position_chart_data(employees):
    colors = ['#29746F', '#F16767']
    level_subsets = {}
    employee_df = json_normalize(employees)
    labels = list(employee_df['position.name'].unique())
    levels = employee_df['position.level'].unique()
    for level in levels:
        level_subsets[level] = dict(employee_df[employee_df['position.level'] == level].groupby(['position.name'])['position.name'].count())
    normalised = pd.DataFrame.from_dict(level_subsets).fillna(0)
    datasets = []
    for level in levels:
        datasets.append({'label': level,
                         'data': list(normalised[level]),
                         'stack': 'Stack 0',
                         'backgroundColor': colors[list(levels).index(level)]
                         })
    # temp response - need to come clean this up and make it more robust
    # return str(datasets).replace("'data'", 'data').replace("'label'", 'label')
    return json.dumps(labels), json.dumps(datasets)


def build_datatable_source(employees):
    table_variables = ['user.first_name', 'user.last_name', 'position.name',
                       'gender', 'birth_date', 'email', 'phone_number', 'years_worked']
    column_names = []
    column_values = []
    for column in table_variables:
        if "." in column:
            column = column.split('.')[1]
        column_names.append({'title': column.capitalize().replace('_', ' ')})
    employee_df = json_normalize(employees)
    column_values = employee_df[table_variables].values.tolist()
    return json.dumps(column_names), json.dumps(column_values)


def build_user_source(user):
    # todo: these types of variables need to all go into a central config file
    user_display = ['user_first_name', 'user_last_name', 'position_name', 'position_level',
                    'years_worked', 'user_username', 'leave_remaining', 'id_number',
                    'phone_number', 'physical_address', 'tax_number', 'email', 'personal_email', 'github_user',
                    'birth_date', 'start_date', 'end_date', 'is_foreigner', 'gender', 'race', 'next_review']
    nested = ['employee_review', 'employee_next_of_kin']
    user_fields = {}

    # generate user data
    for key in user.keys():
        if key not in nested:
            if isinstance(user[key], dict):
                for nested_key in user[key].keys():
                    user_fields['{}_{}'.format(key, nested_key)] = user[key][nested_key]
            else:
                user_fields[key] = user[key]
    user_fields = {k: user_fields[k] for k in user_display}
    user_fields = sorted(user_fields.items(), key=lambda pair: user_display.index(pair[0]))
    user_fields = [(column.capitalize().replace('_', ' '), value) for (column, value) in user_fields]

    # generate review data
    # todo: text replacement for codified fields
    review_columns = []
    for column in list(user['employee_review'][0].keys()):
        review_columns.append({'title': column.capitalize().replace('_', ' ')})

    review_data = []
    for review in user['employee_review']:
        review_data.append(list(review.values()))

    # generate next of kin data
    next_of_kin_fields = {}
    for key in user['employee_next_of_kin'][0].keys():
        next_of_kin_fields[key] = user['employee_next_of_kin'][0][key]
    next_of_kin_fields = list(next_of_kin_fields.items())
    next_of_kin_fields = [(column.capitalize().replace('_', ' '), value) for (column, value) in next_of_kin_fields]

    return json.dumps(user_fields), json.dumps(review_columns), json.dumps(review_data), json.dumps(next_of_kin_fields)


# start the server with the 'run()' method
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.run(debug=True)

