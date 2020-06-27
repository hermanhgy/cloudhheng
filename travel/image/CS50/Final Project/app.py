import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta

from helpers import login_required

# Configure application
app = Flask(__name__)
app.secret_key = "hello"
app.permanent_session_lifetime = timedelta(minutes=15)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Session(app)
# To track what is stored in session, execute print(session)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# # Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure CS50 Library to use SQLite database
connection = sqlite3.connect('education.db', check_same_thread=False)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()


@app.route("/")
@login_required
def index():
    # Check who is the current user and his/her role
    id = session["user_id"]
    cursor.execute("SELECT * FROM people WHERE id=:id", {'id': id})
    check = cursor.fetchall()
    name = check[0]["name"].upper()
    role = check[0]["role"]

    # Check if the upcoming classes has passed
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    # One hour after the lesson, the class will be moved to validate list from upcoming table
    cursor.execute("""SELECT *, TIME("time", '+1 hour') as time_plus
                    FROM upcoming WHERE date < :current_date OR (date = :current_date AND time_plus < :current_time)""", 
                    {'current_date':current_date, 'current_time':current_time})
    passed = cursor.fetchall()

    for row in passed:

        class_id = row["id"]
        # Retrieve the student list 
        cursor.execute("""SELECT * from people WHERE people.id IN (
                        SELECT person_id FROM upcoming JOIN upcoming_students 
                        ON upcoming.id=upcoming_students.class_id WHERE id=:id)""", {'id':class_id})
        data = cursor.fetchall()
        count_student = len(data)

        if count_student != 0:

            # Moved all the information to the validate table if there is a student list (the class was happening)
            cursor.execute("""INSERT INTO validate (id, teacher_id, date, time, duration_hour, duration_min, type, subject, name, level, message) 
                        VALUES (:id, :teacher_id, :date, :time, :duration_hour, :duration_min, :type, :subject, :name, :level, :message)""", 
                        {'id':class_id, 
                        'teacher_id':row["teacher_id"], 
                        'date': row["date"], 
                        'time': row["time"], 
                        'duration_hour': row["duration_hour"], 
                        'duration_min': row["duration_min"],
                        'type': row["type"], 
                        'subject': row["subject"], 
                        'name': row["name"], 
                        'level': row["level"], 
                        'message': row["message"]})
        
            # Also move the student list from upcoming_students to validate_students
            for row in data:
                cursor.execute("""INSERT INTO validate_students (validate_id, person_id) VALUES (:validate_id, :person_id)""",
                                {'validate_id':class_id, 'person_id':row["id"]})

        # And then delete the data from the upcoming table
        cursor.execute("""DELETE FROM upcoming WHERE id=:id""", {'id':class_id})
        cursor.execute("""DELETE FROM upcoming_students WHERE class_id=:id""", {'id':class_id})

        connection.commit()

    # Actions for teachers
    if role == "Teacher":

        # Check what subjects he/she is teaching
        cursor.execute("""SELECT * from subjects JOIN teachers 
                    ON subjects.id=teachers.subject_id 
                    WHERE teachers.person_id=:id ORDER BY type, name""", {'id': id})  
        teaching = cursor.fetchall()
        
        # Track the number of teaching 
        count_teaching = len(teaching) 

        # Select the upcoming classes again to be displayed later
        cursor.execute("""SELECT *,
                        CASE CAST (strftime('%w', date) AS INTEGER)
                            WHEN 0 THEN 'Sunday'
                            WHEN 1 THEN 'Monday'
                            WHEN 2 THEN 'Tuesday'
                            WHEN 3 THEN 'Wednesday'
                            WHEN 4 THEN 'Thursday'
                            WHEN 5 THEN 'Friday'
                            ELSE 'Saturday' END AS day
                        FROM upcoming WHERE teacher_id=:id ORDER BY date, time""", {'id': id})  
        upcoming = cursor.fetchall()

        # A list that stores all the registered students and total number of enrollment
        students = []
        count = []

        for row in upcoming:
            # For each upcoming class, retrieve all students enrolled in that class
            cursor.execute("""SELECT * from people WHERE people.id IN (
                            SELECT person_id FROM upcoming JOIN upcoming_students 
                            ON upcoming.id=upcoming_students.class_id WHERE id=:id)""", {'id':row["id"]}) 
            data = cursor.fetchall()
            students.append(data)
            count.append(len(data))

        return render_template("teacher_index.html", name=name, teaching=teaching, count_teaching=count_teaching,
                                upcoming=upcoming, count_upcoming=len(upcoming), students=students, count=count)

    # Action for students
    elif role == "Student":

        # Retrieve what subjects he/she is learning
        cursor.execute("""SELECT * from subjects JOIN students ON subjects.id=students.subject_id 
                    WHERE students.person_id=:id ORDER BY type, name""", {'id': id})  
        learning = cursor.fetchall()
        
        # Track the number of learning subjects
        count_learning = len(learning)

        # Retrieve upcoming classes, weekday (Mon, Tue, etc), corresponding tachers' info, and total student enrollment
        cursor.execute("""SELECT *, 
                        CASE CAST (strftime('%w', date) AS INTEGER)
                            WHEN 0 THEN 'Sunday'
                            WHEN 1 THEN 'Monday'
                            WHEN 2 THEN 'Tuesday'
                            WHEN 3 THEN 'Wednesday'
                            WHEN 4 THEN 'Thursday'
                            WHEN 5 THEN 'Friday'
                            ELSE 'Saturday' END AS day,
                        (SELECT name FROM people where people.id=teacher_id) as teacher_name,
                        (SELECT skype_id FROM people where people.id=teacher_id) as teacher_skype_id,
                        (SELECT occupation FROM people where people.id=teacher_id) as teacher_occupation,
                        (SELECT organization FROM people where people.id=teacher_id) as teacher_organization,
                        (SELECT COUNT(upcoming_students.person_id) FROM upcoming_students WHERE upcoming_students.class_id=id) AS count_student
                       FROM upcoming JOIN upcoming_students ON upcoming.id = upcoming_students.class_id 
                        WHERE upcoming_students.person_id =:id ORDER BY date, time""", {'id': id})  
        upcoming = cursor.fetchall()

        return render_template("student_index.html", name=name, learning=learning, count_learning=count_learning,
                                upcoming=upcoming, count_upcoming=len(upcoming))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    
    # Check who is the current user
    id = session["user_id"]
    cursor.execute("SELECT role FROM people WHERE id=:id", {'id': id})
    role = cursor.fetchone()["role"]
    
    if request.method == "POST":
    
        name = request.form.get("first") + " " + request.form.get("last")
        skype_id = request.form.get("skype_id") 
        occupation = request.form.get("occupation") 
        organization = request.form.get("organization")

        # Update the user profile in the people table
        cursor.execute("""UPDATE people SET name=:name, skype_id=:skype_id, 
            occupation=:occupation, organization=:organization WHERE id=:id""", 
            {'name':name, 'skype_id':skype_id, 'occupation':occupation, 'organization':organization, 'id':id})

        # Clear all the current teacher's OR student's subjects first (only one can be true below)
        cursor.execute("""DELETE FROM teachers WHERE person_id=:person_id""", {'person_id':id})
        cursor.execute("""DELETE FROM students WHERE person_id=:person_id""", {'person_id':id})
        
        # Then add the new updated subjects into the table
        subjects = request.form.getlist("subjects")
        for item in subjects:
            cursor.execute("""SELECT id FROM subjects WHERE name=:name""", {'name':item})
            subject_id = cursor.fetchone()["id"]

            if role == "Teacher":    
                cursor.execute("""INSERT INTO teachers (subject_id, person_id) VALUES (:subject_id, :person_id)""", 
                {'subject_id':subject_id, 'person_id':id})
            else:
                cursor.execute("""INSERT INTO students (subject_id, person_id) VALUES (:subject_id, :person_id)""", 
                {'subject_id':subject_id, 'person_id':id})

        connection.commit()

        flash("Your profile is successfully updated!", "success")
 
        return redirect("/")

    else: 
        cursor.execute("SELECT * FROM people WHERE id=:id", {'id': id})
        data = cursor.fetchall()
        
        name = data[0]["name"]
        split_name = name.split()
        first = split_name[0]
        last = split_name[1]

        # Some fields might be empty, so need to replace "None" to empty string
        if data[0]["organization"] == None:
            organization = ""
        else: 
            organization = data[0]["organization"]

        if data[0]["skype_id"] == None:
            skype_id = ""
        else: 
            skype_id = data[0]["skype_id"]

        if data[0]["occupation"] == None:
            occupation = ""
        else: 
            occupation = data[0]["occupation"]

        # Create a dictionary that store all the information needed
        item = {'name':name, 'email':data[0]["email"], 'role':data[0]["role"], 'first':first, 'last':last, 
                'skype_id':skype_id, 'occupation':occupation, 'organization':organization}

        # Retrieve the total types available
        cursor.execute("""SELECT DISTINCT type FROM subjects ORDER BY type""")
        type_list = cursor.fetchall()
        count = len(type_list)

        # Design a list that would store "type" and "list of subject"
        type_subj_lists = []

        # Repeat this for n numbers of types
        for i in range (0, count):
        
            # Design a list that would store list of subject
            subject_list = []

            # Retrieve all the subjects correspond to the type
            cursor.execute("""SELECT name FROM subjects WHERE type=:type""", {'type': type_list[i]["type"]})
            data = cursor.fetchall()
            for row in data:
                subject_list.append(row["name"])

            # Store the type + list of subjects together 
            type_subj_lists.append((type_list[i]["type"], (subject_list)))

        if role == "Teacher":
            return render_template("teacher_profile.html", row=item, type_subj_lists=type_subj_lists)
        else:
            return render_template("student_profile.html", row=item, type_subj_lists=type_subj_lists)


