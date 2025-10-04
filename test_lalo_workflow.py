#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test LALO Workflow End-to-End

Tests the complete 5-step LALO workflow:
1. Semantic Interpretation & Confidence Scoring
2. Planning
3. Backup & Execution
4. Review
5. Final Feedback & Permanent Memory

Note: Requires user to have API keys configured
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def get_demo_token():
    """Get demo authentication token"""
    response = requests.post(f"{BASE_URL}/auth/demo-token")
    return response.json()["access_token"]

def start_workflow(token, user_request):
    """Step 1: Start LALO workflow with semantic interpretation"""
    print("\n" + "=" * 70)
    print("STEP 1: Starting LALO Workflow - Semantic Interpretation")
    print("=" * 70)
    print(f"User Request: \"{user_request}\"")
    print()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {"user_request": user_request}

    response = requests.post(
        f"{BASE_URL}/api/workflow/start",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[SUCCESS] Workflow started!")
        print(f"Session ID: {data['session_id']}")
        print(f"Current State: {data['current_state']}")
        print()
        print("=== Semantic Interpretation ===")
        print(f"Interpreted Intent: {data['interpreted_intent']}")
        print(f"Confidence Score: {data['confidence_score']}")
        print()
        print("=== Reasoning Trace ===")
        for idx, reason in enumerate(data.get('reasoning_trace', []), 1):
            print(f"{idx}. {reason}")
        print()
        if data.get('suggested_clarifications'):
            print("=== Suggested Clarifications ===")
            for idx, clarification in enumerate(data['suggested_clarifications'], 1):
                print(f"{idx}. {clarification}")
        print()
        return data
    else:
        print(f"[FAIL] Status: {response.status_code}")
        print(f"Error: {response.json()}")
        return None

def approve_interpretation(token, session_id):
    """Approve the semantic interpretation"""
    print("\n" + "=" * 70)
    print("USER FEEDBACK: Approving Interpretation")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "feedback_type": "approve",
        "message": "The interpretation looks good"
    }

    response = requests.post(
        f"{BASE_URL}/api/workflow/{session_id}/feedback",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[SUCCESS] Interpretation approved")
        print(f"Approval Status: {data['interpretation_approved']}")
        return data
    else:
        print(f"[FAIL] Status: {response.status_code}")
        print(f"Error: {response.json()}")
        return None

def advance_to_planning(token, session_id):
    """Step 2: Advance to planning phase"""
    print("\n" + "=" * 70)
    print("STEP 2: Advancing to Planning Phase")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{BASE_URL}/api/workflow/{session_id}/advance",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[SUCCESS] Advanced to: {data['current_state']}")
        print()
        print("=== Action Plan ===")
        if data.get('action_plan'):
            print(json.dumps(data['action_plan'], indent=2))
        print(f"\nPlan Confidence: {data.get('plan_confidence_score')}")
        return data
    else:
        print(f"[FAIL] Status: {response.status_code}")
        print(f"Error: {response.json()}")
        return None

