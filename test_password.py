from app import app  # importă instanța Flask din app.py
from models import db, User

def test_password():
    with app.app_context():  # intră în contextul aplicației
        # creează user
        user = User(username="testuser", email="test@example.com", role="admin")
        user.set_password("23")
        db.session.add(user)
        db.session.commit()
        
        # caută user
        user_from_db = User.query.filter_by(email="test@example.com").first()
        print("Parola hash din DB:", user_from_db.password_hash)
        print("Check parola corectă (\"23\"):", user_from_db.check_password("23"))  # True
        print("Check parola greșită (\"gresit\"):", user_from_db.check_password("gresit"))  # False
        
        # curăță baza
        db.session.delete(user_from_db)
        db.session.commit()

if __name__ == "__main__":
    test_password()


