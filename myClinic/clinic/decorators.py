from functools import wraps
from flask import request, redirect, url_for, abort
from flask_login import current_user
def nursesnotloggedin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.CASHIER:
            return redirect(url_for('login_my_user', next=request.url))

        return f(*args, **kwargs)

    return decorated_function
