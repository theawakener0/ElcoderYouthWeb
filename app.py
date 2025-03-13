from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail, Message
import os
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

# Make sure the uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics'), exist_ok=True)

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ahmedkhaledahmed009@gmail.com'  # Replace with email
app.config['MAIL_PASSWORD'] = 'gvxz qyys opgk zbry'    # Replace with app password
app.config['MAIL_DEFAULT_SENDER'] = 'ahmedkhaledahmed009@gmail.com'  # Replace with email

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Add profile picture column to User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(200), default='default_profile.jpg')
    bio = db.Column(db.Text)
    posts = db.relationship('Post', backref='author', lazy=True)
    news_items = db.relationship('News', backref='author', lazy=True)
    workshops = db.relationship('Workshop', backref='instructor', lazy=True)
    # Remove this line as it conflicts with the relationship defined in WorkshopRegistration
    # registered_workshops = db.relationship('WorkshopRegistration', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('PostLike', backref='post', lazy=True, cascade='all, delete-orphan')
    thumbnail = db.Column(db.String(200))

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    date_liked = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Add this to your models section
class WorkshopRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshop.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    # Remove or comment out the attendance_status column
    # attendance_status = db.Column(db.String(20), default='registered')
    
    user = db.relationship('User', backref=db.backref('workshop_registrations', lazy=True))
    workshop = db.relationship('Workshop', backref=db.backref('registrations', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'workshop_id', name='unique_registration'),)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(200), nullable=False)
    pdf_url = db.Column(db.String(200), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50))

class Workshop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer)  # Duration in minutes
    location = db.Column(db.String(200))
    max_participants = db.Column(db.Integer)
    current_participants = db.Column(db.Integer, default=0)  # Make sure this field exists
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registration_open = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    news_items = News.query.order_by(News.date_posted.desc()).limit(3).all()
    upcoming_workshops = Workshop.query.filter(
        Workshop.date > datetime.utcnow(),
        Workshop.registration_open == True
    ).order_by(Workshop.date).limit(3).all()
    return render_template('home.html', posts=posts, news_items=news_items, upcoming_workshops=upcoming_workshops)

@app.route('/blog')
def blog():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('blog.html', posts=posts)

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            position = request.form.get('position')
            experience = request.form.get('experience')
            skills = request.form.get('skills')
            portfolio = request.form.get('portfolio')
            motivation = request.form.get('motivation')
            
            # Handle resume file upload
            resume = request.files.get('resume')
            resume_filename = None
            if resume:
                resume_filename = secure_filename(resume.filename)
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
                resume.save(resume_path)
            
            # Create email message
            msg = Message(
                'New Job Application - {position}',
                recipients=['ahmedkhaledahmed009@gmail.com']  # Admin email
            )
            
            # Format email body with HTML
            msg.html = f"""
            <h2>New Job Application Received</h2>
            <h3>Personal Information</h3>
            <ul>
                <li><strong>Name:</strong> {first_name} {last_name}</li>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Phone:</strong> {phone}</li>
            </ul>
            
            <h3>Professional Details</h3>
            <ul>
                <li><strong>Position:</strong> {position}</li>
                <li><strong>Years of Experience:</strong> {experience}</li>
                <li><strong>Skills:</strong> {skills}</li>
                <li><strong>Portfolio:</strong> <a href="{portfolio}">{portfolio}</a></li>
            </ul>
            
            <h3>Motivation</h3>
            <p>{motivation}</p>
            """
            
            # Add plain text alternative
            msg.body = f"""New application received:
            
Personal Information:
- Name: {first_name} {last_name}
- Email: {email}
- Phone: {phone}

Professional Details:
- Position: {position}
- Years of Experience: {experience}
- Skills: {skills}
- Portfolio: {portfolio}

Motivation:
{motivation}
            """
            
            # Attach resume if provided
            if resume_filename:
                with app.open_resource(os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)) as fp:
                    msg.attach(
                        resume_filename,
                        'application/octet-stream',
                        fp.read()
                    )
            
            # Send email
            mail.send(msg)
            
            flash('Your application has been submitted successfully! We will contact you soon.', 'success')
            return redirect(url_for('home'))
            
        except Exception as e:
            app.logger.error(f'Application submission error: {str(e)}')
            flash('An error occurred while submitting your application. Please try again.', 'error')
            return redirect(url_for('apply'))
            
    return render_template('apply.html')

