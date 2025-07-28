# imports 
from flask import *
import pymysql

# import the functions for hashing passwords and verifying the same
import functions


# create a new application based on flask
app = Flask(__name__)
app.secret_key = "fhbcqhasbjfcncwasbhjZVcvwsdvcz"
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


# logs 
def log_to_db(level, message, user_id, endpoint=None):
    try:
        connection = pymysql.connect(host='localhost', user='root', password='', database='school_db')
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO logs (log_level, log_message, endpoint, user_id) VALUES (%s, %s, %s, %s)',
            (level, message, endpoint, user_id)
        )
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"MySQL logging failed: {e}")


# below is the register route
@app.route("/register", methods=["GET", "POST"])
def register():
    log_to_db("INFO", "Accessed register route", session.get("user_id"), "/register")
    if request.method == "GET":
        return render_template("register.html")
    else:
        full_name = request.form["full_name"]
        email = request.form['email']
        phone = request.form["phone"]
        password = request.form['password']
        role = "student"

        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        # create a cursor that enables you to execute sql
        cursor = connection.cursor()

        # structure the sql query for insert
        sql = "INSERT INTO users(full_name, email, phone, password, role) values(%s, %s, %s, %s, %s)"


        # put the data into a tuple
        data = (full_name, email, phone, functions.hash_password_salt(password), role)

        # by use of the cursor, execute the query
        cursor.execute(sql, data)

        # commit the changes into the db
        connection.commit()

        message = "User registered successfully"
        log_to_db("INFO", "User registered", None, "/register")
        # if successful render a message back to the person who has registered
        return render_template("register.html", message = message)



@app.route("/login", methods=["POST", "GET"])
def login():
    log_to_db("INFO", "Accessed login route", session.get("user_id"), "/login")
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form["email"]
        password = request.form["password"]

         # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        # create a cursor that enables you to execute sql
        cursor = connection.cursor()

        # structure a query for login
        sql = "select * from users where email=%s"

        # use the cursor to execute the sql
        cursor.execute(sql, (email,))

        # if the details are correct, put them into a users variable
        user = cursor.fetchone()

        # print(user) 

        if user:
            db_password = user[2]
            role = user[5]
            full_name = user[1]

            # verify the hashed password
            if functions.verify_password_salt(db_password, password):
                session["user_name"] = full_name
                session["user_role"] = role
                session["user_id"] = user[0]
                session["user_email"] = email

                # based on the role redirect a person to a given dashboard
                log_to_db("INFO", f"User {email} logged in as {role}", user[0], "/login")
                if role == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif role == "teacher":
                    return redirect(url_for("teacher_dashboard"))
                else:
                    return redirect(url_for("student_dashboard"))
            else: 
                log_to_db("WARNING", f"Incorrect password for {email}", None, "/login")
                return render_template("login.html", message = "Incorrect Password")
        else:
            log_to_db("WARNING", f"Email not found: {email}", None, "/login")
            return render_template("login.html", message = "Email not found")

        
    
# route for the student dashboard
@app.route("/student/dashboard")
def student_dashboard():
    log_to_db("INFO", "Accessed student dashboard", session.get("user_id"), "/student/dashboard")
    if session.get("user_role") == "student":
        return render_template("student_dashboard.html", name= session.get("user_name"))
    return redirect(url_for("login"))

# student to view assignments
@app.route('/student/assignments')
def student_assignments():
    log_to_db("INFO", "Accessed student assignments", session.get("user_id"), "/student/assignments")
    if session.get("user_role") == "student":
        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        # Get assignments for the logged-in student
        cursor.execute("SELECT * FROM assignments")
        assignments = cursor.fetchall()

            # get the current STUDENT id
    cursor.execute("select user_id from users where email=%s", (session.get("user_email"),))
    student = cursor.fetchone()

    if not student:
        return "Student not Found"
    
    student_id = student[0]

    # Fetch assignments for the student (example: all assignments, or filter as needed)
    cursor.execute("SELECT * FROM assignments ORDER BY posted_at DESC")
    assignments = cursor.fetchall()

    return render_template("student_dashboard.html", name=session.get("user_name"), assignments=assignments)


    #     return render_template("student_dashboard.html", name=session.get("user_name"), assignments=assignments)

    # return redirect(url_for("login"))



# route for a teacher dashboard
@app.route("/teacher/dashboard")
def teacher_dashboard():
    log_to_db("INFO", "Accessed teacher dashboard", session.get("user_id"), "/teacher/dashboard")
    if session.get("user_role") != "teacher":
        return redirect(url_for('login'))
    # establish a connection to the db
    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

    cursor = connection.cursor()

    # get the current teacher id
    cursor.execute("select user_id from users where email=%s", (session.get("user_email"),))
    teacher = cursor.fetchone()

    if not teacher:
        return "Teacher not Found"
    
    teacher_id = teacher[0]

    cursor.execute("select title, description, due_date, posted_at from assignments where teacher_id = %s order by posted_at DESC", (teacher_id,))

    assignments = cursor.fetchall()

    return render_template("teacher_dashboard.html", name=session.get("user_name"), assignments = assignments)
    


