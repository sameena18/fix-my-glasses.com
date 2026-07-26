"""
OTP sending/verification.

Mock mode (default): every login uses a fixed code (Config.MOCK_OTP_CODE) so you
can test the full flow with no SMS account. The code is shown right on the
verify-OTP screen with a "demo mode" banner.

Real mode: set OTP_MOCK_MODE=false and fill in TWILIO_* in your environment
(or config.py). send_otp() below is the only place you need to touch.
"""
import random
from flask import current_app

# in-memory OTP store for the demo (swap for Redis/DB in production so it
# survives restarts and works across multiple app workers)
_otp_store = {}


def generate_and_send_otp(phone: str) -> str:
    if current_app.config["OTP_MOCK_MODE"]:
        code = current_app.config["MOCK_OTP_CODE"]
    else:
        code = f"{random.randint(1000, 9999)}"
        _send_real_sms(phone, code)

    _otp_store[phone] = code
    return code


def verify_otp(phone: str, code: str) -> bool:
    expected = _otp_store.get(phone)
    return expected is not None and expected == code


def _send_real_sms(phone: str, code: str):
    """
    Wire this up once you have Twilio (or Fast2SMS) credentials.
    Example with Twilio (pip install twilio):

        from twilio.rest import Client
        client = Client(current_app.config["TWILIO_ACCOUNT_SID"],
                         current_app.config["TWILIO_AUTH_TOKEN"])
        client.messages.create(
            body=f"Your FixMyGlasses OTP is {code}",
            from_=current_app.config["TWILIO_FROM_NUMBER"],
            to=f"+91{phone}",
        )
    """
    raise NotImplementedError(
        "Real SMS sending is not configured yet. Set OTP_MOCK_MODE=true, "
        "or fill in TWILIO_* config and implement _send_real_sms()."
    )