@app.route("/schedule", methods=["GET", "POST"])
@login_required
def schedule():
    
    # Check who is the current user
    id = session["user_id"]
    
    # Form submit with POST method
    if request.method == "POST":
    
        class_id = request.form.get("class_id")
        subject = request.form.get("subject")
        name = request.form.get("name")
        date = request.form.get("date")
        time = request.form.get("time")
        duration_hour = request.form.get("duration_hour")
        
        # Check if the 'Not Null' field is empty
        if subject == None:
            flash("You must select a subject", "danger")
            return redirect("/schedule")
        elif name == "":
            flash("You must enter a name of your class", "danger")
            return redirect("/schedule")
        elif date == "":
            flash("You must enter a date of your class", "danger")
            return redirect("/schedule")
        elif time == "":
            flash("You must enter a time of your class", "danger")
            return redirect("/schedule")
        elif duration_hour == "":
            flash("You must specify the duration of your class", "danger")
            return redirect("/schedule")

        level = request.form.get("level")
        message = request.form.get("message")
        duration_min = request.form.get("duration_min")

        # Change the NULL value into more meaningful content
        if level == None:
            level = "Not specified"
        if message == "":
            message = "Not provided"

        # Find out the type of subject
        cursor.execute("""SELECT type from subjects WHERE name=:name""", {'name': subject})  
        type = cursor.fetchone()
        type = type["type"]

        if duration_min == "":
            duration_min = "0"

        # Check if there is any conflict in the schedule
        time_minus = datetime.strptime(time, "%H:%M") - timedelta(hours=int(duration_hour), minutes=int(duration_min))
        time_minus = time_minus.strftime("%H:%M")
        time_plus = datetime.strptime(time, "%H:%M") + timedelta(hours=int(duration_hour), minutes=int(duration_min))
        time_plus = time_plus.strftime("%H:%M")
      
        # Then select all to check if there is any conflict with the new schedule
        cursor.execute("""SELECT * FROM upcoming WHERE teacher_id=:id AND date=:date AND (time BETWEEN :time_minus AND :time_plus) """,
                {'id':id, 'date':date, 'time_minus':time_minus, 'time_plus':time_plus})  
        rows = cursor.fetchall()
        
        conflict = []
        for row in rows:
            conflict.append(row["id"])
       
        # Submitting the first registered class     
        if class_id == "None":
            
            # First time registered class should not have any conflict with any other classes
            if len(conflict) > 0:
                flash("The class was not successfully scheduled. It appears you have another class conflicts with this schedule.", "danger")
                return redirect("/")
        
            else:
                cursor.execute("""INSERT INTO upcoming (teacher_id, date, time, duration_hour, duration_min, type, subject, name, level, message) 
                    VALUES (:teacher_id, :date, :time, :duration_hour, :duration_min, :type, :subject, :name, :level, :message)""", 
                    {'teacher_id':id, 'date':date, 'time':time, 'duration_hour':duration_hour, 'duration_min':duration_min,
                    'type':type, 'subject':subject, 'name':name, 'level':level, 'message':message})  
                connection.commit()
                flash("Your class is successfully scheduled.", "success")
            
                # Warn the user for not providing the level and message
                if level == "Not specified":
                    flash("Please consider to specify your class level to ensure the suitable enrollment.", "warning")
                if message == "Not provided":
                    flash("Please consider to write a short message to provide more details about your class.", "warning")

                return redirect("/")

        # Updating existing class       
        else: 
            
            # The maximum conflict should be only one, which is with the "soon to be updated class"
            if len(conflict) > 1:
                flash("The class was not successfully scheduled. It appears you have another class conflicts with this schedule.", "danger")
                return redirect("/")

            # The newly rescheduled class can only conflict with the current "soon to be updated class"
            elif len(conflict) == 1 and (conflict[0] != int(class_id)):
                print("one conflict with other class which is not this class")
                flash("The class was not successfully scheduled. It appears you have another class conflicts with this schedule.", "danger")
                return redirect("/")

            else: 
                # Update current rescheduled class in the upcoming table  
                cursor.execute("""UPDATE upcoming SET date=:date, time=:time, duration_hour=:duration_hour, 
                                duration_min=:duration_min, name=:name, level=:level, message=:message 
                                WHERE id=:class_id""", 
                                {'date':date, 'time':time, 'duration_hour':duration_hour, 'duration_min':duration_min, 
                                'name':name, 'level':level, 'message':message, 'class_id':class_id})  
                connection.commit()
                flash("Your class is successfully updated.", "success")
            
                # Warn the user for not providing the level and message
                if level == "Not specified":
                    flash("Please consider to specify your class level to ensure the suitable enrollment.", "warning")
                if message == "Not provided":
                    flash("Please consider to write a short message to provide more details about your class.", "warning")

                return redirect("/")
            
    # Form submit with GET method
    else:
        cursor.execute("""SELECT * from subjects JOIN teachers ON subjects.id=teachers.subject_id 
                            WHERE teachers.person_id=:id """, {'id': id})  
        rows = cursor.fetchall()
        
        return render_template("teacher_schedule.html", rows=rows)


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():

    if request.method == "POST":
        
        class_id = request.form.get("class_id") 
        cursor.execute("""SELECT * FROM upcoming WHERE id=:id""", {'id':class_id})  
        row = cursor.fetchone()

        return render_template("teacher_update.html", row=row)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    
    # Check who is the current user
    id = session["user_id"]
    
    # Retrieve the subject list registered by students 
    cursor.execute("""SELECT * from subjects JOIN students ON subjects.id=students.subject_id 
                            WHERE students.person_id=:id """, {'id': id})  
    subjects = cursor.fetchall()

    # Retrieve the type list based on the subjects selected
    typelist = []
    for row in subjects:
        cursor.execute("""SELECT type FROM subjects WHERE name=:name""", {'name': row["name"]})
        data = cursor.fetchone()["type"]
        if not data in typelist:
            typelist.append(data)

    # Submitting the form via POST request (when using filter)
    if request.method == "POST":
        
        type = request.form.get("type")
        subject = request.form.get("subject")

        # Filter the class and retrieve corresponding teacher's info and number of enrollment
        if type == "All" and subject == "All":
            cursor.execute("""SELECT *,
                            CASE CAST (strftime('%w', date) AS INTEGER)
                                WHEN 0 THEN 'Sunday'
                                WHEN 1 THEN 'Monday'
                                WHEN 2 THEN 'Tuesday'
                                WHEN 3 THEN 'Wednesday'
                                WHEN 4 THEN 'Thursday'
                                WHEN 5 THEN 'Friday'
                                ELSE 'Saturday' END AS day,
                            (SELECT name FROM people where people.id=teacher_id) as teacher_name,
                            (SELECT skype_id FROM people where people.id=teacher_id) as teacher_skype_id,
                            (SELECT occupation FROM people where people.id=teacher_id) as teacher_occupation,
                            (SELECT organization FROM people where people.id=teacher_id) as teacher_organization,
                            (SELECT COUNT(upcoming_students.person_id) FROM upcoming_students WHERE upcoming_students.class_id=id) AS count_student
                            FROM upcoming ORDER BY date, time""")
            rows = cursor.fetchall()
        elif type != "All":
            cursor.execute("""SELECT *,
                            CASE CAST (strftime('%w', date) AS INTEGER)
                                WHEN 0 THEN 'Sunday'
                                WHEN 1 THEN 'Monday'
                                WHEN 2 THEN 'Tuesday'
                                WHEN 3 THEN 'Wednesday'
                                WHEN 4 THEN 'Thursday'
                                WHEN 5 THEN 'Friday'
                                ELSE 'Saturday' END AS day, 
                            (SELECT name FROM people where people.id=teacher_id) as teacher_name,
                            (SELECT skype_id FROM people where people.id=teacher_id) as teacher_skype_id,
                            (SELECT occupation FROM people where people.id=teacher_id) as teacher_occupation,
                            (SELECT organization FROM people where people.id=teacher_id) as teacher_organization,
                            (SELECT COUNT(upcoming_students.person_id) FROM upcoming_students WHERE upcoming_students.class_id=id) AS count_student
                            FROM upcoming WHERE type=:type ORDER BY date, time""", {'type':type})
            rows = cursor.fetchall()
        else:
            cursor.execute("""SELECT *,
                                CASE CAST (strftime('%w', date) AS INTEGER)
                                WHEN 0 THEN 'Sunday'
                                WHEN 1 THEN 'Monday'
                                WHEN 2 THEN 'Tuesday'
                                WHEN 3 THEN 'Wednesday'
                                WHEN 4 THEN 'Thursday'
                                WHEN 5 THEN 'Friday'
                                ELSE 'Saturday' END AS day,
                            (SELECT name FROM people where people.id=teacher_id) as teacher_name,
                            (SELECT skype_id FROM people where people.id=teacher_id) as teacher_skype_id,
                            (SELECT occupation FROM people where people.id=teacher_id) as teacher_occupation,
                            (SELECT organization FROM people where people.id=teacher_id) as teacher_organization,
                            (SELECT COUNT(upcoming_students.person_id) FROM upcoming_students WHERE upcoming_students.class_id=id) AS count_student
                            FROM upcoming WHERE subject=:subject ORDER BY date, time""", {'subject':subject})
            rows = cursor.fetchall()

        # Create a list of student's upcoming classes
        cursor.execute("""SELECT class_id from upcoming_students WHERE person_id=:id""", {'id':id})
        data = cursor.fetchall()
        classlist = []
        for row in data:
            classlist.append(row["class_id"])

        # If student has registered for this class, remove this record to be shown in "search"
        search = []
        for row in rows:
            if row["id"] not in classlist: # and row["subject"] in learning
                search.append(row)
       
        filter = {'type': type, 'subject': subject}
        
        return render_template("student_search.html", search=search, count_search=len(search), 
                                subjects=subjects, typelist=typelist, filter=filter)

    # Submitting the form via GET request
    else:
    
        # Retrieve all classes and its corresponding teacher's info and number of enrollment
        cursor.execute("""SELECT *,
                        CASE CAST (strftime('%w', date) AS INTEGER)
                            WHEN 0 THEN 'Sunday'
                            WHEN 1 THEN 'Monday'
                            WHEN 2 THEN 'Tuesday'
                            WHEN 3 THEN 'Wednesday'
                            WHEN 4 THEN 'Thursday'
                            WHEN 5 THEN 'Friday'
                            ELSE 'Saturday' END AS day,
                        (SELECT name FROM people where people.id=teacher_id) as teacher_name,
                        (SELECT skype_id FROM people where people.id=teacher_id) as teacher_skype_id,
                        (SELECT occupation FROM people where people.id=teacher_id) as teacher_occupation,
                        (SELECT organization FROM people where people.id=teacher_id) as teacher_organization,
                        (SELECT COUNT(upcoming_students.person_id) FROM upcoming_students WHERE upcoming_students.class_id=id) AS count_student 
                        FROM upcoming ORDER BY date, time""")
        rows = cursor.fetchall()
    
        # Create a list of student's upcoming classes
        cursor.execute("""SELECT class_id from upcoming_students WHERE person_id=:id""", {'id':id})
        data = cursor.fetchall()
        classlist = []
        for row in data:
            classlist.append(row["class_id"])

        # If student has registered for this class, remove this record to be shown in "search"
        search = []
        for row in rows:
            if row["id"] not in classlist: # and row["subject"] in learning 
                search.append(row)

        print(search[0]["day"])

        filter = {'type': "All", 'subject': "All"}

        return render_template("student_search.html", search=search, count_search=len(search),
                                subjects=subjects, typelist=typelist, filter=filter)


