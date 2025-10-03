# Copyright (c) 2025 LALO AI LLC. All rights reserved.
#
# Recursive Task Interpreter (RTI) with VectorStore retrieval example.

from fastapi import FastAPI
from pydantic import BaseModel
import random
import time
from vector_store import VectorStore

app = FastAPI(title="Recursive Task Interpreter (RTI)")

# Initialize the in-memory vector store with some past successful Action Plans
vs = VectorStore()
vs.add_document("Run a report for Q2 high margin shoes, formatted using the Marketing-Samples template from SharePoint.")
vs.add_document("Generate a Workday report for employee productivity in the production department.")
vs.add_document("Prepare a combined S4/HANA and Workday data export for quarterly HR and production review.")

class InterpretRequest(BaseModel):
    user_input: str

class InterpretResponse(BaseModel):
    plan: str
    confidence: float
    critique: str
    retrieved_examples: list

@app.post("/interpret", response_model=InterpretResponse)
async def interpret(req: InterpretRequest):
    """
    Multi-step semantic interpretation:
    1. Retrieve relevant historical Action Plans from vector DB.
    2. Simulate alignment scoring.
    3. Produce a proposed plan with critique.
    """
    time.sleep(0.5)

    # Step 1: Retrieve relevant examples
    examples = vs.query(req.user_input, top_k=2)

    # Step 2: Generate a simulated plan (placeholder for real model output)
    plan = f"Simulated action plan for: {req.user_input}"

    # Step 3: Simulate alignment confidence scoring
    confidence = round(random.uniform(0.85, 0.97), 2)
    critique = (
        "Interpretation aligns with user intent, "
        "based on semantic similarity to prior successful plans."
    )

    return InterpretResponse(
        plan=plan,
        confidence=confidence,
        critique=critique,
        retrieved_examples=[{"document": doc, "similarity": score} for doc, score in examples]
    )
