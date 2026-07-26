import os
import random
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                    session, flash, jsonify)
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Frame, Campaign, Order, AdminSetting, LENS_PRICES
from services import otp_service, payment_service


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_data()

    register_routes(app)
    return app


# --------------------------------------------------------------------------
# Seed data — runs once; safe to call repeatedly (checks before inserting)
# --------------------------------------------------------------------------
def seed_data():
    if Frame.query.count() == 0:
        db.session.add_all([
            Frame(name="Aviator Classic", color_hex="#A6673A", price=1499, stock=8),
            Frame(name="Round Tortoise", color_hex="#6B4A33", price=1299, stock=3),
            Frame(name="Wayfarer Matte", color_hex="#211C17", price=1199, stock=0),
            Frame(name="Cat Eye Blush", color_hex="#B85C6B", price=1699, stock=12),
            Frame(name="Rimless Steel", color_hex="#7C8A93", price=1899, stock=5),
            Frame(name="Square Navy", color_hex="#3F5D6B", price=1399, stock=9),
        ])
    if Campaign.query.count() == 0:
        db.session.add_all([
            Campaign(title="Monsoon Sale — Flat 40% Off",
                     subtitle="On all powered lenses, this week only",
                     bg_gradient="linear-gradient(135deg,#A6673A,#8A5230)", active=True),
            Campaign(title="Buy 1 Get 1 — Sunglasses",
                     subtitle="Every second pair free at checkout",
                     bg_gradient="linear-gradient(135deg,#3F5D6B,#26414C)", active=True),
            Campaign(title="Progressive Lens Launch",
                     subtitle="Introductory price ₹1799 only",
                     bg_gradient="linear-gradient(135deg,#4C7A5D,#355C43)", active=False),
        ])
    if AdminSetting.query.get("qr_enabled") is None:
        db.session.add(AdminSetting(key="qr_enabled", value="true"))
    if AdminSetting.query.get("payment_note") is None:
        db.session.add(AdminSetting(key="payment_note", value="Scan with any UPI app"))
    db.session.commit()


# --------------------------------------------------------------------------
# Auth decorators
# --------------------------------------------------------------------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_phone"):
            flash("Please log in first.")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin login required.")
            return redirect(url_for("staff_login"))
        return fn(*args, **kwargs)
    return wrapper


