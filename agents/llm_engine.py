import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

class LLMEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate_classification(self, sto: Dict[str, Any], context: str) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "classification": "UNKNOWN",
                "rule_applied": 99,
                "root_cause": "LLM unavailable — no API key",
                "confidence": 0.0,
                "reasoning_text": "OpenAI API key not configured."
            }

        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=self.api_key)

        prompt = (
            f"You are a supply chain analyst. Classify this STO as PRODUCTIVE or UNPRODUCTIVE.\n\n"
            f"STO Details:\n"
            f"- Source: {sto.get('source_location')}\n"
            f"- Destination: {sto.get('destination_location')}\n"
            f"- SKU: {sto.get('sku_id')}\n"
            f"- Quantity: {sto.get('quantity')}\n\n"
            f"Context from rules engine: {context}\n\n"
            f"Respond ONLY in this JSON format:\n"
            f'{{"classification": "PRODUCTIVE"|"UNPRODUCTIVE", "root_cause": "...", "confidence": 0.0-1.0, "reasoning_text": "..."}}'
        )

        try:
            res = llm.invoke([HumanMessage(content=prompt)])
            import json, re
            clean = re.sub(r"```json|```", "", res.content).strip()
            parsed = json.loads(clean)
            return {
                "classification": parsed.get("classification", "UNKNOWN"),
                "rule_applied": 99,
                "root_cause": parsed.get("root_cause", "LLM inferred"),
                "confidence": float(parsed.get("confidence", 0.75)),
                "reasoning_text": parsed.get("reasoning_text", "")
            }
        except Exception as e:
            return {
                "classification": "UNKNOWN",
                "rule_applied": 99,
                "root_cause": f"LLM parse error: {str(e)}",
                "confidence": 0.0,
                "reasoning_text": "Could not parse LLM response."
            }
