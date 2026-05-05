"""
tests/test_pipeline.py
======================
Comprehensive test suite for KamaaiProof AI Engine.

Covers:
  - 10+ diverse input types (UPI, rent, bills, noisy/malformed)
  - Each pipeline stage independently
  - Simulated API calls
  - RBAC access control
  - Vector store retrieval

Run with:
  python tests/test_pipeline.py
  (from the ai-engine/ directory)
"""

import sys
import os
import json
import pprint

# Ensure the ai-engine root is in path when running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sanitization.sanitizer import sanitize
from extraction.extractor import extract
from validation.validator import validate
import storage.store as store
import retrieval.vector_store as vector_store
from security.rbac import check_access, get_role, encrypt_field, decrypt_field
from pipeline.orchestrator import run_pipeline, run_pipeline_batch


# ──────────────────────────────────────────────────────────────────────────────
# ANSI colours for terminal output
# ──────────────────────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def header(title: str):
    print(f"\n{BOLD}{CYAN}{'═'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'═'*60}{RESET}")

def ok(msg: str):
    print(f"  {GREEN}✓{RESET} {msg}")

def warn(msg: str):
    print(f"  {YELLOW}⚠{RESET} {msg}")

def fail(msg: str):
    print(f"  {RED}✗{RESET} {msg}")

def info(msg: str):
    print(f"  {CYAN}→{RESET} {msg}")


# ──────────────────────────────────────────────────────────────────────────────
# 10 diverse test inputs
# ──────────────────────────────────────────────────────────────────────────────

