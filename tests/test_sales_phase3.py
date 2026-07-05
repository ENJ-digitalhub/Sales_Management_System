def test_create_sale_cash(client, auth_headers, seeded_product):
    payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 1}],
        "payment_method": "cash"
    }
    res = client.post("/sales", json=payload, headers=auth_headers)
    assert res.status_code == 201
    body = res.get_json()
    assert body["success"] is True
    assert body["sale"]["payment_method"] == "cash"

def test_create_sale_card_provider(client, auth_headers, seeded_product):
    payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 1}],
        "payment_method": "card",
        "payment_provider": "paystack"
    }
    res = client.post("/sales", json=payload, headers=auth_headers)
    assert res.status_code == 201

def test_create_sale_bank_transfer_provider(client, auth_headers, seeded_product):
    payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 1}],
        "payment_method": "bank_transfer",
        "payment_provider": "gtbank"
    }
    res = client.post("/sales", json=payload, headers=auth_headers)
    assert res.status_code == 201

def test_create_sale_digital_wallet_provider(client, auth_headers, seeded_product):
    payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 1}],
        "payment_method": "digital_wallet",
        "payment_provider": "opay"
    }
    res = client.post("/sales", json=payload, headers=auth_headers)
    assert res.status_code == 201

def test_create_sale_split_payment(client, auth_headers, seeded_product):
    payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 1}],
        "payment_method": "split_payment",
        "payment_details": [
            {"method": "cash", "amount": 5000},
            {"method": "bank_transfer", "provider": "moniepoint", "amount": 15000}
        ]
    }
    res = client.post("/sales", json=payload, headers=auth_headers)
    assert res.status_code == 201

def test_create_sale_duplicate_product_ids(client, auth_headers, seeded_product):
    payload = {
        "items": [
            {"product_id": seeded_product.id, "quantity": 1},
            {"product_id": seeded_product.id, "quantity": 2}
        ],
        "payment_method": "cash"
    }
    res = client.post("/sales", json=payload, headers=auth_headers)
    assert res.status_code == 400

def test_create_sale_insufficient_stock(client, auth_headers, seeded_product):
    payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 999999}],
        "payment_method": "cash"
    }
    res = client.post("/sales", json=payload, headers=auth_headers)
    assert res.status_code in (400, 422)

def test_get_sale_by_id(client, auth_headers, seeded_product):
    create_payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 1}],
        "payment_method": "cash"
    }
    create_res = client.post("/sales", json=create_payload, headers=auth_headers)
    sale_id = create_res.get_json()["sale"]["id"]

    res = client.get(f"/sales/{sale_id}", headers=auth_headers)
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert body["sale"]["id"] == sale_id

def test_edit_sale_within_window(client, auth_headers, seeded_product):
    create_payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 1}],
        "payment_method": "cash"
    }
    create_res = client.post("/sales", json=create_payload, headers=auth_headers)
    sale_id = create_res.get_json()["sale"]["id"]

    edit_payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 2}],
        "payment_method": "cash"
    }
    res = client.patch(f"/sales/{sale_id}", json=edit_payload, headers=auth_headers)
    assert res.status_code == 200

def test_edit_sale_outside_window_employee(client, auth_headers, seeded_product, db_session):
    create_payload = {
        "items": [{"product_id": seeded_product.id, "quantity": 1}],
        "payment_method": "cash"
    }
    create_res = client.post("/sales", json=create_payload, headers=auth_headers)
    sale_id = create_res.get_json()["sale"]["id"]

    sale = db_session.get(type(create_res), sale_id)
    assert sale is not None