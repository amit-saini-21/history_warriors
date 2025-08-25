from flask import Flask,render_template,request,redirect,session
from flask_sqlalchemy import SQLAlchemy
import json
from  datetime import datetime
import math
import random
import os
from werkzeug.utils import secure_filename
#variable for flask app
with open('config.json','r') as c:
    params=json.load(c)["params"]

app=Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "fallback-secret-key")
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'assets', 'img') 
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}




#app.config['SQLALCHEMY_DATABASE_URI']=local_server

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URI")
db=SQLAlchemy(app)

#class  for databse contact
class Contact(db.Model):
    sno=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30),nullable=False)
    phone_num=db.Column(db.String(15),nullable=True)
    date=db.Column(db.String(10),nullable=False)
    message=db.Column(db.String(300),nullable=False)
    email=db.Column(db.String(80),nullable=False)

#class for database posts
class Posts(db.Model):
    sno=db.Column(db.Integer,primary_key=True)
    slug=db.Column(db.String(20),nullable=False)
    title=db.Column(db.String(200),nullable=False)
    tagline=db.Column(db.String(200),nullable=False)
    date=db.Column(db.String(10),nullable=False)
    content=db.Column(db.String(5000),nullable=False)
    img=db.Column(db.String(40),nullable=False)
#class for about database
class About(db.Model):
    para_no=db.Column(db.Integer,primary_key=True)
    para=db.Column(db.String(500),nullable=False)

class Admin(db.Model):
    admin_username=db.Column(db.String(100),primary_key=True)
    admin_password=db.Column(db.String(100),nullable=False)
# end point for home page
@app.route('/')
def home():
    posts = Posts.query.all()  # Fetch all posts
    posts.reverse()  # Latest post first

    num_of_post = int(params['num_of_post'])  # Number of posts per page
    total_posts = len(posts)  # Total number of posts
    last = math.ceil(total_posts / num_of_post)  # Calculate last page number

    # Get current page from URL
    page = request.args.get('page', 1)  # Default to page 1 if no page param
    try:
        page = int(page)  # Convert to integer
    except ValueError:
        page = 1  # If invalid, set to first page

    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > last:
        page = last

    # Calculate start and end indexes
    start_idx = (page - 1) * num_of_post
    end_idx = start_idx + num_of_post
    paginated_posts = posts[start_idx:end_idx]  # Slice posts for current page

    # Previous and Next page logic
    prev = f"/?page={page - 1}" if page > 1 else "#"
    next = f"/?page={page + 1}" if page < last else "#"

    return render_template('index.html', params=params, posts=paginated_posts, prev=prev, next=next)

#end point for about page
@app.route('/about')
def about():
    paragraphs=About.query.all()
    return render_template('about.html',params=params,paragraphs=paragraphs)

#end point to edit about
@app.route('/edit_about')
def edit_about():
    return render_template('about.html',params=params)

#end point for contact page
@app.route('/contact',methods=["GET","POST"])
def contact():
    if request.method=="POST":
        name=request.form.get('name')
        phone_num=request.form.get('phone_num')
        email=request.form.get('email')
        message=request.form.get('message')
        date=datetime.now()
        entry=Contact(name=name,phone_num=phone_num,email=email,message=message,date=date)
        db.session.add(entry)
        db.session.commit()
        return  redirect('/contact')
   
    return render_template('contact.html',params=params)
#end point for login page
@app.route('/login',methods=["GET","POST"])
def login():
    admin=Admin.query.filter_by().first()
    if 'user' in session and session['user']==admin.admin_username:
        return redirect('/dashboard')
    if request.method=="POST":
        name=request.form.get('name')
        password=request.form.get('password')
        if name == admin.admin_username and password == admin.admin_password:
            session['user']=name
            #post featch
            return redirect('/dashboard')
        else:
            return render_template('login.html',message="Invalid Username or Password")

    return render_template('login.html')

#end point for dashboard page
@app.route('/dashboard')
def dashboard():
    admin=Admin.query.filter_by().first()
    if 'user' in session and session['user'] == admin.admin_username:
        posts=Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)
    else:
        return redirect('/login')
    
#end point for logout
@app.route('/logout')
def logout():
        session.pop('user')
        return redirect('/login')

