from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db=SQLAlchemy()

class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    books = db.relationship('Book', back_populates='genre')

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(200), index=True)
    isbn = db.Column(db.String(20), index=True)
    publisher = db.Column(db.String(100))
    page = db.Column(db.Integer, default=0)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))
    genre = db.relationship('Genre', back_populates='books')    
    stocks = db.relationship('Stock', back_populates='book', cascade='all, delete-orphan')

class User(db.Model, UserMixin):  # autentificare
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' sau 'librarian'
    phone = db.Column(db.String(20))

    def get_id(self):
        return f"user-{self.id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Member(db.Model, UserMixin):  # cititori
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(9))
    address = db.Column(db.String(200))
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' sau 'teacher'
    class_name = db.Column(db.String(50), index=True) # doar pentru studenți
    password_hash = db.Column(db.String(128)) 

    def get_id(self):
        return f"member-{self.id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    rent_fee = db.Column(db.Float, default=2025)

class Stock(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    book_id=db.Column(db.Integer,db.ForeignKey('book.id'),nullable=False)
    total_quantity=db.Column(db.Integer,default=0)
    available_quantity=db.Column(db.Integer,default=0)
    borrowed_quantity=db.Column(db.Integer,default=0)
    total_borrowed=db.Column(db.Integer,default=0)
    book = db.relationship('Book', back_populates='stocks')

class Charges(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    rentfee=db.Column(db.Integer)