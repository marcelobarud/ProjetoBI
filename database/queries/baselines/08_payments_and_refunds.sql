SELECT 'payment' record_type,m.method_type method_or_status,p.status,
       count(*) records,sum(p.amount) amount
  FROM payments.payments p JOIN payments.payment_methods m USING(payment_method_id)
 GROUP BY 1,2,3
UNION ALL
SELECT 'refund','refund',r.status,count(*),sum(r.amount)
  FROM payments.refunds r GROUP BY r.status
ORDER BY 1,2,3;