@app.route("/enroll_confirm", methods=["GET", "POST"])
@login_required
def enroll_confirm():

    if request.method == "POST":
        # Retrieve the current information to be placed as default values
        subject = request.form.get("subject") 
        name = request.form.get("name")
        date = request.form.get("date")
        day = request.form.get("day")
        time = request.form.get("time")
        duration_hour = request.form.get("duration_hour")
        duration_min = request.form.get("duration_min")
        message = request.form.get("message")
        teacher_name = request.form.get("teacher_name")
        teacher_id = request.form.get("teacher_id")

        row = {'subject':subject, 'name':name, 'date':date, 'day':day, 'time':time, 'duration_hour':duration_hour, 
                'duration_min':duration_min, 'message':message, 'teacher_name':teacher_name, 'teacher_id':teacher_id}
        
        return render_template("student_enroll_confirm.html", row=row)


@app.route("/enroll", methods=["GET", "POST"])
@login_required
def enroll():
    
    # Check who is the current user
    id = session["user_id"]

    if request.method == "POST":

        name = request.form.get("name")
        date = request.form.get("date")
        time = request.form.get("time")
        duration_hour = request.form.get("duration_hour")
        duration_min = request.form.get("duration_min")
        teacher_id = request.form.get("teacher_id")
        confirm = request.form.get("confirm")
     
        if confirm == "yes":
            
            # Check if there is any conflict in the schedule
            time_minus = datetime.strptime(time, "%H:%M") - timedelta(hours=int(duration_hour), minutes=int(duration_min))
            time_minus = time_minus.strftime("%H:%M")
            time_plus = datetime.strptime(time, "%H:%M") + timedelta(hours=int(duration_hour), minutes=int(duration_min))
            time_plus = time_plus.strftime("%H:%M")
            
            # Select all to check if there is any conflict with this schedule
            cursor.execute("""SELECT * FROM upcoming_students WHERE person_id=:id and class_id =
                            (SELECT id FROM upcoming WHERE date=:date AND (time BETWEEN :time_minus AND :time_plus)) """,
                            {'id':id, 'date':date, 'time_minus':time_minus, 'time_plus':time_plus})  
            
            conflict = cursor.fetchall()

            if len(conflict) > 0:        
                flash("Your enrollment was not successful. It appears you have another class conflicts with this schedule.", "danger")
                return redirect("/")
            
            else: 
                # Retrieve the class_id
                cursor.execute("""SELECT id FROM upcoming WHERE teacher_id=teacher_id AND name=:name AND date=:date 
                                AND time=:time""", {'teacher_id':teacher_id, 'name':name, 'date':date, 'time':time})
                class_id = cursor.fetchone()["id"]

                # Insert the enrollment into the database 
                cursor.execute("""INSERT INTO upcoming_students (class_id, person_id) VALUES (:class_id, :person_id)""", 
                        {'class_id':class_id, 'person_id':id})  
                connection.commit()
                
                flash("Your enrollment was successful. See you in the class!", "success")
                return redirect("/")
        
        # If the class is not enrolled by clicking the "No" button
        else:
            flash("The class was not enrolled!", "warning")
            return redirect("/search")


