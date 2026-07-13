from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from backend.models.models import Sale, SaleItem, Item, User
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

        top_items_query = (
            session.query(
                SaleItem.item_id,
                Item.name,
                func.coalesce(func.sum(SaleItem.quantity), 0).label("quantity_sold"),
                func.coalesce(func.sum(SaleItem.total_price), 0).label("revenue")
            )
            .join(Item, SaleItem.item_id == Item.id)
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(Sale.status.in_(VALID_STATUSES), Sale.created_at.between(start, end))
            .group_by(SaleItem.item_id, Item.name)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(5)
        )

        top_items = [
            {
                "item_id": row.item_id,
                "name": row.name,
                "quantity_sold": int(row.quantity_sold),
                "revenue": float(row.revenue)
            }
            for row in top_items_query.all()
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
            "top_items": top_items,
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

        top_items = []
        employee_performance = []

        return {
            "month": year_month.strftime("%Y-%m"),
            "total_sales": float(total_sales),
            "total_profit": float(total_profit),
            "transaction_count": int(transaction_count),
            "payment_breakdown": payment_breakdown,
            "top_items": top_items,
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

        return {
            "user_id": user.id,
            "name": user.name,
            "period": f"{from_date.isoformat()} to {to_date.isoformat()}",
            "transaction_count": int(transaction_count),
            "total_sales": float(total_sales),
            "total_profit": float(total_profit),
            "sales": sales,
        }, None