@app.route('/news')
def news():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    
    # Query with category filter if provided
    if category:
        news_items = News.query.filter_by(category=category).order_by(News.date_posted.desc()).paginate(page=page, per_page=5)
    else:
        news_items = News.query.order_by(News.date_posted.desc()).paginate(page=page, per_page=5)
    
    # Get total count
    total_news_count = News.query.count()
    
    # Get category counts
    category_list = ['Announcement', 'Event', 'Update', 'Community', 'Tutorial']
    categories = []
    
    for cat in category_list:
        count = News.query.filter_by(category=cat).count()
        categories.append({'name': cat, 'count': count})
    
    return render_template('news.html', 
                          news_items=news_items, 
                          total_news_count=total_news_count,
                          categories=categories)

@app.route('/news/create', methods=['GET', 'POST'])
@login_required
def create_news():
    if not current_user.is_admin:
        flash('Only administrators can create news items.')
        return redirect(url_for('news'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        image_url = request.form.get('image_url')
        news_item = News(title=title, content=content, category=category,
                        image_url=image_url, author=current_user)
        db.session.add(news_item)
        db.session.commit()
        flash('News item has been created!')
        return redirect(url_for('news'))
    return render_template('create_news.html')

@app.route('/workshop')
def workshop():
    page = request.args.get('page', 1, type=int)
    upcoming = Workshop.query.filter(
        Workshop.date > datetime.utcnow()
    ).order_by(Workshop.date).paginate(page=page, per_page=10)
    past = Workshop.query.filter(
        Workshop.date <= datetime.utcnow()
    ).order_by(Workshop.date.desc()).paginate(page=page, per_page=10)
    return render_template('workshop.html', upcoming=upcoming, past=past)

@app.route('/manage_workshops')
@login_required
def manage_workshops():
    if not current_user.is_admin:
        flash('Only administrators can manage workshops.')
        return redirect(url_for('workshop'))
    page = request.args.get('page', 1, type=int)
    workshops = Workshop.query.order_by(Workshop.date.desc()).paginate(page=page, per_page=10)
    return render_template('manage_workshops.html', workshops=workshops)

@app.route('/workshop/create', methods=['GET', 'POST'])
@login_required
def create_workshop():
    if not current_user.is_admin:
        flash('Only administrators can create workshops.')
        return redirect(url_for('workshop'))
    if request.method == 'POST':
        workshop = Workshop(
            title=request.form['title'],
            description=request.form['description'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M'),
            duration=int(request.form['duration']),
            location=request.form['location'],
            max_participants=int(request.form['max_participants']),
            instructor=current_user
        )
        db.session.add(workshop)
        db.session.commit()
        flash('Workshop has been created!')
        return redirect(url_for('workshop'))
    return render_template('create_workshop.html')



ADMIN_CODE = 'your-secret-admin-code'  # In production, use environment variables

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        is_admin = 'is_admin' in request.form
        admin_code = request.form.get('admin_code')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        if is_admin and admin_code != ADMIN_CODE:
            flash('Invalid admin code')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email, phone=phone, address=address, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/library')
def library():
    books = Book.query.order_by(Book.date_added.desc()).all()
    return render_template('library.html', books=books)

@app.route('/post/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # Handle thumbnail upload
        thumbnail = None
        if 'thumbnail' in request.files and request.files['thumbnail'].filename:
            file = request.files['thumbnail']
            # Generate a secure filename
            filename = secure_filename(file.filename)
            # Add timestamp to ensure uniqueness
            filename = f"{int(time.time())}_{filename}"
            # Save the file
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            thumbnail = filename
        
        post = Post(title=title, content=content, author=current_user, thumbnail=thumbnail)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('blog'))
    return render_template('create_post.html')


# Add Comment model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    user = db.relationship('User', backref='comments')


# Add search route
@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html', results=None, query=None)
    
    # Search in posts
    posts = Post.query.filter(Post.title.contains(query) | Post.content.contains(query)).all()
    
    # Search in news
    news = News.query.filter(News.title.contains(query) | News.content.contains(query)).all()
    
    # Search in workshops
    workshops = Workshop.query.filter(
        Workshop.title.contains(query) | Workshop.description.contains(query)
    ).all()
    
    # Search in books
    books = Book.query.filter(
        Book.title.contains(query) | Book.author.contains(query) | Book.description.contains(query)
    ).all()
    
    results = {
        'posts': posts,
        'news': news,
        'workshops': workshops,
        'books': books
    }
    
    return render_template('search.html', results=results, query=query)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        current_user.phone = request.form['phone']
        current_user.address = request.form['address']
        current_user.bio = request.form['bio']
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    
    # Get user's registered workshops
    user_registrations = WorkshopRegistration.query.filter_by(user_id=current_user.id).all()
    workshops = [registration.workshop for registration in user_registrations]
    
    return render_template('profile.html', workshops=workshops)

@app.route('/change_profile_photo', methods=['POST'])
@login_required
def change_profile_photo():
    if 'profile_image' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('profile'))
    
    file = request.files['profile_image']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('profile'))
    
    if file:
        # Generate a unique filename with timestamp
        filename = secure_filename(file.filename)
        filename = f"{int(time.time())}_{filename}"
        
        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics', filename)
        file.save(file_path)
        
        # Update user's profile image in database
        current_user.profile_image = filename
        db.session.commit()
        
        flash('Profile picture updated successfully!', 'success')
    
    return redirect(url_for('profile'))

# Add change password route
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('change_password'))
            
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('change_password'))
            
        current_user.set_password(new_password)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('profile'))
        
    return render_template('change_password.html')