@app.route("/cancel_confirm", methods=["GET", "POST"])
@login_required
def cancel_confirm():

    # Check who is the current user
    id = session["user_id"]
    cursor.execute("SELECT * FROM people WHERE id=:id", {'id': id})
    check = cursor.fetchall()
    role = check[0]["role"]

    if request.method == "POST":
        # Retrieve the current information to be placed as default values
        subject = request.form.get("subject") 
        name = request.form.get("name")
        date = request.form.get("date")
        day = request.form.get("day")
        time = request.form.get("time")
        duration_hour = request.form.get("duration_hour")
        duration_min = request.form.get("duration_min")
        message = request.form.get("message")
        
        row = {'subject':subject, 'name':name, 'day':day, 'date':date, 'time':time, 'duration_hour':duration_hour, 
                'duration_min':duration_min, 'message':message}
        
        if role == "Teacher":
            return render_template("teacher_cancel_confirm.html", row=row)
        elif role == "Student":
            return render_template("student_cancel_confirm.html", row=row)


@app.route("/cancel", methods=["GET", "POST"])
@login_required
def cancel():

    # Check who is the current user
    id = session["user_id"]
    cursor.execute("SELECT * FROM people WHERE id=:id", {'id': id})
    check = cursor.fetchall()
    role = check[0]["role"]

    if request.method == "POST":

        # Retrieve the current information to be placed as default values
        name = request.form.get("name")
        date = request.form.get("date")
        time = request.form.get("time")
        confirm = request.form.get("confirm")
     
        if confirm == "yes":
            
            if role == "Teacher":
                
                # Check the class id  
                cursor.execute("""SELECT id from upcoming WHERE teacher_id=:id AND name=:name AND date=:date AND time=:time""",
                                {'id':id, 'name':name, 'date':date, 'time':time})
                class_id = cursor.fetchone()["id"]
                print(class_id)
                # Delete the data for both upcoming and upcoming_students 
                cursor.execute("""DELETE from upcoming WHERE id=:id""", {'id':class_id})
                cursor.execute("""DELETE from upcoming_students WHERE class_id=:class_id""", {'class_id':class_id})
                connection.commit()

                flash("The class was successfully cancelled", "success")
                return redirect("/")
            
            elif role == "Student":
                cursor.execute("""DELETE from upcoming_students WHERE person_id=:id AND class_id = 
                (SELECT id from upcoming WHERE name=:name AND date=:date AND time=:time)""",
                {'id':id, 'name':name, 'date':date, 'time':time})
                connection.commit()
                flash("The class was successfully cancelled", "success")
                return redirect("/")

        # If the class is not cancelled by clicking the "No" button
        else:
            flash("The class was not cancelled", "warning")
            return redirect("/")


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():

    # Check who is the current user
    id = session["user_id"]
    cursor.execute("SELECT * FROM people WHERE id=:id", {'id': id})
    check = cursor.fetchall()
    role = check[0]["role"]

    if role == "Teacher":

        cursor.execute("""SELECT *,
                        CASE CAST (strftime('%w', date) AS INTEGER)
                            WHEN 0 THEN 'Sunday'
                            WHEN 1 THEN 'Monday'
                            WHEN 2 THEN 'Tuesday'
                            WHEN 3 THEN 'Wednesday'
                            WHEN 4 THEN 'Thursday'
                            WHEN 5 THEN 'Friday'
                            ELSE 'Saturday' END AS day
                        from validate WHERE teacher_id=:id ORDER BY date, time""", {'id': id})          
        validate = cursor.fetchall()
        count_validate = len(validate)

        # A list that stores all the registered students and total number of enrollment
        students = []
        count = []

        for row in validate:
            # For each to be validated class, retrieve all students enrolled in that class
            cursor.execute("""SELECT * from people WHERE people.id IN (
                            SELECT person_id FROM validate JOIN validate_students 
                            ON validate.id=validate_students.validate_id WHERE id=:id)""", {'id':row["id"]}) 
            data = cursor.fetchall()
            students.append(data)
            count.append(len(data))

        # Then select all the history record
        cursor.execute("""SELECT * from history WHERE teacher_id=:id ORDER BY date DESC, time DESC""", {'id': id})          
        history = cursor.fetchall()

        # Retrieve the sum of hours and students
        cursor.execute("""SELECT SUM(duration) from history WHERE teacher_id=:id""", {'id': id})
        total_hour = cursor.fetchone()["SUM(duration)"]
        cursor.execute("""SELECT SUM(enrollment) from history WHERE teacher_id=:id""", {'id': id})
        total_student = cursor.fetchone()["SUM(enrollment)"]

        return render_template("teacher_history.html", validate=validate, count_validate=count_validate, 
                                students=students, count=count, history=history, count_history=len(history),
                                total_hour=total_hour, total_student=total_student)

    elif role == "Student":

         # Select all the history record
        cursor.execute("""SELECT * from history JOIN history_students ON history.id = history_students.history_id 
                WHERE history_students.person_id =:id ORDER BY date DESC, time DESC""", {'id': id})  
        history = cursor.fetchall()
        count_history = len(history)

        # Retrieve the sum of hours and students
        cursor.execute("""SELECT SUM(duration) from history JOIN history_students ON history.id = history_students.history_id 
                WHERE history_students.person_id =:id""", {'id': id})
        total_hour = cursor.fetchone()["SUM(duration)"]

        rows = []

        for row in history:

            # Check who is the teacher
            cursor.execute("""SELECT * from people WHERE id =:id""", {'id': row["teacher_id"]})
            teacher_name = cursor.fetchone()["name"]

            # Combine the data from "upcoming" table with the teacher data from "people" table
            data = {'id':row["id"], 'date':row["date"], 'time':row["time"], 'duration':row["duration"], 
                    'type':row["type"], 'subject':row["subject"], 'name':row['name'], 'level':row['level'], 
                    'teacher_name':teacher_name}
            rows.append(data)

        return render_template("student_history.html", rows=rows, count_history=count_history, total_hour=total_hour)


