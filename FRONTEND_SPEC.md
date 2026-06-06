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
* Fallback to full login if PIN fails

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
* Reports Page (non-employee only)
* Employee Management (admin only)

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

### 6.2 Actions

* Add product → allowed
* Edit product → allowed
* Delete product → allowed

(Note: Backend will enforce role restrictions if needed)

---

## 7. PURCHASE (RESTOCK)

### 7.1 Access

* All roles can create purchase entries

### 7.2 Approval

* Purchases require admin approval before affecting inventory

---

## 8. REPORTS

* Daily reports only
* Summary view (no complex charts required initially)

---

## 9. EMPLOYEE MANAGEMENT

### 9.1 User Creation

* Users are NOT created by admin manually
* Users sign up themselves

### 9.2 First Login

* Admin must approve account before access is granted

### 9.3 Stored Fields

* Name
* Username
* Password
* Role
* Phone / Email
* Bank details

### 9.4 Account Control

* Users can be deactivated (not deleted)

---

## 10. ROLE PERMISSIONS (UI BEHAVIOR)

### Employee

* Cannot view reports
* Can create sales
* Can edit sales within 20 minutes
* After 20 minutes → requires manager approval

### Manager

* Can edit any sale without time restriction
* All edits are logged
* Admin is notified of edits

### Admin

* Full access

---

## 11. OFFLINE MODE

### 11.1 Offline Indicator

* Show persistent banner: "Offline Mode"

### 11.2 Behavior

* No features disabled
* All actions continue normally

### 11.3 Unsynced Data

* Mark unsynced sales with label: "Not Synced"

### 11.4 Sync System

* Automatic retry: 5 attempts
* Manual "Sync Now" button available

---

## 12. ERROR HANDLING

* Show toast messages for errors
* No blocking modals unless critical

---

## 13. UI STYLE

* Balanced:

  * Clean
  * Fast
  * Not overly decorative

---

## 14. TARGET DEVICES

* Primary: Android phones
* Secondary: Desktop (basic support required)

---

## 15. LOGGING & AUDIT (UI HOOKS)

* Sales edits must trigger:

  * Log entry
  * Admin notification (handled by backend)

---

## FINAL NOTES

* Keep UI fast and minimal
* Prioritize speed over design complexity
* All critical rules enforced by backend, not frontend

---
