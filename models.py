from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), unique=True, nullable=False, index=True)
    name = db.Column(db.String(80), default="Guest User")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", backref="user", lazy=True)


class Frame(db.Model):
    __tablename__ = "frames"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    color_hex = db.Column(db.String(7), default="#A6673A")
    price = db.Column(db.Integer, nullable=False)  # in rupees
    stock = db.Column(db.Integer, default=0)

    orders = db.relationship("Order", backref="frame", lazy=True)


class Campaign(db.Model):
    __tablename__ = "campaigns"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    subtitle = db.Column(db.String(240))
    bg_gradient = db.Column(db.String(160), default="linear-gradient(135deg,#A6673A,#8A5230)")
    active = db.Column(db.Boolean, default=True)


LENS_PRICES = {
    "Single Vision": 300,
    "Progressive": 1800,
    "Zero Power": 0,
    "Tinted": 600,
}

ORDER_STATUSES = ["Pending", "Approved", "Processing", "Shipped", "Delivered", "Cancelled"]


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(20), unique=True, nullable=False, index=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    frame_id = db.Column(db.Integer, db.ForeignKey("frames.id"), nullable=False)

    power_type = db.Column(db.String(20))       # zero | powered | upload
    lens_type = db.Column(db.String(30))         # Single Vision | Progressive | Zero Power | Tinted
    right_eye_power = db.Column(db.String(20))
    left_eye_power = db.Column(db.String(20))
    prescription_file = db.Column(db.String(255))  # filename in static/uploads, if uploaded

    lens_price = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Integer, nullable=False)

    status = db.Column(db.String(20), default="Pending")  # see ORDER_STATUSES
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminSetting(db.Model):
    """Simple key/value store for QR toggle, payment note, etc."""
    __tablename__ = "admin_settings"
    key = db.Column(db.String(60), primary_key=True)
    value = db.Column(db.String(255))
