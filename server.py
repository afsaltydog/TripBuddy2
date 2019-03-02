from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re, socket, datetime, time
app = Flask(__name__)
app.secret_key='ASFwasHEreIhsdjfqwbfiuw98scjk9@$@'
bcrypt = Bcrypt(app)

# our index route will handle rendering our form
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/process', methods=['POST'])
def process():
    print("Got Post Info")
    print(str(request.form))
    
    is_valid = True

    if len(request.form['fname']) < 1:
        flash("This field is required", 'fname')
        is_valid = False
    elif len(request.form['fname']) < 2:
        flash("Please enter a first name", 'fname')
        is_valid = False
    elif not re.match("^[a-zA-Z]+(?:_[a-zA-Z]+)?$", request.form['fname']):
        flash("The first name must be letters only", 'fname')
        is_valid = False

    if len(request.form['lname']) < 1:
        flash("This field is required", 'lname')
        is_valid = False
    elif len(request.form['lname']) < 2:
        flash("The last name needs to be at least two characters", 'lname')
        is_valid = False
    elif not re.match("^[a-zA-Z]+(?:_[a-zA-Z]+)?$", request.form['lname']):
        flash("The last name must be letters only", 'lname')
        is_valid = False
    
    if len(request.form['email']) < 1:
        flash("This field is required", 'email')
        is_valid = False
    elif len(request.form['email']) < 2:
        flash("The email address should be at least two characters", 'email')
        is_valid = False
    
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
    if not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        print('email is not valid')
        flash("The email address is not valid", 'email')
        is_valid = False
    else:
        mysql = connectToMySQL('TripBuddy2')
        query = "SELECT email FROM Users;"
        emails = mysql.query_db(query)
        print('emails is '+str(emails))
        for e in emails:
            print('e is '+str(e))
            if e['email'] == str(request.form['email']):
                flash("The email address is already being used", 'email')
                is_valid = False
        
    if len(request.form['password']) < 1:
        flash("This field is required", 'pwd')
        is_valid = False
    if len(request.form['confirm']) < 1:
        flash("This field is required", 'confirm')
        is_valid = False
    elif request.form['password'] != request.form['confirm']:
        flash("The passwords do not match", 'pwd')
        is_valid = False
    
    PWD_REGEX = re.compile(r'(?=\D*\d)(?=[^A-Z]*[A-Z])(?=[^a-z]*[a-z])[A-Za-z0-9]{10,}$')
    if not PWD_REGEX.match(request.form['password']):    # test whether a field matches the pattern
        print('The password must contain at least 1 digit, 1 uppercase letter, and 1 lowercase letter, and be greater than 10 characters')
        flash("The password must contain at least 1 digit, 1 uppercase letter, and 1 lowercase letter, and be greater than 10 characters", 'pwd')
        is_valid = False
        
    if is_valid:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        mysql = connectToMySQL('TripBuddy2')
        query = "INSERT INTO Users (first_name, last_name, email, password) VALUES (%(fname)s, %(lname)s, %(email)s, %(pwd)s);"
        data = {"fname": request.form['fname'],
                "lname": request.form['lname'],
                "email": request.form['email'],
                "pwd": pw_hash
        }
        print('query is '+str(query))
        new_id = mysql.query_db(query, data)
        flash("You have been successfully registered! New ID is "+str(new_id), 'regis')
        session['id'] = new_id
        return redirect('/display')
    else:
        print("Something on the form was not valid, so we redirect to '/'")

    return redirect('/')

@app.route('/login', methods=['post'])
def login():
    # do stuff for login

    mysql = connectToMySQL('TripBuddy2')
    query = "SELECT * FROM users WHERE email = '"+str(request.form['email'])+"';"
    print('SELECT query is '+query)
    res = mysql.query_db(query)
    print('result is '+str(res))

    if not res:
        flash("You could not be logged in", 'logout')
        return redirect('/')

    # check password hash
    print("request.form[password] is "+str(request.form['password']))
    print("res[password] is "+str(res[0]['password']))

    if bcrypt.check_password_hash(res[0]['password'], request.form['password']):
        print("we passed the password validation")
        print("res[0][email] is "+str(res[0]['email']))
        print("request.form[email] is "+str(request.form['email']))
        if res[0]['email'] != request.form['email']:
            flash("You could not be logged in", 'logout')
            return redirect('/')

    first_name = res[0]['first_name']
    print("login first_name "+first_name)

    mysql = connectToMySQL('TripBuddy2')
    query = "SELECT id FROM users WHERE first_name = '"+first_name+"';"
    res = mysql.query_db(query)
    print("login res is "+str(res))

    print("**********res[0]['id'] is "+str(res[0]['id'])+"******************")
    session['id'] = res[0]['id']

    return redirect('/display')

