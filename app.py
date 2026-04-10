import hashlib
import json
import os
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.utils import secure_filename

from src.database import Database

BASE_DIR = Path(__file__).resolve().parent


def load_env_file(env_path):
    path = Path(env_path)
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
            value = value[1:-1]
        os.environ.setdefault(key, value)


load_env_file(BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "sales-management-dev-key")
db = Database()


# Helper functions
def pwd_hash(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def one(sql: str, params: tuple = None):
    """Execute a query and return the first result row, or None."""
    results = db.query(sql, params or ())
    return results[0] if results else None


def truthy(value) -> bool:
    """Check if a database value is truthy (for handling true/false strings)."""
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "on", "yes"}


def ensure_main_admin_exists() -> None:
    """
    Ensure the main admin user exists in the database.
    
    Reads MAIN_ADMIN_USERNAME and MAIN_ADMIN_PASSWORD from environment.
    If the admin user doesn't exist, creates it with 'admin' role and 'approved' status.
    
    This runs on app startup to ensure there's always an admin who can approve new users.
    """
    admin_username = os.getenv("MAIN_ADMIN_USERNAME")
    admin_password = os.getenv("MAIN_ADMIN_PASSWORD")
    
    if not admin_username or not admin_password:
        print("[WARN] MAIN_ADMIN_USERNAME or MAIN_ADMIN_PASSWORD not set in environment")
        return
    
    # Check if admin user already exists
    existing = one("SELECT id FROM users WHERE username = ?", (admin_username,))
    if existing:
        return
    
    # Create main admin user
    hashed_password = pwd_hash(admin_password)
    db.run(
        "INSERT INTO users (first_name, last_name, username, password, role, approval_status, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Admin", "User", admin_username, hashed_password, "admin", "approved", "true")
    )
    print(f"[DB] Created main admin user: {admin_username}")

STATIC_DIR = BASE_DIR / "static"
PRODUCT_UPLOADS = STATIC_DIR / "uploads" / "products"
TX_UPLOADS = STATIC_DIR / "uploads" / "transactions"
PROFILE_UPLOADS = STATIC_DIR / "uploads" / "profiles"
for p in (PRODUCT_UPLOADS, TX_UPLOADS, PROFILE_UPLOADS):
    p.mkdir(parents=True, exist_ok=True)

USER_SELECT = """
SELECT id, first_name, last_name, email, username, role, is_active,
       account_name, account_owner_name, bank_name, account_address, phone, image_path
FROM users
"""


# Initialize main admin user
ensure_main_admin_exists()