# route to the admin dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("user_role") == "admin":
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        cursor.execute("select user_id, full_name, email, phone, role from users")
        users = cursor.fetchall()
        cursor.execute("SELECT * FROM logs ORDER BY log_time DESC")
        logs = cursor.fetchall()
        return render_template("admin_dashboard.html", name=session.get("user_name"), users=users, logs=logs)
    return redirect(url_for("login"))

# route to view all users
@app.route("/admin/users")  
def view_users():
    log_to_db("INFO", "Accessed view users route", session.get("user_id"), "/admin/users")
    if session.get("user_role") == "admin":
        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()
        cursor.execute("select user_id, full_name, email, phone, role from users")
        users = cursor.fetchall()
        return render_template("view_users.html", users=users)
    return redirect(url_for("login"))

# route to view logs 
@app.route("/admin/logs")
def view_logs():
    log_to_db("INFO", "Accessed view logs route", session.get("user_id"), "/admin/logs")
    if session.get("user_role") == "admin":
        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM logs")
        logs = cursor.fetchall()
        return render_template("logs.html", logs=logs)
    return redirect(url_for("login"))

# route to edit the details of a user
@app.route("/admin/user/<int:user_id>/edit", methods=["GET"])
def edit_user(user_id):
    log_to_db("INFO", f"Accessed edit user {user_id}", session.get("user_id"), f"/admin/user/{user_id}/edit")
    if session.get("user_role") == "admin":
        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()
        cursor.execute("select user_id, full_name, email, phone, role from users where user_id = %s", (user_id, ))
        user = cursor.fetchone()
        return render_template("edit_user.html", user = user)
    return redirect(url_for("login"))

# route to update the user details
@app.route("/admin/user/<int:user_id>/update", methods=["POST"])
def update_user(user_id):
    log_to_db("INFO", f"Updated user {user_id}", session.get("user_id"), f"/admin/user/{user_id}/update")
    if session.get("user_role") == "admin":
        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        role = request.form["role"]
         # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()

        sql = "update users set full_name=%s, email=%s, phone=%s, role=%s where user_id=%s"
        data = (full_name, email, phone, role, user_id)

        cursor.execute(sql, data)
        connection.commit()

        return redirect(url_for('admin_dashboard'))
    return redirect(url_for("login"))

# route to delete a user
@app.route("/admin/user/<int:user_id>/delete")
def delete_user(user_id):
    log_to_db("INFO", f"Deleted user {user_id}", session.get("user_id"), f"/admin/user/{user_id}/delete")
    if session.get("user_role") == "admin":
        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        sql = "delete from users where user_id=%s"
        cursor.execute(sql, (user_id,))
        connection.commit()
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for("login"))

# create an assignment route
@app.route("/teacher/assignments/create", methods=["GET", "POST"])
def create_assignment():
    log_to_db("INFO", "Accessed create assignment route", session.get("user_id"), "/teacher/assignments/create")
    if session.get("user_role") != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]

        # Get teacher ID from session (assuming you store user_id after login)
        teacher_email = session.get("user_email")

        # Connect to DB to fetch teacher ID
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email=%s", (teacher_email,))
        teacher = cursor.fetchone()

        # print(teacher) 

        if teacher:
            teacher_id = teacher[0]

            sql = "INSERT INTO assignments (title, description, due_date, teacher_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (title, description, due_date, teacher_id))
            connection.commit()
            log_to_db("INFO", f"Assignment created by teacher {teacher_id}", teacher_id, "/teacher/assignments/create")
            return redirect(url_for("teacher_dashboard"))
        else:
            log_to_db("ERROR", "Teacher not found during assignment creation", None, "/teacher/assignments/create")
            return "Teacher not found"

    return render_template("create_assignment.html")


# logs
@app.route("/logs")
def logs():
    log_to_db("INFO", "Accessed logs route", session.get("user_id"), "/logs")
    if session.get("user_role") != "admin":
        return redirect(url_for("login"))

    # establish a connection to the db
    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM logs")
    logs = cursor.fetchall()

    return render_template("logs.html", logs=logs)


# delete logs     
@app.route("/admin/log/<int:log_id>/delete")
def delete_log(log_id):
    if session.get("user_role") == "admin":
        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        sql = "delete from logs where log_id=%s"
        cursor.execute(sql, (log_id,))
        connection.commit()
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for("login"))


# logout Route
@app.route("/logout")
def logout():
    log_to_db("INFO", "User logged out", session.get("user_id"), "/logout")
    session.clear()
    return redirect(url_for("login"))


# run the application on a server
app.run(debug=True)