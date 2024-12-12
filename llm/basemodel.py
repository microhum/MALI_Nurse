from pydantic import BaseModel, Field
from typing import List, Optional

class Name(BaseModel):
    prefix: Optional[str] = Field(None, description="Prefix or title (e.g., Mr., Ms., Dr.)")
    firstname: Optional[str] = Field(None, description="The patient's first name")
    surname: Optional[str] = Field(None, description="The patient's surname")

class FamilyHistory(BaseModel):
    relation: str = Field(..., description="Relation to the patient (e.g., father, sister)")
    condition: str = Field(..., description="Health condition present in the family member")

class PersonalHistory(BaseModel):
    type: str = Field(..., description="Type of personal health aspect (e.g., sleep, medication, health behavior)")
    description: str = Field(..., description="Details about the health aspect")

class EHRModel(BaseModel):
    name: Optional[Name] = Field(None, description="Structured name of the patient")
    age: Optional[int] = Field(None, description="The patient's age")
    gender: Optional[str] = Field(None, description="The patient's gender")
    chief_complaint: List[str] = Field(default_factory=list, description="The main symptom reported by the patient")
    present_illness: List[str] = Field(default_factory=list, description="Details about the current illness (e.g., when it started, nature of symptoms)")
    past_illness: List[str] = Field(default_factory=list, description="Past illnesses, allergies, etc.")
    family_history: List[FamilyHistory] = Field(default_factory=list, description="Health issues in the family")
    personal_history: List[PersonalHistory] = Field(default_factory=list, description="Personal health history (e.g., sleep patterns, medications taken)")