@app.route('/success', methods=['get', 'post'])
def success():
    if 'id' in session:
        id = session['id']
    else:
        flash("You must log in to enter this website", 'logout')
        return redirect('/')

    mysql = connectToMySQL('TripBuddy2')
    query = "SELECT * FROM Users WHERE id = "+str(id)+";"
    print('SELECT query is '+query)
    res = mysql.query_db(query)
    print('result is '+str(res))
    first_name = res[0]['first_name']

    mysql = connectToMySQL('TripBuddy2')
    query = "SELECT * FROM Users;"
    res = mysql.query_db(query)

    flash("You've been successfully registered", 'success')

    return render_template('result.html', fname=first_name, dbInfo=res)

@app.route('/newtrip', methods=['get', 'post'])
def new_trip():
    if 'id' in session:
        id = session['id']
    else:
        flash("You must log in to enter this website", 'logout')
        return redirect('/')

    print("Entering /new_trip...**************")

    mysql = connectToMySQL('TripBuddy2')
    query = "SELECT * FROM Users WHERE id = "+str(id)+";"
    print('SELECT query is '+query)
    res = mysql.query_db(query)
    print('result is '+str(res))
    first_name = res[0]['first_name']

    return render_template('new.html', fname=first_name)

@app.route('/set_trip', methods=['get', 'post'])
def set_trip():
    if 'id' in session:
        id = session['id']
    else:
        flash("You must log in to enter this website", 'logout')
        return redirect('/')

    print("Entering /set_trip...**************")

    isProblem = False
    if len(str(request.form['trip_name'])) < 3:
        flash("A destination needs to be at least 3 characters!", 'logout')
        isProblem = True
    
    if len(str(request.form['trip_plan'])) < 3:
        flash("A plan must be provided!", 'logout')
        isProblem = True

    if len(str(request.form['sdate'])) < 2 or len(str(request.form['edate'])) < 2:
        flash("You are missing a starting/ending date!", 'logout')
        return redirect('/newtrip')

    # datetime.datetime.strftime(datetime.datetime.strptime(userInDate, '%Y-%m-%d'), '%Y-%m-%d')
    sdate = datetime.datetime.strftime(datetime.datetime.strptime(request.form['sdate'], '%Y-%m-%d'), '%Y-%m-%d')
    edate = datetime.datetime.strftime(datetime.datetime.strptime(request.form['edate'], '%Y-%m-%d'), '%Y-%m-%d')

    sdate_object= datetime.datetime.strptime(request.form['sdate'], '%Y-%m-%d')
    edate_object= datetime.datetime.strptime(request.form['edate'], '%Y-%m-%d')
    print("sdate_object is "+str(sdate_object))
    print("sdate is "+sdate)
    print("edate is "+edate)

    print("sdate_object < datetime.datetime.now() is "+str(sdate_object < datetime.datetime.now()))
    print("sdate_object > datetime.datetime.now() is "+str(sdate_object > datetime.datetime.now()))

    if sdate_object < datetime.datetime.now():
        flash("The start date of the trip must be in the future!", 'logout')
        flash("Time travel is not allowed!", 'logout')
        isProblem = True
        print("we set isProblem to "+str(isProblem))

    if sdate_object > edate_object:
        flash("The end date must be after the start date!", 'logout')
        isProblem = True
    
    if isProblem:
        print("we should be redirecting to /newtrip")
        return redirect('/newtrip')

    mysql = connectToMySQL('TripBuddy2')
    query = "INSERT INTO trips (trip_owner, destination, start_date, end_date, plan) VALUES (%(owner)s, %(trip)s, %(sd)s, %(ed)s, %(plan)s);"
    data = {"owner": session['id'],
            "trip": request.form['trip_name'],
            "sd": sdate,
            "ed": edate,
            "plan": request.form['trip_plan']
    }

    print(str(request.form['trip_name']))

    print("query is "+query+"!!!")
    print("data is "+str(data))

    
    res = mysql.query_db(query, data)   #this res will only give success or failure on inserting 
    print("insert into trips was "+str(res))
   
    return redirect('/display')

