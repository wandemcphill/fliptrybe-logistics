import os, secrets, logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Listing, Order, Transaction, Notification, Dispute, Review
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

# ==========================================
# 🛠️ HELPER: IMAGE SAVER
# ==========================================
def save_file(file_obj, folder):
    if not file_obj: return None
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(file_obj.filename)
    filename = random_hex + f_ext
    path = os.path.join(current_app.root_path, 'static/uploads', folder, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_obj.save(path)
    return filename

# ==========================================
# 🏠 LANDING NODE
# ==========================================
@main.route("/")
@main.route("/home")
def index():
    items = Listing.query.filter_by(status='Available').order_by(Listing.created_at.desc()).limit(4).all()
    return render_template('index.html', items=items)

# ==========================================
# ⚙️ SETTINGS NODE
# ==========================================
@main.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    # Handle Profile Update
    if request.method == 'POST':
        # 1. Update Text Data
        current_user.name = request.form.get('name')
        current_user.phone = request.form.get('phone')
        
        # 2. Update Pilot Data
        if current_user.is_driver:
            current_user.vehicle_type = request.form.get('vehicle_type')
            current_user.vehicle_year = request.form.get('vehicle_year')
            current_user.license_plate = request.form.get('license_plate')

        # 3. Update Profile Picture
        if request.files.get('profile_pic'):
            pic_file = save_file(request.files['profile_pic'], 'avatars')
            current_user.image_file = pic_file

        # 4. Update Password (Optional)
        new_pass = request.form.get('password')
        if new_pass:
            current_user.set_password(new_pass)

        db.session.commit()
        flash('Terminal Data Synchronized.', 'success')
        return redirect(url_for('main.settings'))

    return render_template('settings.html', title='Account Settings')

# ==========================================
# 🛡️ KYC SUBMISSION NODE (New!)
# ==========================================
@main.route("/settings/kyc", methods=['POST'])
@login_required
def submit_kyc():
    # 1. Capture Files
    selfie = request.files.get('kyc_selfie')
    id_card = request.files.get('kyc_id')
    video = request.files.get('kyc_video')

    if selfie and id_card:
        current_user.kyc_selfie_file = save_file(selfie, 'kyc_selfies')
        current_user.kyc_id_card_file = save_file(id_card, 'kyc_docs')
        if video:
            current_user.kyc_video_file = save_file(video, 'kyc_videos')
        
        db.session.commit()
        flash('Identity Signals Transmitted. Awaiting HQ Verification.', 'success')
    else:
        flash('Signal Lost: Selfie and ID are mandatory.', 'error')

    return redirect(url_for('main.settings'))

# ==========================================
# 🛰️ MARKETPLACE
# ==========================================
@main.route('/market')
def market():
    query_signal = request.args.get('q', '')
    section_signal = request.args.get('section', '')
    state_signal = request.args.get('state', '')
    cat_signal = request.args.get('category', '')
    min_p = request.args.get('min_price', type=float)
    max_p = request.args.get('max_price', type=float)

    listings_query = Listing.query.filter_by(status='Available')

    if section_signal == 'shortlet':
        listings_query = listings_query.filter(Listing.section == 'shortlet')
    elif section_signal == 'declutter':
        listings_query = listings_query.filter(Listing.section != 'shortlet')

    if query_signal: listings_query = listings_query.filter(Listing.title.ilike(f'%{query_signal}%'))
    if state_signal: listings_query = listings_query.filter(Listing.state == state_signal)
    if cat_signal: listings_query = listings_query.filter(Listing.category == cat_signal)
    if min_p is not None: listings_query = listings_query.filter(Listing.price >= min_p)
    if max_p is not None: listings_query = listings_query.filter(Listing.price <= max_p)

    listings = listings_query.order_by(Listing.created_at.desc()).all()
    active_hubs = db.session.query(Listing.state).filter_by(status='Available').distinct().all()
    active_hubs = [h[0] for h in active_hubs if h[0]]

    return render_template('market.html', items=listings, hubs=active_hubs, current_filters=request.args)

# ==========================================
# 📦 ASSET DETAIL
# ==========================================
@main.route("/listing/<int:listing_id>")
def product_detail(listing_id):
    item = Listing.query.get_or_404(listing_id)
    related_items = Listing.query.filter(
        Listing.category == item.category,
        Listing.id != item.id,
        Listing.status == 'Available'
    ).order_by(Listing.created_at.desc()).limit(3).all()

    return render_template('product_detail.html', item=item, title=item.title, related_items=related_items)

# ==========================================
# 🤝 TRADE INITIALIZATION
# ==========================================
@main.route("/trade/initiate/<int:listing_id>", methods=['POST'])
@login_required
def initiate_trade(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.seller == current_user:
        flash("You cannot trade with yourself.", "warning")
        return redirect(url_for('main.product_detail', listing_id=listing_id))
    
    flash(f"Trade initialized for {listing.title}! (Escrow System Loading...)", "success")
    return redirect(url_for('main.product_detail', listing_id=listing_id))

# ==========================================
# 👤 PROFILE NODE
# ==========================================
@main.route("/user/<string:username>")
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_profile.html', user=user)

# ==========================================
# 🚀 DASHBOARD REDIRECTOR
# ==========================================
@main.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.admin_panel'))
    return redirect(url_for('main.market'))