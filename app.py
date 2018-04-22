# -*- coding: utf-8 -*-
# import the Flask class from the flask module
from flask import Flask, render_template, url_for, request, redirect, session
import site_config as cfg
import requests
from pandas.io.json import json_normalize
import pandas as pd
import json
from datetime import datetime

# create the application object
app = Flask(__name__)


# use decorators to link the function to a url
@app.route('/')
def home():
    error = None
    if 'token' in session.keys():
        employees = get_employee(session['token'])
        bar_labels, bar_datasets = build_position_chart_data(employees)
        gender_labels, gender_data = build_gender_chart_data(employees)
        basic_table_names, basic_table_values = build_datatable_source(employees)
        birthday_labels, birthday_values = birthday_coming_up(employees, 5)
        employee_count = len(employees)  # temporary - need to make more robust
        user_fields, review_columns, review_data, next_of_kin_fields = build_user_source(get_user_full(session['token']))
        return render_template('stats.html',
                               bar_labels=bar_labels,
                               bar_datasets=bar_datasets,
                               gender_labels=gender_labels,
                               gender_data=gender_data,
                               birthday_labels=birthday_labels,
                               birthday_values=birthday_values,
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
            session['token'] = response
            print(session.keys())
            return redirect(url_for('home'))
        else:
            error = response
    return render_template('login.html', error=error)


# Route for handling the logout page logic
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """Log a user out of the microsite

    Returns:
        html-page: Returns the login page
    """
    error = None
    session.clear()
    return redirect(url_for('login'))


def get_token(username, password, url=cfg.token_url):
    """Get the sign-in token

    Args:
        username (string): Provided username.
        password (string): Provided password.
        url (string)     : Login API

    Returns:
        bool: True if successful, otherwise false
        response (string): Returns the token or the returned error message
    """

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


def get_user(token, url=cfg.user_url):
    """Get user info

    Args:
        token (string)   : User auth token.
        url (string)     : User API.

    Returns:
        response (json)  : Return user info in json format
    """

    headers = {
        'authorization': "Token {}".format(token),
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers)

    return response.json()[0]


def get_user_full(token, url=cfg.user_full_url):
    """Get the full user profile

    Args:
        token (string): User auth token.
        url (string)     : User Full Profile API.

    Returns:
        response (json)  : Return full user info in json format
    """

    headers = {
        'authorization': "Token {}".format(token),
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers)

    return response.json()


def get_employee(token, url=cfg.employee_url, race=None, position=None, start_date=None, user=None, gender=None,
                 birth_date=None, email=None):
    """Get an employee's profile

    Args:
        token (string)     : User auth token.
        url (string)       : Employee Profile API.
        race (string)      : Race search param
        position (string)  : Position search param
        start_date (string): Start date search param
        user (string)      : User search param
        gender (string)    : Gender search param
        birth_date (string): Birth Date search param
        email (string)     : Email search param


    Returns:
        response (json)    : Return queried user info in json format
    """

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


# todo: the data coming from the server is incorrect, will have to change this to do a proper date calculation
def birthday_coming_up(employees, list_length):
    """Calculate upcoming birthdays

    Args:
        employees (dictionary) : General employee profile info.
        days (int)             : Search window of days into the future.

    Returns:
        birthdays (list): Return employee name, birthday and age
    """
    employee_df = json_normalize(employees)
    employee_df['birth_date'] = pd.to_datetime(employee_df['birth_date'])

    employee_df['birth_day'] = employee_df['birth_date'].apply(lambda dt: dt.replace(year=datetime.now().year))

    # update the year for birthdays that have passed
    employee_df.loc[(pd.to_datetime('today') - employee_df['birth_day']) > '0 days', 'birth_day'] = employee_df[
        (pd.to_datetime('today') - employee_df['birth_day']) > '0 days']['birth_day'].apply(
        lambda dt: dt.replace(year=datetime.now().year + 1))

    employee_df = employee_df.sort_values('birth_day')
    employee_df['days_to_birthday'] = (employee_df['birth_day'] - pd.to_datetime('today')).dt.days
    birthdays = employee_df[['user.first_name', 'user.last_name', 'days_to_birthday']].values.tolist()
    labels = [{'title': name.replace('user', '').replace('.', '').replace('_', ' ').capitalize()}
              for name in list(employee_df[['user.first_name', 'user.last_name', 'days_to_birthday']].columns)]
    return json.dumps(labels), json.dumps(birthdays[:list_length])


def build_position_chart_data(employees, colors=cfg.chart_colors):
    """Builds stacked bar chart for employee positions in the company

    Args:
        employees (dictionary) : General employee profile info.
        colors (list)          : Default colors for the style.

    Returns:
        labels (list)          : Return plot labels - job positions
        datasets (list)        : Return datasets - job level data
    """
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
    return json.dumps(labels), json.dumps(datasets)


def build_gender_chart_data(employees, colors=cfg.chart_colors):
    """Builds pie chart for employee gender in the company

    Args:
        employees (dictionary) : General employee profile info.
        colors (list)          : Default colors for the style.

    Returns:
        labels (list)          : Return plot labels - gender
        datasets (list)        : Return datasets - counts
    """
    employee_df = json_normalize(employees)
    counts = employee_df.groupby('gender')['gender'].count()
    labels = list(counts.keys())
    # this needs to look like
    # data: [list of numbers], background color: lost of colors, label: one label
    datasets = [{'label': list(counts.index), 'data': list(counts.astype(float)), 'backgroundColor': cfg.chart_colors}]
    return json.dumps(labels), json.dumps(datasets)


def build_datatable_source(employees, table_variables=cfg.dashboard_users_fields):
    """Builds source data for the dashboard data table

    Args:
        employees (dictionary) : General employee profile info.
        table_variables (list) : Fields we want in the output table.

    Returns:
        column_names (list)    : Field names
        column_values (list)   : Field values
    """
    column_names = []
    for column in table_variables:
        if "." in column:
            column = column.split('.')[1]
        column_names.append({'title': column.capitalize().replace('_', ' ')})
    employee_df = json_normalize(employees)
    column_values = employee_df[table_variables].values.tolist()
    return json.dumps(column_names), json.dumps(column_values)


# todo: leverage this in the search tool to help prep data
def build_user_source(user, user_display=cfg.detailed_user_fields, nested=cfg.detailed_user_nested_categories,
                      review_key=cfg.detailed_user_review_key, next_of_kin_key=cfg.detailed_user_next_of_kin_key):
    """Builds user modal data

    Args:
        user (dictionary)       : User dictionary.
        user_display (list)     : Fields we want in the USER output table.
        nested (list)           : List of nested categories we are interested in
        review_key (string)     : Dictionary key for review fields
        next_of_kin_key (string): Dictionary key for next of kin fields

    Returns:
        user_fields (list)       : User data
        review_columns (list)    : Review columns
        review_data (list)       : Review data
        next_of_kin_fields (list): Next of kin data
    """

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
    for column in list(user[review_key][0].keys()):
        review_columns.append({'title': column.capitalize().replace('_', ' ')})

    review_data = []
    for review in user[review_key]:
        review_data.append(list(review.values()))

    # generate next of kin data
    next_of_kin_fields = {}
    for key in user[next_of_kin_key][0].keys():
        next_of_kin_fields[key] = user[next_of_kin_key][0][key]
    next_of_kin_fields = list(next_of_kin_fields.items())
    next_of_kin_fields = [(column.capitalize().replace('_', ' '), value) for (column, value) in next_of_kin_fields]

    return json.dumps(user_fields), json.dumps(review_columns), json.dumps(review_data), json.dumps(next_of_kin_fields)


# start the server with the 'run()' method
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.run(debug=True)