@app.route('/display', methods=['get', 'post'])
def display():
    if 'id' in session:
        id = session['id']
    else:
        flash("You must log in to enter this website", 'logout')
        return redirect('/')

    print("Entering /display...**************")
    print("id is "+str(id))
    
    # get the first name of the user logged in (also known as sender)
    mysql = connectToMySQL('TripBuddy2')
    query = "SELECT first_name FROM Users WHERE id = "+str(id)+";"
    res = mysql.query_db(query)
    first_name = res[0]['first_name']

    print("first_name is "+str(first_name))
    
    # get all trips that have a taken_by that = the logged in user
    mysql = connectToMySQL('TripBuddy2')
    query = "SELECT * FROM trips WHERE trips.trip_owner = "+str(id)+";"
    usertrips = mysql.query_db(query)
    print("usertrips is "+str(usertrips))
    
    # get all trips that have no taken_by
    mysql = connectToMySQL('TripBuddy2')
    query = "SELECT * FROM (SELECT * FROM trips_has_users JOIN trips on trips.id = Trip_id WHERE joined = "+str(id)+") innerQuery WHERE joined = "+str(id)+";"
    print("trips query is "+query)
    tripsJoined = mysql.query_db(query)
    print("tripsJoined is "+str(tripsJoined))

    mysql = connectToMySQL('TripBuddy2')
    query = "SELECT * FROM trips LEFT OUTER JOIN trips_has_users ON trips.id = trips_has_users.Trip_id WHERE trips.trip_owner <> "+str(id)+" AND trips.id NOT IN (SELECT Trip_id FROM trips_has_users WHERE joined = "+str(id)+");"
    trips = mysql.query_db(query)
    print("trips is "+str(trips))

    return render_template('result.html', fname=first_name, tripInfo=usertrips, utInfo=trips, joinedInfo=tripsJoined)

@app.route('/delete/<id>', methods=['get', 'post'])
def delete(id):
    print("delete**************")

    # check message's user id to make sure it is the same as the logged in user's id
    mysql =connectToMySQL('TripBuddy2')
    query = "SELECT * FROM trips JOIN users WHERE trips.id = "+id+";"
    res = mysql.query_db(query)

    print("session['id'] is "+str(session['id']))
    print("res[0]['users.id'] is "+str(res[0]['users.id']))
    print("session['id'] is "+str(session['id']))
    
    mysql = connectToMySQL('TripBuddy2')
    query = "DELETE FROM trips WHERE trips.id = %(trip)s;"
    data = {"trip": str(id)
    } 
    res = mysql.query_db(query, data)
    print("res is "+str(res))
    if not res:
        flash("Someone has joined your trip; you cannot remove it!", 'logout')

    return redirect('/display')

@app.route('/edit/<id>', methods=['get', 'post'])
def edit(id):
    print("edit**************")

    mysql =connectToMySQL('TripBuddy2')
    query = "SELECT first_name FROM users WHERE id = "+str(session['id'])+";"
    nameres = mysql.query_db(query)
    first_name = nameres[0]['first_name']

    # check message's user id to make sure it is the same as the logged in user's id
    mysql =connectToMySQL('TripBuddy2')
    query = "SELECT * FROM trips JOIN users WHERE trips.id = "+id+";"
    res = mysql.query_db(query)
    print("edit res is "+str(res))

    print("session['id'] is "+str(session['id']))
    print("res[0]['users.id'] is "+str(res[0]['users.id']))
    print("session['id'] is "+str(session['id']))

    print("res[0]['destination'] is "+str(res[0]['destination']))

    mysql = connectToMySQL('TripBuddy2')

    return render_template('edit.html', fname=first_name, sdate=res[0]['start_date'], edate=res[0]['end_date'], trip_name=res[0]['destination'], trip_plan=res[0]['plan'], trip_id=id)

@app.route('/add/<id>', methods=['get', 'post'])
def add(id):
    print("add**************")

    # check message's user id to make sure it is the same as the logged in user's id
    mysql =connectToMySQL('TripBuddy2')
    query = "SELECT * FROM trips WHERE trips.id = "+id+";"
    res = mysql.query_db(query)

    print("res[0]['name'] is "+str(res[0]['trip_owner']))
    
    mysql = connectToMySQL('TripBuddy2')
    query = "INSERT INTO trips_has_users (Trip_id, User_id, joined) VALUES (%(trip)s, %(ownerid)s, %(uid)s);"
    data = {"trip": id,
            "ownerid": res[0]['trip_owner'],
            "uid": int(session['id']),
    } 

    print("data is "+str(data))
    res = mysql.query_db(query, data)
    print("res is "+str(res))

    # return render_template('edit.html', wish_name=res[0]['item_name'], wish_desc=res[0]['description'])
    return redirect('/display')

