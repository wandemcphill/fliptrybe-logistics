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
