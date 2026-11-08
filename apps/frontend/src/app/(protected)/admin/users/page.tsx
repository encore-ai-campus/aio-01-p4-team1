"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { adminUsersApi } from "../../../../lib/api/admin-users";
import { me } from "../../../../lib/api/auth";
import type { AccountView, EmployeeAdminView } from "../../../../lib/api/types";

export default function AdminUsersPage() {
  const [employees, setEmployees] = useState<EmployeeAdminView[]>([]);
  const [users, setUsers] = useState<AccountView[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [currentAdminId, setCurrentAdminId] = useState<number | null>(null);
  const [identityReady, setIdentityReady] = useState(false);
  const [identityError, setIdentityError] = useState(false);
  const [employeeId, setEmployeeId] = useState("");
  const [loginId, setLoginId] = useState("");
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const [newEmployeeName, setNewEmployeeName] = useState("");
  const [newEmployeeDept, setNewEmployeeDept] = useState("");
  const [newEmployeeLoginId, setNewEmployeeLoginId] = useState("");
  const [newEmployeePassword, setNewEmployeePassword] = useState("");
  const [resetId, setResetId] = useState<number | null>(null);
  const [resetPassword, setResetPassword] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const resetPanelRef = useRef<HTMLElement>(null);
  const resetPasswordRef = useRef<HTMLInputElement>(null);

  const unissuedEmployees = employees.filter((employee) => employee.user_id == null);
  const resetTarget = users.find((user) => user.id === resetId) ?? null;

  const load = useCallback(async (): Promise<boolean> => {
    setLoading(true);
    setError("");
    try {
      const [employeeResult, userResult] = await Promise.all([
        adminUsersApi.listEmployees(),
        adminUsersApi.listAccounts(),
      ]);
      setEmployees(employeeResult.items);
      setUsers(userResult.items);
      return true;
    } catch (cause) {
      setEmployees([]);
      setUsers([]);
      setError(cause instanceof Error ? cause.message : "계정 정보를 불러오지 못했습니다.");
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    let active = true;
    me().then((user) => {
      if (active && user.role === "admin") setCurrentAdminId(user.id);
    }).catch(() => {
      if (active) setIdentityError(true);
    }).finally(() => {
      if (active) setIdentityReady(true);
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (resetId === null) return;
    resetPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    resetPasswordRef.current?.focus({ preventScroll: true });
  }, [resetId]);

  function isCurrentAdmin(user: AccountView) {
    return user.role === "admin"
      && (!identityReady || identityError || currentAdminId === null || currentAdminId === user.id);
  }

  function protectsCurrentAdmin(user: AccountView) {
    return user.is_active && isCurrentAdmin(user);
  }

  async function create(event: FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    if (busyId !== null || !employeeId || !loginId.trim() || !temporaryPassword) {
      if (!employeeId || !loginId.trim() || !temporaryPassword) setError("직원, 로그인 ID, 임시 비밀번호를 입력해 주세요.");
      return;
    }
    setBusyId(-1);
    try {
      await adminUsersApi.create({ employee_id: Number(employeeId), login_id: loginId.trim(), temporary_password: temporaryPassword });
      setTemporaryPassword("");
      setLoginId("");
      setEmployeeId("");
      if (await load()) setNotice("계정을 발급하고 최신 목록을 다시 불러왔습니다.");
      else setError("계정 발급은 성공했지만 목록 재조회에 실패했습니다. 중복 발급하지 말고 새로고침으로 목록만 다시 확인해 주세요.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "계정을 발급하지 못했습니다.");
    } finally {
      setBusyId(null);
    }
  }

  async function createEmployeeAndAccount(event: FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    const name = newEmployeeName.trim();
    const dept = newEmployeeDept.trim();
    const newLoginId = newEmployeeLoginId.trim();
    if (busyId !== null || !name || !dept || !newLoginId || !newEmployeePassword) {
      if (!name || !dept || !newLoginId || !newEmployeePassword) setError("직원 이름, 부서, 로그인 ID, 임시 비밀번호를 모두 입력해 주세요.");
      return;
    }

    setBusyId(-2);
    let createdEmployee: EmployeeAdminView | null = null;
    try {
      createdEmployee = await adminUsersApi.createEmployee({ name, dept });
      await adminUsersApi.create({ employee_id: createdEmployee.id, login_id: newLoginId, temporary_password: newEmployeePassword });
      setNewEmployeeName("");
      setNewEmployeeDept("");
      setNewEmployeeLoginId("");
      setNewEmployeePassword("");
      if (await load()) setNotice(`${name} 님의 직원 정보와 계정을 등록하고 최신 목록을 불러왔습니다.`);
      else setError("직원 정보와 계정 등록은 성공했지만 목록 재조회에 실패했습니다. 중복 등록하지 말고 새로고침으로 목록만 확인해 주세요.");
    } catch (cause) {
      if (createdEmployee) {
        setNewEmployeeName("");
        setNewEmployeeDept("");
        setNewEmployeeLoginId("");
        setNewEmployeePassword("");
        setEmployeeId(String(createdEmployee.id));
        setLoginId(newLoginId);
        setTemporaryPassword(newEmployeePassword);
        const refreshed = await load();
        setError(refreshed
          ? `${name} 님의 직원 등록은 완료됐지만 계정 발급에 실패했습니다. 미발급 직원에서 대상자를 확인하고 계정 발급을 다시 진행해 주세요.`
          : `${name} 님의 직원 등록은 완료됐지만 계정 발급과 목록 재조회에 실패했습니다. 중복 직원 등록 대신 새로고침 후 미발급 직원으로 계정을 발급해 주세요.`);
      } else {
        setError(cause instanceof Error ? cause.message : "신규 직원 등록에 실패했습니다.");
      }
    } finally {
      setBusyId(null);
    }
  }

  async function toggle(user: AccountView) {
    if (busyId !== null || loading || protectsCurrentAdmin(user)) return;
    setBusyId(user.id);
    setError("");
    setNotice("");
    try {
      await adminUsersApi.setActive(user.id, !user.is_active);
      if (await load()) setNotice("계정 상태를 저장하고 다시 조회했습니다.");
      else setError("계정 상태 변경은 성공했지만 목록 재조회에 실패했습니다. 목록만 새로고침해 확인해 주세요.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "계정 상태를 변경하지 못했습니다.");
    } finally {
      setBusyId(null);
    }
  }

  async function reset(event: FormEvent) {
    event.preventDefault();
    if (busyId !== null || resetId === null || !resetPassword) {
      if (!resetPassword) setError("임시 비밀번호를 입력해 주세요.");
      return;
    }
    setBusyId(resetId);
    setError("");
    setNotice("");
    try {
      await adminUsersApi.resetPassword(resetId, resetPassword);
      setResetPassword("");
      setResetId(null);
      if (await load()) setNotice("임시 비밀번호를 설정하고 계정 목록을 다시 확인했습니다.");
      else setError("비밀번호 초기화는 성공했지만 목록 재조회에 실패했습니다. 목록만 새로고침해 확인해 주세요.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "비밀번호를 초기화하지 못했습니다.");
    } finally {
      setBusyId(null);
    }
  }

  async function removeAccount(user: AccountView) {
    if (busyId !== null || loading || isCurrentAdmin(user)) return;
    const confirmed = window.confirm(`정말 ${user.name} 님의 계정을 삭제하시겠습니까? 계정 삭제 시 로그인 정보만 삭제되며 미발급 상태로 초기화됩니다.`);
    if (!confirmed) return;

    setBusyId(user.id);
    setError("");
    setNotice("");
    try {
      await adminUsersApi.deleteAccount(user.id);
      if (resetId === user.id) {
        setResetId(null);
        setResetPassword("");
      }
      if (await load()) setNotice(`${user.name} 님의 계정을 삭제하고 최신 목록을 다시 불러왔습니다.`);
      else setError("계정 삭제는 완료됐지만 목록 재조회에 실패했습니다. 다시 삭제하지 말고 새로고침으로 목록만 확인해 주세요.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "계정을 삭제하지 못했습니다.");
    } finally {
      setBusyId(null);
    }
  }

  function openResetForm(user: AccountView) {
    if (busyId !== null || loading) return;
    setResetId(user.id);
    setResetPassword("");
    setError("");
    setNotice("");
  }

  function closeResetForm() {
    if (busyId !== null) return;
    setResetId(null);
    setResetPassword("");
  }

  return <main className="admin-content">
    <div className="admin-title">
      <div><span className="eyebrow">ACCOUNT MANAGEMENT</span><h1>계정 관리</h1><p>제공된 직원 계정 발급과 활성 상태를 관리합니다.</p></div>
      <span className="admin-count">계정 {users.length}개</span>
    </div>
    {error && <p className="error" role="alert">{error}</p>}
    {notice && <p role="status">{notice}</p>}
    {identityError && <p className="error" role="alert">관리자 계정을 확인하지 못해 관리자 계정의 비활성화와 삭제를 잠갔습니다. 다시 새로고침해 주세요.</p>}

    <section className="admin-panel new-employee-panel">
      <h2>신규 직원 및 계정 발급</h2>
      <p className="muted">직원 정보 등록 후 해당 직원의 계정을 발급합니다.</p>
      <form className="admin-fields new-employee-fields" onSubmit={createEmployeeAndAccount}>
        <label>직원 이름<input disabled={busyId !== null} value={newEmployeeName} onChange={(event) => setNewEmployeeName(event.target.value)} autoComplete="off" /></label>
        <label>소속 부서<input disabled={busyId !== null} value={newEmployeeDept} onChange={(event) => setNewEmployeeDept(event.target.value)} autoComplete="organization" /></label>
        <label>로그인 ID<input disabled={busyId !== null} value={newEmployeeLoginId} onChange={(event) => setNewEmployeeLoginId(event.target.value)} autoComplete="off" /></label>
        <label>임시 비밀번호<input disabled={busyId !== null} type="password" value={newEmployeePassword} onChange={(event) => setNewEmployeePassword(event.target.value)} autoComplete="new-password" /></label>
        <button className="admin-primary" disabled={busyId !== null}>{busyId === -2 ? "등록 중…" : "직원 등록 및 계정 발급"}</button>
      </form>
    </section>

    <section className="admin-panel">
      <h2>계정 발급</h2>
      {loading ? <p role="status">직원 계정 상태를 확인하고 있습니다…</p>
        : error ? null
          : employees.length > 0 && unissuedEmployees.length === 0
            ? <p className="account-empty-state" role="status">현재 모든 직원의 계정이 발급 완료되었습니다 (전체 {employees.length}명)</p>
            : employees.length === 0
              ? <p>직원 목록을 표시할 수 없습니다.</p>
              : <form className="admin-fields" onSubmit={create}>
                <label>미발급 직원<select disabled={busyId !== null} value={employeeId} onChange={(event) => setEmployeeId(event.target.value)}><option value="">직원을 선택해 주세요</option>{unissuedEmployees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name} · {employee.dept}</option>)}</select></label>
                <label>로그인 ID<input disabled={busyId !== null} autoComplete="off" value={loginId} onChange={(event) => setLoginId(event.target.value)} /></label>
                <label>임시 비밀번호<input disabled={busyId !== null} type="password" autoComplete="new-password" value={temporaryPassword} onChange={(event) => setTemporaryPassword(event.target.value)} /></label>
                <button className="admin-primary" disabled={busyId !== null || !employeeId}>{busyId === -1 ? "발급 중…" : "계정 발급"}</button>
              </form>}
    </section>

    <section className="admin-panel" style={{ marginTop: 18 }}>
      <div className="panel-heading"><h2>등록 계정</h2><button type="button" disabled={busyId !== null || loading} onClick={() => void load()}>새로고침</button></div>
      {loading ? <p role="status">계정 목록을 불러오는 중입니다…</p>
        : error ? null
          : users.length === 0 ? <p>등록된 계정이 없습니다.</p>
            : users.map((user) => {
              const protectsSelf = protectsCurrentAdmin(user);
              return <div className="user-row" key={user.id}>
                <span className="user-avatar" aria-hidden="true">{user.name.slice(0, 1)}</span>
                <span className="user-identity"><b>{user.name}</b><small>{user.dept} · {user.login_id}</small></span>
                <span className="user-role">{user.role === "admin" ? "관리자" : "직원"}{user.must_change_password ? " · 변경 필요" : ""}</span>
                <span className="account-state"><span className={`account-status-badge ${user.is_active ? "is-active" : "is-inactive"}`}>{user.is_active ? "정상 활성" : "비활성"}</span>
                  {protectsSelf && <small className="account-protection-note">현재 관리자 계정 보호</small>}
                </span>
                <button type="button" className={`user-toggle ${user.is_active ? "deactivate" : "activate"}`} disabled={busyId !== null || loading || protectsSelf} title={protectsSelf ? "현재 로그인한 관리자 계정은 비활성화할 수 없습니다." : undefined} onClick={() => void toggle(user)}>{busyId === user.id ? "변경 중…" : user.is_active ? "비활성화하기" : "활성화하기"}</button>
                <button type="button" className="user-reset" disabled={busyId !== null || loading} onClick={() => openResetForm(user)}>임시 비밀번호 설정</button>
                <button type="button" className="user-delete" disabled={busyId !== null || loading || isCurrentAdmin(user)} title={isCurrentAdmin(user) ? "현재 로그인한 관리자 계정은 삭제할 수 없습니다." : undefined} onClick={() => void removeAccount(user)}>{busyId === user.id ? "삭제 중…" : "계정 삭제"}</button>
              </div>;
            })}
    </section>

    {resetId !== null && <section className="admin-panel reset-password-panel" ref={resetPanelRef} style={{ marginTop: 18 }} aria-labelledby="reset-password-heading">
      <h2 id="reset-password-heading">{resetTarget ? `${resetTarget.name} 님의 임시 비밀번호 설정` : "임시 비밀번호 설정"}</h2>
      {resetTarget && <p className="muted">대상: {resetTarget.name} · {resetTarget.dept}</p>}
      <form className="admin-fields" onSubmit={reset}>
        <label>새 임시 비밀번호<input ref={resetPasswordRef} disabled={busyId !== null} type="password" autoComplete="new-password" value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} /></label>
        <div><button className="admin-primary" disabled={busyId !== null || loading || !resetTarget}>{busyId === resetId ? "처리 중…" : "초기화 실행"}</button> <button type="button" disabled={busyId !== null} onClick={closeResetForm}>취소</button></div>
      </form>
    </section>}
  </main>;
}