@app.route("/validate_confirm", methods=["GET", "POST"])
@login_required
def validate_confirm():

    if request.method == "POST":

        # Retrieve the current information to be placed as default values
        validate_id = request.form.get("validate_id") 
        teacher_id = request.form.get("teacher_id") 
        date = request.form.get("date")
        day = request.form.get("day")
        time = request.form.get("time")
        type = request.form.get("type")        
        subject = request.form.get("subject") 
        name = request.form.get("name")
        duration_hour = request.form.get("duration_hour")
        duration_min = request.form.get("duration_min")
        level = request.form.get("level")
        message = request.form.get("message")
        students = request.form.getlist("students")
        count = len(students)

        row = {'validate_id':validate_id, 'teacher_id':teacher_id, 'day':day, 'date':date, 'time':time, 'type': type, 'subject':subject, 
                'name':name, 'duration_hour':duration_hour, 'duration_min':duration_min, 'level':level, 'message':message, 
                'students':students, 'count':count}   

        if request.form['submit_button'] == 'no' or count == 0:

            validate = False
            return render_template("teacher_validate_confirm.html", row=row, validate=validate) 
        
        elif request.form['submit_button'] == 'yes':
        
            validate = True
            return render_template("teacher_validate_confirm.html", row=row, validate=validate) 

        else:
            return redirect("history")


