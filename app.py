from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
import math
import random
import os
from werkzeug.utils import secure_filename

# Load config
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "fallback-secret-key")
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'assets', 'img')
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URI")
db = SQLAlchemy(app)


# --------------------- MODELS ---------------------
class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.String(15), nullable=True)
    date = db.Column(db.String(10), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    email = db.Column(db.String(80), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), nullable=False)   # 🔥 Slug length increased
    title = db.Column(db.String(200), nullable=False)
    tagline = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    content = db.Column(db.String(10000), nullable=False)
    img = db.Column(db.String(80), nullable=False)


class About(db.Model):
    para_no = db.Column(db.Integer, primary_key=True)
    para = db.Column(db.String(500), nullable=False)


class Admin(db.Model):
    admin_username = db.Column(db.String(100), primary_key=True)
    admin_password = db.Column(db.String(100), nullable=False)


# Create tables if not exist
with app.app_context():
    db.create_all()


# --------------------- ROUTES ---------------------
@app.route('/')
def home():
    posts = Posts.query.all()
    posts.reverse()

    num_of_post = int(params['num_of_post'])
    total_posts = len(posts)
    last = math.ceil(total_posts / num_of_post)

    page = request.args.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1

    if page < 1:
        page = 1
    elif page > last:
        page = last

    start_idx = (page - 1) * num_of_post
    end_idx = start_idx + num_of_post
    paginated_posts = posts[start_idx:end_idx]

    prev = f"/?page={page - 1}" if page > 1 else "#"
    next = f"/?page={page + 1}" if page < last else "#"

    return render_template('index.html', params=params, posts=paginated_posts, prev=prev, next=next)


@app.route('/about')
def about():
    paragraphs = About.query.all()
    return render_template('about.html', params=params, paragraphs=paragraphs)


@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get('name')
        phone_num = request.form.get('phone_num')
        email = request.form.get('email')
        message = request.form.get('message')
        date = datetime.now().strftime("%Y-%m-%d")

        entry = Contact(name=name, phone_num=phone_num, email=email, message=message, date=date)
        db.session.add(entry)
        db.session.commit()
        return redirect('/contact')

    return render_template('contact.html', params=params)


@app.route('/login', methods=["GET", "POST"])
def login():
    admin = Admin.query.first()
    if 'user' in session and session['user'] == admin.admin_username:
        return redirect('/dashboard')

    if request.method == "POST":
        name = request.form.get('name')
        password = request.form.get('password')
        if name == admin.admin_username and password == admin.admin_password:
            session['user'] = name
            return redirect('/dashboard')
        else:
            return render_template('login.html', message="Invalid Username or Password")

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    admin = Admin.query.first()
    if 'user' in session and session['user'] == admin.admin_username:
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)
    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/login')


@app.route('/change_password', methods=["GET", "POST"])
def change_password():
    admin = Admin.query.first()
    if 'user' in session and session['user'] == admin.admin_username:
        if request.method == "POST":
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if current_password != admin.admin_password:
                return render_template('change_password.html', params=params, error="Current password is incorrect")
            if new_password != confirm_password:
                return render_template('change_password.html', params=params, error="New passwords do not match")

            admin.admin_password = new_password
            db.session.commit()
            return redirect('/dashboard')

        return render_template('change_password.html', params=params)
    return redirect('/login')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/edit/<string:sno>', methods=["GET", "POST"])
def edit(sno):
    admin = Admin.query.first()
    if 'user' in session and session['user'] == admin.admin_username:
        if request.method == "POST":
            edit_title = request.form.get('title') or ""
            base_slug = (request.form.get('slug') or "").strip()[:50]
            edit_slug = base_slug + "-" + str(random.randint(1000, 9999))
            edit_content = request.form.get('content') or ""
            edit_tagline = request.form.get('tagline') or ""

            post = Posts.query.filter_by(sno=sno).first() if sno != '0' else None
            old_image = post.img if post else None

            if 'img' in request.files and request.files['img'].filename != "":
                file = request.files['img']
                if file and allowed_file(file.filename):
                    filename = str(random.randint(1000, 9999)) + "_" + secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    if old_image:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)

                    edit_img = filename
                else:
                    return render_template('edit.html', params=params, sno=sno, post=post,
                                           message="Invalid image format!")
            else:
                edit_img = request.form.get('imgName') or old_image or "default.jpg"

            if not edit_title or not edit_content or not edit_slug:
                return render_template('edit.html', params=params, sno=sno, post=post, message="Please fill all details")

            if sno == '0':
                entry = Posts(
                    title=edit_title,
                    slug=edit_slug,
                    content=edit_content,
                    tagline=edit_tagline,
                    img=edit_img,
                    date=datetime.now().strftime("%Y-%m-%d")
                )
                db.session.add(entry)
            else:
                post.title = edit_title
                post.slug = edit_slug
                post.content = edit_content
                post.tagline = edit_tagline
                post.img = edit_img

            db.session.commit()
            return redirect('/dashboard')

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, sno=sno, post=post)

    return redirect('/login')


@app.route('/add_post')
def add_post():
    admin = Admin.query.first()
    if 'user' in session and session['user'] == admin.admin_username:
        return redirect('/edit/0')
    return redirect('/login')


@app.route('/delete/<string:sno>', methods=["GET", "POST"])
def delete_post(sno):
    admin = Admin.query.first()
    if 'user' in session and session['user'] == admin.admin_username:
        post = Posts.query.filter_by(sno=sno).first()
        if post:
            if post.img:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], post.img)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            db.session.delete(post)
            db.session.commit()
        return redirect('/dashboard')
    return redirect('/login')


@app.route("/dashboard/about", methods=["GET", "POST"])
def admin_about():
    admin = Admin.query.first()
    if 'user' in session and session['user'] == admin.admin_username:
        if request.method == "POST":
            para_no = request.form.get("para_no")
            para = request.form.get("para")

            par = About.query.filter_by(para_no=para_no).first()
            if par:
                par.para = para
            else:
                new_para = About(para_no=para_no, para=para)
                db.session.add(new_para)

            db.session.commit()
            return redirect("/dashboard")

        paragraphs = About.query.order_by(About.para_no).all()
        return render_template("admin_about.html", paragraphs=paragraphs, params=params)

    return redirect("/login")


@app.route("/delete_about/<int:para_no>", methods=["GET"])
def delete_about(para_no):
    admin = Admin.query.first()
    if 'user' in session and session['user'] == admin.admin_username:
        para = About.query.filter_by(para_no=para_no).first()
        if para:
            db.session.delete(para)
            db.session.commit()
        return redirect("/dashboard")
    return redirect("/login")


@app.route('/post/<string:post_slug>', methods=["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)


if __name__ == "__main__":
    app.run(debug=False)
