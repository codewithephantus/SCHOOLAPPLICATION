# imports 
from flask import Flask, redirect, render_template, request, session, url_for
import pymysql 

# import the function for hashing 
import functions

# create a  new application 
app = Flask(__name__)

# below is the register route 
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
      return render_template("register.html")
    else:
       full_name = request.form["full_name"]
       email = request.form["email"]
       password = request.form["password"]
       phone = request.form["phone"]
       role = "student"

    #    establish connection to db 
       connection = pymysql.connect( host="localhost",password="", user="root", database="school_db")
       cursor=connection.cursor()

       sql = "INSERT INTO users (full_name, email, password, phone, role) VALUES (%s, %s, %s, %s, %s)"

    #    put the data into a tuple 
    data =(full_name, email, functions.hash_password_salt(password), phone, role)

    # using the cursor execute the query 
    cursor.execute(sql, data)

    # commit the changes to the database 
    connection.commit()

    # if successful render a message to the person who has registered 
    message = "user registration was successful"
    return render_template("register.html", message=message)


app.secret_key = "fhbcqhasbjfcncwasbhjZVcvwsdvcz"

@app.route("/login", methods=["POST", "GET"])
def login():
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

      #   print(user)

        if user:
            db_password = user[2]
            role = user[5]
            fullname = user[1]

            # verify the hashed password
            if functions.verify_password_salt(db_password, password):
                session["user_name"] = fullname
                session["user_role"] = role
                session["user_email"] = email
                session["user_id"] = user[0]

                # based on the role redirect a person to a given dashboard
                if role == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif role == "teacher":
                    return redirect(url_for("teacher_dashboard"))
                else:
                    return redirect(url_for("student_dashboard"))
            else:
                return render_template("login.html", message = "Incorrect Password")
        else:
            return render_template("login.html", message = "Email not found")
   


# route for the student dashboard 
@app.route("/student/dashboard")  
def student_dashboard():
   if session.get("user_role") == "student":
      return render_template("student_dashboard.html", user_name=session.get("user_name"))
   return redirect(url_for("login"))


# route for teacher dashboard
@app.route("/teacher_dashboard")
def teacher_dashboard():
   if session.get("user_role") == "teacher":
      return render_template("teacher_dashboard.html", user_name=session.get("user_name"))
   return redirect(url_for("login"))

# route for teacher dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
   if session.get("user_role") == "admin":

      # establish connection to db 
      connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
     
      cursor = connection.cursor()  
      cursor.execute("select user_id, full_name, email, phone, role from users")
      users = cursor.fetchall()

      return render_template("admin_dashboard.html", user_name=session.get("user_name"), users=users)
   return redirect(url_for("login"))


# route to edit users details 
@app.route("/admin/user/<int:user_id>/edit", methods=["GET"])
def edit_user(user_id):
    if session.get("user_role") == "admin":
        # establish connection to db 
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()

        cursor.execute("select user_id, full_name,email,phone,role from users where user_id=%s", (user_id,))
        user = cursor.fetchone()
        return render_template("edit_user.html", user=user)
    else:
        return redirect(url_for("login"))

# log out route 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

    
# run the app 
app.run(debug=True) 
