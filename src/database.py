import os
import sqlite3
from typing import Optional, List, Dict, Any
import psycopg
from psycopg.rows import dict_row


class Database:
    """
    Database abstraction layer supporting both PostgreSQL (production) and SQLite (development).
    
    Automatically selects the database engine based on the DATABASE_URL environment variable:
    - If DATABASE_URL is set: Uses PostgreSQL
    - If DATABASE_URL is empty: Uses SQLite locally (development only)
    
    Example:
        db = Database()
        db.run("INSERT INTO users (username) VALUES (?)", ("john_doe",))
        users = db.query("SELECT * FROM users")
    """
    
    def __init__(self, username: Optional[str] = None) -> None:
        """
        Initialize the database connection handler.
        
        Args:
            username (str, optional): Current logged-in username for audit purposes
        """
        self.database_url: Optional[str] = os.getenv("DATABASE_URL")
        self.current_username: Optional[str] = username

        if self.database_url:
            # Fix: Convert postgres:// to postgresql:// (Render uses postgres://, but psycopg needs postgresql://)
            if self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
                print("[DB] Converted postgres:// to postgresql:// URL format")
            
            self.engine = "postgres"
            print("[DB INIT] Using PostgreSQL")
        else:
            self.engine = "sqlite"
            print("[DB INIT] Using SQLite (DEV ONLY)")

        # Initialize database schema on startup
        self.initialize_database()

    def get_connection(self):
        """
        Get a new database connection (PostgreSQL or SQLite based on engine).
        
        Returns:
            Connection object (psycopg connection or sqlite3 connection)
            
        Raises:
            RuntimeError: If PostgreSQL engine selected but DATABASE_URL not set
            RuntimeError: If PostgreSQL connection fails in production
        """
        if self.engine == "postgres":
            # Validate DATABASE_URL is set (catches configuration errors early)
            if not self.database_url:
                raise RuntimeError(
                    "DATABASE_URL environment variable is not set! "
                    "PostgreSQL requires a valid connection string. "
                    "Set DATABASE_URL=postgresql://user:password@host:5432/dbname"
                )

            try:
                return psycopg.connect(self.database_url, row_factory=dict_row)
            except psycopg.OperationalError as exc:
                if os.getenv("FLASK_ENV", "development") != "production":
                    print(
                        "[DB WARN] PostgreSQL connection failed. "
                        "Falling back to SQLite for development because FLASK_ENV!=production."
                    )
                    print(f"[DB WARN] {exc}")
                    self.engine = "sqlite"
                    return self.get_connection()

                raise RuntimeError(
                    "Failed to connect to PostgreSQL. "
                    "Check DATABASE_URL, network access, and host name resolution."
                ) from exc
        else:
            conn = sqlite3.connect("database.db")
            conn.row_factory = sqlite3.Row
            return conn

    def initialize_database(self) -> None:
        """Create all required tables if they don't exist."""
        conn = self.get_connection()
        try:
            self.create_tables_if_not_exist(conn)
        finally:
            conn.close()

    def create_tables_if_not_exist(self, conn) -> None:
        """
        Create database schema (users, product, transactions tables).
        
        This method is called automatically on Database initialization.
        Safe to call multiple times as it uses CREATE TABLE IF NOT EXISTS.
        
        Database-specific syntax handling:
        - PostgreSQL: Uses SERIAL, DOUBLE PRECISION, TIMESTAMP
        - SQLite: Uses INTEGER PRIMARY KEY AUTOINCREMENT, REAL, DATETIME
        
        Args:
            conn: Database connection object
        """
        cursor = conn.cursor()

        # Fix: Use correct syntax for each database engine
        if self.engine == "postgres":
            # PostgreSQL: SERIAL auto-increments, DOUBLE PRECISION for decimals, TIMESTAMP for dates
            id_column = "SERIAL PRIMARY KEY"
            number_type = "DOUBLE PRECISION"
            timestamp_type = "TIMESTAMP"
        else:
            # SQLite: INTEGER PRIMARY KEY AUTOINCREMENT, REAL for decimals, DATETIME for dates
            id_column = "INTEGER PRIMARY KEY AUTOINCREMENT"
            number_type = "REAL"
            timestamp_type = "DATETIME"

        # Users table: stores employee and admin accounts
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {id_column},
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user',
            approval_status TEXT DEFAULT 'approved',
            is_active TEXT DEFAULT 'true',
            account_name TEXT,
            account_owner_name TEXT,
            bank_name TEXT,
            account_address TEXT,
            phone TEXT,
            image_path TEXT,
            created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Product table: inventory management
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS product (
            id {id_column},
            name TEXT UNIQUE,
            price {number_type},
            quantity INTEGER DEFAULT 0,
            image_path TEXT,
            created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Transactions table: sales and purchase records
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS transactions (
            id {id_column},
            user_id INTEGER,
            product_id INTEGER,
            amount {number_type},
            quantity INTEGER DEFAULT 1,
            type TEXT,
            status TEXT DEFAULT 'completed',
            customer_name TEXT,
            invoice_path TEXT,
            proof_path TEXT,
            created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()
        print("[DB] Tables ready")

    def run(self, sql: str, params: Optional[tuple] = None) -> None:
        """
        Execute a write operation (INSERT, UPDATE, DELETE).
        
        Example:
            db.run("INSERT INTO users (username) VALUES (?)", ("john",))
        
        Args:
            sql (str): SQL query with ? placeholders
            params (tuple, optional): Query parameters
            
        Raises:
            Exception: If query execution fails
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("[DB ERROR RUN]", e)
            raise e
        finally:
            conn.close()

    def query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a read operation (SELECT).
        
        Returns results as list of dictionaries for consistent interface.
        
        Example:
            users = db.query("SELECT * FROM users WHERE role = ?", ("admin",))
            for user in users:
                print(user["username"])
        
        Args:
            sql (str): SQL query with ? placeholders
            params (tuple, optional): Query parameters
            
        Returns:
            List of result dictionaries (empty list if no results or error)
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            if self.engine == "postgres":
                return cursor.fetchall()
            else:
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print("[DB ERROR QUERY]", e)
            return []
        finally:
            conn.close()

    def user_exists(self, username: str) -> bool:
        """
        Check if a user account already exists.
        
        Args:
            username (str): Username to check
            
        Returns:
            bool: True if user exists, False otherwise
        """
        rows = self.query("SELECT COUNT(*) as count FROM users WHERE username = ?", (username,))
        return rows[0]['count'] > 0 if rows else False

    def verify_user(self, username: str, password: str) -> bool:
        """
        Verify user credentials (username and password match).
        
        Args:
            username (str): Username to verify
            password (str): Hashed password to verify
            
        Returns:
            bool: True if credentials match, False otherwise
        """
        rows = self.query(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        return bool(rows)

    def is_database_ready(self) -> bool:
        """
        Check if database is initialized and ready to use.
        
        Returns:
            bool: Always True (database is initialized in __init__)
        """
        return True