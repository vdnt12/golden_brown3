"""CUAD (Contract Understanding Atticus Dataset) Clause Extractor & Reviewer.

Implements full 41-category detection from The Atticus Project CUAD dataset & benchmark
(https://www.atticusprojectai.org/cuad and https://github.com/The-Atticus-Project/cuad.git).

Directly reproduces the visual output layout shown in the CUAD contract review
architecture (contract_review.png):
  * Governing Law
  * ⚠️ Covenant Not to Sue (warning)
  * 🚩 Perpetual / Irrevocable License (red flag / high attention)
  * Cap on Liability / Uncapped Liability
  * Non-Compete & Exclusivity
  * Termination for Convenience
  * Anti-Assignment & Change of Control
  * Audit Rights & Liquidated Damages
  * License Grant & IP Ownership Assignment
  * Warranty, Insurance, and Notice Period
  ... and all 41 official Atticus categories.

Every hit is bound to a verified sentence record with exact quote, page and section.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.config import Settings
from app.store import sentences as sentences_store
from app.store.repo import open_document


@dataclass(frozen=True)
class CUADCategoryDef:
    key: str
    label: str
    description: str
    answer_format: str
    group: str
    badge_type: str  # "normal" | "warning" | "danger"
    badge_icon: str  # "" | "⚠️" | "🚩"
    patterns: tuple[str, ...]
    priority: int  # lower = higher display priority


CUAD_CATEGORIES: tuple[CUADCategoryDef, ...] = (
    # Top 3 from CUAD architecture diagram (contract_review.png)
    CUADCategoryDef(
        key="governing_law",
        label="Governing Law",
        description="Which state/country's law governs the interpretation and disputes of the contract.",
        answer_format="Name of State / Province, Country",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\b(?:governed\s+by\s+(?:the\s+)?laws?|laws?\s+of\s+(?:the\s+)?(?:state|country|republic|commonwealth|province|territory))\b",
            r"\b(?:exclusive\s+)?jurisdiction\s+of\s+(?:the\s+)?courts?\b",
            r"\bcourts?\s+at\s+[\w\s]{3,30}\s+shall\s+have\s+jurisdiction\b",
            r"\bchoice\s+of\s+law\b",
            r"\bgoverning\s+law\b",
            r"\bsubject\s+to\s+the\s+(?:exclusive\s+)?jurisdiction\b",
        ),
        priority=1,
    ),
    CUADCategoryDef(
        key="covenant_not_to_sue",
        label="Covenant Not to Sue",
        description="Is a party restricted from contesting the validity of IP ownership or otherwise bringing a claim against the counterparty?",
        answer_format="Yes/No",
        group="-",
        badge_type="warning",
        badge_icon="⚠️",
        patterns=(
            r"\bcovenants?\s+not\s+to\s+sue\b",
            r"\bnot\s+now\s+or\s+in\s+the\s+future\s+contest\b",
            r"\bshall\s+not\s+(?:at\s+any\s+time\s+)?(?:contest|challenge|dispute)\s+(?:the\s+)?validity\b",
            r"\bagrees?\s+not\s+to\s+sue\b",
            r"\bwaives?\s+(?:any\s+and\s+all\s+)?rights?\s+to\s+(?:sue|bring\s+(?:a\s+)?claim)\b",
            r"\bno\s+claim\s+shall\s+be\s+brought\b",
        ),
        priority=2,
    ),
    CUADCategoryDef(
        key="perpetual_license",
        label="Perpetual / Irrevocable License",
        description="Does the contract contain a license grant that is irrevocable or perpetual?",
        answer_format="Yes/No",
        group="4",
        badge_type="danger",
        badge_icon="🚩",
        patterns=(
            r"\b(?:irrevocable\s+and\s+perpetual|perpetual\s+and\s+irrevocable|perpetual,\s*irrevocable|irrevocable,\s*perpetual)\b",
            r"\b(?:worldwide,\s*royalty-free,\s*exclusive,\s*irrevocable|worldwide,\s*irrevocable)\b",
            r"\b(?:perpetual\s+license|irrevocable\s+license)\b",
            r"\bgrants?\s+[^.\n]{0,80}\b(?:in\s+perpetuity|perpetually)\b",
            r"\broyalty-free,\s*perpetual\b",
            r"\b(?:irrevocable|perpetual)\s+right\s+to\s+use\b",
        ),
        priority=3,
    ),
    CUADCategoryDef(
        key="cap_on_liability",
        label="Cap on Liability",
        description="Limitation on maximum aggregate liability recoverable upon breach or time limitation for claims.",
        answer_format="Yes/No",
        group="6",
        badge_type="warning",
        badge_icon="⚠️",
        patterns=(
            r"\b(?:aggregate|total|maximum)\s+liability\s+(?:under|arising\s+out\s+of)?[^.\n]{0,50}?(?:shall\s+not\s+exceed|capped\s+at|limited\s+to)\b",
            r"\bin\s+no\s+event\s+shall\s+(?:either\s+party|liability)[^.\n]{0,60}?exceed\b",
            r"\blimitation\s+of\s+liability\b",
            r"\bcap\s+on\s+liability\b",
        ),
        priority=4,
    ),
    CUADCategoryDef(
        key="uncapped_liability",
        label="Uncapped Liability",
        description="Is a party's liability uncapped upon breach (e.g. for IP infringement, confidentiality breach, gross negligence)?",
        answer_format="Yes/No",
        group="6",
        badge_type="danger",
        badge_icon="🚩",
        patterns=(
            r"\bliability\s+shall\s+not\s+be\s+(?:limited|capped)\b",
            r"\bwithout\s+limitation\s+to\s+liability\b",
            r"\buncapped\s+liability\b",
            r"\bshall\s+not\s+apply\s+to\s+(?:gross\s+negligence|willful\s+misconduct|breach\s+of\s+confidentiality)\b",
            r"\bunlimited\s+liability\b",
        ),
        priority=5,
    ),
    CUADCategoryDef(
        key="non_compete",
        label="Non-Compete",
        description="Restriction on the ability of a party to compete with the counterparty or operate in a certain sector.",
        answer_format="Yes/No",
        group="2",
        badge_type="warning",
        badge_icon="⚠️",
        patterns=(
            r"\bshall\s+not\s+(?:directly\s+or\s+indirectly\s+)?(?:engage\s+in|carry\s+on|compete|participate\s+in)\b",
            r"\bnon-compete\b",
            r"\brestraint\s+of\s+trade\b",
            r"\bnegative\s+covenant\b",
            r"\bcompeting\s+business\b",
        ),
        priority=6,
    ),
    CUADCategoryDef(
        key="exclusivity",
        label="Exclusivity",
        description="Exclusive dealing commitment with counterparty, including sole supplier or prohibition on third-party sales.",
        answer_format="Yes/No",
        group="2",
        badge_type="warning",
        badge_icon="⚠️",
        patterns=(
            r"\bexclusive\s+(?:provider|supplier|partner|distributor|dealing|rights?)\b",
            r"\bsole\s+and\s+exclusive\b",
            r"\bshall\s+not\s+(?:license|sell|distribute)\s+to\s+any\s+third\s+party\b",
            r"\bon\s+an\s+exclusive\s+basis\b",
        ),
        priority=7,
    ),
    CUADCategoryDef(
        key="termination_for_convenience",
        label="Termination for Convenience",
        description="Can a party terminate this contract without cause solely by giving notice and allowing waiting period to expire?",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bterminate\s+(?:this\s+agreement\s+)?without\s+cause\b",
            r"\bterminate\s+for\s+convenience\b",
            r"\b(?:either\s+party\s+may\s+terminate|give|giving)\s+[^.\n]{0,50}?\b\d+\s+days'?\s+written\s+notice\b",
            r"\bterminate\s+at\s+any\s+time\s+by\s+giving\b",
            r"\bwritten\s+notice\s+before\s+vacating\b",
        ),
        priority=8,
    ),
    CUADCategoryDef(
        key="anti_assignment",
        label="Anti-Assignment",
        description="Is consent or notice required of a party if the contract is assigned to a third party?",
        answer_format="Yes/No",
        group="3",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bmay\s+not\s+assign\s+(?:this\s+agreement|its\s+rights)\b",
            r"\bwithout\s+(?:the\s+)?prior\s+written\s+consent\s+of\s+(?:the\s+other\s+party|landlord|lessor)\b",
            r"\bassignment\s+by\s+operation\s+of\s+law\b",
            r"\bprohibition\s+against\s+assignment\b",
        ),
        priority=9,
    ),
    CUADCategoryDef(
        key="change_of_control",
        label="Change of Control",
        description="Does counterparty have termination or consent rights if a party undergoes merger, acquisition, or stock sale?",
        answer_format="Yes/No",
        group="3",
        badge_type="warning",
        badge_icon="⚠️",
        patterns=(
            r"\bchange\s+of\s+control\b",
            r"\bmerger,\s*acquisition\s+or\s+sale\s+of\s+assets\b",
            r"\btransfer\s+of\s+substantially\s+all\s+(?:of\s+the\s+)?assets\b",
            r"\bcontrolling\s+interest\b",
        ),
        priority=10,
    ),
    CUADCategoryDef(
        key="audit_rights",
        label="Audit Rights",
        description="Does a party have the right to audit books, records, premises, or operations to ensure compliance?",
        answer_format="Yes/No",
        group="5",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bright\s+to\s+audit\b",
            r"\baudit\s+(?:the\s+)?(?:books|records|premises)\b",
            r"\binspect\s+(?:the\s+)?(?:premises|property|records)\b",
            r"\bexamination\s+of\s+records\b",
        ),
        priority=11,
    ),
    CUADCategoryDef(
        key="liquidated_damages",
        label="Liquidated Damages",
        description="Does the contract contain a clause awarding liquidated damages or early termination fees for breach?",
        answer_format="Yes/No",
        group="-",
        badge_type="warning",
        badge_icon="⚠️",
        patterns=(
            r"\bliquidated\s+damages\b",
            r"\bpenalty\s+of\b",
            r"\binterest\s+at\s+\d+%\s+per\s+month\b",
            r"\blate\s+(?:payment\s+)?fee\b",
            r"\bforfeit\w*\s+(?:the\s+)?(?:security\s+)?deposit\b",
        ),
        priority=12,
    ),
    CUADCategoryDef(
        key="ip_ownership_assignment",
        label="IP Ownership Assignment",
        description="Does intellectual property created by one party become the property of the counterparty?",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\b(?:assigns?|transfers?)\s+(?:all\s+)?(?:right,\s*title\s*and\s*interest|ip)\b",
            r"\bintellectual\s+property\s+shall\s+(?:belong|vest|be\s+owned)\b",
            r"\bownership\s+of\s+intellectual\s+property\b",
            r"\bwork\s+made\s+for\s+hire\b",
        ),
        priority=13,
    ),
    CUADCategoryDef(
        key="joint_ip_ownership",
        label="Joint IP Ownership",
        description="Is there any clause providing for joint or shared ownership of intellectual property between the parties?",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bjoint\s+(?:ownership|intellectual\s+property|ip)\b",
            r"\bjointly\s+owned\b",
            r"\bshared\s+ownership\b",
            r"\bco-owned\s+ip\b",
        ),
        priority=14,
    ),
    CUADCategoryDef(
        key="license_grant",
        label="License Grant",
        description="Does the contract contain a license granted by one party to its counterparty?",
        answer_format="Yes/No",
        group="4",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bgrants?\s+(?:to\s+)?(?:licensee|tenant|buyer|client)\s+(?:a\s+)?(?:non-exclusive|exclusive)?\s*license\b",
            r"\blicense\s+grant\b",
            r"\bright\s+and\s+license\s+to\s+use\b",
            r"\bhereby\s+grants\s+a\s+license\b",
        ),
        priority=15,
    ),
    CUADCategoryDef(
        key="non_transferable_license",
        label="Non-Transferable License",
        description="Does the contract limit the ability of a party to transfer or sublicense the license granted?",
        answer_format="Yes/No",
        group="4",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bnon-transferable\s+(?:and\s+non-assignable\s+)?license\b",
            r"\bmay\s+not\s+(?:transfer|sublicense|assign)\s+the\s+license\b",
            r"\bnon-sublicensable\b",
            r"\bpersonal\s+and\s+non-transferable\b",
        ),
        priority=16,
    ),
    CUADCategoryDef(
        key="affiliate_license_licensor",
        label="Affiliate License-Licensor",
        description="License grant by affiliates of the licensor or including intellectual property of affiliates.",
        answer_format="Yes/No",
        group="4",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\blicensor\s+and\s+its\s+affiliates\s+hereby\s+grant\b",
            r"\baffiliates?\s+of\s+licensor\b",
            r"\blicenses?\s+from\s+affiliates?\b",
        ),
        priority=17,
    ),
    CUADCategoryDef(
        key="affiliate_license_licensee",
        label="Affiliate License-Licensee",
        description="License grant extending to licensee and affiliates of such licensee.",
        answer_format="Yes/No",
        group="4",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\blicensee\s+and\s+its\s+affiliates\b",
            r"\bextend\s+to\s+affiliates?\s+of\s+licensee\b",
            r"\buse\s+by\s+affiliates\b",
        ),
        priority=18,
    ),
    CUADCategoryDef(
        key="unlimited_license",
        label="Unlimited/All-You-Can-Eat-License",
        description="Clause granting an enterprise-wide, all-you-can-eat, or unlimited usage license.",
        answer_format="Yes/No",
        group="4",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bunlimited\s+(?:use|license|seats?|access|users?)\b",
            r"\benterprise-wide\s+license\b",
            r"\ball-you-can-eat\b",
            r"\bwithout\s+restriction\s+on\s+volume\b",
        ),
        priority=19,
    ),
    CUADCategoryDef(
        key="source_code_escrow",
        label="Source Code Escrow",
        description="Requirement to deposit source code into third-party escrow for release on bankruptcy or default.",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bsource\s+code\s+escrow\b",
            r"\bescrow\s+agreement\b",
            r"\bdeposit\s+(?:the\s+)?source\s+code\b",
            r"\brelease\s+conditions?\s+from\s+escrow\b",
        ),
        priority=20,
    ),
    CUADCategoryDef(
        key="post_termination_services",
        label="Post-Termination Services",
        description="Obligations after termination, including transition assistance, wind-down, or data return.",
        answer_format="Yes/No",
        group="5",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bpost-termination\s+(?:services?|obligations?|transition)\b",
            r"\btransition\s+assistance\b",
            r"\bupon\s+termination,\s*[^.\n]{0,60}?\b(?:return|destroy|deliver)\b",
            r"\bwind-down\s+period\b",
        ),
        priority=21,
    ),
    CUADCategoryDef(
        key="warranty_duration",
        label="Warranty Duration",
        description="Duration of warranty against defects or errors in technology, products, or premises.",
        answer_format="Number of months or years",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bwarranty\s+period\s+of\s+\d+\s+(?:days?|months?|years?)\b",
            r"\bwarrant(?:s|y)\s+for\s+(?:a\s+period\s+of\s+)?\d+\s+(?:months?|years?)\b",
            r"\bguarantee\s+for\s+\d+\s+months\b",
        ),
        priority=22,
    ),
    CUADCategoryDef(
        key="insurance",
        label="Insurance",
        description="Requirement for commercial liability, property, or workers' compensation insurance.",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bmaintain\s+(?:commercial\s+general\s+liability\s+)?insurance\b",
            r"\bpolicy\s+of\s+insurance\b",
            r"\bcomprehensive\s+general\s+liability\b",
            r"\binsurance\s+coverage\s+of\s+not\s+less\s+than\b",
        ),
        priority=23,
    ),
    CUADCategoryDef(
        key="third_party_beneficiary",
        label="Third Party Beneficiary",
        description="Clause stating whether non-contracting third parties can enforce terms of the agreement.",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bno\s+third[- ]party\s+beneficiar(?:y|ies)\b",
            r"\bthird[- ]party\s+beneficiar(?:y|ies)\b",
            r"\bnot\s+intended\s+to\s+confer\s+rights\s+on\s+any\s+third\s+party\b",
            r"\bcontracts?\s+\(rights\s+of\s+third\s+parties\)\b",
        ),
        priority=24,
    ),
    CUADCategoryDef(
        key="parties",
        label="Parties",
        description="Identified contracting entities, licensors, licensees, lessors, and lessees.",
        answer_format="Entity or individual names",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bbetween\s+[\w\s\"\'().,]{3,120}\s+and\b",
            r"\bby\s+and\s+between\b",
            r"\b(?:landlord|lessor|licensor|owner)\b[^.\n]{0,40}\b(?:tenant|lessee|licensee)\b",
        ),
        priority=25,
    ),
    CUADCategoryDef(
        key="document_name",
        label="Document Name",
        description="The formal title or name of the agreement.",
        answer_format="Contract Name",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\b(?:leave\s+and\s+licen[sc]e|lease\s+agreement|tenancy\s+agreement|master\s+services\s+agreement|non-disclosure\s+agreement|employment\s+agreement|software\s+licen[sc]e\s+agreement)\b",
            r"\bthis\s+agreement\s+is\s+entered\s+into\b",
        ),
        priority=26,
    ),
    CUADCategoryDef(
        key="agreement_date",
        label="Agreement Date",
        description="The date of execution of the agreement.",
        answer_format="Date (mm/dd/yyyy)",
        group="1",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bexecuted\s+on\s+(?:this\s+)?(?:\d{1,2}(?:st|nd|rd|th)?\s+day\s+of\s+[A-Za-z]+,?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4})\b",
            r"\bmade\s+(?:and\s+entered\s+into\s+)?on\s+(?:this\s+)?(?:\d{1,2}\s+[A-Za-z]+,?\s+\d{4})\b",
            r"\bdate\s+of\s+agreement\b",
        ),
        priority=27,
    ),
    CUADCategoryDef(
        key="effective_date",
        label="Effective Date",
        description="The date when the contract becomes effective and binding.",
        answer_format="Date (mm/dd/yyyy)",
        group="1",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\beffective\s+date\s*[:=]?\s*[\w\s,/-]{4,25}\b",
            r"\bshall\s+come\s+into\s+force\s+on\b",
            r"\bcommence\s+on\s+(?:the\s+)?\d{1,2}",
        ),
        priority=28,
    ),
    CUADCategoryDef(
        key="expiration_date",
        label="Expiration Date",
        description="Date on which the initial term expires.",
        answer_format="Date / Perpetual",
        group="1",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bexpir(?:es?|ation\s+date)\s*[:=]?\s*[\w\s,/-]{4,25}\b",
            r"\bterm\s+shall\s+end\s+on\b",
            r"\bshall\s+expire\s+on\b",
        ),
        priority=29,
    ),
    CUADCategoryDef(
        key="renewal_term",
        label="Renewal Term",
        description="Renewal terms including automatic extensions or options to renew.",
        answer_format="Number of years/months / Perpetual",
        group="1",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\boption\s+to\s+renew\s+(?:for\s+an\s+additional\s+period\s+of)?\b",
            r"\bautomatically\s+renew\b",
            r"\bextended\s+by\s+mutual\s+consent\b",
            r"\brenewal\s+term\b",
        ),
        priority=30,
    ),
    CUADCategoryDef(
        key="notice_period_to_terminate_renewal",
        label="Notice Period to Terminate Renewal",
        description="Notice period required to prevent or terminate renewal.",
        answer_format="Number of days/months",
        group="1",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bwritten\s+notice\s+of\s+non-renewal\s+(?:at\s+least\s+)?\d+\s+days\b",
            r"\bnotice\s+not\s+to\s+renew\b",
            r"\bopt\s+out\s+of\s+automatic\s+renewal\b",
        ),
        priority=31,
    ),
    CUADCategoryDef(
        key="most_favored_nation",
        label="Most Favored Nation",
        description="Right of counterparty to receive equal or better pricing/terms given to any other customer.",
        answer_format="Yes/No",
        group="-",
        badge_type="warning",
        badge_icon="⚠️",
        patterns=(
            r"\bmost\s+favou?red\s+nation\b",
            r"\bmfn\s+(?:clause|pricing|status)\b",
            r"\bno\s+less\s+favou?rable\s+than\s+terms\s+offered\s+to\b",
        ),
        priority=32,
    ),
    CUADCategoryDef(
        key="no_solicit_customers",
        label="No-Solicit of Customers",
        description="Restriction from soliciting or contracting customers of counterparty.",
        answer_format="Yes/No",
        group="2",
        badge_type="warning",
        badge_icon="⚠️",
        patterns=(
            r"\bshall\s+not\s+(?:solicit|entice\s+away)\s+(?:any\s+)?customers?\b",
            r"\bnon-solicitation\s+of\s+clients\b",
            r"\brefrain\s+from\s+soliciting\s+business\s+from\b",
        ),
        priority=33,
    ),
    CUADCategoryDef(
        key="no_solicit_employees",
        label="No-Solicit of Employees",
        description="Restriction from soliciting or hiring employees/contractors of counterparty.",
        answer_format="Yes/No",
        group="-",
        badge_type="warning",
        badge_icon="⚠️",
        patterns=(
            r"\bshall\s+not\s+(?:solicit|recruit|hire)\s+(?:any\s+)?employees?\b",
            r"\bnon-solicitation\s+of\s+personnel\b",
            r"\bentice\s+away\s+any\s+staff\b",
        ),
        priority=34,
    ),
    CUADCategoryDef(
        key="non_disparagement",
        label="Non-Disparagement",
        description="Requirement not to make disparaging statements about counterparty.",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bnon-disparagement\b",
            r"\bshall\s+not\s+(?:make\s+any\s+)?disparaging\s+remarks\b",
            r"\bdefame\s+or\s+disparage\b",
        ),
        priority=35,
    ),
    CUADCategoryDef(
        key="rofr_rofo_rofn",
        label="Rofr/Rofo/Rofn",
        description="Right of first refusal, offer, or negotiation to purchase, license, or market assets.",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bright\s+of\s+first\s+refusal\b",
            r"\brofr\b",
            r"\bright\s+of\s+first\s+offer\b",
            r"\brofo\b",
            r"\bright\s+of\s+first\s+negotiation\b",
        ),
        priority=36,
    ),
    CUADCategoryDef(
        key="revenue_profit_sharing",
        label="Revenue/Profit Sharing",
        description="Requirement to share revenue, royalties, or profit for goods/services provided.",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\brevenue\s+shar(?:e|ing)\b",
            r"\bprofit\s+shar(?:e|ing)\b",
            r"\broyalt(?:y|ies)\s+of\s+\d+%\b",
            r"\bpercentage\s+of\s+gross\s+revenue\b",
        ),
        priority=37,
    ),
    CUADCategoryDef(
        key="price_restrictions",
        label="Price Restrictions",
        description="Restrictions on the ability to raise, reduce, or alter pricing for goods/services.",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bprice\s+increase\s+shall\s+not\s+exceed\b",
            r"\bfixed\s+price\s+for\s+the\s+duration\b",
            r"\bprice\s+restriction\b",
            r"\brates?\s+shall\s+remain\s+firm\b",
        ),
        priority=38,
    ),
    CUADCategoryDef(
        key="minimum_commitment",
        label="Minimum Commitment",
        description="Minimum order size, units, or purchase commitment required under contract.",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bminimum\s+commitment\b",
            r"\bminimum\s+purchase\s+obligation\b",
            r"\bminimum\s+guaranteed\s+amount\b",
            r"\bminimum\s+spend\b",
        ),
        priority=39,
    ),
    CUADCategoryDef(
        key="volume_restriction",
        label="Volume Restriction",
        description="Fee increases or consent requirements if usage exceeds specified volume thresholds.",
        answer_format="Yes/No",
        group="-",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bvolume\s+restriction\b",
            r"\bthreshold\s+of\s+\d+\s+units\b",
            r"\boverage\s+fees?\b",
            r"\bexcess\s+usage\s+charge\b",
        ),
        priority=40,
    ),
    CUADCategoryDef(
        key="competitive_restriction_exception",
        label="Competitive Restriction Exception",
        description="Exceptions or carve-outs to non-compete, exclusivity, or non-solicit provisions.",
        answer_format="Yes/No",
        group="2",
        badge_type="normal",
        badge_icon="",
        patterns=(
            r"\bnotwithstanding\s+the\s+foregoing,\s*neither\s+party\s+shall\s+be\s+restricted\b",
            r"\bexception\s+to\s+non-compete\b",
            r"\bcarve-?out\s+for\s+passive\s+investment\b",
        ),
        priority=41,
    ),
)

_COMPILED_CUAD: list[tuple[CUADCategoryDef, tuple[re.Pattern[str], ...]]] = [
    (cat, tuple(re.compile(p, re.IGNORECASE) for p in cat.patterns))
    for cat in CUAD_CATEGORIES
]


@dataclass(frozen=True)
class CUADFinding:
    category: str
    label: str
    description: str
    badge_type: str
    badge_icon: str
    quote: str
    page: int
    section: str | None
    sid: str
    priority: int


def analyze_cuad(settings: Settings, doc_id: str) -> dict[str, Any]:
    """Run CUAD clause extraction on all stored sentences of the document."""
    findings: list[CUADFinding] = []

    with open_document(settings.data_dir, doc_id) as handle:
        doc = handle.connection.execute(
            "SELECT source_filename, page_count FROM document WHERE doc_id = ?",
            (doc_id,),
        ).fetchone()
        if doc is None:
            raise LookupError(doc_id)

        rows = sentences_store.all_sentences(handle.connection, doc_id)
        sentences = [
            (
                row["sid"],
                int(row["page_no"]),
                row["section"] or row["heading"] or "",
                row["text"],
            )
            for row in rows
        ]

    for cat_def, patterns in _COMPILED_CUAD:
        for sid, page, section, text in sentences:
            if any(pattern.search(text) for pattern in patterns):
                findings.append(
                    CUADFinding(
                        category=cat_def.key,
                        label=cat_def.label,
                        description=cat_def.description,
                        badge_type=cat_def.badge_type,
                        badge_icon=cat_def.badge_icon,
                        quote=text.strip(),
                        page=page,
                        section=section,
                        sid=sid,
                        priority=cat_def.priority,
                    )
                )
                break  # one representative finding per category for the overview banner

    # Sort findings by priority (Governing Law, Covenant Not to Sue, Perpetual License first)
    findings.sort(key=lambda f: f.priority)

    return {
        "document_id": doc_id,
        "document_name": doc["source_filename"] or "Document",
        "page_count": int(doc["page_count"]),
        "findings": [
            {
                "category": f.category,
                "label": f.label,
                "description": f.description,
                "badge_type": f.badge_type,
                "badge_icon": f.badge_icon,
                "quote": f.quote,
                "page": f.page,
                "section": f.section,
                "sid": f.sid,
            }
            for f in findings
        ],
        "total_categories_checked": len(CUAD_CATEGORIES),
        "found_count": len(findings),
    }
