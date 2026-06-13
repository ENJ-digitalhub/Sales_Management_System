# FRONTEND_SPEC.md

## 1. AUTHENTICATION FLOW

### 1.1 Login Screen

* Inputs:

  * Username
  * Password
* Login button

### 1.2 PIN Login

* PIN is used for fast login after app reopen
* Show PIN input screen if session exists
* Fallback to full login if PIN fails or PIN is not set

### 1.3 Post-Login Redirect

* Redirect based on role:

  * Admin → Admin Dashboard
  * Manager → Manager Dashboard
  * Employee → Sales Dashboard

---

## 2. NAVIGATION

### Mobile Navigation

* Bottom Tab Navigation

### Tabs:

* Sales
* Inventory
* Purchases
* Reports (hidden for employees)
* More (settings / logout)

---

## 3. CORE SCREENS

* Sales Dashboard
* Purchase Dashboard (restocking)
* Inventory Page
* Reports Page (Admin and Manager only)
* Employee Management (Admin only)

---

## 4. SALES FLOW

### 4.1 Product Selection

* Search bar
* Category filter

### 4.2 Cart

* Add products to cart
* Edit quantity
* Remove items

### 4.3 Complete Sale

* "Complete Sale" button
* Confirmation modal before submission

### 4.4 After Sale

* Cart resets automatically
* Show success toast: "Sale completed"

### 4.5 Sale Rejection

* If server rejects sale due to insufficient stock:

  * Show error toast identifying which product(s) caused the rejection
  * Cart is preserved so user can adjust quantities and retry

---

## 5. PAYMENT UI

* Payment method selection via buttons:

  * Cash
  * Transfer
  * POS

---

## 6. INVENTORY

### 6.1 Product List

Display:

* Product name
* Price
* Stock quantity

Only active products (is_active = true) are shown.

### 6.2 Actions

* Add product → allowed
* Edit product → allowed
* Delete product → soft delete (product hidden from list, not permanently removed)

---

## 7. PURCHASE (RESTOCK)

### 7.1 Access

* All roles can create purchase entries

### 7.2 Status Display

* Purchases show status: `pending`, `approved`, or `rejected`
* Pending purchases show clearly in admin view awaiting action

### 7.3 Approval (Admin only)

* Admin sees "Approve" and "Reject" buttons on pending purchases
* Approval triggers stock update
* Rejection closes the purchase without stock change

---

## 8. REPORTS

* Daily reports (default view)
* Monthly summary available
* Summary view — no complex charts required in Phase 1
* Accessible by Admin and Manager only
* Reports reflect only synced, committed data

---

## 9. EMPLOYEE MANAGEMENT

### 9.1 User Creation

* Users sign up themselves
* Admin is NOT required to manually create accounts

### 9.2 First Login

* Admin must approve account before access is granted

### 9.3 Stored Fields

* Name
* Username
* Password
* Role
* Phone / Email
* Bank details (optional)

### 9.4 Account Control

* Users can be **deactivated** (not deleted)
* Deactivated users cannot log in
* Their history and records remain intact

---

## 10. ROLE PERMISSIONS (UI BEHAVIOR)

### Employee

* Cannot view Reports tab
* Can create sales
* Can edit own sales within 20 minutes
* After 20 minutes → must request manager authorization

### Manager

* Can edit any sale without time restriction
* All edits are logged
* Admin is notified of edits
* Can approve late sale edit requests from employees
* Can cancel sales

### Admin

* Full access to all features
* Can approve and reject purchases
* Can deactivate user accounts
* Can view full audit logs

---

## 11. OFFLINE MODE

### 11.1 Offline Indicator

* Show persistent banner: "Offline Mode — changes will sync when reconnected"

### 11.2 Behavior

* All sales and purchase entry creation continue normally
* Purchase approvals require server connection (admin action only)

### 11.3 Unsynced Data

* Mark unsynced sales with label: "Not Synced"

### 11.4 Sync System

* Automatic sync triggers immediately on reconnection
* Retry up to 5 times with exponential backoff
* Manual "Sync Now" button available at all times
* After 5 failures, item is marked FAILED and manager is notified

---

## 12. ERROR HANDLING

* Show toast messages for errors
* No blocking modals unless action is critical (e.g. confirming a sale cancellation)
* On sale rejection: preserve cart contents, show which item caused the rejection

---

## 13. UI STYLE

* Clean, fast, minimal
* Prioritize speed and usability over decoration
* Target non-technical users

---

## 14. TARGET DEVICES

* Primary: Android phones
* Secondary: Desktop (basic support required)

---

## 15. LOGGING & AUDIT (UI HOOKS)

* Sales edits must trigger:

  * Log entry (handled by backend)
  * Admin notification (handled by backend)
* Purchase approvals and rejections:

  * Logged automatically by backend

---

## FINAL NOTES

* Keep UI fast and minimal
* Prioritize speed over design complexity
* All critical business rules enforced by backend, not frontend
* Frontend displays state — backend owns truth