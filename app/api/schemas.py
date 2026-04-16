from pydantic import BaseModel, Field


class EmailRequest(BaseModel):
    intent: str = Field(..., description="Core purpose of the email", min_length=5)
    key_facts: list[str] = Field(
        ..., description="Bullet points to include in the email", min_length=1
    )
    tone: str = Field(..., description="Desired tone (e.g., formal, casual, urgent)")
    strategy: str = Field(
        default="advanced",
        description="Prompting strategy: 'advanced' or 'baseline'",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "intent": "Follow up after a demo call",
                    "key_facts": [
                        "Demo was held last Tuesday",
                        "Client liked the reporting feature",
                        "Next step is a pilot program",
                    ],
                    "tone": "formal",
                    "strategy": "advanced",
                }
            ]
        }
    }


class EmailResponse(BaseModel):
    email: str
    model_name: str
    strategy: str
    was_revised: bool


class EvaluationRequest(BaseModel):
    strategies: list[str] = Field(
        default=["advanced", "baseline"],
        description="Which strategies to evaluate",
    )


class MetricScore(BaseModel):
    metric_name: str
    score: float
    details: str


class ScenarioResult(BaseModel):
    scenario_id: int
    intent: str
    tone: str
    strategy: str
    model_name: str
    generated_email: str
    scores: list[MetricScore]


class EvaluationResponse(BaseModel):
    results: list[ScenarioResult]
    summary: dict
