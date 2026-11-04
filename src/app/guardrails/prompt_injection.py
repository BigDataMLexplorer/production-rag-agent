from __future__ import annotations
import re
from dataclasses import dataclass
from app.retrieval.schemas import RetrievedChunk
_PATTERNS=[re.compile(r"\bignore (all |any |the )?(previous|prior|system) instructions?\b",re.I),re.compile(r"\b(system|developer) message\b",re.I),re.compile(r"\breveal (the )?(system prompt|hidden prompt|secret|credentials?)\b",re.I),re.compile(r"\bdo not follow (the )?(system|developer|previous) instructions?\b",re.I),re.compile(r"\bexfiltrat(e|ion)\b",re.I),re.compile(r"\bapi[_ -]?key\b",re.I)]
@dataclass(frozen=True)
class InjectionFinding: chunk_id:str; matched_patterns:tuple[str,...]
def detect_prompt_injection(text:str)->tuple[str,...]: return tuple(p.pattern for p in _PATTERNS if p.search(text))
def filter_suspicious_chunks(chunks:list[RetrievedChunk])->tuple[list[RetrievedChunk],list[InjectionFinding]]:
    safe=[]; findings=[]
    for chunk in chunks:
        matches=detect_prompt_injection(chunk.content)
        if matches: findings.append(InjectionFinding(chunk_id=str(chunk.chunk_id),matched_patterns=matches))
        else: safe.append(chunk)
    return safe,findings