# Update post route to handle comments
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST' and current_user.is_authenticated:
        content = request.form.get('content')
        if content:
            comment = Comment(content=content, user_id=current_user.id, post_id=post.id)
            db.session.add(comment)
            db.session.commit()
            flash('Your comment has been added!', 'success')
            return redirect(url_for('post', post_id=post.id))
    
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.date_posted.desc()).all()
    return render_template('post.html', post=post, comments=comments)

# Helper function for file uploads
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Update workshop registration to use the new model
@app.route('/workshop/<int:workshop_id>/register', methods=['GET', 'POST'])
@login_required
def register_workshop(workshop_id):
    workshop = Workshop.query.get_or_404(workshop_id)
    
    # Check if workshop is in the past
    if workshop.date < datetime.utcnow():
        flash('Registration is closed for past workshops.', 'danger')
        return redirect(url_for('workshop'))
    
    # Check if workshop is full
    if workshop.current_participants >= workshop.max_participants:
        flash('This workshop is already full.', 'danger')
        return redirect(url_for('workshop'))
    
    # Check if user is already registered
    existing_registration = WorkshopRegistration.query.filter_by(
        user_id=current_user.id, workshop_id=workshop.id
    ).first()
    
    if existing_registration:
        flash('You are already registered for this workshop.', 'info')
        return redirect(url_for('workshop'))
    
    # Process the registration
    registration = WorkshopRegistration(
        user_id=current_user.id,
        workshop_id=workshop.id
    )
    
    db.session.add(registration)
    
    # Increment the participant count
    workshop.current_participants += 1
    
    try:
        db.session.commit()
        flash('You have successfully registered for this workshop!', 'success')
        return redirect(url_for('user_workshops'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during registration. Please try again.', 'danger')
        print(str(e))  # Log the error
        return redirect(url_for('workshop'))

@app.route('/workshop/cancel-registration/<int:registration_id>', methods=['GET', 'POST'])
@login_required
def cancel_registration(registration_id):
    registration = WorkshopRegistration.query.get_or_404(registration_id)
    
    # Ensure the user owns this registration
    if registration.user_id != current_user.id:
        flash('You do not have permission to cancel this registration.', 'danger')
        return redirect(url_for('user_workshops'))
    
    # Check if the workshop is in the past
    workshop = Workshop.query.get(registration.workshop_id)
    if workshop.date < datetime.utcnow():
        flash('You cannot cancel registration for past workshops.', 'danger')
        return redirect(url_for('user_workshops'))
    
    try:
        # Decrement the participant count
        if workshop.current_participants > 0:
            workshop.current_participants -= 1
            
        db.session.delete(registration)
        db.session.commit()
        flash('Your registration has been cancelled.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while cancelling your registration.', 'danger')
        print(str(e))  # Log the error
    
    return redirect(url_for('user_workshops'))
@app.route('/workshop/<int:workshop_id>')
def workshop_detail(workshop_id):
    workshop = Workshop.query.get_or_404(workshop_id)
    
    # Check if the current user is registered for this workshop
    is_registered = False
    if current_user.is_authenticated:
        registration = WorkshopRegistration.query.filter_by(
            user_id=current_user.id, 
            workshop_id=workshop.id
        ).first()
        is_registered = registration is not None
    
    return render_template('workshop_detail.html', workshop=workshop, is_registered=is_registered, now=datetime.utcnow())

@app.route('/workshop/edit/<int:workshop_id>', methods=['GET', 'POST'])
@login_required
def edit_workshop(workshop_id):
    if not current_user.is_admin:
        flash('Only administrators can edit workshops.')
        return redirect(url_for('workshop'))
        
    workshop = Workshop.query.get_or_404(workshop_id)
    
    if request.method == 'POST':
        workshop.title = request.form['title']
        workshop.description = request.form['description']
        workshop.date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
        workshop.duration = int(request.form['duration'])
        workshop.location = request.form['location']
        workshop.max_participants = int(request.form['max_participants'])
        workshop.registration_open = 'registration_open' in request.form
        
        db.session.commit()
        flash('Workshop has been updated successfully!', 'success')
        return redirect(url_for('manage_workshops'))
        
    return render_template('edit_workshop.html', workshop=workshop)
@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        abort(403)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        
        # Handle thumbnail upload or removal
        if 'remove_thumbnail' in request.form and post.thumbnail:
            # Remove the file if it exists
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.thumbnail))
            except:
                pass  # File might not exist
            post.thumbnail = None
        
        if 'thumbnail' in request.files and request.files['thumbnail'].filename:
            # Remove old thumbnail if exists
            if post.thumbnail:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.thumbnail))
                except:
                    pass  # File might not exist
            
            file = request.files['thumbnail']
            # Generate a secure filename
            filename = secure_filename(file.filename)
            # Add timestamp to ensure uniqueness
            filename = f"{int(time.time())}_{filename}"
            # Save the file
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post.thumbnail = filename
        
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    
    return render_template('edit_post.html', post=post)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!')
    return redirect(url_for('home'))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('post', post_id=comment.post_id))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        subject = request.form.get('subject')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if not all([subject, email, message]):
            flash('Please fill out all fields.', 'error')
            return redirect(url_for('contact'))
        
        try:
            # Create the email message
            msg = Message(
                subject=f'Contact Form: {subject}',
                recipients=['admin1@example.com', 'admin2@example.com'],  # Replace with admin emails
                body=f'From: {email}\n\nMessage:\n{message}',
                reply_to=email
            )
            
            # Send the email
            mail.send(msg)
            
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            flash('An error occurred while sending your message. Please try again later.', 'error')
            return redirect(url_for('contact'))
            
    return render_template('contact.html')

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    # Get related news in the same category
    related_news = News.query.filter(News.category == news.category, News.id != news.id).order_by(News.date_posted.desc()).limit(3).all()
    return render_template('news_detail.html', news=news, related_news=related_news)