@app.route("/validate", methods=["GET", "POST"])
@login_required
def validate():

    if request.method == "POST":

        # Retrieve the current information to be placed as default values
        validate_id = request.form.get("validate_id") 
        teacher_id = request.form.get("teacher_id") 
        date = request.form.get("date")
        time = request.form.get("time")
        
        duration_hour = request.form.get("duration_hour")
        duration_min = request.form.get("duration_min")
        duration = int(duration_hour) + int(duration_min)/60

        type = request.form.get("type")        
        subject = request.form.get("subject") 
        name = request.form.get("name")
        level = request.form.get("level")
        message = request.form.get("message")
        
        students = request.form.getlist("students")     
        enrollment = len((students))

        # Confirm validate
        if request.form['submit_button'] == "validate_yes":
            
            # Moved all the information to the history table from validate table
            cursor.execute("""INSERT INTO history (id, teacher_id, date, time, duration, type, subject, name, level, message, enrollment) 
                        VALUES (:id, :teacher_id, :date, :time, :duration, :type, :subject, :name, :level, :message, :enrollment)""", 
                        {'id': validate_id, 
                        'teacher_id': teacher_id, 
                        'date': date, 
                        'time': time, 
                        'duration': duration_hour, 
                        'type': type, 
                        'subject': subject, 
                        'name': name, 
                        'level': level,
                        'message': message,
                        'enrollment': enrollment})
                
            # Also move the student list from validate_students to history_students
            for item in students:
                cursor.execute("""SELECT id FROM people WHERE name=:name""", {'name':item})
                person_id = cursor.fetchone()["id"]
                cursor.execute("""INSERT INTO history_students (history_id, person_id) VALUES (:history_id, :person_id)""",
                                {'history_id':validate_id, 'person_id':person_id})
    
            # And then delete the data from the upcoming table
            cursor.execute("""DELETE FROM validate WHERE id=:id""", {'id':validate_id})
            cursor.execute("""DELETE FROM validate_students WHERE validate_id=:id""", {'id':validate_id})
            connection.commit()

            flash("The class was successfully validated", "success")
            return redirect("/history")

        # Don't confirm validate
        elif request.form['submit_button'] == "validate_no":
            flash("The class was not confirmed to be validated", "warning")
            return redirect("/history")

        # If the class should not be validated (not happening) 
        elif request.form['submit_button'] == "not_validate_yes":
            cursor.execute("""DELETE FROM validate WHERE id=:id""", {'id':validate_id})
            cursor.execute("""DELETE FROM validate_students WHERE validate_id=:id""", {'id':validate_id})
            connection.commit()

            flash("Thanks for informting us this class was not run. It has been removed from the record.", "success")
            return redirect("/history")

        # Don't confirm should not be validated (by clicking no button) 
        elif request.form['submit_button'] == "not_validate_no":
            flash("The class was kept for your re-validation if needed", "warning")
            return redirect("/history")

        else:
            return redirect("/history")
            

