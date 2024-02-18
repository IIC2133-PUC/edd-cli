from typing import Literal

from pydantic import BaseModel, Field


class TestOkResult(BaseModel):
    verdict: Literal["ok"] = Field("ok", init=False)
    name: str
    time: float
    percentage: float


class TestErrorResult(BaseModel):
    verdict: Literal["error"] = Field("error", init=False)
    name: str
    error: str


class TestGroupOkResults(BaseModel):
    verdict: Literal["ok"] = Field("ok", init=False)
    name: str
    results: list[TestOkResult | TestErrorResult] = Field(
        discriminator="verdict", default_factory=list
    )


class TestGroupErrorResults(BaseModel):
    verdict: Literal["error"] = Field("error", init=False)
    name: str
    error: str


class AssignmentResults(BaseModel):
    name: str
    user: str
    results: list[TestGroupOkResults | TestGroupErrorResults] = Field(
        discriminator="verdict",
        default_factory=list,
    )