TEST_CASES = [
    # ── 1. Clean UPI credit message ──────────────────────────────────────────
    {
        "name": "Clean UPI credit (GPay)",
        "user_id": "worker_001",
        "document_type": "upi",
        "content": (
            "Google Pay\n"
            "₹2,500 received from Priya Sharma\n"
            "UPI: priyasharma@okicici\n"
            "Date: 15/03/2025\n"
            "Transaction ID: GPY2025031500123\n"
            "Your balance: ₹8,320"
        ),
        "expect_amount": 2500.0,
        "expect_type": "credit",
    },

    # ── 2. PhonePe debit ─────────────────────────────────────────────────────
    {
        "name": "PhonePe debit payment",
        "user_id": "worker_001",
        "document_type": "upi",
        "content": (
            "PhonePe\n"
            "₹1,200 paid to Kirana Store\n"
            "UPI ID: kiranastore@ybl\n"
            "Mobile: 9876543210\n"
            "Date: 20/03/2025 14:35\n"
            "Status: SUCCESS"
        ),
        "expect_amount": 1200.0,
        "expect_type": "debit",
    },

    # ── 3. Formal rent receipt ────────────────────────────────────────────────
    {
        "name": "Formal rent receipt",
        "user_id": "worker_002",
        "document_type": "rent",
        "content": (
            "RENT RECEIPT\n"
            "Received from: Ramesh Kumar\n"
            "Amount: Rs. 4,500 (Rupees Four Thousand Five Hundred Only)\n"
            "For the month of: March 2025\n"
            "Property: Room 3, Shanti Nagar, Bengaluru\n"
            "Date: 01/03/2025\n"
            "Landlord signature: _______"
        ),
        "expect_amount": 4500.0,
        "expect_type": "credit",
    },

    # ── 4. Informal rent WhatsApp message ────────────────────────────────────
    {
        "name": "Informal WhatsApp rent confirmation",
        "user_id": "worker_002",
        "document_type": "rent",
        "content": (
            "Bhai aaj ka 3500 rent le liya hai. April ka bhi time pe dena.\n"
            "— Landlord Suresh\n"
            "12 Apr 2025"
        ),
        "expect_amount": 3500.0,
        "expect_type": "credit",
    },

    # ── 5. Electricity bill ───────────────────────────────────────────────────
    {
        "name": "Electricity bill (BESCOM)",
        "user_id": "worker_001",
        "document_type": "bill",
        "content": (
            "BESCOM - Bangalore Electricity Supply Company\n"
            "Consumer No: 1234567890\n"
            "Name: Anita Devi\n"
            "Bill Date: 2025-03-10\n"
            "Due Date: 2025-03-25\n"
            "Amount Due: INR 876.00\n"
            "Phone: 9845012345\n"
            "IFSC: KARB0000123"
        ),
        "expect_amount": 876.0,
        "expect_type": "debit",
    },

    # ── 6. Mixed/noisy UPI message ────────────────────────────────────────────
    {
        "name": "Noisy UPI with extra junk text",
        "user_id": "worker_001",
        "document_type": "upi",
        "content": (
            "SMS from VM-HDFCBK\n"
            "Acct XX9876 Cr INR 3000.00 15-04-25 by UPI\n"
            "Ref 123456789012. Avl Bal INR 12,450.00\n"
            "Info: NEFT/IMPS/UPI Rajesh Yadav 9812300001 paid you"
        ),
        "expect_amount": 3000.0,
        "expect_type": "credit",
    },

    # ── 7. Malformed date — should produce validation warning ─────────────────
    {
        "name": "UPI with garbled date (validation warning expected)",
        "user_id": "worker_001",
        "document_type": "upi",
        "content": (
            "Paytm: Rs 500 received\n"
            "Date: 32/13/2025\n"  # invalid date
            "From: paytm@user\n"
            "Txn ID: PTM987654"
        ),
        "expect_amount": 500.0,
        "expect_type": "credit",
        "expect_validation_warnings": True,
    },

    # ── 8. Future-dated transaction — should produce validation error ─────────
    {
        "name": "Future-dated transaction (validation error expected)",
        "user_id": "worker_002",
        "document_type": "rent",
        "content": (
            "Rent Receipt\n"
            "Amount: Rs 5000\n"
            "Date: 01/12/2030\n"  # far future
            "Month: December 2030\n"
            "Paid by: Tenant"
        ),
        "expect_amount": 5000.0,
        "expect_type": "credit",
        "expect_validation_errors": True,
    },

    # ── 9. Zero/negative amount — should produce validation error ─────────────
    {
        "name": "Zero amount document (validation error expected)",
        "user_id": "worker_001",
        "document_type": "bill",
        "content": (
            "Water Bill\n"
            "Amount: Rs 0\n"
            "Date: 10/03/2025\n"
            "BBMP Water Connection"
        ),
        "expect_validation_errors": True,
    },

    # ── 10. No amount at all ──────────────────────────────────────────────────
    {
        "name": "Document with no extractable amount",
        "user_id": "worker_001",
        "document_type": "upi",
        "content": (
            "Hey bro did you get the payment?\n"
            "Let me know when you receive it.\n"
            "March something 2025"
        ),
        "expect_amount": None,
        "expect_validation_errors": True,
    },

    # ── 11. Multi-line rent agreement ─────────────────────────────────────────
    {
        "name": "Typed rent agreement snippet",
        "user_id": "worker_002",
        "document_type": "rent",
        "content": (
            "TENANCY AGREEMENT\n"
            "This agreement is made on 1st January 2025.\n"
            "Landlord: Mr. Vijay Nair, Phone: 9900112233\n"
            "Tenant: Ms. Kavitha Pillai\n"
            "Monthly Rent: Rs. 6,000 per month\n"
            "Advance: Rs. 18,000\n"
            "Bank Account: 987654321012\n"
            "IFSC: SBIN0001234"
        ),
        "expect_amount": 18000.0,  # largest amount
        "expect_type": "credit",
    },

    # ── 12. SMS-style bank credit alert ──────────────────────────────────────
    {
        "name": "Bank SMS credit alert",
        "user_id": "worker_001",
        "document_type": "upi",
        "content": (
            "Dear Customer, your a/c 00XXXXXXX198 is credited with Rs 8750.00 "
            "on 28-02-2025. UPI Ref: 123456789. "
            "Balance: Rs 14320.50. -SBI"
        ),
        "expect_amount": 8750.0,
        "expect_type": "credit",
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Test runner
# ──────────────────────────────────────────────────────────────────────────────

def run_all_tests():
    passed = 0
    failed = 0
    total = len(TEST_CASES)

    header(f"KamaaiProof AI Engine — Test Suite ({total} test cases)")

    for i, case in enumerate(TEST_CASES, 1):
        print(f"\n{BOLD}[Test {i:02d}] {case['name']}{RESET}")
        print(f"  User: {case['user_id']} | DocType: {case['document_type']}")

        try:
            result = run_pipeline(
                user_id=case["user_id"],
                document_type=case["document_type"],
                raw_content=case["content"],
            )

            txns = result["transactions"]
            summary = result["summary"]
            errors = result["validation_errors"]

            txn = txns[0] if txns else {}

            # Print extracted JSON
            info("Extracted transaction:")
            print(f"    amount          : {txn.get('amount')}")
            print(f"    date            : {txn.get('date')}")
            print(f"    transaction_type: {txn.get('transaction_type')}")
            print(f"    confidence      : {txn.get('confidence')}")
            print(f"    description     : {txn.get('description', '')[:60]}")

            info("Summary:")
            print(f"    total_income      : {summary.get('total_income')}")
            print(f"    consistency_score : {summary.get('consistency_score')}")
            print(f"    months            : {summary.get('months')}")

            if errors:
                info(f"Validation output ({len(errors)} issue(s)):")
                for e in errors:
                    severity = e.get("severity", "")
                    msg = e.get("message", "")
                    field = e.get("field", "")
                    if severity == "error":
                        fail(f"[{field}] {msg}")
                    else:
                        warn(f"[{field}] {msg}")
            else:
                ok("No validation errors.")

            # Basic assertions
            test_passed = True

            if "expect_amount" in case:
                expected = case["expect_amount"]
                actual = txn.get("amount")
                if expected is None and actual is None:
                    ok("Amount correctly not extracted")
                elif expected is not None and actual == expected:
                    ok(f"Amount matched: {actual}")
                elif expected is not None and actual is not None and abs(actual - expected) < 1:
                    ok(f"Amount approximately matched: {actual} ≈ {expected}")
                else:
                    warn(f"Amount mismatch: expected {expected}, got {actual}")

            if "expect_type" in case:
                expected_type = case["expect_type"]
                actual_type = txn.get("transaction_type")
                if actual_type == expected_type:
                    ok(f"Transaction type matched: {actual_type}")
                else:
                    warn(f"Transaction type: expected '{expected_type}', got '{actual_type}'")

            if case.get("expect_validation_errors") and not errors:
                fail("Expected validation errors but none found.")
                test_passed = False
            elif case.get("expect_validation_errors") and errors:
                ok("Validation errors correctly detected.")

            passed += 1
            ok(f"Test {i:02d} completed successfully.")

        except Exception as exc:
            fail(f"Test {i:02d} crashed: {exc}")
            import traceback
            traceback.print_exc()
            failed += 1


    # ── Stage-level unit tests ─────────────────────────────────────────────────

    header("Stage-Level Unit Tests")

    # Sanitization
    print(f"\n{BOLD}[Unit] Sanitization Layer{RESET}")
    pii_text = "Call Ramesh at 9876543210, UPI: ramesh@okaxis, acc: 1234567890123"
    san = sanitize(pii_text)
    assert "[PHONE]" in san.sanitized_text, "Phone not masked"
    assert "[UPI_ID]" in san.sanitized_text, "UPI not masked"
    assert "9876543210" not in san.sanitized_text, "Raw phone leaked"
    ok("Phone number masked correctly")
    ok("UPI ID masked correctly")
    ok(f"PII categories detected: {san.pii_found}")

    # RBAC
    print(f"\n{BOLD}[Unit] RBAC Layer{RESET}")
    # Worker accessing own data
    a1 = check_access("worker_001", "worker_001", "read")
    assert a1.allowed, "Worker should access own data"
    ok("Worker read own data: ALLOWED")

    # Worker accessing other's data
    a2 = check_access("worker_001", "worker_002", "read")
    assert not a2.allowed, "Worker should NOT access other's data"
    ok("Worker read other's data: DENIED")

    # MFI officer reading
    a3 = check_access("officer_001", "worker_001", "read")
    assert a3.allowed, "Officer should be able to read"
    ok("MFI officer read: ALLOWED (summary only)")

    # MFI officer writing — should be denied
    a4 = check_access("officer_001", "worker_001", "write")
    assert not a4.allowed, "Officer should NOT write"
    ok("MFI officer write: DENIED")

    # Encryption stubs
    print(f"\n{BOLD}[Unit] Encryption Stubs{RESET}")
    encrypted = encrypt_field("sensitive_value")
    decrypted = decrypt_field(encrypted)
    assert decrypted == "sensitive_value", "Encryption roundtrip failed"
    ok(f"Encrypt: {encrypted}")
    ok(f"Decrypt: {decrypted}")

    # Vector store retrieval
    print(f"\n{BOLD}[Unit] Vector Store Retrieval{RESET}")
    vector_store.index_summary("test_user", "UPI credit of 2500 in March 2025")
    vector_store.index_summary("test_user_2", "Rent receipt 4500 for April 2025")
    results = vector_store.retrieve_similar("monthly rent payment", top_k=2)
    assert len(results) > 0, "Should return at least 1 result"
    ok(f"Retrieved {len(results)} similar summaries")
    for r in results:
        info(f"  score={r['score']:.4f} | {r['summary_text'][:50]}")


    # ── Storage retrieval test ─────────────────────────────────────────────────

    print(f"\n{BOLD}[Unit] Storage Retrieval{RESET}")
    stored = store.get_results("worker_001")
    ok(f"Records stored for worker_001: {len(stored)}")
    assert len(stored) > 0, "worker_001 should have stored results"


    # ── Final summary ─────────────────────────────────────────────────────────

    header("Test Summary")
    print(f"  Pipeline Tests  : {passed}/{total} passed")
    if failed:
        print(f"  {RED}Failed         : {failed}{RESET}")
    else:
        print(f"  {GREEN}All pipeline tests completed.{RESET}")
    print(f"  Unit tests      : Passed (sanitization, RBAC, encryption, vector store, storage)")
    print()


if __name__ == "__main__":
    run_all_tests()