@app.route('/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    if not current_user.is_admin:
        flash('Only administrators can edit news items.', 'danger')
        return redirect(url_for('news'))
        
    news = News.query.get_or_404(news_id)
    
    if request.method == 'POST':
        news.title = request.form['title']
        news.content = request.form['content']
        news.category = request.form['category']
        news.image_url = request.form.get('image_url')
        
        db.session.commit()
        flash('News item has been updated successfully!', 'success')
        return redirect(url_for('manage_news'))
        
    return render_template('edit_news.html', news=news)

@app.route('/news/delete/<int:news_id>', methods=['POST'])
@login_required
def delete_news(news_id):
    if not current_user.is_admin:
        flash('Only administrators can delete news items.', 'danger')
        return redirect(url_for('news'))
        
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash('News item has been deleted successfully!', 'success')
    return redirect(url_for('manage_news'))

@app.route('/manage_news')
@login_required
def manage_news():
    if not current_user.is_admin:
        flash('Only administrators can manage news items.', 'danger')
        return redirect(url_for('news'))
        
    page = request.args.get('page', 1, type=int)
    news_items = News.query.order_by(News.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('manage_news.html', news_items=news_items)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin dashboard.', 'danger')
        return redirect(url_for('home'))
    
    user_count = User.query.count()
    post_count = Post.query.count()
    news_count = News.query.count()
    workshop_count = Workshop.query.count()
    
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    recent_posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    
    upcoming_workshops = Workshop.query.filter(
        Workshop.date > datetime.utcnow()
    ).order_by(Workshop.date).limit(5).all()
    
    stats = {
        'user_count': user_count,
        'post_count': post_count,
        'news_count': news_count,
        'workshop_count': workshop_count
    }
    
    return render_template(
        'admin_dashboard.html', 
        stats=stats, 
        recent_users=recent_users,
        recent_posts=recent_posts,
        upcoming_workshops=upcoming_workshops
    )

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to edit users.', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    # Update user details
    user.username = request.form.get('username', user.username)
    user.email = request.form.get('email', user.email)
    user.phone = request.form.get('phone', user.phone)
    user.is_admin = 'is_admin' in request.form
    
    db.session.commit()
    flash(f'User {user.username} has been updated successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete users.', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent self-deletion
    if user.id == current_user.id:
        flash('You cannot delete your own account from this interface.', 'danger')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin_users'))

 #Add this function to update all workshop participant counts
@app.route('/admin/update-workshop-counts', methods=['GET'])
@login_required
def update_workshop_counts():
    if not current_user.is_admin:
        flash('Only administrators can access this function.', 'danger')
        return redirect(url_for('home'))
        
    workshops = Workshop.query.all()
    updated = 0
    
    for workshop in workshops:
        # Count actual registrations
        actual_count = WorkshopRegistration.query.filter_by(workshop_id=workshop.id).count()
        
        # Update if different
        if workshop.current_participants != actual_count:
            workshop.current_participants = actual_count
            updated += 1
    
    db.session.commit()
    flash(f'Updated participant counts for {updated} workshops.', 'success')
    return redirect(url_for('manage_workshops'))

# Add this route to view user's registered workshops
@app.route('/user/workshops')
@login_required
def user_workshops():
    # Get user's registered workshops
    user_registrations = WorkshopRegistration.query.filter_by(user_id=current_user.id).all()
    
    # Get the workshop objects
    registrations = []
    for registration in user_registrations:
        registrations.append(registration)
    
    return render_template('user_workshops.html', registrations=registrations, now=datetime.utcnow())



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

