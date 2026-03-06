from .vector_store import add_knowledge, collection_count

# ---------------------------------------------------------------------------
# All the domain knowledge your RAG bot can draw from.
# Add more entries here and re-start the service — they load automatically.
# ---------------------------------------------------------------------------
KNOWLEDGE = [
    # ── Auth & Account ──────────────────────────────────────────────────────
    {
        "id": "qa_register",
        "text": (
            "Q: How do I register on Vestique? "
            "A: Click 'Sign Up', enter your email, full name and password, "
            "then choose your role (Customer, Designer, Boutique Owner or Tailor) and submit."
        ),
    },
    {
        "id": "qa_verify_email",
        "text": (
            "Q: How do I verify my email? "
            "A: After registration a 6-digit OTP is sent to your email. "
            "Open the verification page and enter that code within 10 minutes."
        ),
    },
    {
        "id": "qa_2fa",
        "text": (
            "Q: How do I enable two-factor authentication (2FA)? "
            "A: Go to Profile → Security → Enable 2FA. "
            "Choose between TOTP (Google Authenticator) or SMS, then follow the on-screen steps."
        ),
    },
    {
        "id": "qa_reset_password",
        "text": (
            "Q: How do I reset my password? "
            "A: On the login page click 'Forgot Password', enter your email address, "
            "wait for the OTP, and set a new password."
        ),
    },
    {
        "id": "qa_roles",
        "text": (
            "Q: What user roles are available on Vestique? "
            "A: There are four roles — Customer (browse & order), "
            "Designer (upload designs), Boutique Owner (manage a boutique), "
            "and Tailor (accept tailoring jobs)."
        ),
    },
    # ── Orders & Shopping ───────────────────────────────────────────────────
    {
        "id": "qa_place_order",
        "text": (
            "Q: How do I place an order? "
            "A: Browse the catalogue, add items to your cart, proceed to checkout, "
            "enter your shipping address and payment details, then confirm."
        ),
    },
    {
        "id": "qa_cancel_order",
        "text": (
            "Q: Can I cancel an order? "
            "A: Yes, you can cancel within 24 hours of placing the order from "
            "My Orders → Cancel. After 24 hours contact support."
        ),
    },
    {
        "id": "qa_track_order",
        "text": (
            "Q: How do I track my order? "
            "A: Go to My Orders, select the order and click 'Track'. "
            "You will see real-time delivery status and an estimated delivery date."
        ),
    },
    {
        "id": "qa_returns",
        "text": (
            "Q: What is the return policy? "
            "A: Items can be returned within 7 days of delivery if unused and in original packaging. "
            "Custom or tailored items are non-returnable."
        ),
    },
    # ── Payments ────────────────────────────────────────────────────────────
    {
        "id": "qa_payment_methods",
        "text": (
            "Q: What payment methods are accepted? "
            "A: Vestique accepts credit/debit cards, UPI, net banking and cash on delivery "
            "(for eligible pin codes)."
        ),
    },
    {
        "id": "qa_refund",
        "text": (
            "Q: How long does a refund take? "
            "A: Refunds are processed within 5-7 business days after the returned item is received. "
            "The amount is credited back to the original payment method."
        ),
    },
    # ── Designers & Boutiques ───────────────────────────────────────────────
    {
        "id": "qa_upload_design",
        "text": (
            "Q: How does a designer upload a new design? "
            "A: Log in as Designer, go to Dashboard → My Designs → Upload Design, "
            "add photos, set pricing, choose fabric options and publish."
        ),
    },
    {
        "id": "qa_boutique_setup",
        "text": (
            "Q: How do I set up my boutique? "
            "A: Register as Boutique Owner, complete your profile, add your shop name, "
            "location and business details, then start listing products."
        ),
    },
    # ── Tailoring ───────────────────────────────────────────────────────────
    {
        "id": "qa_custom_tailoring",
        "text": (
            "Q: How do I request custom tailoring? "
            "A: On the product page click 'Request Tailoring', enter your measurements "
            "and any special instructions, then choose an available tailor."
        ),
    },
    {
        "id": "qa_tailor_accept",
        "text": (
            "Q: How does a tailor accept a job? "
            "A: Tailors see new job requests in their Dashboard. "
            "They can review measurements and customer notes, then Accept or Decline."
        ),
    },
    # ── Support ─────────────────────────────────────────────────────────────
    {
        "id": "qa_contact_support",
        "text": (
            "Q: How do I contact Vestique support? "
            "A: Use the in-app chat (this assistant), email support@vestique.com, "
            "or call our helpline Monday–Saturday 9 AM–6 PM IST."
        ),
    },
    {
        "id": "qa_app_download",
        "text": (
            "Q: Is there a Vestique mobile app? "
            "A: Yes, the Vestique app is available on the Google Play Store and Apple App Store."
        ),
    },
]


def load_knowledge() -> None:
    """
    Upsert all knowledge entries into ChromaDB.
    Safe to call on every startup — duplicate IDs are just overwritten.
    """
    loaded = 0
    for entry in KNOWLEDGE:
        try:
            add_knowledge(entry["id"], entry["text"])
            loaded += 1
        except Exception as e:
            print(f"⚠️  Could not load '{entry['id']}': {e}")

    print(f"✅ Knowledge base ready — {loaded}/{len(KNOWLEDGE)} entries loaded.")