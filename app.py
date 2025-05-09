import datetime
from flask import Flask,render_template,request,redirect,flash,url_for,jsonify
from flask_migrate import Migrate
from models import db,Book,Member,Transaction,Stock,Charges,Genre
from datetime import datetime, timedelta
import requests 
from sqlalchemy import desc,or_
from sqlalchemy.exc import IntegrityError,NoResultFound


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///library.db'
app.config['SECRET_KEY']='af9d4e10d142994285d0c1f861a70925'
db.init_app(app)
migrate=Migrate(app,db)

@app.route('/')
def index():
    borrowed_books = db.session.query(Transaction).filter(Transaction.return_date == None).count()
    total_books = Book.query.count()
    total_members = Member.query.count()
    total_rent_current_month = calculate_total_rent_current_month()
    recent_transactions  =  db.session.query(Transaction,Book).join(Book).order_by(Transaction.issue_date.desc()).limit(5).all()

    return render_template('index.html', borrowed_books=borrowed_books, total_books=total_books,total_members=total_members,recent_transactions=recent_transactions,total_rent_current_month=total_rent_current_month)

def calculate_total_rent_current_month():
    current_month = datetime.now().month
    current_year = datetime.now().year
    start_date = datetime(current_year, current_month, 1)
    end_date = datetime(current_year, current_month + 1, 1) - timedelta(days=1)  # Используй timedelta без 'datetime.'

    total_rent = db.session.query(db.func.sum(Transaction.rent_fee)).filter(
        Transaction.issue_date >= start_date,
        Transaction.issue_date <= end_date
    ).scalar()

    return total_rent if total_rent else 0

@app.route('/init_genres')
def init_genres():
    genres = ['Roman', 'Istorie', 'Geografie', 'Știință', 'Ficțiune', 'Poezie']
    for name in genres:
        if not Genre.query.filter_by(name=name).first():
            db.session.add(Genre(name=name))
    db.session.commit()
    return 'Genurile au fost adăugate.'