@app.route("/teacher_register", methods=["GET", "POST"])
def teacher_register():

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("teacher_email"):
            flash("You must provide an email!", "danger")
            return redirect("/teacher_register")

        # Ensure password was submitted
        elif not request.form.get("teacher_first_name"):
            flash("You must provide your first name!", "danger")
            return redirect("/teacher_register")

        # Ensure password was submitted
        elif not request.form.get("teacher_password"):
            flash("You must provide a password!", "danger")
            return redirect("/teacher_register")

        elif not request.form.get("teacher_confirm_password"):
            flash("You must retype your password!", "danger")
            return redirect("/teacher_register")

        elif request.form.get("teacher_password") != request.form.get("teacher_confirm_password"):
            flash("Retype password doesn't match!", "danger")
            return redirect("/teacher_register")
 
        email = request.form.get("teacher_email")
        name = request.form.get("teacher_first_name") + " " + request.form.get("teacher_last_name") 
        password = request.form.get("teacher_password")
        role = "Teacher"

        cursor.execute("SELECT * FROM people WHERE email = :email", {'email': email})
        check = cursor.fetchall()

        #Check if the username has been taken
        if len(check) > 0:    
            flash("Sorry! This email has been registered before", "danger")
            return redirect("/teacher_register")
        else:
            cursor.execute("INSERT INTO people (email, name, password, role) VALUES (:email, :name, :password, :role)", 
                {'email': email, 'name': name, 'password': generate_password_hash(password), 'role': role})

        connection.commit()
            
        flash("Your registration is successful! You can login now!", "success")

        # Redirect user to home page
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/student_register", methods=["GET", "POST"])
def student_register():

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("student_email"):
            flash("You must provide an email!", "danger")
            return redirect("/student_register")

        # Ensure password was submitted
        elif not request.form.get("student_first_name"):
            flash("You must provide your first name!", "danger")
            return redirect("/student_register")

        # Ensure password was submitted
        elif not request.form.get("student_password"):
            flash("You must provide a password!", "danger")
            return redirect("/student_register")

        elif not request.form.get("student_confirm_password"):
            flash("You must retype your password!", "danger")
            return redirect("/student_register")

        elif request.form.get("student_password") != request.form.get("student_confirm_password"):
            flash("Retype password doesn't match!", "danger")
            return redirect("/student_register")

        email = request.form.get("student_email")
        name = request.form.get("student_first_name") + " " + request.form.get("student_last_name") 
        password = request.form.get("student_password")
        role = "Student"

        cursor.execute("SELECT * FROM people WHERE email = :email", {'email': email})
        check = cursor.fetchall()
        print(check)

        #Check if the username has been taken
        if len(check) > 0:    
            flash("Sorry! This email has been registered before", "danger")
            return redirect("/student_register")
        else:
            cursor.execute("INSERT INTO people (email, name, password, role) VALUES (:email, :name, :password, :role)", 
                {'email': email, 'name': name, 'password': generate_password_hash(password), 'role': role})

        connection.commit()
            
        flash("Your registration is successful! You can login now!", "success")

        # Redirect user to home page
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    
    # Forget any user_id
    session.clear()
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted

        if not request.form.get("email"):
            flash("You must provide an email!", "danger")
            return render_template("login.html")

        if not request.form.get("email"):
            flash("You must provide your registered email", "danger")
            return render_template("login.html")
                    
        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("You must provide your password", "danger")
            return render_template("login.html")

        # Query database for username
        cursor.execute("SELECT * FROM people WHERE email = :email", {'email': request.form.get("email")})
        rows = cursor.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            flash("Invalid email and/or password!", "danger")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)



