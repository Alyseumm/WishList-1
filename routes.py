from app import db
from forms import RegistrationForm, EditProfileForm, LoginForm, PostForm
from flask import render_template, flash, redirect, url_for, request, send_from_directory
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import app
from flask_login import current_user, login_user, logout_user, login_required
from models import User, Post
from datetime import datetime
import os


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Home Page', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Sign Up', form=form)


# ------------------------------------------------------------------


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'JPG'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/uploads/<username>/<filename>')
def uploaded_file(username, filename):
    dir = os.path.join(app.config['UPLOAD_FOLDER'], username)
    return send_from_directory(dir, filename)


@app.route('/uploads/<filename>')
def uploaded_file_default(filename):
    dir = app.config['UPLOAD_FOLDER']
    return send_from_directory(dir, filename)


# ------------------------------------------------------------------


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        form = PostForm()
        if request.method == 'POST':
            file = request.files['file']
            if form.validate_on_submit():
                if file and allowed_file(file.filename):
                    is_post = True
                    filename = secure_filename(file.filename)
                    dir = os.path.join(app.config['UPLOAD_FOLDER'], username)
                    if not os.path.isdir(dir):
                        os.mkdir(dir)
                    file.save(os.path.join(dir, filename))
                else:
                    is_post = False
                    filename = "default.png"
                post = Post(title=form.title.data, description=form.description.data,
                            filename=filename,
                            author=current_user, is_post=is_post, is_taken=False)
                db.session.add(post)
                db.session.commit()
                flash('Your post has been successfully added!')
                return redirect(url_for('user', username=current_user.username))
    page = request.args.get('page', 1, type=int)
    posts = user.own_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    if user == current_user:
        return render_template('user.html', user=user, form=form, posts=posts.items,
                               next_url=next_url, prev_url=prev_url, title=username)
    else:
        return render_template('user.html', user=user, posts=posts.items,
                               next_url=next_url, prev_url=prev_url, title=username)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/delete/<id>')
@login_required
def delete_post(id):
    post = Post.query.get(id)
    db.session.delete(post)
    db.session.commit()
    flash("Your post have been successfully deleted!")
    return redirect(url_for('user', username=current_user.username))


@app.route('/take/<id>')
@login_required
def take_item(id):
    post = Post.query.get(id)
    post.is_taken = True
    db.session.commit()
    flash("Wow, you've taken this gift!")
    return redirect(url_for('user', username=post.author.username))
