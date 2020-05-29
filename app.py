from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from secrets import lst
import mysql.connector as mariadb
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

#Init 
app = Flask(__name__)

#config db 
print(lst)
mariadb_connection = mariadb.connect(user=lst['user'], password=lst['password'], database=lst['database'])

#Index
@app.route('/')
def index():
    return render_template('home.html')

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():  #if post request, register the user
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data)) #need to encrypt password before submitting

        #Create cursor
        cur = mariadb_connection.cursor(buffered=True)

        #Execute query
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s, %s, %s, %s)", (name, email, username,password))

        #Commit to DB
        mariadb_connection.commit()

        #Close the connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))

    return render_template('register.html', form=form) #pass the form into our template

#Login 
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        #Get Form Fields if login successful
        username = request.form['username']
        password_candidate = request.form['password']


    #create cursor
        cur = mariadb_connection.cursor(buffered=True)

    # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = '{}'".format(username))

        data = cur.fetchone()

        if data:
            password = data[4]
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('blogpost'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            #close the connection
            cur.close()

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


#Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized. Please login', 'danger') #error message
            return redirect(url_for('login'))
    return wrap

#Blogpost page 
@app.route('/blogpost')
@is_logged_in
def blogpost():
    #Create cursor
    cur = mariadb_connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()
    if articles:
        return render_template('blogpost.html', articles=articles) #have access to articles in the dashboard template
    else:
        msg = 'No Articles Found'
        return render_template('blogpost.html', msg=msg)
    #Close connection
    cur.close()



#Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

#Add Article
@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create cursor
        cur = mariadb_connection.cursor()

        #Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        #Commit to DB
        mariadb_connection.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('blogpost'))

    return render_template('add_article.html', form=form) #this renders the template even before checking for the POST

#Edit Article
@app.route('/edit_article/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    #Create cursor
    cur = mariadb_connection.cursor()

    #Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()

    #Get form
    form = ArticleForm(request.form)

    #Populate article form fields
    form.title.data = article[1]
    form.body.data = article[3]

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #Create cursor
        cur = mariadb_connection.cursor()

        #Execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title,body,id))

        #Commit to DB
        mariadb_connection.commit()

        #Close the connection
        cur.close()
        flash('Article Updated','success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)



#Delete Article
@app.route('/delete_article/<string:id>', methods=['POST']) #GET shouldnt be able to do anything here
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mariadb_connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mariadb_connection.commit()

    # Close the connection
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('blogpost'))


#Item Class 

class ItemFormClass(Form):
   
    item = TextAreaField('item', [validators.Length(min=5)])



#Add item in to-do list 
@app.route('/todo', methods=['GET','POST'])
def additem(): 
    form = ItemFormClass(request.form) 
    if request.method == 'POST' and form.validate():
        item = form.item.data
        
        #Create cursor
        cur = mariadb_connection.cursor()

        #Execute
        cur.execute("INSERT INTO todo(item, status) VALUES(%s, %s)", (item, 'Incomplete'))

        #Commit to DB
        mariadb_connection.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')
 
        return redirect(url_for('todo'))


    return render_template('additem.html',form=form)




#Todo
@app.route('/tasks')
@is_logged_in
def todo():
    #Create cursor
        cur = mariadb_connection.cursor()

        #Execute
        cur.execute("SELECT * FROM todo")

        data = cur.fetchall()
        
        #Close conn
        cur.close() 
        
        return render_template('tasks.html', data=data)


#Tasks page 
@app.route('/tasks')
@is_logged_in
def tasks():
    return render_template('tasks.html')


#Complete task 
@app.route('/update_tasks/<string:id>', methods=['POST'])
@is_logged_in
def update_tasks(id):
    #Create cursor
    cur = mariadb_connection.cursor()
    # Execute
    cur.execute("UPDATE todo SET status=%s WHERE id = %s", ('Completed',id))
        

    # Commit to DB
    mariadb_connection.commit()

    # Close the connection
    cur.close()

    flash('Tasks updated', 'success')
    return redirect(url_for('tasks'))





#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success') #success message
    return render_template('home.html')


if __name__ == '__main__':
    app.static_folder = 'static'
    app.secret_key = lst['secret_key']
    app.run(debug=True)


