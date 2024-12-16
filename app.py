from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from telebot import TeleBot
from werkzeug.utils import secure_filename
from datetime import datetime
from helpers.auth import user_middleware, User, EmailUsernameNotUnique, admin_only_middleware, auth_only_middleware
from helpers.db import db
from helpers.webforms import SearchForm

app = Flask(__name__)

app.secret_key = bytes.fromhex(os.environ['SECRET_KEY'])

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ID = os.environ["TELEGRAM_ID"]

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.context_processor
@user_middleware
def global_context(user: User):
    form = SearchForm()
    return dict(user = user, form = form)

@app.route('/')
def home():
    latest_articles = list(db.articles.find().sort("published_at", -1).limit(3))

    all_articles = list(db.articles.find().sort("published_at", -1))

    return render_template('index.html', latest_articles=latest_articles, articles=all_articles)

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if request.method == 'GET':
        return render_template('Contact.html')

    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    bot = TeleBot(TELEGRAM_BOT_TOKEN, parse_mode = 'HTML', threaded = False)
    text = f"""
Ada request artikel dari {name} {email}

Isi Pesan: {message} 
""".strip()
    bot.send_message(TELEGRAM_ID, text)
    flash("Pesan berhasil dikirim", 'success')
    return redirect('/contact')

@app.route('/adminpage')
@admin_only_middleware
@user_middleware
def dashboard(user: User):
    # print(user.role)
    # print(user.is_login())
    # print(user.username)
    
    return render_template('AdminPage.html')
    # if user.role == "admin":
    #     return render_template('AdminPage.html')

    # return redirect(url_for('home'))

@app.route('/list')
def list_article():
    category = request.args.get('category')
    page = int(request.args.get('page', 1))
    per_page = 5

    # Filter artikel berdasarkan kategori jika ada
    query = {'category': category} if category else {}
    articles = list(db.articles.find(query).skip((page - 1) * per_page).limit(per_page))

    # Ambil 5 artikel terbaru untuk Recent Posts
    recent_posts = list(db.articles.find().sort('published_at', -1).limit(5))

    # Hitung total halaman
    total_articles = db.articles.count_documents(query)
    total_pages = (total_articles + per_page - 1) // per_page

    return render_template(
        'listarticle.html',
        articles=articles,
        selected_category=category,
        recent_posts=recent_posts,
        current_page=page,
        total_pages=total_pages
    )

@app.route('/fpass', methods=['GET', 'POST'])
def fpass():
    if request.method == 'POST':
        if 'email' in request.form and 'password' not in request.form:
            email = request.form['email']
            user = db.users.find_one({'email': email})

            if user:
                flash('Email ditemukan. Silakan masukkan password baru.', 'success')
                return render_template('fpass.html', email=email)  
            else:
                flash('Email tidak ditemukan. Mohon periksa alamat email Anda.', 'danger')

        elif 'password' in request.form:
            email = request.form['email']
            new_password = request.form['password']

            if not new_password:
                flash('Password baru tidak boleh kosong.', 'danger')
                return render_template('fpass.html', email=email)

            hashed_password = generate_password_hash(new_password)

            result = db.users.update_one({'email': email}, {'$set': {'password': hashed_password}})
            
            if result.modified_count > 0:
                flash('Password berhasil direset. Silakan login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Gagal memperbarui password. Silakan coba lagi.', 'danger')

    return render_template('fpass.html')

@app.route('/login', methods=['GET', 'POST'])
@user_middleware
def login(user: User):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        client = db.users.find_one({'email': email})

        if client and check_password_hash(client['password'], password):
            # print(client)
            user.login(client['_id'])
            flash('Login successful!', 'success')
            if client['role'] == 'admin':
                return redirect(url_for('dashboard'))
            elif client['role'] == 'user':
                return redirect(url_for('home')) 
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  
        avatar = request.form.get('avatar') 

        try:
            User.create(username, email, password, role, avatar)
        except EmailUsernameNotUnique:
            flash('Username/email already exists', 'error')
            return redirect(url_for('signup'))            
        
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
@user_middleware
def logout(user: User):
    user.logout()
    flash('You have logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/publish', methods=['GET', 'POST'])
@admin_only_middleware
def publish_article():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        
        if 'thumbnail' in request.files:
            thumbnail_file = request.files['thumbnail']
            if thumbnail_file and allowed_file(thumbnail_file.filename):
                filename = secure_filename(thumbnail_file.filename)
                thumbnail_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                thumbnail_path = f'uploads/{filename}'
            else:
                thumbnail_path = None
        else:
            thumbnail_path = None

        published_at = datetime.now()

        db.articles.insert_one({
            'title': title,
            'description': description,
            'category': category,
            'thumbnail': thumbnail_path,
            'published_at': published_at  
        })

        flash('Article published successfully!', 'success')
        return redirect(url_for('publish_article'))

    return render_template('publish.html')

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/singlepage/<string:title>', methods=['GET'])
def singlepage(title):
    article = db.articles.find_one({'title': title})
    
    if not article:
        flash("Artikel tidak ditemukan", "danger")
        return redirect(url_for('home'))  # Redirect ke halaman utama jika artikel tidak ditemukan

    comments = list(db.comments.find({"article_id": article['_id']}).sort('published_at', -1))
    # comments = list(db.comments.find({"article_id": article['_id']}))
    # biar ada index (i) pake enumerate bang
    for i, comment in enumerate(comments):
        comments[i]['user'] = db.users.find_one({"_id": comment['user_id']})

    # print(comments)        
    return render_template('singlepage.html', article=article, url=request.url, comments=comments)

@app.route('/singlepage/<string:title>/comment', methods = ['POST'])
@auth_only_middleware
@user_middleware
def article_comment(user: User, title: str = ""):
    article = db.articles.find_one({'title': title})
    if not article:
        flash("Artikel tidak ditemukan", "danger")
        return redirect(url_for('home'))  # Redirect ke halaman utama jika artikel tidak ditemukan
    
    user.add_comment(article['_id'], request.form['text'])
    flash("Berhasil komentar", "success")
    return redirect('/singlepage/'+title)

@app.route('/articles', methods=['GET'])
def get_articles():
    articles = list(db.articles.find({}, {'_id': 0})) 
    return {'articles': articles}, 200

@app.route('/update_article/<string:title>', methods=['GET', 'POST'])
def update_article(title):
    if request.method == 'POST':
        new_title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        
        db.articles.update_one(
            {'title': title},
            {'$set': {
                'title': new_title,
                'description': description,
                'category': category,
                'updated_at': datetime.now()
            }}
        )
        flash('Article updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    article = db.articles.find_one({'title': title})
    return render_template('update.html', article=article)

@app.route('/delete_article/<string:title>', methods=['POST'])
def delete_article(title):
    result = db.articles.delete_one({'title': title})
    if result.deleted_count > 0:
        flash('Article deleted successfully!', 'success')
    else:
        flash('Failed to delete the article. Article not found.', 'error')
    return redirect(url_for('dashboard'))

# @app.context_processor
# def base():
#     form = SearchForm()
#     return dict(form=form)

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    results = None
    if form.validate_on_submit():
        searched = form.searched.data
        results = list(db.articles.find({"title": {"$regex": searched, "$options": "i"}}))
    
    # print(results)
    return render_template('search.html', form=form, searched=searched, results=results)
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)