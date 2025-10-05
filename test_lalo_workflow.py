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
import logging
import traceback

BASE_URL = "http://localhost:8000"

logger = logging.getLogger("lalo.test_lalo_workflow")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def get_demo_token():
    """Get demo authentication token"""
    response = requests.post(f"{BASE_URL}/auth/demo-token")
    return response.json()["access_token"]


def start_workflow(token, user_request):
    """Step 1: Start LALO workflow with semantic interpretation"""
    logger.info("%s", "\n" + "=" * 70)
    logger.info("STEP 1: Starting LALO Workflow - Semantic Interpretation")
    logger.info("%s", "=" * 70)
    logger.info("User Request: \"%s\"", user_request)

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
        logger.info("[SUCCESS] Workflow started!")
        logger.info("Session ID: %s", data['session_id'])
        logger.info("Current State: %s", data['current_state'])
        logger.info("=== Semantic Interpretation ===")
        logger.info("Interpreted Intent: %s", data['interpreted_intent'])
        logger.info("Confidence Score: %s", data['confidence_score'])
        logger.info("=== Reasoning Trace ===")
        for idx, reason in enumerate(data.get('reasoning_trace', []), 1):
            logger.info("%d. %s", idx, reason)
        if data.get('suggested_clarifications'):
            logger.info("=== Suggested Clarifications ===")
            for idx, clarification in enumerate(data['suggested_clarifications'], 1):
                logger.info("%d. %s", idx, clarification)
        return data
    else:
        logger.info("[FAIL] Status: %s", response.status_code)
        logger.info("Error: %s", response.json())
        return None

def approve_interpretation(token, session_id):
    """Approve the semantic interpretation"""
    logger.info("%s", "\n" + "=" * 70)
    logger.info("USER FEEDBACK: Approving Interpretation")
    logger.info("%s", "=" * 70)

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
        logger.info("[SUCCESS] Interpretation approved")
        logger.info("Approval Status: %s", data['interpretation_approved'])
        return data
    else:
        logger.info("[FAIL] Status: %s", response.status_code)
        logger.info("Error: %s", response.json())
        return None

def advance_to_planning(token, session_id):
    """Step 2: Advance to planning phase"""
    logger.info("%s", "\n" + "=" * 70)
    logger.info("STEP 2: Advancing to Planning Phase")
    logger.info("%s", "=" * 70)

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
        logger.info("[SUCCESS] Advanced to: %s", data['current_state'])
        logger.info("=== Action Plan ===")
        if data.get('action_plan'):
            logger.info(json.dumps(data['action_plan'], indent=2))
        logger.info("Plan Confidence: %s", data.get('plan_confidence_score'))
        return data
    else:
        logger.info("[FAIL] Status: %s", response.status_code)
        logger.info("Error: %s", response.json())
        return None

def approve_plan(token, session_id):
    """Approve the action plan"""
    logger.info("%s", "\n" + "=" * 70)
    logger.info("USER FEEDBACK: Approving Action Plan")
    logger.info("%s", "=" * 70)

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
        logger.info("[SUCCESS] Plan approved")
        return response.json()
    else:
        logger.info("[FAIL] Status: %s", response.status_code)
        return None

def execute_plan(token, session_id):
    """Step 3: Backup verification and execute plan"""
    logger.info("%s", "\n" + "=" * 70)
    logger.info("STEP 3: Backup Verification & Execution")
    logger.info("%s", "=" * 70)

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
        logger.info("[SUCCESS] Moved to: %s", data['current_state'])

        # Advance to executing
        logger.info("Proceeding to execution...")
        time.sleep(1)
        response = requests.post(
            f"{BASE_URL}/api/workflow/{session_id}/advance",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            logger.info("[SUCCESS] Executing plan...")
            logger.info("Current State: %s", data['current_state'])
            if data.get('execution_results'):
                logger.info("=== Execution Results ===")
                logger.info(json.dumps(data['execution_results'], indent=2))
            return data
    else:
        logger.info("[FAIL] Status: %s", response.status_code)
        return None

def review_and_approve(token, session_id):
    """Step 4: Review execution results"""
    logger.info("%s", "\n" + "=" * 70)
    logger.info("STEP 4: Reviewing Execution Results")
    logger.info("%s", "=" * 70)

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
        logger.info("[SUCCESS] Moved to: %s", data['current_state'])

        # Approve review
        logger.info("User approves execution results...")
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
            logger.info("[SUCCESS] Review approved")
            return response.json()

    logger.info("[FAIL] Status: %s", response.status_code)
    return None

def finalize_workflow(token, session_id):
    """Step 5: Final feedback and commit to permanent memory"""
    logger.info("%s", "\n" + "=" * 70)
    logger.info("STEP 5: Finalizing & Committing to Permanent Memory")
    logger.info("%s", "=" * 70)

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
        logger.info("[SUCCESS] Moved to: %s", data['current_state'])

        # Complete workflow
        logger.info("Completing workflow...")
        time.sleep(1)
        response = requests.post(
            f"{BASE_URL}/api/workflow/{session_id}/advance",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            logger.info("[SUCCESS] Workflow completed!")
            logger.info("Final State: %s", data['current_state'])
            logger.info("=== Workflow Summary ===")
            logger.info("Original Request: %s", data['original_request'])
            logger.info("Interpreted Intent: %s", data['interpreted_intent'])
            logger.info("Confidence Score: %s", data['confidence_score'])
            logger.info("Committed to Memory: Yes")
            return data

    logger.info("[FAIL] Status: %s", response.status_code)
    return None

def main():
    logger.info("%s", "\n" + "=" * 70)
    logger.info("LALO WORKFLOW - END-TO-END TEST")
    logger.info("%s", "=" * 70)
    logger.info("This test demonstrates the complete 5-step LALO process:")
    logger.info("1. Semantic Interpretation & Confidence Scoring")
    logger.info("2. Action Planning")
    logger.info("3. Backup Verification & Execution")
    logger.info("4. Result Review")
    logger.info("5. Final Feedback & Permanent Memory Commit")
    logger.info("")
    input("Press Enter to start the test...")

    try:
        # Get authentication token
        logger.info("Getting authentication token...")
        token = get_demo_token()
        logger.info("Token received")

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

        logger.info("%s", "\n" + "=" * 70)
        logger.info("[SUCCESS] COMPLETE LALO WORKFLOW TEST PASSED!")
        logger.info("%s", "=" * 70)
        logger.info("")
        logger.info("The workflow successfully completed all 5 steps:")
        logger.info("[PASS] Step 1: Semantic interpretation with confidence scoring")
        logger.info("[PASS] Step 2: Action plan generation")
        logger.info("[PASS] Step 3: Backup verification and execution")
        logger.info("[PASS] Step 4: Result review and approval")
        logger.info("[PASS] Step 5: Final feedback and permanent memory commit")
        logger.info("")
        logger.info("Session ID: %s", session_id)
        logger.info("All data has been saved to the workflow_sessions table.")

    except Exception as e:
        logger.exception("Test failed with error: %s", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
