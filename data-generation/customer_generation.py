
from faker import Faker
import random
import csv
import os

fake = Faker()
random.seed(42)
OUT_DIR = os.path.dirname(__file__)

def write_csv(filename, rows):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"{filename}: {len(rows)} rows")

# ---------- customers.csv ----------
customers = []
customer_ids = []
for i in range(300):
    cid = f"CUST{i:05d}"
    customer_ids.append(cid)
    customers.append({
        "customer_id": cid,
        "full_name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "signup_date": fake.date_between(start_date="-2y", end_date="today"),
        "source_system": "crm"
    })
write_csv("customers.csv", customers)

# ---------- orders.csv + order_items.csv ----------
orders, order_items = [], []
order_id_counter = 0
for cid in customer_ids:
    num_orders = random.choices([0, 1, 2, 3, 5], weights=[10, 40, 30, 15, 5])[0]
    for _ in range(num_orders):
        oid = f"ORD{order_id_counter:06d}"
        order_id_counter += 1
        order_date = fake.date_between(start_date="-1y", end_date="today")
        num_items = random.randint(1, 5)
        total = 0
        for _ in range(num_items):
            price = round(random.uniform(5, 200), 2)
            qty = random.randint(1, 3)
            total += price * qty
            order_items.append({
                "order_item_id": f"OI{len(order_items):06d}",
                "order_id": oid,
                "product_name": fake.word().capitalize() + " " + fake.word().capitalize(),
                "quantity": qty,
                "unit_price": price
            })
        orders.append({
            "order_id": oid,
            "customer_id": cid,
            "order_date": order_date,
            "status": random.choice(["completed", "completed", "completed", "cancelled", "refunded"]),
            "total_amount": round(total, 2)
        })
write_csv("orders.csv", orders)
write_csv("order_items.csv", order_items)

# ---------- support_tickets.csv (messy: sometimes email instead of customer_id) ----------
tickets = []
ticket_customers = random.sample(customers, k=int(len(customers) * 0.3))
for c in ticket_customers:
    for _ in range(random.randint(1, 3)):
        use_email_instead = random.random() < 0.35   # deliberate messiness
        tickets.append({
            "ticket_id": f"TIX{len(tickets):05d}",
            "customer_ref": c["email"] if use_email_instead else c["customer_id"],
            "created_date": fake.date_between(start_date="-1y", end_date="today"),
            "category": random.choice(["shipping", "billing", "product_defect", "general_inquiry"]),
            "csat_score": random.randint(1, 5)
        })
write_csv("support_tickets.csv", tickets)

# ---------- web_events.csv (messy: mix of real customer_id and anonymous cookie ids) ----------
events = []
for _ in range(1500):
    known = random.random() < 0.6
    ref = random.choice(customer_ids) if known else f"anon_{fake.uuid4()[:8]}"
    events.append({
        "event_id": f"EVT{len(events):06d}",
        "anon_or_cust_id": ref,
        "event_type": random.choice(["page_view", "add_to_cart", "checkout_start", "product_view"]),
        "event_timestamp": fake.date_time_between(start_date="-6M", end_date="now")
    })
write_csv("web_events.csv", events)

print("\nAll 5 CSVs generated in:", OUT_DIR)