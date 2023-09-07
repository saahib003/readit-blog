from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user, logout_user, login_required, UserMixin, LoginManager
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

app.app_context().push()

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# https://www.alexhyett.com/backend-developer-roadmap/


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    # backref='author'

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def toDict(self):
       return dict(id=self.id, title=self.title, content=self.content, date=self.date_posted)
    
    def __repr__(self):
        return f"Post('{self.title}', '{self.content}','{self.date_posted}')"



@app.route('/register', methods=["POST"])
def register():
    input = request.get_json()
    user = User.query.filter_by(email=input['email']).first()
    if user:
        return jsonify({"error":"Already has account by this email."})
    hashed_password = bcrypt.generate_password_hash(input["password"]).decode('utf-8')
    new_user = User(name = input["name"],username = input["username"],email = input["email"],password = hashed_password)
    db.session.add(new_user)
    db.session.commit()
    details = {"name": new_user.name,"username": new_user.username,"email":new_user.email,"id":new_user.id}
    return jsonify(details)

@app.route('/login', methods=["POST"])
def login():
    input = request.get_json()
    user = User.query.filter_by(email=input['email']).first()
    if user is None:
         return jsonify({"error":"Unauthorized"})
    if not bcrypt.check_password_hash(user.password, input["password"]):
         return jsonify({"error":"Unauthorized"})
    login_user(user)
    return jsonify({
                  "name":user.name,
                   "username":user.username,
                   "email":user.email,
                   "password":user.password
              })

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"Info":"User log out"})


@app.route("/post/new", methods=['POST'])
@login_required
def new_post():
    blog = request.get_json()
    post = Post(title=blog["title"], content=blog["content"], author=current_user)
    db.session.add(post)
    db.session.commit()
    return jsonify({
        "post_id":post.id,
        "title":post.title,
        "content":post.content
    })



@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return jsonify({"seccess":"Post deleted"})


@app.route("/post/<int:post_id>", methods=['GET'])
@login_required
def getpost(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    return jsonify({"post_id":post.id,"title":post.title,"content":post.content})

@app.route("/post/<int:post_id>/update", methods=['POST'])
@login_required
def update_post(post_id):
    updated_post = request.get_json()
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    post.title = updated_post["title"]
    post.content = updated_post["content"]
    db.session.commit()
    return jsonify({"title":post.title,"content":post.content})


@app.route('/<string:username>/posts')
@login_required
def getIndividualsPost(username):
    user = User.query.filter_by(username=username).first()
    user_posts = user.posts
    
    array = []
    for post in user_posts:
        array.append({'title': post.title, 'content': post.content, "id":post.id})
    return jsonify(array)


# @app.route("/totalposts")
# @login_required
# def getPosts():
#     users = User.query.all()
#     array = []
#     for user in users:
#         user_posts = user.posts
#         for post in user_posts:
#             array.append({'title': post.title, 'id':post.id, 'content': post.content, "username":user.username, "name":user.name,"date":post.date_posted})
#     return jsonify(array)

@app.route("/totalposts")
@login_required
def getPosts():
    posts = Post.query.order_by(Post.date_posted.desc())
    array = []
    for post in posts:
        user = User.query.filter_by(id=post.user_id).first()
        array.append({'title': post.title, 'id':post.id, 'content': post.content, "username":user.username, "name":user.name,"date":post.date_posted})
    return jsonify(array)






if __name__ == "__main__":
     app.run(debug=True)