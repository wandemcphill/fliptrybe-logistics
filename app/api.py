import os
from datetime import datetime
from flask import Blueprint, request, jsonify, url_for, current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from app import db
from app.models import Listing, User, Order

api = Blueprint('api', __name__)


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=None):
    try:
        return int(value)
    except Exception:
        return default


def _listing_image_url(filename):
    if not filename:
        return ""
    try:
        return url_for('static', filename=f"uploads/products/{filename}", _external=True)
    except Exception:
        return f"/static/uploads/products/{filename}"


def _listing_to_dict(item):
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "price": item.price,
        "category": item.category,
        "state": item.state,
        "status": item.status,
        "image": _listing_image_url(item.image_filename),
        "image_path": item.image_filename,
        "user_id": item.user_id,
        "merchant_id": item.user_id,
        "owner_id": item.user_id,
        "created_at": item.date_posted.isoformat() if item.date_posted else None,
        "is_demo": False,
    }


def _get_or_create_demo_user():
    user = User.query.order_by(User.id.asc()).first()
    if user:
        return user
    demo = User(
        name="Demo Merchant",
        email="demo@fliptrybe.local",
        phone="0000000000",
        password_hash=generate_password_hash("demo"),
        wallet_balance=0.0,
        merchant_tier="Novice",
    )
    db.session.add(demo)
    db.session.commit()
    return demo


def _save_listing_image(file_storage):
    if not file_storage:
        return None
    filename = secure_filename(file_storage.filename or "")
    if not filename:
        return None
    uploads_root = os.path.join(current_app.root_path, "static", "uploads", "products")
    os.makedirs(uploads_root, exist_ok=True)
    file_storage.save(os.path.join(uploads_root, filename))
    return filename


def _query_listings(q=None, state=None, category=None):
    try:
        query = Listing.query
        if q:
            query = query.filter((Listing.title.ilike(f"%{q}%")) | (Listing.description.ilike(f"%{q}%")))
        if state:
            query = query.filter_by(state=state)
        if category:
            query = query.filter_by(category=category)

        return query.order_by(Listing.date_posted.desc()).all()
    except SQLAlchemyError:
        return []


def _build_listing_payload():
    payload = request.get_json(silent=True) or {}
    if request.form:
        payload = dict(request.form)
    return payload


def _create_listing_from_payload(payload, category_override=None):
    title = (payload.get("title") or "").strip()
    if not title:
        return None, ("title_required", 400)

    description = (payload.get("description") or "").strip()
    price = _safe_float(payload.get("price"), 0.0)
    category = (category_override or payload.get("category") or "").strip() or "Listing"
    state = (payload.get("state") or "").strip() or "Lagos"

    user_id = _safe_int(payload.get("user_id")) or _safe_int(payload.get("merchant_id")) or _safe_int(payload.get("owner_id"))
    if user_id:
        user = User.query.get(user_id)
    else:
        user = _get_or_create_demo_user()

    image_filename = None
    if "image" in request.files:
        image_filename = _save_listing_image(request.files.get("image"))

    item = Listing(
        title=title,
        description=description,
        price=price,
        category=category,
        state=state,
        image_filename=image_filename or "default.jpg",
        date_posted=datetime.utcnow(),
        status="Available",
        user_id=user.id,
    )
    db.session.add(item)
    db.session.commit()
    return item, None


@api.get("/listings")
def list_listings():
    q = (request.args.get("q") or "").strip()
    state = (request.args.get("state") or "").strip()
    category = (request.args.get("category") or "").strip()
    items = _query_listings(q=q, state=state, category=category)
    return jsonify([_listing_to_dict(item) for item in items]), 200


@api.get("/listings/<int:listing_id>")
def get_listing(listing_id):
    try:
        item = Listing.query.get_or_404(listing_id)
        return jsonify(_listing_to_dict(item)), 200
    except SQLAlchemyError:
        return jsonify({"error": "db_unavailable"}), 503


@api.post("/listings")
def create_listing():
    try:
        payload = _build_listing_payload()
        item, err = _create_listing_from_payload(payload)
        if err:
            return jsonify({"error": err[0]}), err[1]
        return jsonify({"listing": _listing_to_dict(item)}), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "db_unavailable"}), 503


@api.get("/shortlets")
def list_shortlets():
    q = (request.args.get("q") or "").strip()
    state = (request.args.get("state") or "").strip()
    items = _query_listings(q=q, state=state, category="Shortlet")
    return jsonify([_listing_to_dict(item) for item in items]), 200


