from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
class Rent(db.Model):
    __tablename__ = 'rent'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(255))
    place = db.Column(db.String(255))
    date = db.Column(db.Date, default=db.func.current_date())
    name1 = db.Column(db.String(255))
    district1 = db.Column(db.String(255))
    province1 = db.Column(db.String(255))
    name2 = db.Column(db.String(255))
    idcard2 = db.Column(db.String(255)) #add this
    age2 = db.Column(db.String(255))
    house2 = db.Column(db.String(255))
    vilno2 = db.Column(db.String(255))
    street2 = db.Column(db.String(255))
    lane2 = db.Column(db.String(255))
    subd2 = db.Column(db.String(255))
    district2 = db.Column(db.String(255))
    province2 = db.Column(db.String(255))
    idcard2 = db.Column(db.String(255))
    authority = db.Column(db.String(255))
    dateofid = db.Column(db.String(255))
    property = db.Column(db.String(255))
    purpose = db.Column(db.String(255))
    duration = db.Column(db.String(255))
    fromdate = db.Column(db.String(255))
    todate = db.Column(db.String(255))
    typeofrent = db.Column(db.String(255))
    price = db.Column(db.String(255))
    duedate = db.Column(db.String(255))
    tax = db.Column(db.String(255))


class State(db.Model):
    __tablename__ = 'current_state'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(100), nullable=False)
    current_state = db.Column(db.String(100), nullable=False)
    type_contract = db.Column(db.String(100), nullable=False)