# Improvements:
# - page design (better template)
# - make the checbox and dropdown list automatically selected
# - create end time so that the time can be monitored dynamically 
#      - use end time to automatically move the upcoming to validate
#      - use end time to check for conflict scheduling (previous class end time should not clash with start time of another class)
# - delete database (cancelled calss, not-validated-class) needs to be revisited (maybe backup in another table) 
# - more filter (on date, day, time, teacher) - filter automatically once the dropdown list is selected
# - cannot select a date before now when scheduling
# - when the not null input is submitted and get flash warning message, the previous input needs to be saved and displayed automatically 
# - change password function 
# - conflict manageent (after teacher reschedule a class, students need to reconfirm if they still want it)
# - No enrollment after a certain period (e.g. 2 hours before the class start)


# Consider to add:
# - teacher + student in one account (can teach and also can learn) - now only one email can be used in the database, i.e. if sign up as a student, can't sign up as a teacher
# - more meaningful unique person id and class id (like 6 digits with alphabet instead of just random autoincrement)
# - email function 
#       - when the class is cancelled / updated
#       - communication between teacher and student
# - reminder when the class is nearing 
# - scheduling master like reoccurence (e.g. every wednesday)
# - student "request for a class" function 
# - upload images (profile picture)
# - link to online learning platform (zoom)
# - flexibility to choose location 
# - maximum enrollment
# - add another teacher as colloborator in one class
# - attendance "check all" function
# - report "no teacher" function
# - don't display all history in one page (split it to multiple pages)
# - split name - to revisit in case there is middle name
# - give teacher a star