@api.post("/shortlets")
def create_shortlet():
    payload = _build_listing_payload()
    if "price" not in payload and "nightly_price" in payload:
        payload["price"] = payload.get("nightly_price")
    try:
        item, err = _create_listing_from_payload(payload, category_override="Shortlet")
        if err:
            return jsonify({"error": err[0]}), err[1]
        return jsonify({"listing": _listing_to_dict(item)}), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "db_unavailable"}), 503


@api.get("/shortlets/popular")
def popular_shortlets():
    items = _query_listings(category="Shortlet")
    return jsonify([_listing_to_dict(item) for item in items]), 200


@api.post("/shortlets/<int:shortlet_id>/review")
def review_shortlet(shortlet_id):
    return jsonify({"ok": True}), 200


@api.post("/shortlets/<int:shortlet_id>/book")
def book_shortlet(shortlet_id):
    return jsonify({"ok": True, "booking_id": shortlet_id}), 200


@api.get("/declutter")
def list_declutter():
    q = (request.args.get("q") or "").strip()
    state = (request.args.get("state") or "").strip()
    items = _query_listings(q=q, state=state, category="Declutter")
    return jsonify([_listing_to_dict(item) for item in items]), 200


@api.post("/declutter")
def create_declutter():
    payload = _build_listing_payload()
    try:
        item, err = _create_listing_from_payload(payload, category_override="Declutter")
        if err:
            return jsonify({"error": err[0]}), err[1]
        return jsonify({"listing": _listing_to_dict(item)}), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "db_unavailable"}), 503


@api.post("/orders")
def create_order():
    payload = request.get_json(silent=True) or {}
    listing_id = _safe_int(payload.get("listing_id"))
    amount = _safe_float(payload.get("amount"), 0.0)
    buyer_id = _safe_int(payload.get("buyer_id")) or _safe_int(payload.get("user_id"))
    if not buyer_id:
        buyer = _get_or_create_demo_user()
        buyer_id = buyer.id

    if not listing_id or amount <= 0:
        return jsonify({"error": "invalid_payload"}), 400

    try:
        order = Order(
            total_price=amount,
            buyer_id=buyer_id,
            listing_id=listing_id,
            status="Escrowed",
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({"order": {"id": order.id, "status": order.status, "total_price": order.total_price}}), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "db_unavailable"}), 503


@api.get("/orders/my")
def my_orders():
    buyer_id = _safe_int(request.args.get("buyer_id"))
    try:
        query = Order.query
        if buyer_id:
            query = query.filter_by(buyer_id=buyer_id)
        items = query.order_by(Order.timestamp.desc()).all()
        data = [{"id": o.id, "status": o.status, "total_price": o.total_price} for o in items]
        return jsonify(data), 200
    except SQLAlchemyError:
        return jsonify([]), 200


@api.get("/orders/<int:order_id>")
def get_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        return jsonify({"id": order.id, "status": order.status, "total_price": order.total_price}), 200
    except SQLAlchemyError:
        return jsonify({"error": "db_unavailable"}), 503


@api.get("/orders/<int:order_id>/timeline")
def order_timeline(order_id):
    return jsonify({"items": []}), 200


@api.post("/orders/<int:order_id>/merchant/accept")
def merchant_accept(order_id):
    return jsonify({"ok": True}), 200


@api.post("/orders/<int:order_id>/driver/assign")
def assign_driver(order_id):
    return jsonify({"ok": True}), 200


@api.post("/orders/<int:order_id>/driver/status")
def driver_status(order_id):
    return jsonify({"ok": True}), 200


def _ok(payload=None, status=200):
    data = {"ok": True}
    if isinstance(payload, dict):
        data.update(payload)
    return jsonify(data), status


def _items(items=None):
    return jsonify({"items": items or []}), 200


def _empty_list():
    return jsonify([]), 200


# --- AUTH ---

@api.post("/auth/register")
def auth_register():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name") or "Demo User"
    email = payload.get("email") or "demo@fliptrybe.local"
    user = {
        "id": 1,
        "name": name,
        "email": email,
        "wallet_balance": 0,
        "is_verified": False,
        "tier": "Novice",
        "role": "buyer",
        "kyc_tier": 0,
        "is_available": False,
    }
    return jsonify({"token": "demo-token", "user": user}), 200


@api.post("/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email") or "demo@fliptrybe.local"
    user = {
        "id": 1,
        "name": "Demo User",
        "email": email,
        "wallet_balance": 0,
        "is_verified": False,
        "tier": "Novice",
        "role": "buyer",
        "kyc_tier": 0,
        "is_available": False,
    }
    return jsonify({"token": "demo-token", "user": user}), 200


@api.get("/auth/me")
def auth_me():
    user = {
        "id": 1,
        "name": "Demo User",
        "email": "demo@fliptrybe.local",
        "wallet_balance": 0,
        "is_verified": False,
        "tier": "Novice",
        "role": "buyer",
        "kyc_tier": 0,
        "is_available": False,
    }
    return jsonify(user), 200


