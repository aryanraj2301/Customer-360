with customers as (
    select customer_id, email from {{ source('bronze', 'customers') }}
),

resolved_tickets as (
    select
        t.ticket_id,
        coalesce(c.customer_id, t.customer_ref) as resolved_customer_id,
        t.category,
        t.csat_score,
        t.created_date,
        case when c.customer_id is not null then 'matched_by_email' else 'unmatched' end as match_method
    from {{ source('bronze', 'support_tickets') }} t
    left join customers c on lower(trim(t.customer_ref)) = lower(trim(c.email))
)

select * from resolved_tickets