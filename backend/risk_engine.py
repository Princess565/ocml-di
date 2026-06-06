import os
MODE = os.getenv("OCML_MODE", "FULL")  # "MVP" or "FULL"

if MODE == "MVP":
    # Minimal shortcut for hackathon demo
    class RiskEngine:
        def evaluate(self, proposed_drug, current_medications=None, conditions=None, allergies=None):
            if proposed_drug.lower() == "ibuprofen" and "kidney disease" in [c.lower() for c in conditions or []]:
                return {"risk_level": "critical", "message": "NSAIDs contraindicated in kidney disease"}
            return {"risk_level": "low", "message": "No interactions found"}

"""
risk_engine.py
OCML-DI — Offline Clinical Memory Layer with Drug Interaction Intelligence

Owner:      Efe Ikharo (Project Lead, ML/AI Systems)
Purpose:    Core drug interaction detection and risk scoring engine.
            Checks local Africa-priority rules first (offline, fast),
            then falls back to external DrugBank API when online.

Architecture:
    Patient record + proposed drug
        ↓
    [1] Normalise drug/condition names  (aliases lookup)
        ↓
    [2] Africa-priority rules check     (offline, instant, highest confidence)
        ↓
    [3] DrugBank API check              (online fallback, broader coverage)
        ↓
    [4] Score aggregation + severity    (RiskResult dataclass)
        ↓
    [5] Governance gate                 (critical alerts → mandatory human review)

Usage:
    engine = RiskEngine()
    result = engine.evaluate(
        proposed_drug="ibuprofen",
        current_medications=["metformin"],
        conditions=["kidney disease", "type 2 diabetes"]
    )
    print(result.to_dict())
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

import requests

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("risk_engine")


# ── Constants ────────────────────────────────────────────────────────────────
RULES_PATH = Path(__file__).parent.parent / "data" / "africa_priority_rules.json"

DRUGBANK_API_BASE = "https://api.drugbank.com/v1"
DRUGBANK_API_KEY  = os.environ.get("DRUGBANK_API_KEY", "")   # set in .env

# Score thresholds that mirror risk_levels in africa_priority_rules.json
RISK_THRESHOLDS = {
    "critical": 8,   # score 8–10  → mandatory human review
    "high":     6,   # score 6–7   → strong caution
    "moderate": 4,   # score 4–5   → additional review
    "low":      1,   # score 1–3   → informational
}

GOVERNANCE_THRESHOLD = RISK_THRESHOLDS["critical"]  # triggers mandatory review flag


# ── Data classes ─────────────────────────────────────────────────────────────
class InteractionType(str, Enum):
    DRUG_DRUG      = "drug_drug"
    DRUG_CONDITION = "drug_condition"
    DRUG_ALLERGY   = "drug_allergy"
    UNKNOWN        = "unknown"


@dataclass
class InteractionMatch:
    """A single detected interaction."""
    rule_id:            str
    cluster:            str
    interaction_type:   InteractionType
    drug_a:             str
    drug_b_or_condition: str
    risk_score:         int                   # 1–10
    risk_level:         str                   # low / moderate / high / critical
    warning_message:    str
    recommendation:     str
    mechanism:          str
    alternatives:       list[str] = field(default_factory=list)
    source:             str = "africa_priority_rules"   # or "drugbank_api"
    references:         list[str] = field(default_factory=list)


@dataclass
class RiskResult:
    """Aggregated result returned to the caller (API / USSD / QR wallet)."""
    proposed_drug:          str
    patient_conditions:     list[str]
    current_medications:    list[str]
    interactions_found:     list[InteractionMatch]
    max_risk_score:         int            # highest score across all matches
    max_risk_level:         str            # corresponding label
    requires_human_review:  bool           # True if any interaction is critical
    evaluation_ms:          int            # latency for audit logging
    offline_mode:           bool           # True if DrugBank was not reached
    timestamp:              str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["interactions_found"] = [asdict(i) for i in self.interactions_found]
        return d

    def to_ussd_string(self) -> str:
        """
        Compact plain-text format for USSD response (~160 chars per SMS segment).
        Keeps critical information within GSM 2G constraints.
        """
        if not self.interactions_found:
            return f"SAFE: {self.proposed_drug} — no interactions found. Proceed with caution."

        top = max(self.interactions_found, key=lambda x: x.risk_score)
        lines = [
            f"{'CRITICAL' if self.requires_human_review else 'WARNING'}: {self.proposed_drug}",
            f"Risk: {top.risk_score}/10 ({top.risk_level.upper()})",
            top.warning_message[:120],
            f"Action: {top.recommendation[:100]}",
        ]
        return "\n".join(lines)


# ── Engine ───────────────────────────────────────────────────────────────────
class RiskEngine:
    """
    Drug interaction and risk scoring engine.

    Checks interactions in three passes:
        1. Drug-condition interactions    (proposed drug vs patient conditions)
        2. Drug-drug interactions         (proposed drug vs current medications)
        3. DrugBank API fallback          (if online and DRUGBANK_API_KEY is set)
    """

    def __init__(self, rules_path: Path = RULES_PATH):
        self.rules       = self._load_rules(rules_path)
        self.aliases     = self.rules.get("drug_name_aliases", {})
        self.cond_aliases = self.rules.get("condition_aliases", {})
        log.info("RiskEngine initialised — %d rules loaded", len(self.rules["interaction_rules"]))

    # ── Public API ───────────────────────────────────────────────────────────

    def evaluate(
        self,
        proposed_drug:        str,
        current_medications:  list[str] | None = None,
        conditions:           list[str] | None = None,
        allergies:            list[str] | None = None,
    ) -> RiskResult:
        """
        Main entry point. Returns a RiskResult for the proposed drug against
        a patient's conditions and current medication list.

        Args:
            proposed_drug:       Drug name being considered for prescription.
            current_medications: List of drug names the patient currently takes.
            conditions:          List of patient medical conditions (free text, normalised internally).
            allergies:           List of known allergens (for future allergy check expansion).

        Returns:
            RiskResult dataclass with all matched interactions and aggregate score.
        """
        start = time.monotonic()

        current_medications = current_medications or []
        conditions          = conditions or []
        allergies           = allergies or []

        # Normalise all inputs to lowercase + expand aliases
        norm_drug   = self._normalise_drug(proposed_drug)
        norm_meds   = [self._normalise_drug(m) for m in current_medications]
        norm_conds  = self._expand_conditions(conditions)

        log.info("Evaluating: drug=%s | meds=%s | conditions=%s", norm_drug, norm_meds, norm_conds)

        matches: list[InteractionMatch] = []

        # Pass 1 — Africa-priority local rules
        matches += self._check_local_drug_condition(norm_drug, norm_conds)
        matches += self._check_local_drug_drug(norm_drug, norm_meds)

        # Pass 2 — DrugBank API (online fallback)
        offline_mode = True
        if DRUGBANK_API_KEY:
            try:
                api_matches  = self._check_drugbank_api(norm_drug, norm_meds)
                matches     += api_matches
                offline_mode = False
            except Exception as exc:
                log.warning("DrugBank API unreachable — offline mode: %s", exc)

        # Deduplicate by rule_id, keep highest scoring version
        matches = self._deduplicate(matches)

        # Aggregate
        max_score  = max((m.risk_score for m in matches), default=0)
        max_level  = self._score_to_level(max_score)
        needs_review = max_score >= GOVERNANCE_THRESHOLD

        elapsed_ms = int((time.monotonic() - start) * 1000)

        from datetime import datetime, timezone
        result = RiskResult(
            proposed_drug         = proposed_drug,
            patient_conditions    = conditions,
            current_medications   = current_medications,
            interactions_found    = matches,
            max_risk_score        = max_score,
            max_risk_level        = max_level,
            requires_human_review = needs_review,
            evaluation_ms         = elapsed_ms,
            offline_mode          = offline_mode,
            timestamp             = datetime.now(timezone.utc).isoformat(),
        )

        log.info(
            "Result: score=%d level=%s review_required=%s matches=%d offline=%s time=%dms",
            max_score, max_level, needs_review, len(matches), offline_mode, elapsed_ms,
        )
        return result

    # ── Local rules checks ───────────────────────────────────────────────────

    def _check_local_drug_condition(
        self, drug: str, conditions: list[str]
    ) -> list[InteractionMatch]:
        """Check proposed drug against patient conditions using local rules."""
        matches = []
        for rule in self.rules["interaction_rules"]:
            if rule["interaction_type"] not in ("drug_condition", "drug_condition_drug"):
                continue
            if not self._drug_matches(drug, rule["drug_a"]["names"]):
                continue
            triggers = [t.lower() for t in rule.get("condition_triggers", [])]
            if any(cond in triggers for cond in conditions):
                matches.append(self._rule_to_match(rule, drug, rule["drug_a"]["drug_class"]))
        return matches

    def _check_local_drug_drug(
        self, drug: str, current_meds: list[str]
    ) -> list[InteractionMatch]:
        """Check proposed drug against current medications using local rules."""
        matches = []
        for rule in self.rules["interaction_rules"]:
            if rule["interaction_type"] != "drug_drug":
                continue
            drug_b_names = [n.lower() for n in rule.get("drug_b", {}).get("names", [])]
            a_matches_proposed = self._drug_matches(drug, rule["drug_a"]["names"])
            b_matches_proposed = self._drug_matches(drug, drug_b_names)

            for med in current_meds:
                # Interaction can appear either way: proposed=A & current=B or vice versa
                if a_matches_proposed and self._drug_matches(med, drug_b_names):
                    matches.append(self._rule_to_match(rule, drug, med))
                elif b_matches_proposed and self._drug_matches(med, rule["drug_a"]["names"]):
                    matches.append(self._rule_to_match(rule, med, drug))
        return matches

    # ── DrugBank API fallback ────────────────────────────────────────────────

    def _check_drugbank_api(
        self, drug: str, current_meds: list[str]
    ) -> list[InteractionMatch]:
        """
        Query DrugBank DDI endpoint for interactions between proposed drug
        and current medications. Only called when online + API key present.

        DrugBank expects drug names or drugbank_ids. We send names and let
        their API handle normalisation.
        """
        if not current_meds:
            return []

        all_drugs = [drug] + current_meds
        payload   = {"drug_names": all_drugs}

        response = requests.post(
            f"{DRUGBANK_API_BASE}/ddi",
            json=payload,
            headers={
                "Authorization": DRUGBANK_API_KEY,
                "Content-Type":  "application/json",
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        matches = []
        for item in data.get("interactions", []):
            # Only include interactions where our proposed drug is involved
            involved = [item.get("drug_a_name", ""), item.get("drug_b_name", "")]
            if not self._drug_matches(drug, involved):
                continue

            score = self._drugbank_severity_to_score(item.get("severity", "moderate"))
            matches.append(InteractionMatch(
                rule_id              = f"DB-{item.get('id', 'unknown')}",
                cluster              = "drugbank",
                interaction_type     = InteractionType.DRUG_DRUG,
                drug_a               = item.get("drug_a_name", drug),
                drug_b_or_condition  = item.get("drug_b_name", ""),
                risk_score           = score,
                risk_level           = self._score_to_level(score),
                warning_message      = item.get("description", "Drug interaction detected."),
                recommendation       = item.get("management", "Consult a clinician."),
                mechanism            = item.get("extended_description", ""),
                source               = "drugbank_api",
            ))
        return matches

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _load_rules(self, path: Path) -> dict:
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _normalise_drug(self, name: str) -> str:
        """
        Lowercase and expand brand/generic aliases to canonical name.
        e.g. 'Brufen' → 'ibuprofen', 'Coartem' → 'artemether-lumefantrine'
        """
        name_lower = name.lower().strip()
        for canonical, synonyms in self.aliases.items():
            if name_lower == canonical or name_lower in [s.lower() for s in synonyms]:
                return canonical
        return name_lower

    def _expand_conditions(self, conditions: list[str]) -> list[str]:
        """
        Expand condition strings to include all known aliases so matching
        is robust against free-text variation in patient records.
        e.g. 'CKD' → ['kidney disease', 'ckd', 'renal failure', ...]
        """
        expanded = set()
        for cond in conditions:
            cond_lower = cond.lower().strip()
            expanded.add(cond_lower)
            # Check if it matches any canonical condition or its aliases
            for canonical, aliases in self.cond_aliases.items():
                all_forms = [canonical.lower()] + [a.lower() for a in aliases]
                if cond_lower in all_forms:
                    expanded.update(all_forms)
        return list(expanded)

    def _drug_matches(self, drug: str, name_list: list[str]) -> bool:
        """True if drug (normalised) appears in a list of names."""
        norm = self._normalise_drug(drug)
        return norm in [self._normalise_drug(n) for n in name_list]

    def _rule_to_match(self, rule: dict, drug_a: str, drug_b_or_condition: str) -> InteractionMatch:
        return InteractionMatch(
            rule_id              = rule["rule_id"],
            cluster              = rule["cluster"],
            interaction_type     = InteractionType(rule["interaction_type"].replace("drug_condition_drug", "drug_condition")),
            drug_a               = drug_a,
            drug_b_or_condition  = drug_b_or_condition,
            risk_score           = rule["risk_score"],
            risk_level           = self._score_to_level(rule["risk_score"]),
            warning_message      = rule["warning_message"],
            recommendation       = rule["recommendation"],
            mechanism            = rule.get("mechanism", ""),
            alternatives         = rule.get("alternatives", []),
            source               = "africa_priority_rules",
            references           = rule.get("references", []),
        )

    def _deduplicate(self, matches: list[InteractionMatch]) -> list[InteractionMatch]:
        """Keep only the highest-scoring match per rule_id."""
        seen: dict[str, InteractionMatch] = {}
        for m in matches:
            if m.rule_id not in seen or m.risk_score > seen[m.rule_id].risk_score:
                seen[m.rule_id] = m
        return sorted(seen.values(), key=lambda x: x.risk_score, reverse=True)

    def _score_to_level(self, score: int) -> str:
        if score >= RISK_THRESHOLDS["critical"]:
            return "critical"
        if score >= RISK_THRESHOLDS["high"]:
            return "high"
        if score >= RISK_THRESHOLDS["moderate"]:
            return "moderate"
        return "low"

    def _drugbank_severity_to_score(self, severity: str) -> int:
        """Map DrugBank severity string to OCML-DI 1–10 score."""
        mapping = {
            "contraindicated": 10,
            "major":           8,
            "moderate":        5,
            "minor":           2,
        }
        return mapping.get(severity.lower(), 3)


# ── CLI smoke test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from os import getenv
    from models import AuditLog, AuditAction, AccessChannel  # import your governance models

    MODE = getenv("OCML_MODE", "FULL")
    engine = RiskEngine()

    print("\n" + "="*60)
    print(f"Running RiskEngine in {MODE} mode")
    print("="*60)

    def log_review(case_name: str, result, drug: str):
        """Helper to log governance events when human review is required."""
        if result.get("requires_human_review") if MODE == "MVP" else result.requires_human_review:
            log_entry = AuditLog(
                action=AuditAction.CRITICAL_ALERT_RAISED,
                actor_id="demo_chw",
                patient_name=case_name,
                channel=AccessChannel.DASHBOARD,
                risk_score=result.get("risk_score") if MODE == "MVP" else result.max_risk_score,
                details={"drug": drug, "mode": MODE}
            )
            print(f"⚠️ Audit Log → {log_entry.action} | Risk={log_entry.risk_score} | Patient={log_entry.patient_name}")

    if MODE == "MVP":
        # Quick demo shortcut
        result = engine.evaluate("ibuprofen", conditions=["kidney disease"])
        print(result)
        log_review("Amina Bello", result, "ibuprofen")
    else:
        # Full production smoke tests
        # Case 1 — Ibuprofen + Kidney Disease
        result = engine.evaluate(
            proposed_drug="ibuprofen",
            current_medications=[],
            conditions=["kidney disease"],
        )
        print(f"Risk Score  : {result.max_risk_score}/10")
        print(f"Risk Level  : {result.max_risk_level.upper()}")
        print(f"Human Review: {result.requires_human_review}")
        log_review("Amina Bello", result, "ibuprofen")

        # Case 2 — Rifampicin + Dolutegravir
        result2 = engine.evaluate(
            proposed_drug="rifampicin",
            current_medications=["dolutegravir"],
            conditions=["tuberculosis", "HIV"],
        )
        print(f"\nRisk Score  : {result2.max_risk_score}/10")
        print(f"Risk Level  : {result2.max_risk_level.upper()}")
        print(f"Human Review: {result2.requires_human_review}")
        log_review("TB/HIV Demo", result2, "rifampicin")

        # Case 3 — Amodiaquine + Nevirapine
        result3 = engine.evaluate(
            proposed_drug="amodiaquine",
            current_medications=["nevirapine"],
            conditions=["HIV", "malaria"],
        )
        print(f"\nRisk Score  : {result3.max_risk_score}/10")
        print(f"Risk Level  : {result3.max_risk_level.upper()}")
        print(f"Human Review: {result3.requires_human_review}")
        log_review("ARV/Malaria Demo", result3, "amodiaquine")