@api.post("/auth/set-role")
def auth_set_role():
    return _ok({"role": (request.get_json(silent=True) or {}).get("role", "buyer")})


# --- FEED / DISCOVERY ---

@api.get("/feed")
def feed():
    items = _query_listings()
    return _items([_listing_to_dict(item) for item in items])


@api.get("/locations")
def locations():
    return jsonify({"states": [], "cities": [], "lgas": []}), 200


@api.get("/heatmap")
def heatmap():
    return jsonify({"items": []}), 200


@api.get("/heat")
def heat():
    return jsonify({"value": 0}), 200


@api.get("/metrics")
def metrics():
    return jsonify({
        "mode": "mock",
        "users": 0,
        "listings": 0,
        "gmv": 0,
        "commissions_total": 0,
    }), 200


@api.get("/kpis/merchant")
def kpis_merchant():
    return jsonify({"ok": True, "listings": 0, "orders": 0, "sales": 0}), 200


@api.get("/leaderboards/featured")
def leaderboard_featured():
    return _items([])


@api.get("/leaderboards/states")
def leaderboard_states():
    return jsonify({"items": {}}), 200


@api.get("/leaderboards/cities")
def leaderboard_cities():
    return jsonify({"items": {}}), 200


@api.get("/public/sales_ticker")
def sales_ticker():
    return jsonify({"items": []}), 200


@api.get("/fees/quote")
def fees_quote():
    return jsonify({"fee": 0, "currency": "NGN"}), 200


# --- RIDES ---

@api.post("/ride/request")
def ride_request():
    return _ok({"ride_id": 1})


# --- ADMIN ---

@api.get("/admin/overview")
def admin_overview():
    return jsonify({
        "ok": True,
        "counts": {"users": 0, "listings": 0, "orders": 0},
    }), 200


@api.get("/admin/users")
def admin_users():
    return _empty_list()


@api.post("/admin/users/<int:user_id>/disable")
def admin_disable_user(user_id):
    return _ok({"user_id": user_id})


@api.get("/admin/listings")
def admin_listings():
    return _empty_list()


@api.post("/admin/listings/<int:listing_id>/disable")
def admin_disable_listing(listing_id):
    return _ok({"listing_id": listing_id})


@api.get("/admin/audit")
def admin_audit():
    return _items([])


@api.get("/admin/autopilot")
def admin_autopilot():
    return jsonify({"enabled": False}), 200


@api.post("/admin/autopilot/toggle")
def admin_autopilot_toggle():
    payload = request.get_json(silent=True) or {}
    return jsonify({"enabled": bool(payload.get("enabled"))}), 200


@api.post("/admin/autopilot/tick")
def admin_autopilot_tick():
    return _ok({"processed": 0})


@api.get("/admin/notify-queue")
def admin_notify_queue():
    return _items([])


@api.post("/admin/notifications/process")
def admin_notifications_process():
    return _ok({"processed": 0})


@api.post("/admin/notifications/broadcast")
def admin_notifications_broadcast():
    return _ok({"sent": 0})


@api.get("/admin/commission")
def admin_commission_list():
    return _empty_list()


@api.post("/admin/commission")
def admin_commission_upsert():
    return _ok()


@api.post("/admin/commission/<int:rule_id>/disable")
def admin_commission_disable(rule_id):
    return _ok({"id": rule_id})


# --- WALLET / PAYOUTS ---

@api.get("/wallet")
def wallet():
    return jsonify({"wallet": {"balance": 0, "currency": "NGN"}}), 200


@api.get("/wallet/ledger")
def wallet_ledger():
    return _empty_list()


@api.post("/wallet/topup-demo")
def wallet_topup_demo():
    return _ok()


@api.get("/wallet/payouts")
def wallet_payouts():
    return _empty_list()


@api.post("/wallet/payouts")
def wallet_request_payout():
    return _ok()


@api.get("/wallet/admin/payouts")
def wallet_admin_payouts():
    return _empty_list()


@api.get("/wallet/analytics")
def wallet_analytics():
    return jsonify({"total": 0, "inflow": 0, "outflow": 0}), 200


@api.post("/wallet/payouts/<int:payout_id>/admin/approve")
def wallet_admin_approve(payout_id):
    return _ok({"payout_id": payout_id})


@api.post("/wallet/payouts/<int:payout_id>/admin/reject")
def wallet_admin_reject(payout_id):
    return _ok({"payout_id": payout_id})


@api.post("/wallet/payouts/<int:payout_id>/admin/process")
def wallet_admin_process(payout_id):
    return _ok({"payout_id": payout_id})


