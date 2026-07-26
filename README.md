# FixMyGlasses.com

A full-stack eyewear ordering website: mobile OTP login, home campaigns/ads,
frame + lens configuration (zero power / powered / upload prescription,
single vision / progressive / zero power / tinted lenses), QR/UPI payment,
order ID + live tracking, and three panels — **User**, **Team Leader**, and
**Admin** (default password `2002`).

Stack: Python (Flask) · SQLAlchemy ORM · SQLite (swappable to MySQL) ·
HTML/Jinja2 templates · vanilla CSS + JavaScript.

## Quick start

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

The database (SQLite) and demo data are created automatically on first run —
no setup needed. To reset it, just delete `instance/fixmyglasses.db` and
restart the app.

## Logins (demo/mock mode)

| Role | How to log in |
|---|---|
| Customer | Enter any 10-digit mobile number → OTP is always **1234** (shown on screen) |
| Admin | Home → profile icon → "Staff / Admin login" → password **2002** |
| Team Leader | Same staff login screen → "Login as Team Leader" (no password) |

Mock mode means no SMS provider or payment gateway account is required to
try the whole flow end to end. When you're ready to go live, see below.

## Project structure

```
app.py                     Routes / controllers
config.py                  All settings (DB, admin password, mock toggles)
models.py                  SQLAlchemy models: User, Frame, Order, Campaign, AdminSetting
schema.sql                 Same schema, hand-written for MySQL if you skip SQLAlchemy's auto-create
services/
  otp_service.py           OTP generation + verification (mock now, Twilio wiring point)
  payment_service.py       QR/payment context (mock now, Razorpay wiring point)
templates/                 Jinja2 templates (one per screen)
static/css/style.css       All styling (minimalist, single stylesheet)
static/uploads/            Uploaded prescription files land here
```

## Feature map → code

- **Mobile + OTP login** — `login`/`verify_otp` routes in `app.py`, logic in `services/otp_service.py`
- **Home campaigns/ads** — `Campaign` model; toggle live from the Admin → "Ads & Campaigns" tab
- **Frame → lens configuration** — `/frames` → `/configure` (power type, prescription upload, lens type) → `/summary`
- **QR payment** — `/payment` route, logic in `services/payment_service.py`
- **Order ID + tracking** — `Order` model (`order_code`, `status`); statuses: Pending → Approved → Processing → Shipped → Delivered (or Cancelled)
- **User panel** — `/my-orders`, `/` (home), profile
- **Admin panel** (password `2002`) — `/admin`: approve/cancel orders, edit stock, toggle QR payments + note, view users, run/pause campaigns
- **Team Leader panel** — `/teamlead`: can only progress Approved → Processing → Shipped → Delivered; cannot approve, cancel, or touch stock/QR/campaigns

## Going from mock to real

**Real SMS OTP** (e.g. Twilio):
1. `pip install twilio` (already listed, commented, in `requirements.txt`)
2. Set `OTP_MOCK_MODE=false` and fill in `TWILIO_*` in your `.env`
3. Implement `_send_real_sms()` in `services/otp_service.py` (a working example is commented in the file)

**Real QR/UPI payment** (e.g. Razorpay):
1. `pip install razorpay`
2. Set `PAYMENT_MOCK_MODE=false` and fill in `RAZORPAY_*` in your `.env`
3. Implement the live branch in `services/payment_service.get_qr_context()` and add a webhook route to verify payment signatures before marking an order paid — don't trust a client-side "I've paid" click for real money.

**Switching SQLite → MySQL:**
1. `pip install pymysql`
2. Create the database using `schema.sql`, or just point `DATABASE_URL` at an empty
   MySQL database and let `db.create_all()` build the tables for you:
   ```
   DATABASE_URL=mysql+pymysql://user:password@localhost/fixmyglasses
   ```

## Security notes before you go live

- The `2002` admin password is a plaintext default straight from the spec —
  fine for a local demo, but change it (`ADMIN_PASSWORD` env var) and move to
  a hashed, per-admin login before deploying anywhere public.
- `SECRET_KEY` in `config.py` must be a long random value in production —
  it signs your login sessions.
- Validate uploaded prescription files server-side beyond the extension check
  already in place (`allowed_file()` in `app.py`) — e.g. file-size limits are
  set, but consider virus scanning if you accept public uploads at scale.
- Add HTTPS (e.g. behind Nginx + Let's Encrypt, or a platform like Render/
  Railway/PythonAnywhere) before handling real phone numbers or payments.
