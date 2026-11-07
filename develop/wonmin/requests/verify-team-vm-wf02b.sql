-- Run only on the approved team VM, using its existing read-only DB session.
BEGIN READ ONLY;
SET LOCAL statement_timeout = '5s';
WITH target(request_id) AS (VALUES
    ('real-qa-e9ea1cdc3ffa41999f2ac269e1237db5'),
    ('real-qa-f1c560ff39bd46cda7ed866ca4c02461'),
    ('real-qa-2db1971503a241428cf4d30ecab63bac')
)
SELECT q.request_id,
       (SELECT count(*) FROM app.inquiries i WHERE i.request_id=q.request_id) AS inquiry_rows,
       (SELECT count(*) FROM app.tickets t WHERE t.request_key=q.request_id) AS ticket_rows,
       i.id AS inquiry_id, t.ticket_id, t.inquiry_id AS ticket_inquiry_id,
       i.requester_id AS inquiry_requester_id, t.requester_id AS ticket_requester_id,
       (i.id=t.inquiry_id AND i.requester_id=t.requester_id) AS ownership_and_link_match,
       i.attempt, i.status AS inquiry_status, t.status AS ticket_status,
       (i.result->'ticket'->>'ticket_id'=t.ticket_id) AS stored_result_ticket_match,
       (t.reply='실제 연동 QA 처리 확인') AS expected_admin_reply_match,
       (SELECT count(*) FROM app.alerts a WHERE a.event_key=q.request_id||':ticket-created') AS created_alert_rows,
       (SELECT count(*) FROM app.dlq d WHERE d.request_id=q.request_id) AS dlq_rows
FROM target q
LEFT JOIN app.inquiries i ON i.request_id=q.request_id
LEFT JOIN app.tickets t ON t.request_key=q.request_id
ORDER BY q.request_id;
ROLLBACK;