def login_required(f):
    """
    Decorator to check if user is logged in before accessing protected routes.
    Redirects to login page if user is not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login") if request.path != "/" else redirect(url_for("index")))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to check if user is logged in AND has admin role.
    Redirects to employee dashboard if user is not an admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("index"))
        if session.get("role") != "admin":
            return redirect(url_for("employee"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("admin") if session.get("role") == "admin" else url_for("employee"))
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(STATIC_DIR / "img", "logo.png")


@app.route("/signin", methods=["POST"])
def signin():
    data = request.get_json(silent=True) or {}
    first = (data.get("firstname") or "").strip()
    last = (data.get("lastname") or "").strip()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not all([first, last, username, password]):
        return jsonify({"message": "All fields are required."}), 400
    if one("SELECT id FROM users WHERE username=? LIMIT 1", (username,)):
        return jsonify({"message": "Username already exists."}), 409
    db.run(
        "INSERT INTO users (first_name, last_name, username, password, role, approval_status, is_active) VALUES (?, ?, ?, ?, 'user', 'pending', 'false')",
        (first, last, username, pwd_hash(password)),
    )
    return jsonify({"message": "Registration submitted.", "redirect": url_for("pending_approval", username=username)})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    row = one("SELECT id, password, role, is_active, COALESCE(approval_status, 'approved') FROM users WHERE username=? LIMIT 1", (username,))
    if not row:
        return jsonify({"message": "User not found."}), 404
    uid, stored, role, is_active, approval = row
    if approval == "pending":
        return jsonify({"redirect": url_for("pending_approval", username=username)})
    if approval == "declined":
        return jsonify({"message": "Registration request was declined."}), 403
    if not truthy(is_active):
        return jsonify({"message": "Account is deactivated."}), 403
    if pwd_hash(password) != stored:
        return jsonify({"message": "Incorrect password."}), 401
    session["user_id"] = uid
    session["username"] = username
    session["role"] = role
    return redirect(url_for("admin") if role == "admin" else url_for("employee"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/pending-approval")
def pending_approval():
    return render_template("pending_approval.html", username=request.args.get("username", ""))


@app.route("/api/pending-approval-status")
def pending_approval_status():
    username = (request.args.get("username") or "").strip()
    row = one("SELECT id, role, is_active, COALESCE(approval_status, 'approved') FROM users WHERE username=? LIMIT 1", (username,))
    if not row:
        return jsonify({"exists": False, "approved": False, "declined": False})
    approved = row[3] == "approved" and truthy(row[2])
    return jsonify(
        {
            "exists": True,
            "approved": approved,
            "declined": row[3] == "declined",
            "redirect": "/?approved=1" if approved else "",
        }
    )


@app.route("/admin")
@login_required
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("employee"))
    totals = one("SELECT COALESCE(SUM(CASE WHEN type='sale' THEN amount ELSE 0 END),0) as sales_total, COALESCE(SUM(CASE WHEN type='purchase' THEN amount ELSE 0 END),0) as purchase_total FROM transactions")
    sales = fnum(totals['sales_total'] if totals else 0)
    purchase = fnum(totals['purchase_total'] if totals else 0)
    top = one("SELECT COALESCE(p.name,'-') FROM transactions t LEFT JOIN product p ON p.id=t.product_id WHERE t.type='sale' GROUP BY p.name ORDER BY COALESCE(SUM(t.amount),0) DESC LIMIT 1")
    staff = one("SELECT COUNT(*) as count FROM users WHERE role='user' AND is_active='true'")
    recent = db.query("SELECT t.id, COALESCE(u.username,'system'), COALESCE(p.name,'-'), t.type, t.amount, t.status, t.created_at FROM transactions t LEFT JOIN users u ON u.id=t.user_id LEFT JOIN product p ON p.id=t.product_id ORDER BY t.id DESC LIMIT 7")
    return render_app("admin_dashboard.html", revenue=fmt(sales - purchase), revenue_value=sales - purchase, total_sales=fmt(sales), total_sales_value=sales, top_product=top['coalesce'] if top else "N/A", staff_count=int(staff['count'] if staff else 0), recent_transactions=recent)


@app.route("/employee")
@login_required
def employee():
    row = one("SELECT COUNT(*) as sale_count, COALESCE(SUM(amount),0) as total_amount FROM transactions WHERE type='sale' AND user_id=?", (session["user_id"],))
    recent = db.query("SELECT t.id, COALESCE(u.username,'system'), COALESCE(p.name,'-'), t.type, t.amount, t.status, t.created_at FROM transactions t LEFT JOIN users u ON u.id=t.user_id LEFT JOIN product p ON p.id=t.product_id ORDER BY t.id DESC LIMIT 7")
    return render_app("employee_dashboard.html", sale_count=int(row['sale_count'] if row else 0), total_sales=fmt(row['total_amount'] if row else 0), total_sales_value=fnum(row['total_amount'] if row else 0), recent_transactions=recent)


@app.route("/transaction")
@login_required
def transaction():
    totals = one("SELECT COALESCE(SUM(CASE WHEN type='sale' THEN amount ELSE 0 END),0) as sales_total, COALESCE(SUM(CASE WHEN type='purchase' THEN amount ELSE 0 END),0) as purchase_total FROM transactions")
    sales = fnum(totals['sales_total'] if totals else 0)
    purchase = fnum(totals['purchase_total'] if totals else 0)
    txs = db.query("SELECT t.id, COALESCE(u.username,'system'), COALESCE(p.name,'-'), t.type, t.status, t.amount, t.quantity, t.customer_name, t.invoice_path, t.proof_path, t.created_at FROM transactions t LEFT JOIN users u ON u.id=t.user_id LEFT JOIN product p ON p.id=t.product_id ORDER BY t.id DESC LIMIT 50")
    return render_app("transaction.html", total_sales=fmt(sales), total_sales_value=sales, total_expenses=fmt(purchase), total_expenses_value=purchase, profit=fmt(sales - purchase), profit_value=sales - purchase, transactions=txs, initial_transaction_count=len(txs))


@app.route("/product")
@login_required
def product():
    return render_app("product.html", products=db.query("SELECT id, name, price, quantity, image_path FROM product ORDER BY id DESC"))


@app.route("/report")
@login_required
def report():
    return render_app("report.html")


@app.route("/user")
@login_required
def user_page():
    if session.get("role") != "admin":
        return redirect(url_for("employee"))
    return render_app("user.html", users=db.query(f"{USER_SELECT} ORDER BY id DESC"))


@app.route("/notifications")
@login_required
def notifications():
    if session.get("role") != "admin":
        return redirect(url_for("employee"))
    uid = session["user_id"]
    tx = db.query("SELECT t.id, 'transaction', COALESCE(u.username,'system'), COALESCE(p.name,'-'), t.type, t.amount, t.created_at, '' FROM transactions t LEFT JOIN users u ON u.id=t.user_id LEFT JOIN product p ON p.id=t.product_id WHERE t.user_id != ? ORDER BY t.id DESC LIMIT 100", (uid,))
    role = db.query("SELECT n.id, 'role', COALESCE(a.username,'system'), COALESCE(t.username,'-'), n.type, 0, n.created_at, n.message FROM notifications n LEFT JOIN users a ON a.id=n.actor_user_id LEFT JOIN users t ON t.id=n.target_user_id WHERE n.actor_user_id != ? ORDER BY n.id DESC LIMIT 100", (uid,))
    items = list(tx) + list(role)
    items.sort(key=lambda x: str(x[6]), reverse=True)
    return render_app("notifications.html", notifications=items[:150])


@app.route("/setting")
@login_required
def setting():
    return render_app("setting.html")


@app.route("/change-password")
@login_required
def change_password():
    return render_app("change_password.html")


@app.route("/account-details")
@login_required
def account_details():
    return render_app("account_details.html")


@app.route("/add-email")
@login_required
def add_email():
    return render_app("add_email.html")


@app.route("/profile-details")
@login_required
def profile_details():
    return render_app("profile_details.html")


@app.route("/api/products")
@login_required
def api_products():
    rows = db.query("SELECT id, name, price, quantity, image_path FROM product ORDER BY name ASC")
    return jsonify({"products": [product_json(r) for r in rows]})


@app.route("/api/products", methods=["POST"])
@login_required
def api_create_product():
    if session.get("role") != "admin":
        return jsonify({"message": "Only admins can create products."}), 403
    form = request.form
    name = (form.get("name") or "").strip()
    price = fnum(form.get("price"))
    quantity = int(form.get("quantity") or 0)
    if not name or price < 0 or quantity < 0:
        return jsonify({"message": "Provide valid product values."}), 400
    image_rel = save_upload(request.files.get("image"), PRODUCT_UPLOADS)
    existing = product_by_name(name)
    if existing:
        db.run("UPDATE product SET price=?, quantity=?, image_path=COALESCE(NULLIF(?, ''), image_path) WHERE id=?", (price, quantity, image_rel, existing[0]))
        prod = product_by_id(existing[0])
    else:
        db.run("INSERT INTO product (name, price, quantity, image_path) VALUES (?, ?, ?, ?)", (name, price, quantity, image_rel))
        pid = one("SELECT id FROM product ORDER BY id DESC LIMIT 1")
        prod = product_by_id(pid[0] if pid else 0)
    return jsonify({"message": "Product saved successfully.", "product": product_json(prod)})


@app.route("/api/products/<int:product_id>/adjust", methods=["POST"])
@login_required
def api_adjust_product(product_id):
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip().lower()
    qty = int(data.get("quantity") or 0)
    if action not in {"add", "remove"} or qty <= 0:
        return jsonify({"message": "Invalid adjustment payload."}), 400
    try:
        adjust_inventory(product_id, qty if action == "add" else -qty, session["user_id"], action, data.get("reason") or "")
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    return jsonify({"message": "Product updated successfully.", "product": product_json(product_by_id(product_id))})


@app.route("/api/products/<int:product_id>", methods=["PATCH"])
@admin_required
def api_edit_product(product_id):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    price = fnum(data.get("price"))
    quantity = int(data.get("quantity") or 0)
    if not name or price < 0 or quantity < 0:
        return jsonify({"message": "Invalid product values."}), 400
    db.run("UPDATE product SET name=?, price=?, quantity=? WHERE id=?", (name, price, quantity, product_id))
    return jsonify({"message": "Product updated successfully.", "product": product_json(product_by_id(product_id))})


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
@admin_required
def api_delete_product(product_id):
    if not product_by_id(product_id):
        return jsonify({"message": "Product not found."}), 404
    delete_product_with_dependencies(product_id)
    return jsonify({"message": "Product deleted successfully."})


@app.route("/api/uploads/transaction-assets", methods=["POST"])
@login_required
def api_upload_transaction_assets():
    invoice = save_upload(request.files.get("invoice"), TX_UPLOADS)
    proof = save_upload(request.files.get("proof"), TX_UPLOADS)
    return jsonify({"invoice_path": static_path(invoice), "proof_path": static_path(proof)})


@app.route("/api/transactions/last-sale")
@login_required
def api_last_sale():
    row = one("SELECT t.id, COALESCE(p.name,''), t.quantity, t.amount, t.customer_name FROM transactions t LEFT JOIN product p ON p.id=t.product_id WHERE t.type='sale' ORDER BY t.id DESC LIMIT 1")
    if not row:
        return jsonify({"message": "No sale found."}), 404
    return jsonify({"id": row[0], "product_name": row[1], "quantity": int(row[2] or 0), "amount": fnum(row[3]), "customer_name": row[4] or ""})


@app.route("/api/transactions/last-sale-today")
@login_required
def api_last_sale_today():
    today = datetime.now().strftime("%Y-%m-%d")
    row = one("SELECT t.id, COALESCE(p.name,''), t.quantity, t.amount FROM transactions t LEFT JOIN product p ON p.id=t.product_id WHERE t.type='sale' AND CAST(t.created_at AS TEXT) LIKE ? ORDER BY t.id DESC LIMIT 1", (f"{today}%",))
    if not row:
        return jsonify({"message": "No sale found for today."}), 404
    return jsonify({"id": row[0], "product_name": row[1], "quantity": int(row[2] or 0), "amount": fnum(row[3])})


def create_tx(payload, user_id):
    tx_type = (payload.get("type") or "").strip().lower()
    pname = (payload.get("product_name") or "").strip()
    qty = int(payload.get("quantity") or 0)
    amount = fnum(payload.get("amount"))
    status = (payload.get("status") or "completed").strip().lower()
    customer = (payload.get("customer_name") or "").strip()
    is_unpaid_sale = tx_type == "sale" and status == "unpaid"
    amount_invalid = amount < 0 if is_unpaid_sale else amount <= 0
    if tx_type not in {"sale", "purchase"} or not pname or qty <= 0 or amount_invalid:
        raise ValueError("Invalid transaction payload.")
    if is_unpaid_sale and not customer:
        raise ValueError("Customer name is required for unpaid sales.")
    prod = product_by_name(pname)
    if not prod:
        raise ValueError("Product not found.")
    if tx_type == "sale":
        adjust_inventory(prod[0], -qty, user_id, "sale")
    else:
        adjust_inventory(prod[0], qty, user_id, "purchase")
    db.run("INSERT INTO transactions (user_id, product_id, amount, quantity, type, status, customer_name, invoice_path, proof_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, prod[0], amount, qty, tx_type, status, customer, (payload.get("invoice_path") or "").strip(), (payload.get("proof_path") or "").strip()))
    txid = one("SELECT id FROM transactions ORDER BY id DESC LIMIT 1")
    if txid:
        db.run("INSERT INTO transaction_audit_logs (transaction_id, user_id, action, payload) VALUES (?, ?, ?, ?)", (txid[0], user_id, "created", json.dumps(payload)))
    return txid[0] if txid else None


@app.route("/api/transactions", methods=["POST"])
@login_required
def api_create_transaction():
    data = request.get_json(silent=True) or {}
    try:
        tx_id = create_tx(data, session["user_id"])
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    return jsonify({"message": "Transaction saved successfully.", "id": tx_id})


@app.route("/api/transactions")
@login_required
def api_transactions():
    offset = int(request.args.get("offset", 0) or 0)
    limit = int(request.args.get("limit", 50) or 50)
    category = (request.args.get("category") or "").strip().lower()
    status = (request.args.get("status") or "").strip().lower()
    where = []
    params = []
    if category in {"sale", "purchase"}:
        where.append("t.type=?")
        params.append(category)
    if status:
        where.append("t.status=?")
        params.append(status)
    sql_where = f"WHERE {' AND '.join(where)}" if where else ""
    params.extend([limit + 1, offset])
    rows = db.query(
        f"""
        SELECT t.id, COALESCE(u.username,'system'), COALESCE(p.name,'-'), t.type, t.status, t.amount, t.quantity,
               t.customer_name, t.invoice_path, t.proof_path, t.created_at
        FROM transactions t
        LEFT JOIN users u ON u.id=t.user_id
        LEFT JOIN product p ON p.id=t.product_id
        {sql_where}
        ORDER BY t.id DESC
        LIMIT ? OFFSET ?
        """,
        tuple(params),
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    return jsonify(
        {
            "transactions": [
                {
                    "id": r[0], "username": r[1], "product_name": r[2], "type": r[3], "status": r[4],
                    "amount": fnum(r[5]), "quantity": int(r[6] or 0), "customer_name": r[7] or "",
                    "invoice_path": r[8] or "", "proof_path": r[9] or "", "created_at": str(r[10]),
                }
                for r in rows
            ],
            "has_more": has_more,
        }
    )


@app.route("/api/transactions/<int:tx_id>")
@login_required
def api_transaction_detail(tx_id):
    row = one(
        """
        SELECT t.id, COALESCE(u.username,'system'), COALESCE(p.name,'-'), t.type, t.status, t.amount, t.quantity,
               t.customer_name, t.invoice_path, t.proof_path, t.created_at
        FROM transactions t
        LEFT JOIN users u ON u.id=t.user_id
        LEFT JOIN product p ON p.id=t.product_id
        WHERE t.id=? LIMIT 1
        """,
        (tx_id,),
    )
    if not row:
        return jsonify({"message": "Transaction not found."}), 404
    audit = db.query("SELECT action, created_at FROM transaction_audit_logs WHERE transaction_id=? ORDER BY id DESC", (tx_id,))
    return jsonify(
        {
            "id": row[0], "username": row[1], "product_name": row[2], "type": row[3], "status": row[4],
            "amount": fnum(row[5]), "quantity": int(row[6] or 0), "customer_name": row[7] or "",
            "invoice_path": row[8] or "", "proof_path": row[9] or "", "created_at": str(row[10]),
            "audit_history": [{"action": a[0], "created_at": str(a[1])} for a in audit],
        }
    )


@app.route("/api/transactions/<int:tx_id>", methods=["PATCH"])
@login_required
def api_update_transaction(tx_id):
    old = one("SELECT id, product_id, quantity, type FROM transactions WHERE id=? LIMIT 1", (tx_id,))
    if not old:
        return jsonify({"message": "Transaction not found."}), 404
    data = request.get_json(silent=True) or {}
    pname = (data.get("product_name") or "").strip()
    qty = int(data.get("quantity") or 0)
    amount = fnum(data.get("amount"))
    status = (data.get("status") or "completed").strip().lower()
    ttype = (data.get("type") or old[3]).strip().lower()
    customer = (data.get("customer_name") or "").strip()
    is_unpaid_sale = ttype == "sale" and status == "unpaid"
    amount_invalid = amount < 0 if is_unpaid_sale else amount <= 0
    if not pname or qty <= 0 or amount_invalid or ttype not in {"sale", "purchase"}:
        return jsonify({"message": "Invalid transaction values."}), 400
    if is_unpaid_sale and not customer:
        return jsonify({"message": "Customer name is required for unpaid sales."}), 400
    new_prod = product_by_name(pname)
    if not new_prod:
        return jsonify({"message": "Product not found."}), 404
    try:
        adjust_inventory(old[1], int(old[2] or 0) if old[3] == "sale" else -int(old[2] or 0), session["user_id"], "edit")
        adjust_inventory(new_prod[0], -qty if ttype == "sale" else qty, session["user_id"], "edit")
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    db.run("UPDATE transactions SET product_id=?, quantity=?, amount=?, type=?, status=?, customer_name=? WHERE id=?", (new_prod[0], qty, amount, ttype, status, customer, tx_id))
    db.run("INSERT INTO transaction_audit_logs (transaction_id, user_id, action, payload) VALUES (?, ?, 'updated', ?)", (tx_id, session["user_id"], json.dumps(data)))
    return jsonify({"message": "Transaction updated successfully."})


@app.route("/api/transactions/<int:tx_id>", methods=["DELETE"])
@login_required
def api_delete_transaction(tx_id):
    row = one("SELECT id, product_id, quantity, type FROM transactions WHERE id=? LIMIT 1", (tx_id,))
    if not row:
        return jsonify({"message": "Transaction not found."}), 404
    qty = int(row[2] or 0)
    try:
        adjust_inventory(row[1], qty if row[3] == "sale" else -qty, session["user_id"], "cancelled")
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    db.run("DELETE FROM transactions WHERE id=?", (tx_id,))
    db.run("INSERT INTO transaction_audit_logs (transaction_id, user_id, action, payload) VALUES (?, ?, 'cancelled', '{}')", (tx_id, session["user_id"]))
    return jsonify({"message": "Transaction deleted successfully."})


@app.route("/api/users", methods=["POST"])
@admin_required
def api_create_user():
    data = request.get_json(silent=True) or {}
    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    active = "true" if bool(data.get("is_active")) else "false"
    if not all([first, last, username, password]):
        return jsonify({"message": "All fields are required."}), 400
    if one("SELECT id FROM users WHERE username=? LIMIT 1", (username,)):
        return jsonify({"message": "Username already exists."}), 409
    db.run("INSERT INTO users (first_name, last_name, username, password, role, approval_status, is_active) VALUES (?, ?, ?, ?, 'user', 'approved', ?)", (first, last, username, pwd_hash(password), active))
    return jsonify({"message": "User created successfully."})


@app.route("/api/users/<int:user_id>/active", methods=["PATCH"])
@admin_required
def api_user_active(user_id):
    data = request.get_json(silent=True) or {}
    db.run("UPDATE users SET is_active=? WHERE id=?", ("true" if bool(data.get("is_active")) else "false", user_id))
    return jsonify({"message": "User status updated successfully."})


@app.route("/api/users/<int:user_id>/role", methods=["PATCH"])
@admin_required
def api_user_role(user_id):
    data = request.get_json(silent=True) or {}
    role = (data.get("role") or "").strip().lower()
    if role not in {"admin", "user"}:
        return jsonify({"message": "Invalid role."}), 400
    target = one("SELECT id, username FROM users WHERE id=? LIMIT 1", (user_id,))
    actor = one("SELECT username FROM users WHERE id=? LIMIT 1", (session["user_id"],))
    if not target:
        return jsonify({"message": "User not found."}), 404
    db.run("UPDATE users SET role=? WHERE id=?", (role, user_id))
    ntype = "role_promoted" if role == "admin" else "role_removed"
    msg = f"@{actor[0] if actor else 'admin'} changed @{target[1]}'s role to {role}."
    db.run("INSERT INTO notifications (actor_user_id, target_user_id, type, message) VALUES (?, ?, ?, ?)", (session["user_id"], user_id, ntype, msg))
    return jsonify({"message": "User role updated successfully."})


@app.route("/api/users/pending")
@admin_required
def api_pending_users():
    rows = db.query("SELECT id, first_name, last_name, username, created_at FROM users WHERE COALESCE(approval_status,'approved')='pending' ORDER BY id DESC")
    return jsonify({"users": [{"id": r[0], "first_name": r[1], "last_name": r[2], "username": r[3], "created_at": str(r[4])} for r in rows]})


@app.route("/api/users/pending/<int:user_id>/allow", methods=["POST"])
@admin_required
def api_pending_allow(user_id):
    db.run("UPDATE users SET approval_status='approved', is_active='true' WHERE id=?", (user_id,))
    return jsonify({"message": "User approved successfully."})


@app.route("/api/users/pending/<int:user_id>/decline", methods=["POST"])
@admin_required
def api_pending_decline(user_id):
    db.run("UPDATE users SET approval_status='declined', is_active='false' WHERE id=?", (user_id,))
    return jsonify({"message": "User declined."})


@app.route("/api/settings/password", methods=["PATCH"])
@login_required
def api_settings_password():
    data = request.get_json(silent=True) or {}
    current = data.get("current_password") or ""
    new = data.get("new_password") or ""
    confirm = data.get("confirm_password") or ""
    if not current or not new:
        return jsonify({"message": "Password fields are required."}), 400
    if new != confirm:
        return jsonify({"message": "Passwords do not match."}), 400
    row = one("SELECT password FROM users WHERE id=? LIMIT 1", (session["user_id"],))
    if not row or row[0] != pwd_hash(current):
        return jsonify({"message": "Current password is incorrect."}), 400
    db.run("UPDATE users SET password=? WHERE id=?", (pwd_hash(new), session["user_id"]))
    return jsonify({"message": "Password updated successfully."})


@app.route("/api/settings/account", methods=["PATCH"])
@login_required
def api_settings_account():
    data = request.get_json(silent=True) or {}
    db.run("UPDATE users SET bank_name=?, account_name=?, account_owner_name=? WHERE id=?", ((data.get("bank_name") or "").strip(), (data.get("account_name") or "").strip(), (data.get("account_owner_name") or "").strip(), session["user_id"]))
    return jsonify({"message": "Account details updated successfully."})


@app.route("/api/settings/email", methods=["PATCH"])
@login_required
def api_settings_email():
    data = request.get_json(silent=True) or {}
    db.run("UPDATE users SET email=? WHERE id=?", ((data.get("email") or "").strip(), session["user_id"]))
    return jsonify({"message": "Email updated successfully."})


@app.route("/api/settings/profile", methods=["POST"])
@login_required
def api_settings_profile():
    first = (request.form.get("first_name") or "").strip()
    last = (request.form.get("last_name") or "").strip()
    if not first or not last:
        return jsonify({"message": "First and last name are required."}), 400
    image_rel = save_upload(request.files.get("image"), PROFILE_UPLOADS)
    db.run("UPDATE users SET first_name=?, last_name=?, image_path=COALESCE(NULLIF(?, ''), image_path) WHERE id=?", (first, last, image_rel, session["user_id"]))
    return jsonify({"message": "Profile details updated successfully."})


@app.route("/api/settings/profile/image", methods=["DELETE"])
@login_required
def api_settings_profile_image_delete():
    db.run("UPDATE users SET image_path='' WHERE id=?", (session["user_id"],))
    return jsonify({"message": "Profile picture removed successfully."})


@app.route("/api/notifications/mark-all-read", methods=["POST"])
@admin_required
def api_notifications_mark_all_read():
    uid = session["user_id"]
    for r in db.query("SELECT id FROM transactions WHERE user_id IS NOT NULL AND user_id != ?", (uid,)):
        mark_notification_read(uid, "transaction", r[0])
    for r in db.query("SELECT id FROM notifications WHERE actor_user_id IS NOT NULL AND actor_user_id != ?", (uid,)):
        mark_notification_read(uid, "role", r[0])
    return jsonify({"message": "All notifications marked as read."})


@app.route("/api/reports/<report_type>")
@login_required
def api_reports(report_type):
    rpt = (report_type or "").strip().lower()
    if rpt not in {"sales", "purchase", "activity"}:
        return jsonify({"message": "Unsupported report type."}), 404
    if rpt in {"sales", "purchase"}:
        rows = db.query(f"SELECT t.amount, t.status, COALESCE(p.name,'-'), t.created_at FROM transactions t LEFT JOIN product p ON p.id=t.product_id WHERE t.type='{rpt if rpt != 'sales' else 'sale'}' ORDER BY t.id DESC")
        total = sum(fnum(r[0]) for r in rows)
        by_day, by_status, by_subject = {}, {}, {}
        for amount, status, subject, created in rows:
            day = str(created)[:10]
            by_day[day] = by_day.get(day, 0.0) + fnum(amount)
            by_status[status] = by_status.get(status, 0) + 1
            by_subject[subject] = by_subject.get(subject, 0.0) + fnum(amount)
        count = len(rows)
        chart = [{"label": d, "value": round(v, 2)} for d, v in sorted(by_day.items())[-10:]]
        pie = [{"label": k.capitalize(), "value": round((v / count) * 100, 2) if count else 0, "count": v} for k, v in by_status.items()]
        leaderboard = [{"label": k, "value": round(v, 2)} for k, v in sorted(by_subject.items(), key=lambda x: x[1], reverse=True)[:5]]
        return jsonify({"summary": {"total": round(total, 2), "count": count}, "chart": chart, "pie": pie, "leaderboard": leaderboard})
    if session.get("role") != "admin":
        return jsonify({"summary": {"total": 0, "count": 0}, "chart": [], "pie": [], "leaderboard": []})
    rows = db.query("SELECT COALESCE(u.username,'system'), t.created_at FROM transactions t LEFT JOIN users u ON u.id=t.user_id ORDER BY t.id DESC")
    by_day, by_user = {}, {}
    for username, created in rows:
        day = str(created)[:10]
        by_day[day] = by_day.get(day, 0) + 1
        by_user[username] = by_user.get(username, 0) + 1
    count = len(rows)
    chart = [{"label": d, "value": v} for d, v in sorted(by_day.items())[-10:]]
    pie = [{"label": u, "value": round((v / count) * 100, 2) if count else 0, "count": v} for u, v in sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:6]]
    leaderboard = [{"label": u, "value": v} for u, v in sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:5]]
    return jsonify({"summary": {"total": 0, "count": count}, "chart": chart, "pie": pie, "leaderboard": leaderboard})


def fnum(value) -> float:
    """
    Convert a value to float, handling None and string values.
    
    Args:
        value: The value to convert (can be None, string, or numeric)
        
    Returns:
        float: The converted value, or 0.0 if conversion fails
    """
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def fmt(value) -> str:
    """
    Format a numeric value for display (currency format).
    
    Args:
        value: The numeric value to format
        
    Returns:
        str: Formatted string with commas and 2 decimal places
    """
    try:
        num = fnum(value)
        return f"{num:,.2f}"
    except (ValueError, TypeError):
        return "0.00"


def render_app(template_name: str, **kwargs) -> str:
    """
    Render a template with common app context variables.
    
    Args:
        template_name: The template file name
        **kwargs: Additional context variables
        
    Returns:
        str: Rendered HTML template
    """
    # Get current user data if not already provided
    if 'current_user' not in kwargs:
        user_id = session.get("user_id")
        if user_id:
            user_data = db.query("SELECT * FROM users WHERE id = ?", (user_id,))
            kwargs['current_user'] = user_data[0] if user_data else None
    
    # Add common context variables
    context = {
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "role": session.get("role"),
        "is_admin": session.get("role") == "admin",
        "is_employee": session.get("role") == "user",
        "role_theme": "admin" if session.get("role") == "admin" else "user",
        "dashboard_url": url_for("admin") if session.get("role") == "admin" else url_for("employee"),
    }
    
    # Get notification count for admin users
    if session.get("role") == "admin" and 'notification_count' not in kwargs:
        pending_users = db.query("SELECT COUNT(*) as count FROM users WHERE approval_status = 'pending'")
        context['notification_count'] = pending_users[0]['count'] if pending_users else 0
    
    context.update(kwargs)
    return render_template(template_name, **context)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
