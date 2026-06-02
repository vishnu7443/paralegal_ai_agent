import logging

logger = logging.getLogger(__name__)

# List of high-risk legal phrases/terms with weights (1 to 10) and categories
RISK_LEXICON = [
    {
        "term": "indemnify",
        "weight": 8.5,
        "category": "Indemnification",
        "explanation": "Obligates one party to pay for the other party's legal liabilities, costs, and damages, creating severe financial exposure."
    },
    {
        "term": "hold harmless",
        "weight": 8.0,
        "category": "Indemnification",
        "explanation": "Releases the other party from liability for damages arising out of the contract, transferring risk entirely to the signing party."
    },
    {
        "term": "consequential damages",
        "weight": 7.5,
        "category": "Liability Limit",
        "explanation": "Includes indirect losses (like lost profits) in damages, which can multiply potential liability exponentially unless explicitly waived."
    },
    {
        "term": "indirect damages",
        "weight": 7.0,
        "category": "Liability Limit",
        "explanation": "Covers damages not directly resulting from a breach, potentially leading to unpredictable financial claims."
    },
    {
        "term": "punitive damages",
        "weight": 8.0,
        "category": "Liability Limit",
        "explanation": "Refers to damages intended to reform or deter the defendant, which can exceed the actual loss suffered."
    },
    {
        "term": "liquidated damages",
        "weight": 8.5,
        "category": "Damages",
        "explanation": "Pre-determines the exact compensation amount in case of a breach, which can lead to high penalties regardless of actual damage suffered."
    },
    {
        "term": "unilateral termination",
        "weight": 8.0,
        "category": "Termination",
        "explanation": "Allows only one party to end the contract without cause, creating an unbalanced business relationship."
    },
    {
        "term": "terminate for convenience",
        "weight": 6.5,
        "category": "Termination",
        "explanation": "Allows ending the contract without any default, potentially causing unexpected business disruption."
    },
    {
        "term": "automatic renewal",
        "weight": 5.5,
        "category": "Term",
        "explanation": "Automatically extends the contract term unless active notice is given, leading to unwanted long-term commitments."
    },
    {
        "term": "perpetual license",
        "weight": 6.0,
        "category": "Intellectual Property",
        "explanation": "Grants a license that lasts forever, preventing the owner from renegotiating or revoking access easily."
    },
    {
        "term": "ip assignment",
        "weight": 8.0,
        "category": "Intellectual Property",
        "explanation": "Transfers all rights, titles, and interests in created works/inventions, causing loss of critical proprietary technology."
    },
    {
        "term": "work for hire",
        "weight": 7.5,
        "category": "Intellectual Property",
        "explanation": "Designates created deliverables as owned from inception by the client, stripping the creator of copyright ownership."
    },
    {
        "term": "non-compete",
        "weight": 9.0,
        "category": "Restrictive Covenants",
        "explanation": "Restricts the ability to work in similar industries or set up competing businesses, limiting future professional mobility."
    },
    {
        "term": "non-solicit",
        "weight": 7.0,
        "category": "Restrictive Covenants",
        "explanation": "Prevents hiring employees or soliciting clients from the other party, restricting recruiting capabilities."
    },
    {
        "term": "exclusivity",
        "weight": 7.5,
        "category": "Restrictive Covenants",
        "explanation": "Prevents doing business with competitors or other parties, restricting potential market opportunities."
    },
    {
        "term": "most favored nation",
        "weight": 7.0,
        "category": "Pricing",
        "explanation": "Guarantees a buyer the lowest price given to any other customer, restricting pricing flexibility and profit margins."
    },
    {
        "term": "injunctive relief",
        "weight": 6.5,
        "category": "Remedies",
        "explanation": "Allows a party to obtain an immediate court order to halt activities without proving actual monetary damages first."
    },
    {
        "term": "waives any right",
        "weight": 7.5,
        "category": "Waiver",
        "explanation": "Causes the signing party to forfeit legal rights (such as trial by jury or class action participation)."
    },
    {
        "term": "limitation of liability",
        "weight": 7.0,
        "category": "Liability Limit",
        "explanation": "Caps total potential damages at a low threshold (e.g., fees paid), leaving the other party under-compensated in case of major breach."
    },
    {
        "term": "exclusive jurisdiction",
        "weight": 5.0,
        "category": "Jurisdiction",
        "explanation": "Restricts any legal disputes to a specific court or venue, potentially forcing expensive travel and legal representation."
    }
]

def get_lexicon_terms() -> list[str]:
    """Returns a list of all terms defined in the lexicon."""
    return [item["term"] for item in RISK_LEXICON]

def get_lexicon_term_meta(term: str) -> dict:
    """Returns the metadata for a matching term, or a default dict."""
    for item in RISK_LEXICON:
        if item["term"].lower() in term.lower():
            return item
    return {
        "term": term,
        "weight": 1.0,
        "category": "General",
        "explanation": "No specific lexicon match found; flagged for manual review."
    }
