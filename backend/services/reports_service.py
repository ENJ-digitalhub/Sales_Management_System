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

        return {
            "user_id": user.id,
            "name": user.name,
            "period": f"{from_date.isoformat()} to {to_date.isoformat()}",
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