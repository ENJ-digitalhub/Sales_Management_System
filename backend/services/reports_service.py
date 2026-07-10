<<<<<<< HEAD
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import select, func, and_
from backend.models.models import Sale, SaleItem, Product, User

COUNTED_STATUSES = ("completed", "edited")


def _day_bounds(d: date):
    start = datetime.combine(d, datetime.min.time())
    end = start + timedelta(days=1)
    return start, end


def _month_bounds(year: int, month: int):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


def _year_bounds(year: int):
    return datetime(year, 1, 1), datetime(year + 1, 1, 1)


def _payment_breakdown(session, start, end):
    """
    Dynamic breakdown keyed by whatever payment methods actually appear —
    NOT a fixed {cash, transfer, pos} shape. The real system supports 15+
    payment methods (see validators.py ALLOWED_PAYMENT_METHODS); a fixed
    3-key contract would misrepresent real data and silently drop totals
    for every other method.
    """
    rows = session.execute(
        select(Sale.payment_method, func.sum(Sale.total_amount))
        .where(
            Sale.status.in_(COUNTED_STATUSES),
            Sale.created_at >= start,
            Sale.created_at < end,
        )
        .group_by(Sale.payment_method)
    ).all()
    return {method: float(total) for method, total in rows}


def _top_products(session, start, end, limit=5):
    rows = session.execute(
        select(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label("quantity_sold"),
            func.sum(SaleItem.total_price).label("revenue"),
        )
        .join(Sale, SaleItem.sale_id == Sale.id)
        .join(Product, SaleItem.product_id == Product.id)
        .where(
            Sale.status.in_(COUNTED_STATUSES),
            Sale.created_at >= start,
            Sale.created_at < end,
        )
        .group_by(Product.id, Product.name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(limit)
    ).all()

    return [
        {
            "product_id": pid,
            "name": name,
            "quantity_sold": int(qty),
            "revenue": float(revenue),
        }
        for pid, name, qty, revenue in rows
    ]


def _employee_performance(session, start, end):
    """
    LEFT OUTER JOIN from User to Sale so employees with zero sales in the
    period still appear with zero counts, per the locked business rule.
    A normal (inner) join would silently exclude them.

    Scope decision: filtered to role == 'employee' specifically, matching
    the field name "employee_performance" and the guiding question's
    framing. If admins/managers who also process sales should appear
    here too, this filter is the one line to change.
    """
    rows = session.execute(
        select(
            User.id,
            User.name,
            func.count(Sale.id).label("transaction_count"),
            func.coalesce(func.sum(Sale.total_amount), 0).label("total_sales"),
        )
        .outerjoin(
            Sale,
            and_(
                Sale.user_id == User.id,
                Sale.status.in_(COUNTED_STATUSES),
                Sale.created_at >= start,
                Sale.created_at < end,
            ),
        )
        .where(User.role == "employee", User.is_active == 1)
        .group_by(User.id, User.name)
    ).all()

    return [
        {
            "user_id": uid,
            "name": name,
            "transaction_count": int(count),
            "total_sales": float(total),
        }
        for uid, name, count, total in rows
    ]


def _summary_totals(session, start, end):
    row = session.execute(
        select(
            func.coalesce(func.sum(Sale.total_amount), 0),
            func.coalesce(func.sum(Sale.profit_at_sale), 0),
            func.count(Sale.id),
        ).where(
            Sale.status.in_(COUNTED_STATUSES),
            Sale.created_at >= start,
            Sale.created_at < end,
        )
    ).one()

    total_sales, total_profit, transaction_count = row
    return float(total_sales), float(total_profit), int(transaction_count)


class ReportsService:
    @staticmethod
    def get_daily_report(session, report_date: date) -> dict:
        start, end = _day_bounds(report_date)
        total_sales, total_profit, transaction_count = _summary_totals(session, start, end)

        return {
            "date": report_date.isoformat(),
            "total_sales": total_sales,
            "total_profit": total_profit,
            "transaction_count": transaction_count,
            "payment_breakdown": _payment_breakdown(session, start, end),
            "top_products": _top_products(session, start, end),
            "employee_performance": _employee_performance(session, start, end),
        }

    @staticmethod
    def get_monthly_report(session, year: int, month: int) -> dict:
        start, end = _month_bounds(year, month)
        total_sales, total_profit, transaction_count = _summary_totals(session, start, end)

        return {
            "month": f"{year:04d}-{month:02d}",
            "total_sales": total_sales,
            "total_profit": total_profit,
            "transaction_count": transaction_count,
            "payment_breakdown": _payment_breakdown(session, start, end),
            "top_products": _top_products(session, start, end),
            "employee_performance": _employee_performance(session, start, end),
        }

    @staticmethod
    def get_yearly_report(session, year: int) -> dict:
        start, end = _year_bounds(year)
        total_sales, total_profit, transaction_count = _summary_totals(session, start, end)

        # Monthly breakdown via SQLite's strftime — groups by YYYY-MM.
        rows = session.execute(
            select(
                func.strftime("%Y-%m", Sale.created_at),
                func.coalesce(func.sum(Sale.total_amount), 0),
                func.coalesce(func.sum(Sale.profit_at_sale), 0),
                func.count(Sale.id),
            )
            .where(
                Sale.status.in_(COUNTED_STATUSES),
                Sale.created_at >= start,
                Sale.created_at < end,
            )
            .group_by(func.strftime("%Y-%m", Sale.created_at))
            .order_by(func.strftime("%Y-%m", Sale.created_at))
        ).all()

        monthly_breakdown = [
            {
                "month": month_str,
                "total_sales": float(sales),
                "total_profit": float(profit),
                "transaction_count": int(count),
            }
            for month_str, sales, profit, count in rows
        ]

        return {
            "year": str(year),
            "total_sales": total_sales,
            "total_profit": total_profit,
            "transaction_count": transaction_count,
            "payment_breakdown": _payment_breakdown(session, start, end),
            "monthly_breakdown": monthly_breakdown,
        }

    @staticmethod
    def get_employee_report(session, user_id: str, from_date: date, to_date: date) -> dict | None:
        user = session.get(User, user_id)
        if not user:
            return None

        start = datetime.combine(from_date, datetime.min.time())
        end = datetime.combine(to_date, datetime.min.time()) + timedelta(days=1)

        sales = session.execute(
            select(Sale)
            .where(
                Sale.user_id == user_id,
                Sale.status.in_(COUNTED_STATUSES),
                Sale.created_at >= start,
                Sale.created_at < end,
            )
            .order_by(Sale.created_at.desc())
        ).scalars().all()

        total_sales = sum(float(s.total_amount) for s in sales)
        total_profit = sum(float(s.profit_at_sale) for s in sales)
=======
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from backend.models.models import Sale, SaleItem, Product, User
from datetime import datetime, date, timedelta

VALID_STATUSES = ["completed", "edited"]

class ReportsService:
    @staticmethod
    def _base_sales_query(session: Session):
        return session.query(Sale).filter(Sale.status.in_(VALID_STATUSES))

    @staticmethod
    def _date_range_for_day(target_date: date):
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        return start, end

    @staticmethod
    def _date_range_for_month(target_date: date):
        start = datetime.combine(target_date.replace(day=1), datetime.min.time())
        next_month = (target_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = datetime.combine(next_month - timedelta(seconds=1), datetime.max.time())
        return start, end

    @staticmethod
    def _date_range_for_year(year: int):
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31, 23, 59, 59)
        return start, end

    @staticmethod
    def get_daily_report(session: Session, report_date=None):
        if report_date is None:
            report_date = datetime.utcnow().date()

        start, end = ReportsService._date_range_for_day(report_date)
        sales_query = ReportsService._base_sales_query(session).filter(Sale.created_at.between(start, end))

        total_sales = sales_query.with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0
        total_profit = sales_query.with_entities(func.coalesce(func.sum(Sale.profit_at_sale), 0)).scalar() or 0
        transaction_count = sales_query.with_entities(func.count(Sale.id)).scalar() or 0

        payment_breakdown = {
            "cash": sales_query.filter(Sale.payment_method == "cash").with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0,
            "transfer": sales_query.filter(Sale.payment_method == "transfer").with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0,
            "pos": sales_query.filter(Sale.payment_method == "pos").with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0,
        }

        top_products_query = (
            session.query(
                SaleItem.product_id,
                Product.name,
                func.coalesce(func.sum(SaleItem.quantity), 0).label("quantity_sold"),
                func.coalesce(func.sum(SaleItem.total_price), 0).label("revenue")
            )
            .join(Product, SaleItem.product_id == Product.id)
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(Sale.status.in_(VALID_STATUSES), Sale.created_at.between(start, end))
            .group_by(SaleItem.product_id, Product.name)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(5)
        )

        top_products = [
            {
                "product_id": row.product_id,
                "name": row.name,
                "quantity_sold": int(row.quantity_sold),
                "revenue": float(row.revenue)
            }
            for row in top_products_query.all()
        ]

        employee_performance_query = (
            session.query(
                User.id.label("user_id"),
                User.name,
                func.coalesce(func.count(Sale.id), 0).label("transaction_count"),
                func.coalesce(func.sum(Sale.total_amount), 0).label("total_sales")
            )
            .outerjoin(Sale, and_(Sale.user_id == User.id, Sale.status.in_(VALID_STATUSES), Sale.created_at.between(start, end)))
            .filter(User.role.in_(["admin", "manager", "employee"]))
            .group_by(User.id, User.name)
            .order_by(User.name)
        )

        employee_performance = [
            {
                "user_id": row.user_id,
                "name": row.name,
                "transaction_count": int(row.transaction_count),
                "total_sales": float(row.total_sales)
            }
            for row in employee_performance_query.all()
        ]

        return {
            "date": report_date.isoformat(),
            "total_sales": float(total_sales),
            "total_profit": float(total_profit),
            "transaction_count": int(transaction_count),
            "payment_breakdown": payment_breakdown,
            "top_products": top_products,
            "employee_performance": employee_performance,
        }, None

    @staticmethod
    def get_monthly_report(session: Session, year_month=None):
        if year_month is None:
            year_month = datetime.utcnow().date().replace(day=1)

        start, end = ReportsService._date_range_for_month(year_month)
        sales_query = ReportsService._base_sales_query(session).filter(Sale.created_at.between(start, end))

        total_sales = sales_query.with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0
        total_profit = sales_query.with_entities(func.coalesce(func.sum(Sale.profit_at_sale), 0)).scalar() or 0
        transaction_count = sales_query.with_entities(func.count(Sale.id)).scalar() or 0

        payment_breakdown = {
            "cash": sales_query.filter(Sale.payment_method == "cash").with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0,
            "transfer": sales_query.filter(Sale.payment_method == "transfer").with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0,
            "pos": sales_query.filter(Sale.payment_method == "pos").with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0,
        }

        top_products = []
        employee_performance = []

        return {
            "month": year_month.strftime("%Y-%m"),
            "total_sales": float(total_sales),
            "total_profit": float(total_profit),
            "transaction_count": int(transaction_count),
            "payment_breakdown": payment_breakdown,
            "top_products": top_products,
            "employee_performance": employee_performance,
        }, None

    @staticmethod
    def get_yearly_report(session: Session, year=None):
        if year is None:
            year = datetime.utcnow().year

        start, end = ReportsService._date_range_for_year(year)
        sales_query = ReportsService._base_sales_query(session).filter(Sale.created_at.between(start, end))

        total_sales = sales_query.with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0
        total_profit = sales_query.with_entities(func.coalesce(func.sum(Sale.profit_at_sale), 0)).scalar() or 0
        transaction_count = sales_query.with_entities(func.count(Sale.id)).scalar() or 0

        monthly_breakdown = []
        for month in range(1, 13):
            month_start = datetime(year, month, 1)
            next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end = next_month - timedelta(seconds=1)
            month_sales_query = ReportsService._base_sales_query(session).filter(Sale.created_at.between(month_start, month_end))
            monthly_breakdown.append({
                "month": month_start.strftime("%Y-%m"),
                "total_sales": float(month_sales_query.with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0),
                "total_profit": float(month_sales_query.with_entities(func.coalesce(func.sum(Sale.profit_at_sale), 0)).scalar() or 0),
                "transaction_count": int(month_sales_query.with_entities(func.count(Sale.id)).scalar() or 0),
            })

        return {
            "year": str(year),
            "total_sales": float(total_sales),
            "total_profit": float(total_profit),
            "transaction_count": int(transaction_count),
            "payment_breakdown": {
                "cash": sales_query.filter(Sale.payment_method == "cash").with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0,
                "transfer": sales_query.filter(Sale.payment_method == "transfer").with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0,
                "pos": sales_query.filter(Sale.payment_method == "pos").with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0,
            },
            "monthly_breakdown": monthly_breakdown,
        }, None

    @staticmethod
    def get_employee_report(session: Session, user_id: str, from_date=None, to_date=None):
        if from_date is None:
            from_date = datetime.utcnow().date() - timedelta(days=30)
        if to_date is None:
            to_date = datetime.utcnow().date()
        if from_date > to_date:
            return None, "from date cannot be after to date"

        start = datetime.combine(from_date, datetime.min.time())
        end = datetime.combine(to_date, datetime.max.time())

        sales_query = ReportsService._base_sales_query(session).filter(Sale.user_id == user_id, Sale.created_at.between(start, end))
        total_sales = sales_query.with_entities(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0
        total_profit = sales_query.with_entities(func.coalesce(func.sum(Sale.profit_at_sale), 0)).scalar() or 0
        transaction_count = sales_query.with_entities(func.count(Sale.id)).scalar() or 0

        sales = [
            {
                "id": sale.id,
                "receipt_number": sale.receipt_number,
                "total_amount": float(sale.total_amount),
                "profit_at_sale": float(sale.profit_at_sale),
                "payment_method": sale.payment_method,
                "status": sale.status,
                "created_at": sale.created_at.isoformat(),
            }
            for sale in sales_query.all()
        ]

        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return None, "User not found"
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

        return {
            "user_id": user.id,
            "name": user.name,
            "period": f"{from_date.isoformat()} to {to_date.isoformat()}",
<<<<<<< HEAD
            "transaction_count": len(sales),
            "total_sales": total_sales,
            "total_profit": total_profit,
            "sales": [
                {
                    "id": s.id,
                    "receipt_number": s.receipt_number,
                    "total_amount": float(s.total_amount),
                    "profit_at_sale": float(s.profit_at_sale),
                    "payment_method": s.payment_method,
                    "status": s.status,
                    "created_at": s.created_at.isoformat(),
                }
                for s in sales
            ],
        }
=======
            "transaction_count": int(transaction_count),
            "total_sales": float(total_sales),
            "total_profit": float(total_profit),
            "sales": sales,
        }, None
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