@api.post("/wallet/payouts/<int:payout_id>/admin/pay")
def wallet_admin_pay(payout_id):
    return _ok({"payout_id": payout_id})


@api.post("/wallet/payouts/<int:payout_id>/admin/mark-paid")
def wallet_admin_mark_paid(payout_id):
    return _ok({"payout_id": payout_id})


# --- PAYMENTS ---

@api.post("/payments/initialize")
def payments_initialize():
    return jsonify({"ok": True, "reference": "demo-ref"}), 200


@api.post("/payments/confirm")
def payments_confirm():
    return _ok({"reference": (request.get_json(silent=True) or {}).get("reference", "demo-ref")})


# --- PAYOUT RECIPIENTS ---

@api.get("/payout/recipient")
def payout_recipient_get():
    return jsonify({"recipient": None}), 200


@api.post("/payout/recipient")
def payout_recipient_set():
    return _ok()


# --- RECEIPTS ---

@api.get("/receipts")
def receipts_list():
    return jsonify({"items": []}), 200


@api.post("/receipts/demo")
def receipts_demo():
    return _ok({"receipt_id": 1}, status=201)


@api.get("/receipts/<int:receipt_id>/pdf")
def receipts_pdf(receipt_id):
    return jsonify({"ok": True, "url": f"/api/receipts/{receipt_id}/pdf"}), 200


# --- SETTINGS ---

@api.get("/settings")
def settings_get():
    return jsonify({"settings": {}}), 200


@api.post("/settings")
def settings_save():
    return _ok()


# --- SUPPORT ---

@api.get("/support/tickets")
def support_tickets():
    return jsonify({"items": []}), 200


@api.post("/support/tickets")
def support_tickets_create():
    return _ok({"ticket_id": 1})


@api.post("/support/tickets/<int:ticket_id>/status")
def support_tickets_status(ticket_id):
    return _ok({"ticket_id": ticket_id})


# --- NOTIFICATIONS ---

@api.get("/notify/inbox")
def notify_inbox():
    return _empty_list()


@api.post("/notify/flush-demo")
def notify_flush_demo():
    return _ok()


# --- DRIVERS ---

@api.get("/drivers")
def drivers_list():
    return _empty_list()


@api.get("/driver/jobs")
def driver_jobs():
    return _empty_list()


@api.post("/driver/jobs/<int:job_id>/accept")
def driver_job_accept(job_id):
    return _ok({"job_id": job_id})


@api.post("/driver/jobs/<int:job_id>/status")
def driver_job_status(job_id):
    return _ok({"job_id": job_id})


@api.get("/driver/offers")
def driver_offers():
    return _empty_list()


@api.post("/driver/offers/<int:offer_id>/accept")
def driver_offer_accept(offer_id):
    return _ok({"offer_id": offer_id})


@api.post("/driver/offers/<int:offer_id>/reject")
def driver_offer_reject(offer_id):
    return _ok({"offer_id": offer_id})


@api.post("/driver/availability")
def driver_availability():
    return _ok()


@api.get("/driver/active")
def driver_active():
    return jsonify({"job": None}), 200


@api.get("/driver/profile")
def driver_profile():
    return jsonify({"profile": {}}), 200


@api.post("/driver/profile")
def driver_profile_save():
    return _ok()


# --- MERCHANTS ---

@api.get("/merchant/orders")
def merchant_orders():
    return _empty_list()


@api.get("/merchant/leaderboard")
def merchant_leaderboard():
    return _empty_list()


@api.get("/merchant/kpis")
def merchant_kpis():
    return jsonify({"ok": True, "listings": 0, "orders": 0, "sales": 0}), 200


@api.get("/merchant/drivers")
def merchant_drivers():
    return _empty_list()


@api.get("/merchants/top")
def merchants_top():
    return _items([])


@api.get("/merchants/<int:user_id>")
def merchant_detail(user_id):
    return jsonify({"id": user_id, "name": "Demo Merchant", "score": 0, "orders": 0, "listings": 0}), 200


@api.post("/merchants/<int:user_id>/simulate-sale")
def merchant_simulate_sale(user_id):
    return _ok({"user_id": user_id})


@api.post("/merchants/<int:user_id>/review")
def merchant_review(user_id):
    return _ok({"user_id": user_id})


@api.post("/merchants/profile")
def merchant_profile():
    return _ok()


# --- KYC ---

@api.get("/kyc/status")
def kyc_status():
    return jsonify({"status": "pending"}), 200


@api.post("/kyc/submit")
def kyc_submit():
    return _ok({"status": "received"})


@api.post("/kyc/admin/set")
def kyc_admin_set():
    return _ok()
