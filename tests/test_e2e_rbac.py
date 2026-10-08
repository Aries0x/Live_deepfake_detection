import requests
import json
import time

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_full_rbac_system():
    print("==================================================")
    print("STARTING COMPLETE E2E RBAC & AUTH TEST SUITE")
    print("==================================================")

    # 1. Health Check
    health_res = requests.get(f"{BASE_URL}/api/v1/health")
    assert health_res.status_code == 200, f"Backend health failed: {health_res.text}"
    print("[PASS] 1. Backend health check 200 OK")

    # 2. Citizen Flow: Request OTP, Verify OTP, Check /auth/me, Check Permissions
    cz_session = requests.Session()
    req_otp_res = cz_session.post(f"{BASE_URL}/auth/citizen/request-otp", json={"identifier": "alex@citizen.demo"})
    assert req_otp_res.status_code == 200, f"Citizen OTP request failed: {req_otp_res.text}"
    print("[PASS] 2a. Citizen requested OTP")

    verify_otp_res = cz_session.post(f"{BASE_URL}/auth/citizen/verify-otp", json={
        "identifier": "alex@citizen.demo",
        "otp": "123456",
        "name": "Alex Rivera",
        "consent": True,
    })
    assert verify_otp_res.status_code == 200, f"Citizen verify OTP failed: {verify_otp_res.text}"
    cz_data = verify_otp_res.json()
    assert cz_data["role"] == "citizen"
    print(f"[PASS] 2b. Citizen verified & authenticated: user_id={cz_data['user_id']}")

    # 3. Citizen Permission Enforcement:
    # Citizen CANNOT view court cases (403 expected)
    cz_cases_res = cz_session.get(f"{BASE_URL}/auth/cases")
    assert cz_cases_res.status_code == 403, f"Expected 403 for Citizen on cases, got {cz_cases_res.status_code}"
    print("[PASS] 3a. Citizen access to /auth/cases correctly denied with 403 Forbidden")

    # Citizen CANNOT upload bulk media (403 expected)
    cz_bulk_res = cz_session.post(f"{BASE_URL}/api/v1/bulk", files={})
    assert cz_bulk_res.status_code == 403, f"Expected 403 for citizen on /api/v1/bulk, got {cz_bulk_res.status_code}"
    print(f"[PASS] 3b. Citizen bulk upload correctly rejected with 403 Forbidden")

    # 4. Court Forensic Officer Flow:
    fo_session = requests.Session()
    fo_login_res = fo_session.post(f"{BASE_URL}/auth/court/login", json={
        "email": "officer@court.demo",
        "password": "Demo@1234",
        "role": "forensic_officer",
    })
    assert fo_login_res.status_code == 200, f"Forensic login failed: {fo_login_res.text}"
    pending_token = fo_login_res.json()["pending_token"]
    print("[PASS] 4a. Forensic officer credentials verified -> pending 2FA token issued")

    fo_2fa_res = fo_session.post(f"{BASE_URL}/auth/court/verify-2fa", json={
        "pending_token": pending_token,
        "totp_code": "123456",
    })
    assert fo_2fa_res.status_code == 200, f"Forensic 2FA failed: {fo_2fa_res.text}"
    fo_user = fo_2fa_res.json()
    assert fo_user["role"] == "forensic_officer"
    print(f"[PASS] 4b. Forensic officer 2FA complete -> session active for user {fo_user['user_id']}")

    # Forensic officer CAN list cases:
    fo_cases_res = fo_session.get(f"{BASE_URL}/auth/cases")
    assert fo_cases_res.status_code == 200, f"Forensic list cases failed: {fo_cases_res.text}"
    assigned_cases = fo_cases_res.json()
    print(f"[PASS] 4c. Forensic officer retrieved {len(assigned_cases)} assigned cases")

    # Forensic officer CAN create a new case:
    create_case_res = fo_session.post(f"{BASE_URL}/auth/cases", json={
        "title": "State v. Automated Deepfake Syndicate",
        "description": "Evidence from phone wiretap and remote video conference.",
    })
    assert create_case_res.status_code == 200, f"Case creation failed: {create_case_res.text}"
    new_case = create_case_res.json()
    print(f"[PASS] 4d. Forensic officer created case: {new_case['case_id']}")

    # Forensic officer CANNOT approve case reports (403 expected):
    fo_approve_res = fo_session.post(f"{BASE_URL}/auth/cases/{new_case['case_id']}/approve", json={
        "totp_code": "123456",
        "action": "bulk.approve_report",
    })
    assert fo_approve_res.status_code == 403, f"Expected 403 for Officer approving report, got {fo_approve_res.status_code}"
    print("[PASS] 4e. Forensic officer report approval denied with 403 Forbidden")

    # 5. Judge Flow:
    judge_session = requests.Session()
    judge_login_res = judge_session.post(f"{BASE_URL}/auth/court/login", json={
        "email": "judge@court.demo",
        "password": "Demo@1234",
        "role": "judge",
    })
    assert judge_login_res.status_code == 200, f"Judge login failed: {judge_login_res.text}"
    judge_pending = judge_login_res.json()["pending_token"]

    judge_2fa_res = judge_session.post(f"{BASE_URL}/auth/court/verify-2fa", json={
        "pending_token": judge_pending,
        "totp_code": "123456",
    })
    assert judge_2fa_res.status_code == 200, f"Judge 2FA failed: {judge_2fa_res.text}"
    print("[PASS] 5a. Judge authenticated with credentials + TOTP")

    # Judge CAN approve the case report with TOTP step-up reauthentication:
    judge_approve_res = judge_session.post(f"{BASE_URL}/auth/cases/{new_case['case_id']}/approve", json={
        "totp_code": "123456",
        "action": "bulk.approve_report",
    })
    assert judge_approve_res.status_code == 200, f"Judge approval failed: {judge_approve_res.text}"
    print(f"[PASS] 5b. Judge approved case report with step-up TOTP verification: {judge_approve_res.json()}")

    # 6. Admin Flow:
    admin_session = requests.Session()
    admin_login_res = admin_session.post(f"{BASE_URL}/auth/admin/login", json={
        "email": "admin@securecall.demo",
        "password": "Demo@1234",
    })
    assert admin_login_res.status_code == 200, f"Admin login failed: {admin_login_res.text}"
    admin_pending = admin_login_res.json()["pending_token"]

    admin_2fa_res = admin_session.post(f"{BASE_URL}/auth/admin/verify-2fa", json={
        "pending_token": admin_pending,
        "totp_code": "123456",
    })
    assert admin_2fa_res.status_code == 200, f"Admin 2FA failed: {admin_2fa_res.text}"
    print("[PASS] 6a. Admin authenticated with credentials + TOTP")

    # Admin CAN view all users:
    users_res = admin_session.get(f"{BASE_URL}/auth/admin/users")
    assert users_res.status_code == 200, f"Admin list users failed: {users_res.text}"
    users_list = users_res.json()
    print(f"[PASS] 6b. Admin retrieved all platform accounts: {len(users_list)} registered")

    # Admin CAN update thresholds with TOTP step-up reauthentication:
    thresh_update_res = admin_session.post(f"{BASE_URL}/auth/admin/thresholds", json={
        "risk_threshold": 0.70,
        "face_weight": 0.55,
        "audio_weight": 0.25,
        "temporal_weight": 0.20,
        "totp_code": "123456",
    })
    assert thresh_update_res.status_code == 200, f"Admin update thresholds failed: {thresh_update_res.text}"
    print(f"[PASS] 6c. Admin updated detection thresholds with TOTP authorization: {thresh_update_res.json()}")

    # 7. Cryptographic Hash Chain Audit Verification:
    chain_verify_res = admin_session.get(f"{BASE_URL}/auth/audit/verify")
    assert chain_verify_res.status_code == 200, f"Chain verify failed: {chain_verify_res.text}"
    chain_status = chain_verify_res.json()
    assert chain_status["valid"] is True, f"Audit chain broken! {chain_status}"
    print(f"[PASS] 7. SHA-256 Forward Hash Chain verified unbroken! Chain length: {chain_status['chain_length']} blocks")

    print("\n==================================================")
    print("ALL 7 CORE RBAC & AUTH CRITERIA PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    test_full_rbac_system()
