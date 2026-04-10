from typing import Optional
import hashlib
from src import database, commands


class User:
    """
    Manages user authentication and account operations.
    
    Handles user registration, login, logout, and profile management.
    - Passwords are hashed using SHA256
    - New users start in "pending" state, awaiting admin approval
    - Supports role-based access: "user" (employee) and "admin"
    
    Example:
        user = User()
        status = user.register("john_doe", "John", "Doe", "password123")
        if status == "pending":
            print("Registration pending admin approval")
    
    Attributes:
        db (Database): Database connection instance
        cmds (Commands): CLI commands instance
        current_user (str): Currently authenticated username
    """
    
    def __init__(self) -> None:
        """Initialize User manager with database connection."""
        self.db = database.Database()
        self.cmds = commands.Commands()
        self.current_user: Optional[str] = None
    
    def register(self, first_name: str, last_name: str, 
                username: str, password: str) -> str:
        """
        Register a new user account.
        
        Business logic:
        - Username must be unique (case-sensitive)
        - Password is hashed using SHA256 before storage
        - New users are inactive until admin approval
        - Default role is "user" (employee)
        
        Example:
            status = user.register("john_doe", "John", "Doe", "secret123")
            if status == "pending":
                print("Waiting for admin approval")
        
        Args:
            first_name (str): User's first name
            last_name (str): User's last name
            username (str): Unique username (alphanumeric recommended)
            password (str): User's password (plaintext, gets hashed)
        
        Returns:
            str: Registration status:
                - "taken" if username already exists
                - "pending" if registration successful, awaiting approval
                
        Raises:
            Exception: If database insert fails
        """
        # Check if username is already taken
        if self.db.user_exists(username):
            return "taken"
        
        # Hash password using SHA256 for security
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Create user account in pending state (awaiting admin approval)
        self.db.run(
            "INSERT INTO users (first_name, last_name, username, password, "
            "role, approval_status, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (first_name, last_name, username, password_hash, 
             "user", "pending", "false")
        )

        self.current_user = username
        return "pending"
    
    def login(self, username: str, password: str) -> str:
        """
        Authenticate user with username and password.
        
        Checks multiple conditions before granting access:
        - Account exists with matching credentials
        - Account has been approved by admin (approval_status = 'approved')
        - Account is active (is_active = 'true')
        
        Example:
            result = user.login("john_doe", "secret123")
            if result == "successful":
                print("Logged in!")
            elif result == "pending":
                print("Account awaiting admin approval")
        
        Args:
            username (str): User's username
            password (str): User's plaintext password
        
        Returns:
            str: Login result:
                - "successful" if login OK, user can proceed
                - "none" if username doesn't exist
                - "incorrect" if password doesn't match
                - "pending" if account awaits admin approval
                - "declined" if admin rejected account
                - "deactivated" if account disabled by admin
        """
        # Query user account from database
        user_row = self.db.query(
            "SELECT id, password, is_active, "
            "COALESCE(approval_status, 'approved') FROM users "
            "WHERE username = ? LIMIT 1",
            (username,)
        )

        # User doesn't exist
        if not user_row:
            return "none"

        # Extract user data (format depends on database engine)
        if isinstance(user_row[0], dict):
            stored_password = user_row[0]['password']
            is_active = user_row[0]['is_active']
            approval_status = user_row[0]['COALESCE(approval_status, \'approved\')']
        else:
            # SQLite Row format - fall back to tuple indexing
            stored_password = user_row[0][1]
            is_active = user_row[0][2]
            approval_status = user_row[0][3]

        # Check account approval status
        # Accounts must be explicitly approved by admin
        if str(approval_status).strip().lower() == "pending":
            return "pending"
        
        # Admin may have explicitly declined the account
        if str(approval_status).strip().lower() == "declined":
            return "declined"
        
        # Admin may have deactivated the account
        if str(is_active).strip().lower() not in {"true", "1", "on"}:
            return "deactivated"

        # Hash submitted password and compare with stored hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash != stored_password:
            return "incorrect"

        # All checks passed - login successful
        self.current_user = username
        return "successful"
    
    def logout(self) -> str:
        """
        Logout the current user.
        
        Clears session data (current_user, database connection).
        
        Returns:
            str: Logout confirmation message
        """
        self.current_user = None
        self.db = None
        return "Logged out successfully."
    
    def get_current_user(self) -> Optional[str]:
        """
        Get the currently logged-in username.
        
        Example:
            username = user.get_current_user()
            print(f"Logged in as: {username}")
        
        Returns:
            str: Currently authenticated username, or None if not logged in
        """
        return self.current_user
