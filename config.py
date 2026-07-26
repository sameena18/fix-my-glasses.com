import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # SQLite by default. To switch to MySQL, set DATABASE_URL, e.g.:
    # mysql+pymysql://user:password@localhost/fixmyglasses
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'fixmyglasses.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

    # --- Admin / staff access ---
    # Per project spec: admin panel password is 2002. Change this for real deployments,
    # ideally via environment variable + hashed storage.
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "2002")

    # --- Mock OTP mode ---
    # True = OTP is fixed/mocked and shown on screen (no SMS account needed).
    # Set to False once TWILIO_* / FAST2SMS_* env vars below are filled in.
    OTP_MOCK_MODE = os.environ.get("OTP_MOCK_MODE", "true").lower() == "true"
    MOCK_OTP_CODE = "1234"

    # Fill these in when you're ready to send real SMS (Twilio example)
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")

    # --- Mock payment mode ---
    # True = "Pay" just shows a QR image and a demo "confirm payment" button.
    # Set to False once RAZORPAY_* env vars are filled in and payment.py webhook is wired up.
    PAYMENT_MOCK_MODE = os.environ.get("PAYMENT_MOCK_MODE", "true").lower() == "true"
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
