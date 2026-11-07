-- Explicit local-only application fixture seed. This is not an Alembic migration.
-- Target: the private develop/jihye Compose database named oke_jihye_p0.
BEGIN;

DO $local_seed_guard$
DECLARE
    current_revision text;
BEGIN
    IF current_database() <> 'oke_jihye_p0' THEN
        RAISE EXCEPTION 'local mock seed refused: unexpected database';
    END IF;
    IF current_user <> 'oke_migration' THEN
        RAISE EXCEPTION 'local mock seed refused: migration owner connection required';
    END IF;
    SELECT version_num INTO current_revision FROM public.alembic_version;
    IF current_revision IS DISTINCT FROM '0005' THEN
        RAISE EXCEPTION 'local mock seed refused: expected migration 0005';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'local mock seed refused: pgvector is not installed';
    END IF;
END
$local_seed_guard$;

DO $employee_guard$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM (VALUES
            ('이준호', '영업팀'), ('박서연', '재무팀'), ('최유진', '인사팀'),
            ('한지훈', '개발팀'), ('김민지', 'IT팀'), ('정우성', 'IT팀')
        ) AS expected(name, dept)
        JOIN app.employees AS existing USING (name)
        WHERE existing.dept <> expected.dept
    ) THEN
        RAISE EXCEPTION 'local mock seed refused: employee fixture conflicts with existing roster';
    END IF;
END
$employee_guard$;

-- This is the team's fixed six-person test roster, not a VM/API fetch.
INSERT INTO app.employees (name, dept) VALUES
    ('이준호', '영업팀'), ('박서연', '재무팀'), ('최유진', '인사팀'),
    ('한지훈', '개발팀'), ('김민지', 'IT팀'), ('정우성', 'IT팀')
ON CONFLICT (name) DO NOTHING;

INSERT INTO app.inquiries
    (request_id, requester_id, question, attempt, context, result, status)
SELECT fixture.request_id, employee.id, fixture.question, 1, NULL, NULL, fixture.status
FROM (VALUES
    ('localmock-vpn-001', '박서연', 'VPN 연결이 자주 끊겨요. 점검 방법이 궁금합니다.', 'submitted'),
    ('localmock-device-002', '이준호', '노트북 반납 절차를 확인하고 싶어요.', 'completed'),
    ('localmock-security-003', '최유진', '의심스러운 메일을 받았어요. 확인이 필요합니다.', 'failed')
) AS fixture(request_id, employee_name, question, status)
JOIN app.employees AS employee ON employee.name = fixture.employee_name
ON CONFLICT (request_id) DO NOTHING;

INSERT INTO app.tickets
    (request_key, inquiry_id, requester_id, title, category, priority, status, assignee_id, reply)
SELECT fixture.request_key, inquiry.id, requester.id, fixture.title, fixture.category,
       fixture.priority, fixture.status, assignee.id, fixture.reply
FROM (VALUES
    ('localmock-device-002', '이준호', '장비 반납 절차 문의', 'device', 'normal', 'open', NULL::text, NULL::text),
    ('localmock-security-003', '최유진', '의심 메일 확인 요청', 'security', 'high', 'in_progress', '김민지', '[로컬 mock] 보안 담당자가 확인 중입니다.')
) AS fixture(request_key, requester_name, title, category, priority, status, assignee_name, reply)
JOIN app.inquiries AS inquiry ON inquiry.request_id = fixture.request_key
JOIN app.employees AS requester ON requester.name = fixture.requester_name
LEFT JOIN app.employees AS assignee ON assignee.name = fixture.assignee_name
ON CONFLICT (request_key) DO NOTHING;

INSERT INTO app.alerts (ticket_id, event_key, workflow, node, message, severity)
SELECT ticket.id, fixture.event_key, 'local-mock-seed', fixture.node,
       fixture.message, fixture.severity
FROM (VALUES
    ('localmock-alert-security-001', 'localmock-security-003', 'security-review',
     '[로컬 mock] 보안 문의 확인 알림', 'high'),
    ('localmock-alert-device-002', 'localmock-device-002', 'ticket-created',
     '[로컬 mock] 장비 반납 문의 접수 알림', 'low')
) AS fixture(event_key, request_key, node, message, severity)
JOIN app.tickets AS ticket ON ticket.request_key = fixture.request_key
ON CONFLICT (event_key) DO NOTHING;

INSERT INTO app.dlq
    (request_id, execution_ref, workflow, node, reason, safe_payload, status)
SELECT 'localmock-security-003', 'localmock-execution-001', 'local-mock-seed',
       'mock-recovery', 'synthetic_failure',
       '{"fixture":"local-mock-seed-v1","request_type":"security"}'::jsonb,
       'pending'
WHERE NOT EXISTS (
    SELECT 1 FROM app.dlq
    WHERE workflow = 'local-mock-seed'
      AND request_id = 'localmock-security-003'
      AND execution_ref = 'localmock-execution-001'
);

