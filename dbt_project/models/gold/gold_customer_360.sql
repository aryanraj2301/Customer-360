with orders_agg as (
    select
        customer_id,
        count(*) as total_orders,
        sum(total_amount) as lifetime_value,
        max(order_date) as last_order_date
    from {{ ref('silver_orders') }}
    group by customer_id
),

tickets_agg as (
    select
        resolved_customer_id as customer_id,
        count(*) as total_tickets,
        avg(csat_score) as avg_csat
    from {{ ref('silver_identity_map') }}
    group by resolved_customer_id
)

select
    c.customer_id,
    c.full_name,
    c.email,
    c.signup_date,
    coalesce(o.total_orders, 0) as total_orders,
    coalesce(o.lifetime_value, 0) as lifetime_value,
    o.last_order_date,
    coalesce(t.total_tickets, 0) as total_tickets,
    round(t.avg_csat, 2) as avg_csat,
    case
        when o.last_order_date is null then true
        when o.last_order_date < current_date - interval '90 days' then true
        else false
    end as churn_risk_flag
from {{ source('bronze', 'customers') }} c
left join orders_agg o on c.customer_id = o.customer_id
left join tickets_agg t on c.customer_id = t.customer_id