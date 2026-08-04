select
    order_id,
    customer_id,
    cast(order_date as date) as order_date,
    lower(trim(status)) as status,
    round(total_amount, 2) as total_amount
from {{ source('bronze', 'orders') }}
where status != 'cancelled'