-- Store an unmistakably synthetic C02-shaped result for the completed fixture.
UPDATE app.inquiries AS inquiry
SET result = jsonb_build_object(
    'fixture_marker', 'local-mock-seed-v1',
    'request_id', inquiry.request_id,
    'route', '담당자 이관',
    'answer', '[로컬 mock] 이 문의는 화면 확인용 합성 데이터입니다.',
    'sources', '[]'::jsonb,
    'ticket', jsonb_build_object(
        'ticket_id', ticket.ticket_id, 'priority', ticket.priority,
        'duplicate', false, 'status', ticket.status, 'reply', ticket.reply
    ),
    'agents', jsonb_build_array('triage'),
    'security', jsonb_build_object('blocked_by', NULL, 'reason', NULL, 'masked', 0)
)
FROM app.tickets AS ticket
WHERE inquiry.request_id = 'localmock-device-002'
  AND ticket.request_key = inquiry.request_id
  AND (inquiry.result IS NULL OR inquiry.result->>'fixture_marker' = 'local-mock-seed-v1');

DO $fixture_guard$
BEGIN
    IF (SELECT count(*) FROM app.inquiries WHERE request_id LIKE 'localmock-%') <> 3
       OR (SELECT count(*) FROM app.tickets WHERE request_key LIKE 'localmock-%') <> 2
       OR (SELECT count(*) FROM app.alerts WHERE event_key LIKE 'localmock-alert-%') <> 2
       OR (SELECT count(*) FROM app.dlq WHERE workflow = 'local-mock-seed') <> 1
       OR NOT EXISTS (
           SELECT 1 FROM app.inquiries
           WHERE request_id = 'localmock-device-002'
             AND result->>'fixture_marker' = 'local-mock-seed-v1'
       ) THEN
        RAISE EXCEPTION 'local mock seed refused: fixture key conflicts with existing data';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM (VALUES
            ('localmock-vpn-001', '박서연', 'VPN 연결이 자주 끊겨요. 점검 방법이 궁금합니다.', 'submitted'),
            ('localmock-device-002', '이준호', '노트북 반납 절차를 확인하고 싶어요.', 'completed'),
            ('localmock-security-003', '최유진', '의심스러운 메일을 받았어요. 확인이 필요합니다.', 'failed')
        ) AS expected(request_id, employee_name, question, status)
        LEFT JOIN app.inquiries AS inquiry ON inquiry.request_id = expected.request_id
        LEFT JOIN app.employees AS employee ON employee.name = expected.employee_name
        WHERE inquiry.id IS NULL OR inquiry.requester_id <> employee.id
           OR inquiry.question <> expected.question OR inquiry.attempt <> 1
           OR inquiry.status <> expected.status
    ) OR EXISTS (
        SELECT 1
        FROM (VALUES
            ('localmock-device-002', '이준호', '장비 반납 절차 문의', 'device', 'normal', 'open'),
            ('localmock-security-003', '최유진', '의심 메일 확인 요청', 'security', 'high', 'in_progress')
        ) AS expected(request_key, requester_name, title, category, priority, status)
        LEFT JOIN app.tickets AS ticket ON ticket.request_key = expected.request_key
        LEFT JOIN app.employees AS employee ON employee.name = expected.requester_name
        WHERE ticket.id IS NULL OR ticket.requester_id <> employee.id
           OR ticket.title <> expected.title OR ticket.category <> expected.category
           OR ticket.priority <> expected.priority OR ticket.status <> expected.status
    ) OR EXISTS (
        SELECT 1
        FROM (VALUES
            ('localmock-alert-security-001', 'localmock-security-003', 'security-review',
             '[로컬 mock] 보안 문의 확인 알림', 'high'),
            ('localmock-alert-device-002', 'localmock-device-002', 'ticket-created',
             '[로컬 mock] 장비 반납 문의 접수 알림', 'low')
        ) AS expected(event_key, request_key, node, message, severity)
        LEFT JOIN app.alerts AS alert ON alert.event_key = expected.event_key
        LEFT JOIN app.tickets AS ticket ON ticket.request_key = expected.request_key
        WHERE alert.id IS NULL OR alert.ticket_id <> ticket.id
           OR alert.workflow <> 'local-mock-seed' OR alert.node <> expected.node
           OR alert.message <> expected.message OR alert.severity <> expected.severity
    ) OR NOT EXISTS (
        SELECT 1 FROM app.dlq
        WHERE request_id = 'localmock-security-003'
          AND execution_ref = 'localmock-execution-001'
          AND workflow = 'local-mock-seed' AND node = 'mock-recovery'
          AND reason = 'synthetic_failure'
          AND safe_payload = '{"fixture":"local-mock-seed-v1","request_type":"security"}'::jsonb
          AND status = 'pending'
    ) THEN
        RAISE EXCEPTION 'local mock seed refused: existing fixture values differ';
    END IF;
END
$fixture_guard$;

COMMIT;

SELECT
    (SELECT count(*) FROM app.employees) AS employees,
    (SELECT count(*) FROM app.inquiries WHERE request_id LIKE 'localmock-%') AS mock_inquiries,
    (SELECT count(*) FROM app.tickets WHERE request_key LIKE 'localmock-%') AS mock_tickets,
    (SELECT count(*) FROM app.alerts WHERE event_key LIKE 'localmock-alert-%') AS mock_alerts,
    (SELECT count(*) FROM app.dlq WHERE workflow = 'local-mock-seed') AS mock_dlq,
    (SELECT count(*) FROM rag.documents) AS rag_documents,
    (SELECT count(*) FROM rag.chunks) AS rag_chunks;