#change Password
@app.route('/change_password', methods=["GET", "POST"])
def change_password():
    admin=Admin.query.filter_by().first()
    if 'user' in session and session['user'] ==admin.admin_username :
        if request.method == "POST":
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if current_password != admin.admin_password:
                return render_template('change_password.html', params=params, error="Current password is incorrect")
            if new_password != confirm_password:
                return render_template('change_password.html', params=params, error="New passwords do not match")
            
            admin.admin_password=new_password
            db.session.commit()
           # params['admin_password'] = new_password  # Update the in-memory params
            return redirect('/dashboard')
        return render_template('change_password.html', params=params)
    return redirect('/login')

def allowed_file(filename):
    """Check if uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/edit/<string:sno>', methods=["GET", "POST"])
def edit(sno):
    admin=Admin.query.filter_by().first()
    if 'user' in session and session['user'] == admin.admin_username:
        if request.method == "POST":
            edit_title = request.form.get('title')
            edit_slug = request.form.get('slug') + str(random.randint(1000, 9999))
            edit_content = request.form.get('content')
            edit_tagline = request.form.get('tagline')

            post = Posts.query.filter_by(sno=sno).first() if sno != '0' else None
            old_image = post.img if post else None  # Store old image name

            # Handle file upload
            if 'img' in request.files and request.files['img'].filename != "":
                file = request.files['img']
                if file and allowed_file(file.filename):
                    # Generate unique filename
                    filename = str(random.randint(1000, 9999)) + "_" + secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)  # Save new image

                    # Delete old image if it exists
                    if old_image:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)

                    edit_img = filename  # Update image name for database
                else:
                    return render_template('edit.html', params=params, sno=sno, post=post, message="Invalid image format!")
            else:
                edit_img = request.form.get('imgName')  # Keep old image if no new one uploaded

            # Validate required fields
            if edit_title == "" or edit_content == "" or edit_slug == "":
                return render_template('edit.html', params=params, sno=sno, post=post, message="Please fill all details")

            if sno == '0':  # New post
                entry = Posts(title=edit_title, slug=edit_slug, content=edit_content, tagline=edit_tagline, img=edit_img, date=datetime.now())
                db.session.add(entry)
            else:  # Edit existing post
                post.title = edit_title
                post.slug = edit_slug
                post.content = edit_content
                post.tagline = edit_tagline
                post.img = edit_img  # Update image

            db.session.commit()
            return redirect('/dashboard')

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, sno=sno, post=post)

    return redirect('/login')
#add a new post
@app.route('/add_post')
def add_post():
    admin=Admin.query.filter_by().first()
    if 'user' in session and session['user'] == admin.admin_username:
        return redirect('/edit/0')
    return redirect('/login')
#deleta a post
@app.route('/delete/<string:sno>',methods=["GET","POST"])
def delete_post(sno):
    admin=Admin.query.filter_by().first()
    if 'user' in session and session['user'] ==admin.admin_username :
             post=Posts.query.filter_by(sno=sno).first()
             if post:
                if post.img:  # Database me image ka naam stored hai
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], post.img)
                    if os.path.exists(old_image_path):
                      os.remove(old_image_path)
                db.session.delete(post)
                db.session.commit()
             return redirect('/dashboard')
    return redirect('/login')
#edit about paargraphs
@app.route("/dashboard/about", methods=["GET", "POST"])
def admin_about():
    admin=Admin.query.filter_by().first()
    if 'user' in session and session['user'] ==admin.admin_username:
        if request.method == "POST":
            para_no = request.form.get("para_no")
            para = request.form.get("para")
            
            # Check if paragraph already exists (Update case)
            par = About.query.filter_by(para_no=para_no).first()
            if par:
                par.para = para  # Update content
            else:
                new_para = About(para_no=para_no, para=para)  # Add new paragraph
                db.session.add(new_para)

            db.session.commit()
            return redirect("/dashboard")

        # Fetch all paragraphs from the database
        paragraphs = About.query.order_by(About.para_no).all()
        return render_template("admin_about.html", paragraphs=paragraphs,params=params)
    
    return redirect("/login")
#delete a paragraphs
@app.route("/delete_about/<int:para_no>", methods=["GET"])
def delete_about(para_no):
    admin=Admin.query.filter_by().first()
    if 'user' in session and session['user'] ==admin.admin_username:
        para = About.query.filter_by(para_no=para_no).first()
        if para:
            db.session.delete(para)
            db.session.commit()
        return redirect("/dashboard")
    return redirect("/login")
#This is to show post after click on a particular post
@app.route('/post/<string:post_slug>', methods=["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)

if __name__=="__main__":
    app.run(debug=False)

