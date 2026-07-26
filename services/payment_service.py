"""
Payment handling.

Mock mode (default): the /payment page shows a QR placeholder image and a
"I've completed the payment" button that immediately marks the order paid.
No money moves and no external account is needed.

Real mode: set PAYMENT_MOCK_MODE=false and fill in RAZORPAY_* credentials.
Typical real flow:
  1. Create a Razorpay Order (amount, currency) server-side.
  2. Render Razorpay's checkout / a dynamic UPI QR pointing at that order.
  3. Razorpay calls your /payment/webhook route on success.
  4. Verify the webhook signature, then mark the order paid.
"""
from flask import current_app


def get_qr_context(order_amount: int) -> dict:
    """Returns whatever the payment template needs to render the QR step."""
    if current_app.config["PAYMENT_MOCK_MODE"]:
        return {
            "mode": "mock",
            "upi_id": "fixmyglasses@upi",
            "amount": order_amount,
            "note": "Demo mode — this QR is a placeholder. Click the button below to simulate payment.",
        }
    else:
        # Plug in real Razorpay order creation here, e.g.:
        # import razorpay
        # client = razorpay.Client(auth=(current_app.config["RAZORPAY_KEY_ID"],
        #                                 current_app.config["RAZORPAY_KEY_SECRET"]))
        # rp_order = client.order.create({"amount": order_amount * 100, "currency": "INR"})
        # return {"mode": "live", "razorpay_order_id": rp_order["id"], "amount": order_amount}
        raise NotImplementedError(
            "Real payments are not configured yet. Set PAYMENT_MOCK_MODE=true, "
            "or fill in RAZORPAY_* config and implement the live branch here."
        )


def confirm_mock_payment() -> bool:
    """In mock mode, confirming payment always succeeds."""
    return True