@app.route('/add_genre', methods=['GET', 'POST'])
def add_genre():
    if request.method == 'POST':
        genre_name = request.form.get('genre_name')
        # Verifică dacă genul nu există deja
        if Genre.query.filter_by(name=genre_name).first():
            flash("Genul există deja!", 'danger')
            return redirect(url_for('add_genre'))
        
        new_genre = Genre(name=genre_name)
        db.session.add(new_genre)
        db.session.commit()
        flash("Gen adăugat cu succes!", 'success')
        return redirect(url_for('index'))
    
    return render_template('add_genre.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    genres = Genre.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        publisher = request.form.get('publisher')
        page = request.form.get('page')
        stock = request.form.get('stock')
        genre_id = request.form.get('genre_id')

        try:
            page = int(page)
            stock = int(stock)
            genre_id = int(genre_id)
        except ValueError:
            flash('Datele introduse nu sunt valide!', 'danger')
            return redirect(url_for('add_book'))

        # Verifică dacă genul există
        genre = Genre.query.get(genre_id)
        if not genre:
            flash("Genul selectat nu există!", 'danger')
            return redirect(url_for('add_book'))

        new_book = Book(
            title=title,
            author=author,
            isbn=isbn,
            publisher=publisher,
            page=page,
            genre_id=genre_id
        )

        db.session.add(new_book)
        db.session.flush()  # obține ID-ul cărții pentru stock

        new_stock = Stock(
            book_id=new_book.id,
            total_quantity=stock,
            available_quantity=stock
        )
        db.session.add(new_stock)
        
        try:
            db.session.commit()
            flash('Carte adăugată cu succes!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Erroare la adăugarea cărții: {e}", 'danger')
            return redirect(url_for('add_book'))

        return redirect(url_for('index'))

    return render_template('add_book.html', genres=genres)

@app.route('/view_books', methods=['GET', 'POST'])
def book_list():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    genres = Genre.query.all()

    search_term = request.form.get('search') if request.method == 'POST' else None
    genre_name = request.form.get('genre_name') if request.method == 'POST' else None

    books_query = db.session.query(Book, Stock).join(Stock)

    if search_term:
        books_query = books_query.filter(
            (Book.title.ilike(f'%{search_term}%')) |
            (Book.author.ilike(f'%{search_term}%')) |
            (Book.isbn.ilike(f'%{search_term}%'))
        )

    if genre_name:
        genre = Genre.query.filter(Genre.name.ilike(f"%{genre_name}%")).first()
        if genre:
            books_query = books_query.filter(Book.genre_id == genre.id)

    books = books_query.paginate(page=page, per_page=per_page, error_out=False)


    page_range = []
    if books.page > 2:
        page_range.append(1)

    for i in range(max(1, books.page - 1), min(books.page + 2, books.pages) + 1):
        if i not in page_range:
            page_range.append(i)

    if books.page > 3:
        page_range.insert(1, '...')

    if books.page < books.pages - 2:
        page_range.append('...')
        page_range.append(books.pages)

    return render_template('view_books.html', books=books, page_range=page_range, genres=genres)

@app.route('/view_members', methods=['GET', 'POST'])
def member_list():
    page = request.args.get('page', 1, type=int)
    per_page = 15  

    search = request.form.get('search') if request.method == 'POST' else None

    members_query = db.session.query(Member)

    if search:
        members_query = members_query.filter(Member.name.like(f'%{search}%'))

    members = members_query.paginate(page=page, per_page=per_page, error_out=False)

    page_range = []
    if members.page > 2:
        page_range.append(1)

    for i in range(max(1, members.page - 1), min(members.page + 2, members.pages) + 1):
        if i not in page_range:
            page_range.append(i)

    if members.page > 3:
        page_range.insert(1, '...')

    if members.page < members.pages - 2:
        page_range.append('...')
        page_range.append(members.pages)

    return render_template('view_members.html', members=members, page_range=page_range)

@app.route('/edit_book/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    book = Book.query.get(id)
    stock = Stock.query.get(book.id)
    genres = Genre.query.all()  

    try:
        if request.method == 'POST':
            book.title = request.form.get('title')
            book.author = request.form.get('author')
            book.isbn = request.form.get('isbn')
            book.publisher = request.form.get('publisher')
            book.page = request.form.get('page')
            stock.total_quantity = request.form.get('stock')

            # Verifică dacă genul selectat există
            genre_id = request.form.get('genre_id')
            genre = Genre.query.get(genre_id)
            if genre:
                book.genre = genre  # Atribuie genul selectat
            db.session.commit()
            flash("Actualizat cu succes", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erroare \n{e}", 'error')

    return render_template('edit_book.html', book=book, stock=stock, genres=genres)

@app.route('/edit_member/<int:id>',methods=['GET','POST'])
def edit_member(id):
    member=Member.query.get(id)
    try:
        if request.method=="POST":
            member.name=request.form['name']
            member.phone=request.form['phone']
            member.email=request.form['email']
            member.address=request.form['address']
            db.session.commit()
            flash("Actualizat cu succes","success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erroare \n{e}",'error') 
    return render_template('edit_member.html',member=member)

@app.route('/delete_member/<int:id>',methods=['GET','POST'])
def delete_member(id):
    try:
        member=Member.query.get(id)
        db.session.delete(member)
        db.session.commit()
        flash("Utilizator șters cu succes","success")
    except Exception as e:
        flash(f"Erroare \n{e}",'error')
    return redirect('/view_members')

@app.route('/delete_book/<int:id>',methods=['GET','POST'])
def delete_book(id):
    try:
        book=Book.query.get(id)
        stock=Stock.query.get(book.id)
        db.session.delete(book)
        db.session.delete(stock)
        db.session.commit()
        flash("Carte ștearsă cu succes","success")
    except Exception as e:
        flash(f"Erroaee \n{e}",'error')
    return redirect('/view_members')

@app.route('/view_book/<int:id>')
def view_book(id):
    book = Book.query.get(id)
    stock = Stock.query.filter_by(book_id=id).first()
    transactions = Transaction.query.filter_by(book_id=id).all()

    trans_data = []
    for trans in transactions:
        member = Member.query.get(trans.member_id)
        trans_data.append({
            'id': trans.id,
            'member_id': trans.member_id,
            'member_name': member.name if member else 'Necunoscut',
            'issue_date': trans.issue_date,
            'return_date': trans.return_date
        })

    return render_template('view_book.html', book=book, trans=trans_data, stock=stock)

@app.route('/view_member/<int:id>')
def view_member(id):
    member = Member.query.get(id)
    transaction = db.session.query(Transaction, Book).join(Book).filter(Transaction.member_id == member.id).all()
    dbt = calculate_dbt(member)
    return render_template('view_member.html', member=member, trans=transaction, debt=dbt)


def calculate_dbt(member):
    transactions = Transaction.query.filter_by(member_id=member.id).all()
    dbt = 0


    for transaction in transactions:
        if transaction.return_date is None:
            due_date = transaction.issue_date + timedelta(days=14)  # calculăm data limită
            if due_date < datetime.now():
                days_difference = (datetime.now() - due_date).days
                charge = Book.query.get(transaction.book_id)
                if charge:
                    dbt += days_difference * charge.rent_fee
    return dbt

@app.route('/issuebook', methods=['GET', 'POST'])
def issue_book():
    if request.method == "POST":
        member_query = request.form['mk']
        book_query = request.form['bk']

        mem = db.session.query(Member).filter(
            (Member.id.like(f'%{member_query}%')) |
            (Member.name.ilike(f'%{member_query}%'))
        ).first()

        book = db.session.query(Book, Stock).join(Stock).filter(
            (Book.id.like(f'%{book_query}%')) |
            (Book.title.ilike(f'%{book_query}%')) |
            (Book.isbn.like(f'%{book_query}%'))
        ).first()

        if mem and book:
            dbt = calculate_dbt(mem)
            return render_template('issuebook.html', book=book, member=mem, debt=dbt)
        else:
            flash("Nu s-au găsit rezultate potrivite.", "error")
            return redirect('/issuebook')

    return render_template('issuebook.html', member=None, book=None, debt=0)

@app.route('/issuebookconfirm', methods=['GET', 'POST'])
def issue_book_confirm():
    if request.method == "POST":
        memberid = request.form['memberid']
        bookid = request.form['bookid']

        stock = db.session.query(Stock).filter_by(book_id=bookid).first()
        if stock.available_quantity <= 0:
            flash("Cartea nu este disponibilă.", "error")
            return redirect('/issuebook')

        new_transaction = Transaction(book_id=bookid, member_id=memberid, issue_date=datetime.today().date())
        print(new_transaction)

        stock.available_quantity -= 1
        stock.borrowed_quantity += 1
        stock.total_borrowed += 1

        db.session.add(new_transaction)
        db.session.commit()

        flash("Tranzacție cu succes", "success")
        return redirect('/issuebook')

    return render_template('issuebook.html')

@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email').strip().lower()
        phone = request.form.get('phone')
        address = request.form.get('address')

        new_member = Member(name=name, email=email, phone=phone, address=address)

        db.session.add(new_member)
        db.session.commit()

        flash('Utilizator adăugat cu succes!', 'success')
        return redirect(url_for('add_member'))
    return render_template('add_member.html')

@app.route('/transactions', methods=['GET', 'POST'])
def view_borrowings():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    genres = Genre.query.all()  

    transactions_query = db.session.query(Transaction, Member, Book)\
        .join(Book).join(Member)\
        .order_by(desc(Transaction.return_date.is_(None)))

    if request.method == "POST":
        search = request.form['search']

        transactions_by_name = transactions_query.filter(Member.name.ilike(f'%{search}%'))
        transaction_by_id = transactions_query.filter(Transaction.id == search)

        if transactions_by_name.count() > 0:
            transactions_query = transactions_by_name
        elif transaction_by_id.count() > 0:
            transactions_query = transaction_by_id
        else:
            transactions_query = transactions_query.filter(False)  

    transactions = transactions_query.paginate(page=page, per_page=per_page, error_out=False)

    page_range = []
    if transactions.page > 2:
        page_range.append(1)

    for i in range(max(1, transactions.page - 1), min(transactions.page + 2, transactions.pages) + 1):
        if i not in page_range:
            page_range.append(i)

    if transactions.page > 3:
        page_range.insert(1, '...')

    if transactions.page < transactions.pages - 2:
        page_range.append('...')
        page_range.append(transactions.pages)

    return render_template('transactions.html', trans=transactions, page_range=page_range)

@app.route('/return_book/<int:book_id>', methods=['POST'])
def return_book(book_id):
    stock = Stock.query.filter_by(book_id=book_id).first()
    transaction = Transaction.query.filter_by(book_id=book_id, return_date=None).order_by(Transaction.issue_date.desc()).first()

    if stock and transaction:
        stock.available_quantity += 1
        stock.borrowed_quantity -= 1

        transaction.return_date = datetime.now()

        db.session.commit()

    return redirect(url_for('imp'))

@app.route('/returnbookconfirm', methods=['POST'])
def return_book_confirm():
    if request.method == "POST":
        id = request.form["id"]
        trans, member = db.session.query(Transaction, Member).join(Member).filter(Transaction.id == id).first()
        stock = Stock.query.filter_by(book_id=trans.book_id).first()
        charge=Charges.query.first()
        rent=(datetime.date.today() - trans.issue_date.date() ).days * charge.rentfee
        if stock:
            stock.available_quantity += 1
            stock.borrowed_quantity -= 1

            trans.return_date = datetime.date.today()
            trans.rent_fee =rent
            db.session.commit()
            flash(f"{member.name} Carte returnată cu succes", 'success')
        else:
            flash("Erroare în actualizarea datelor", 'error')

    return redirect('transactions')

def calculate_rent(transaction):
    charge=Charges.query.first()
    rent=(datetime.date.today() - transaction.Transaction.issue_date.date() ).days * charge.rentfee
    return rent

API_BASE_URL = "https://frappe.io/api/method/frappe-library"

@app.route('/import_book', methods=['GET'])
def imp():
    borrowed_books = db.session.query(Book, Member).\
        select_from(Book).\
        join(Stock, Stock.book_id == Book.id).\
        join(Transaction, Transaction.book_id == Book.id).\
        join(Member, Member.id == Transaction.member_id).\
        filter(Stock.available_quantity == 0).\
        all()
    return render_template('imp.html', data=borrowed_books, title='Cărți împrumutate', num_books=len(borrowed_books))

@app.route('/save_all_books', methods=['POST'])
def save_all_books():
    data = request.json

    for book_data in data:
        book_id = book_data['id']
        existing_book = Book.query.get(book_id)

        if existing_book is None:
            book = Book(
                id=book_id,
                title=book_data['title'],
                author=book_data['authors'],
                isbn=book_data['isbn'],
                publisher=book_data['publisher'],
                page=book_data['numPages']
            )
            st = book_data['stock']

            try:
                db.session.add(book)
                stock = Stock(book_id=book_id, total_quantity=st, available_quantity=st)
                db.session.add(stock)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()  
                print(f"Erroare adăugare carte ID {book_id}: {str(e)}")
        else:
            print(f"Carte cu așa ID {book_id} deja există.")

    flash("Carte adăugată cu succes", "success")
    return redirect('/import_book')

@app.route('/stockupdate/<int:id>',methods=['GET','POST'])
def stock_update(id):
    stock,book=db.session.query(Stock,Book).join(Book).filter(Stock.book_id == id).first()
    if request.method=="POST":
        qty=int(request.form['qty'])
        if qty > stock.total_quantity:
            stock.available_quantity+=qty
            stock.total_quantity+=qty
        else:
            stock.available_quantity-=qty
            stock.total_quantity-=qty
        db.session.commit()
        flash("Stoc Actualizat" , "success")
    return render_template('stockupdate.html',stock=stock,book=book)
if __name__ == '__main__':
    app.run(debug=True)
