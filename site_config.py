# todo: refactor stats.html & login.html
# todo: implement employee search functionality
# todo: add map to user modal

# app urls
token_url = r"http://staging.tangent.tngnt.co/api-token-auth/"
user_url = r"http://staging.tangent.tngnt.co/api/user/me/"
user_full_url = r"http://staging.tangent.tngnt.co/api/employee/me/"
employee_url = r"http://staging.tangent.tngnt.co/api/employee/"

# chart config
chart_colors = ['#29746F', '#F16767']

# dashboard data table
dashboard_users_fields = ['user.first_name', 'user.last_name', 'position.name',
                          'gender', 'birth_date', 'email', 'phone_number', 'years_worked']

#user model config
detailed_user_fields = ['user_first_name', 'user_last_name', 'position_name', 'position_level',
                        'years_worked', 'user_username', 'leave_remaining', 'id_number',
                        'phone_number', 'physical_address', 'tax_number', 'email', 'personal_email', 'github_user',
                        'birth_date', 'start_date', 'end_date', 'is_foreigner', 'gender', 'race', 'next_review']
detailed_user_nested_categories = ['employee_review', 'employee_next_of_kin']
detailed_user_review_key = 'employee_review'
detailed_user_next_of_kin_key = 'employee_next_of_kin'

