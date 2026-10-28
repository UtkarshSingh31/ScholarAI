"""Compatibility exports for workflow agent nodes.

Implementations live under agents; this module preserves the original
public imports and test patch points.
"""

from tools import (
    search_web,
    extract_pages,
    extract_requirements,
    extract_pdf_text,
    extract_profile_urls,
    extract_student_profile,
)
from langchain_google_genai import ChatGoogleGenerativeAI

from agents import profile as _profile
from agents import hunter as _hunter
from agents import auditor as _auditor
from agents import matchmaker as _matchmaker
from agents import application_coach as _application_coach
from agents import evidence as _evidence


def profile_intelligence_agent(state):
    _profile.extract_pdf_text = extract_pdf_text
    _profile.extract_profile_urls = extract_profile_urls
    _profile.extract_student_profile = extract_student_profile
    _profile.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
    return _profile.profile_intelligence_agent(state)


def opportunity_hunter_agent(state):
    return _hunter.opportunity_hunter_agent(state)


def eligibility_auditor_agent(state):
    _auditor.extract_requirements = extract_requirements
    return _auditor.eligibility_auditor_agent(state)


def matchmaker_agent(state):
    return _matchmaker.matchmaker_agent(state)


def application_coach_agent(state):
    _application_coach.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
    return _application_coach.application_coach_agent(state)


def evidence_node(state):
    return _evidence.evidence_node(state)