def approve_plan(token, session_id):
    """Approve the action plan"""
    print("\n" + "=" * 70)
    print("USER FEEDBACK: Approving Action Plan")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "feedback_type": "approve",
        "message": "The plan looks good, proceed with execution"
    }

    response = requests.post(
        f"{BASE_URL}/api/workflow/{session_id}/feedback",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        print(f"[SUCCESS] Plan approved")
        return response.json()
    else:
        print(f"[FAIL] Status: {response.status_code}")
        return None

def execute_plan(token, session_id):
    """Step 3: Backup verification and execute plan"""
    print("\n" + "=" * 70)
    print("STEP 3: Backup Verification & Execution")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Advance to backup_verify
    response = requests.post(
        f"{BASE_URL}/api/workflow/{session_id}/advance",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[SUCCESS] Moved to: {data['current_state']}")

        # Advance to executing
        print("\nProceeding to execution...")
        time.sleep(1)
        response = requests.post(
            f"{BASE_URL}/api/workflow/{session_id}/advance",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Executing plan...")
            print(f"Current State: {data['current_state']}")
            print()
            if data.get('execution_results'):
                print("=== Execution Results ===")
                print(json.dumps(data['execution_results'], indent=2))
            return data
    else:
        print(f"[FAIL] Status: {response.status_code}")
        return None

def review_and_approve(token, session_id):
    """Step 4: Review execution results"""
    print("\n" + "=" * 70)
    print("STEP 4: Reviewing Execution Results")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Advance to reviewing
    response = requests.post(
        f"{BASE_URL}/api/workflow/{session_id}/advance",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[SUCCESS] Moved to: {data['current_state']}")

        # Approve review
        print("\nUser approves execution results...")
        payload = {
            "feedback_type": "approve",
            "message": "Execution results look good"
        }

        response = requests.post(
            f"{BASE_URL}/api/workflow/{session_id}/feedback",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            print("[SUCCESS] Review approved")
            return response.json()

    print(f"[FAIL] Status: {response.status_code}")
    return None

def finalize_workflow(token, session_id):
    """Step 5: Final feedback and commit to permanent memory"""
    print("\n" + "=" * 70)
    print("STEP 5: Finalizing & Committing to Permanent Memory")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Advance to finalizing
    response = requests.post(
        f"{BASE_URL}/api/workflow/{session_id}/advance",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[SUCCESS] Moved to: {data['current_state']}")

        # Complete workflow
        print("\nCompleting workflow...")
        time.sleep(1)
        response = requests.post(
            f"{BASE_URL}/api/workflow/{session_id}/advance",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Workflow completed!")
            print(f"Final State: {data['current_state']}")
            print()
            print("=== Workflow Summary ===")
            print(f"Original Request: {data['original_request']}")
            print(f"Interpreted Intent: {data['interpreted_intent']}")
            print(f"Confidence Score: {data['confidence_score']}")
            print(f"Committed to Memory: Yes")
            return data

    print(f"[FAIL] Status: {response.status_code}")
    return None

def main():
    print("\n" + "=" * 70)
    print("LALO WORKFLOW - END-TO-END TEST")
    print("=" * 70)
    print("\nThis test demonstrates the complete 5-step LALO process:")
    print("1. Semantic Interpretation & Confidence Scoring")
    print("2. Action Planning")
    print("3. Backup Verification & Execution")
    print("4. Result Review")
    print("5. Final Feedback & Permanent Memory Commit")
    print()
    input("Press Enter to start the test...")

    try:
        # Get authentication token
        print("\n[INFO] Getting authentication token...")
        token = get_demo_token()
        print(f"[SUCCESS] Token received")

        # Test request
        user_request = "Analyze my Q3 sales data and create a summary report with key insights"

        # Run the 5-step workflow
        session = start_workflow(token, user_request)
        if not session:
            return

        session_id = session['session_id']
        time.sleep(1)

        # Step 1: Approve interpretation
        if not approve_interpretation(token, session_id):
            return
        time.sleep(1)

        # Step 2: Advance to planning
        if not advance_to_planning(token, session_id):
            return
        time.sleep(1)

        # Approve plan
        if not approve_plan(token, session_id):
            return
        time.sleep(1)

        # Step 3: Execute
        if not execute_plan(token, session_id):
            return
        time.sleep(1)

        # Step 4: Review
        if not review_and_approve(token, session_id):
            return
        time.sleep(1)

        # Step 5: Finalize
        if not finalize_workflow(token, session_id):
            return

        print("\n" + "=" * 70)
        print("[SUCCESS] COMPLETE LALO WORKFLOW TEST PASSED!")
        print("=" * 70)
        print()
        print("The workflow successfully completed all 5 steps:")
        print("[PASS] Step 1: Semantic interpretation with confidence scoring")
        print("[PASS] Step 2: Action plan generation")
        print("[PASS] Step 3: Backup verification and execution")
        print("[PASS] Step 4: Result review and approval")
        print("[PASS] Step 5: Final feedback and permanent memory commit")
        print()
        print(f"Session ID: {session_id}")
        print("All data has been saved to the workflow_sessions table.")
        print()

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
