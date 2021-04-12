from flask  import Flask,render_template,flash,redirect,session,url_for,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,TextAreaField,StringField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.secret_key = "BLOG"
# flask-nan mysql-in elaqe qururluwu(configuration)
app.config["MYSQL_HOST"] = 'Localhost'
app.config["MYSQL_USER"] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config["MYSQL_DB"] = 'BLOG'
app.config["MYSQL_CURSORCLASS"] ='DictCursor'

mysql = MySQL(app)

#loggin decartator == girise gore control panelin idare edirik
def login_required(f):

    @wraps(f)
    def decorated_function( *args,**kwargs):

        if "loggin" in session:
    
           return f(*args, **kwargs)
        else:
            flash("bu addrese getmel ucun giris edin... ", "danger")
            return  redirect(url_for("login"))   
        
        
    return decorated_function


class MYform(Form): 
    # MYform adli class  yaradiram ve bu classim Form -dan inherinince edirem.

    name = StringField("AD SOYAD:",validators=[validators.length(min=5, max=20),
        validators.DataRequired(message= "YENI AD")])

    username = StringField("Istifadeci Adi:",validators=[validators.length(min=7, max= 25),
        validators.DataRequired(message= "YENI isdifadeci adi:")])

    email = StringField("Email:", validators=[validators.Email(message="dogru emil deyil")])

    password = PasswordField('Password:',validators=[validators.DataRequired("doldurun"),
        validators.EqualTo(fieldname='confirm',message= 'parollar eyni deyil')])

    confirm = PasswordField('Password dogrulama:' )

#register template == Qeydiyyatdan kecme funksiyasi
@app.route('/register', methods= ['GET','POST'])
def register():
    myform = MYform(request.form) #request form bu cllasin icine gonderib her defe yeniliyirem . 
    if request.method=='POST' and myform.validate():

        name = myform.name.data
        username = myform.username.data
        email = myform.email.data
        password = sha256_crypt.encrypt(myform.password.data)

        cursor = mysql.connection.cursor()
        query = "INSERT INTO users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(query, (name, username, email, password))
      
        mysql.connection.commit()
        cursor.close()

        flash("tebrikler, bir oturum acdiniz...","warning")
        return redirect(url_for("login"))
    
    else:
        return render_template("register.html", form = myform)



# logir formu 
class loginForm(Form):

    username = StringField("Isdifadeci Adi: ")
    password_entered = PasswordField("Password: ")


#login template 
@app.route("/login", methods=["GET", "POST"])
def login():

    lgform = loginForm(request.form)

    if request.method == "POST":

        username = lgform.username.data
        password_get = lgform.password_entered.data

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM users WHERE username=%s"

        result = cursor.execute(query, (username,))

        if result>0:

            data = cursor.fetchone()
            password_real = data["password"]

            if  sha256_crypt.verify(password_get, password_real):
                flash('Ugurla giris etdiniz..','success')
                session["loggin"] = True
                session["username"] = username


                return redirect(url_for("index"))
            else:
                flash("username ve passworddan birri yalniwdir", "danger") 
                return redirect(url_for("login"))   


        else:
            flash("bele bir isdifadeci yoxdur..","danger")
            return redirect(url_for('login'))
    else:    
        return render_template("login.html", form = lgform)

#logout tamplate
@app.route("/logout")
def logout():
    session.clear()

    flash('ugurla cixis etdiniz.. ', 'info')
    return redirect(url_for('index'))

#article template
@app.route("/article")
def article():

    cursor = mysql.connection.cursor()
    query = "SELECT * FROM article"
    result = cursor.execute(query)

    if result>0:
        articles = cursor.fetchall()
        return render_template('article.html', articles = articles)

    else:
        return render_template('article.html')

#dashboard template
@app.route("/dashboard")
@login_required
def dashboard():

    cursor = mysql.connection.cursor()
    query = "select * FROM article WHERE author=%s"
    result = cursor.execute(query,(session["username"], ))

    if result>0:
        myarticle = cursor.fetchall()
        return render_template("dashboard.html", articles= myarticle)
    else:
        return render_template("dashboard.html") 

#addaricle tempalte
@app.route("/addarticle", methods = ['GET', 'POST'])
def addaricle():

    form  = addartForm(request.form)
    if request.method == 'POST'  and form.validate():

        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        query = "INSERT INTO article(title, author, content) VALUES(%s, %s, %s)"
        cursor.execute(query, (title,session["username"], content))

        mysql.connection.commit()
        cursor.close()

        flash('ugurla bir article yaratdiniz..', 'success')
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form = form)       

# Article form template
class addartForm(Form):
    title = StringField("Basliq", validators=[validators.length(min=5, max=55)])
    content = TextAreaField("Mezmun", validators=[ validators.DataRequired("mutleq doldur..")])

#open template
@app.route("/open/<string:id>")
def open(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM article where id = %s"
   
    result = cursor.execute(query, (id, ))

    if result>0:

        data = cursor.fetchone()
        return render_template("open.html", data = data) 

    return render_template("open.html") 


#delete template
@app.route("/delete/<string:id>")
@login_required
def delete(id):

    cursor = mysql.connection.cursor()
    query = "SELECT * FROM article WHERE author = %s and id = %s"

    result = cursor.execute(query, (session["username"], id))

    if result>0:
        cursor2 = mysql.connection.cursor()
        query2 = "DELETE FROM article WHERE id = %s"

        cursor2.execute(query2, (id, ))
        mysql.connection.commit()
        flash("ugurla  silindi..","success")

        return redirect(url_for("dashboard"))
    else:
        flash("ya girs etmediniz yada bu maqale adresi size aid deyi..", "danger")
        return redirect(url_for("index"))    

# Update template == meqalledeki deyiwiklikler..
@app.route("/edit/<string:id>", methods = ["GET", "POST"])
@login_required
def edit(id):

    
    if request.method =="GET":

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM  article WHERE id=%s AND author=%s"
        result = cursor.execute(query, (id, session["username"]))

        if result== 0:

            flash("bu meqale siz aid deyil yada bele meqale yoxdur..","danger" )
            return redirect(url_for("index"))

        else:
            form = addartForm()
     
            info = cursor.fetchone()
            form.title.data = info['title']
            form.content.data = info["content"] 

            return render_template("edit.html", form = form )
    # post rerquest 
    else:
        form = addartForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        cursor = mysql.connection.cursor()
        query2 = "UPDATE article SET title=%s, content= %s WHERE id=%s"
        
        cursor.execute(query2, (newTitle, newContent, id))
        mysql.connection.commit()

        flash("ugurla meqaleniz update edildi..", "success")


        return redirect(url_for("dashboard"))

#search template (article into)         
@app.route("/search", methods = [ "GET", "POST"])
def search():
   
    if request.method == "GET":

        return render_template("index.html")

    #post request
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        query = "select * from article where  title like '%"+ keyword +"%' "
        result = cursor.execute(query)

        if result == 0:

            flash("bele bir meqale yoxdur..","warning")
            return redirect(url_for("article"))

        else:

            data=cursor.fetchall()
            return render_template("article.html",articles =data)

@app.route('/')
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")  

if __name__ == "__main__":
    app.run(debug = True)