@app.route('/cancel/<id>', methods=['get', 'post'])
def cancel(id):
    print("cancel/"+str(id))

    mysql =connectToMySQL('TripBuddy2')
    query = "SELECT * FROM trips WHERE trips.id = "+id+";"
    res = mysql.query_db(query)

    print("res[0]['name'] is "+str(res[0]['trip_owner']))
    
    mysql = connectToMySQL('TripBuddy2')

    query = "DELETE FROM trips_has_users WHERE trip_id = %(trip)s and user_id = %(uid)s and joined = %(joined)s;"
    
    data = {"trip": id,
            "uid": res[0]['trip_owner'],
            "joined": session['id']
    } 

    print("data is "+str(data))
    res = mysql.query_db(query, data)
    print("res is "+str(res))

    # return render_template('edit.html', wish_name=res[0]['item_name'], wish_desc=res[0]['description'])
    return redirect('/display')

@app.route('/update/<id>', methods=['get', 'post'])
def update(id):
    print("update**************")
    
    sdate = datetime.datetime.strftime(datetime.datetime.strptime(request.form['sdate'], '%Y-%m-%d'), '%Y-%m-%d')
    edate = datetime.datetime.strftime(datetime.datetime.strptime(request.form['edate'], '%Y-%m-%d'), '%Y-%m-%d')
    # UPDATE table_name
    # SET column1 = value1, column2 = value2, ...
    # WHERE condition
        
    mysql = connectToMySQL('TripBuddy2')
    # UPDATE trips SET trip_owner = 1, destination = 'Wales', start_date = '2019-03-02', end_date = '2019-03-07', plan ='Castles' WHERE id = 2;
    query = "UPDATE trips SET trip_owner = %(owner)s, destination = %(trip)s, start_date = %(sd)s, end_date = %(ed)s, plan = %(plan)s WHERE trips.id = "+str(id)+";"
    data = {"owner": session['id'],
            "trip": request.form['trip_name'],
            "sd": sdate,
            "ed": edate,
            "plan": request.form['trip_plan']
    }

    print(str(request.form['trip_name']))
    
    mysql = connectToMySQL('TripBuddy2')
    print("update query is "+query)
    print("data is "+str(data))

    res = mysql.query_db(query, data)   #this res will only give success or failure on inserting 

    print("res is "+str(res))

    return redirect('/display')

@app.route('/view/<id>', methods=['get', 'post'])
def view(id):
    print("view**************")

    # check message's user id to make sure it is the same as the logged in user's id
    mysql =connectToMySQL('TripBuddy2')
    query = "SELECT * FROM trips WHERE trips.id = "+id+";"
    res = mysql.query_db(query)

    print("res[0]['destination'] is "+str(res[0]['destination']))
    print("res is "+str(res))

    print("trip_destination is "+str(res[0]['destination']))
    print("tripInfo is "+str(res))

    mysql =connectToMySQL('TripBuddy2')
    query = "SELECT first_name FROM users WHERE id = "+str(res[0]['trip_owner'])+";"
    first_name = mysql.query_db(query)
    print("first_name = "+str(first_name))

    return render_template('view.html', trip_name=res[0]['destination'], tripInfo=res, owner=first_name[0]['first_name'])

@app.route("/email", methods=['POST'])
def email():
    print("|||||*****email route*****|||||")
    found = False
    mysql = connectToMySQL('TripBuddy2')        # connect to the database
    # query = "SELECT username from users WHERE users.username = %(user)s;"
    query = "SELECT email from users WHERE users.email = %(email)s;"
    data = { 'email': request.form['email'] }
    result = mysql.query_db(query, data)
    print("email route result: "+str(result))
    if result:
        found = True
    return render_template('partials/email.html', found=found)  # render a partial and return it
    
@app.route('/logout', methods=['GET','POST'])
def logout():
    print("logout**************")
    
    session.clear()
    flash('You have been logged out', 'logout')

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)