def teamlead_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not (session.get("is_teamlead") or session.get("is_admin")):
            flash("Team leader login required.")
            return redirect(url_for("staff_login"))
        return fn(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def gen_order_code():
    return f"FMG-{random.randint(1000, 9999)}"


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
def register_routes(app):

    @app.route("/")
    def index():
        if session.get("user_phone"):
            return redirect(url_for("home"))
        return redirect(url_for("login"))

    # ---------------- AUTH: mobile + OTP ----------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            phone = request.form.get("phone", "").strip()
            if not (phone.isdigit() and len(phone) == 10):
                flash("Enter a valid 10-digit mobile number.")
                return redirect(url_for("login"))
            otp_service.generate_and_send_otp(phone)
            session["pending_phone"] = phone
            return redirect(url_for("verify_otp"))
        return render_template("login.html")

    @app.route("/verify-otp", methods=["GET", "POST"])
    def verify_otp():
        phone = session.get("pending_phone")
        if not phone:
            return redirect(url_for("login"))

        if request.method == "POST":
            code = request.form.get("otp", "").strip()
            if otp_service.verify_otp(phone, code):
                user = User.query.filter_by(phone=phone).first()
                if not user:
                    user = User(phone=phone)
                    db.session.add(user)
                    db.session.commit()
                session["user_phone"] = phone
                session.pop("pending_phone", None)
                flash("Logged in successfully.")
                return redirect(url_for("home"))
            flash("Incorrect OTP, please try again.")
        return render_template("otp.html", phone=phone,
                               mock_mode=app.config["OTP_MOCK_MODE"],
                               mock_code=app.config["MOCK_OTP_CODE"])

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ---------------- HOME / campaigns & ads ----------------
    @app.route("/home")
    @login_required
    def home():
        campaigns = Campaign.query.filter_by(active=True).all()
        frames = Frame.query.limit(4).all()
        return render_template("home.html", campaigns=campaigns, frames=frames)

    # ---------------- FRAME SELECTION ----------------
    @app.route("/frames")
    @login_required
    def frames():
        all_frames = Frame.query.all()
        return render_template("frames.html", frames=all_frames)

    @app.route("/frames/<int:frame_id>/select")
    @login_required
    def select_frame(frame_id):
        frame = Frame.query.get_or_404(frame_id)
        if frame.stock <= 0:
            flash("That frame is out of stock.")
            return redirect(url_for("frames"))
        session["cart"] = {"frame_id": frame.id}
        return redirect(url_for("configure"))

    # ---------------- LENS CONFIG (power type + lens type + prescription) ----------------
    @app.route("/configure", methods=["GET", "POST"])
    @login_required
    def configure():
        cart = session.get("cart")
        if not cart:
            return redirect(url_for("frames"))
        frame = Frame.query.get_or_404(cart["frame_id"])

        if request.method == "POST":
            power_type = request.form.get("power_type")   # zero | powered | upload
            lens_type = request.form.get("lens_type")      # Single Vision | Progressive | Zero Power | Tinted

            cart["power_type"] = power_type
            cart["lens_type"] = lens_type
            cart["right_eye_power"] = request.form.get("right_eye", "")
            cart["left_eye_power"] = request.form.get("left_eye", "")

            if power_type == "upload":
                file = request.files.get("prescription")
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{session['user_phone']}_{file.filename}")
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    cart["prescription_file"] = filename
                elif not cart.get("prescription_file"):
                    flash("Please upload a prescription file.")
                    session["cart"] = cart
                    return redirect(url_for("configure"))

            session["cart"] = cart
            return redirect(url_for("summary"))

        return render_template("configure.html", frame=frame, cart=cart,
                                lens_prices=LENS_PRICES)

    # ---------------- ORDER SUMMARY ----------------
    @app.route("/summary")
    @login_required
    def summary():
        cart = session.get("cart")
        if not cart or "lens_type" not in cart:
            return redirect(url_for("frames"))
        frame = Frame.query.get_or_404(cart["frame_id"])
        lens_price = LENS_PRICES.get(cart["lens_type"], 0)
        total = frame.price + lens_price
        return render_template("summary.html", frame=frame, cart=cart,
                                lens_price=lens_price, total=total)

    # ---------------- PAYMENT (QR) ----------------
    @app.route("/payment")
    @login_required
    def payment():
        cart = session.get("cart")
        if not cart or "lens_type" not in cart:
            return redirect(url_for("frames"))
        frame = Frame.query.get_or_404(cart["frame_id"])
        total = frame.price + LENS_PRICES.get(cart["lens_type"], 0)
        qr_ctx = payment_service.get_qr_context(total)
        return render_template("payment.html", total=total, qr=qr_ctx)

    @app.route("/payment/confirm", methods=["POST"])
    @login_required
    def payment_confirm():
        cart = session.get("cart")
        if not cart or "lens_type" not in cart:
            return redirect(url_for("frames"))

        if not payment_service.confirm_mock_payment():
            flash("Payment could not be confirmed. Please try again.")
            return redirect(url_for("payment"))

        frame = Frame.query.get_or_404(cart["frame_id"])
        user = User.query.filter_by(phone=session["user_phone"]).first()
        lens_price = LENS_PRICES.get(cart["lens_type"], 0)

        order = Order(
            order_code=gen_order_code(),
            user_id=user.id,
            frame_id=frame.id,
            power_type=cart.get("power_type"),
            lens_type=cart.get("lens_type"),
            right_eye_power=cart.get("right_eye_power"),
            left_eye_power=cart.get("left_eye_power"),
            prescription_file=cart.get("prescription_file"),
            lens_price=lens_price,
            total_amount=frame.price + lens_price,
            status="Pending",
        )
        frame.stock = max(0, frame.stock - 1)
        db.session.add(order)
        db.session.commit()

        session.pop("cart", None)
        session["last_order_code"] = order.order_code
        return redirect(url_for("order_success"))

    @app.route("/order/success")
    @login_required
    def order_success():
        code = session.get("last_order_code")
        order = Order.query.filter_by(order_code=code).first_or_404() if code else None
        return render_template("order_success.html", order=order)

    # ---------------- MY ORDERS / TRACKING ----------------
    @app.route("/my-orders")
    @login_required
    def my_orders():
        user = User.query.filter_by(phone=session["user_phone"]).first()
        orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
        return render_template("my_orders.html", orders=orders)

    # ---------------- STAFF LOGIN (Admin / Team Leader) ----------------
    @app.route("/staff/login", methods=["GET", "POST"])
    def staff_login():
        if request.method == "POST":
            role = request.form.get("role")
            if role == "admin":
                if request.form.get("password") == app.config["ADMIN_PASSWORD"]:
                    session["is_admin"] = True
                    return redirect(url_for("admin_panel"))
                flash("Incorrect admin password.")
            elif role == "teamlead":
                session["is_teamlead"] = True
                return redirect(url_for("teamlead_panel"))
        return render_template("staff_login.html")

    @app.route("/staff/logout")
    def staff_logout():
        session.pop("is_admin", None)
        session.pop("is_teamlead", None)
        return redirect(url_for("login"))

    # ---------------- ADMIN PANEL ----------------
    @app.route("/admin")
    @admin_required
    def admin_panel():
        orders = Order.query.order_by(Order.created_at.desc()).all()
        frames_ = Frame.query.all()
        campaigns = Campaign.query.all()
        users = User.query.all()
        qr_enabled = AdminSetting.query.get("qr_enabled").value == "true"
        payment_note = AdminSetting.query.get("payment_note").value
        return render_template("admin.html", orders=orders, frames=frames_,
                                campaigns=campaigns, users=users,
                                qr_enabled=qr_enabled, payment_note=payment_note)

    @app.route("/admin/order/<int:order_id>/status", methods=["POST"])
    @admin_required
    def admin_update_order(order_id):
        order = Order.query.get_or_404(order_id)
        order.status = request.form.get("status", order.status)
        db.session.commit()
        flash(f"{order.order_code} updated to {order.status}.")
        return redirect(url_for("admin_panel"))

    @app.route("/admin/stock/<int:frame_id>", methods=["POST"])
    @admin_required
    def admin_update_stock(frame_id):
        frame = Frame.query.get_or_404(frame_id)
        try:
            frame.stock = max(0, int(request.form.get("stock", frame.stock)))
        except ValueError:
            pass
        db.session.commit()
        flash(f"{frame.name} stock set to {frame.stock}.")
        return redirect(url_for("admin_panel"))

    @app.route("/admin/campaign/<int:campaign_id>/toggle", methods=["POST"])
    @admin_required
    def admin_toggle_campaign(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        campaign.active = not campaign.active
        db.session.commit()
        return redirect(url_for("admin_panel"))

    @app.route("/admin/qr/toggle", methods=["POST"])
    @admin_required
    def admin_toggle_qr():
        setting = AdminSetting.query.get("qr_enabled")
        setting.value = "false" if setting.value == "true" else "true"
        db.session.commit()
        return redirect(url_for("admin_panel"))

    @app.route("/admin/qr/note", methods=["POST"])
    @admin_required
    def admin_update_qr_note():
        setting = AdminSetting.query.get("payment_note")
        setting.value = request.form.get("note", setting.value)
        db.session.commit()
        return redirect(url_for("admin_panel"))

    # ---------------- TEAM LEADER PANEL ----------------
    @app.route("/teamlead")
    @teamlead_required
    def teamlead_panel():
        orders = Order.query.filter(
            Order.status.in_(["Approved", "Processing", "Shipped"])
        ).order_by(Order.created_at.desc()).all()
        delivered_count = Order.query.filter_by(status="Delivered").count()
        return render_template("teamlead.html", orders=orders, delivered_count=delivered_count)

    @app.route("/teamlead/order/<int:order_id>/status", methods=["POST"])
    @teamlead_required
    def teamlead_update_order(order_id):
        order = Order.query.get_or_404(order_id)
        # Team leaders may only progress fulfilment steps, never approve/cancel
        allowed_next = {"Approved": "Processing", "Processing": "Shipped", "Shipped": "Delivered"}
        next_status = allowed_next.get(order.status)
        if next_status:
            order.status = next_status
            db.session.commit()
            flash(f"{order.order_code} moved to {next_status}.")
        return redirect(url_for("teamlead_panel"))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
