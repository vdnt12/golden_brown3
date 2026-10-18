"""Open India Law Primary Dataset & Legal Research Service.

Implements structured primary law retrieval inspired by the open-india-law dataset
for GBDoc.

Contains normalized, official-source primary Indian law:
1. Central & State Legislation (Enactments, Chapters, Sections, Official Gazette sources)
2. Supreme Court of India & High Court Judgments (Citations, Bench, Ratio Decidendi)
3. Regulatory & Tribunal Determinations (RERA, NCLT, CCI, TDSAT)
4. Statutory Contract Compliance Evaluator (Cross-referencing contract clauses with statutory law)

All responses strictly cite official sources (Act Year, Section, Official Gazette URL, Court Citation).
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class StatutorySection:
    section_id: str
    section_number: str
    title: str
    text: str
    act_id: str
    act_name: str
    year: int
    jurisdiction: str
    keywords: tuple[str, ...]
    source_url: str
    gazette_ref: str


@dataclass(frozen=True)
class PrecedentJudgment:
    judgment_id: str
    citation: str
    case_name: str
    court: str
    date: str
    bench: str
    relevant_acts: tuple[str, ...]
    sections_interpreted: tuple[str, ...]
    issue: str
    holding: str
    quote: str
    ratio_decidendi: str
    source_url: str


@dataclass(frozen=True)
class EnactmentMetadata:
    act_id: str
    act_number: str
    title: str
    year: int
    enactment_date: str
    ministry: str
    jurisdiction: str
    total_sections: int
    summary: str
    source_url: str


@dataclass(frozen=True)
class StatutoryAuditFinding:
    clause_category: str
    contract_quote: str
    contract_page: int
    statute: str
    section: str
    legal_rule: str
    compliance_status: str  # "COMPLIANT" | "CAUTION" | "VOID_UNENFORCEABLE"
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH"
    statutory_citation: str
    relevant_precedent: str
    explanation: str


# ==============================================================================
# 1. Primary Legislation Dataset (Open India Law Schema)
# ==============================================================================

ENACTMENTS: dict[str, EnactmentMetadata] = {
    "central_1872_9": EnactmentMetadata(
        act_id="central_1872_9",
        act_number="Act No. 9 of 1872",
        title="The Indian Contract Act, 1872",
        year=1872,
        enactment_date="1872-04-25",
        ministry="Ministry of Law and Justice",
        jurisdiction="Central",
        total_sections=238,
        summary="Defines and amends laws relating to contracts, offer, acceptance, consideration, void agreements, contingent contracts, quasi-contracts, breach, damages, indemnity and guarantee.",
        source_url="https://www.indiacode.nic.in/handle/123456789/2187",
    ),
    "central_1882_4": EnactmentMetadata(
        act_id="central_1882_4",
        act_number="Act No. 4 of 1882",
        title="The Transfer of Property Act, 1882",
        year=1882,
        enactment_date="1882-02-17",
        ministry="Ministry of Law and Justice",
        jurisdiction="Central",
        total_sections=137,
        summary="Regulates the transfer of property by act of parties, including sales, mortgages, leases of immovable property, exchanges, gifts and actionable claims.",
        source_url="https://www.indiacode.nic.in/handle/123456789/2338",
    ),
    "central_1882_5": EnactmentMetadata(
        act_id="central_1882_5",
        act_number="Act No. 5 of 1882",
        title="The Indian Easements Act, 1882",
        year=1882,
        enactment_date="1882-02-17",
        ministry="Ministry of Law and Justice",
        jurisdiction="Central",
        total_sections=64,
        summary="Governs easements and licenses. Section 52 defines a License as distinct from a lease, and Section 60 sets out when licenses are revocable or irrevocable.",
        source_url="https://www.indiacode.nic.in/handle/123456789/2340",
    ),
    "central_1908_16": EnactmentMetadata(
        act_id="central_1908_16",
        act_number="Act No. 16 of 1908",
        title="The Registration Act, 1908",
        year=1908,
        enactment_date="1908-12-18",
        ministry="Ministry of Rural Development",
        jurisdiction="Central",
        total_sections=93,
        summary="Consolidates enactments relating to the registration of documents. Section 17 makes registration compulsory for leases exceeding one year; Section 49 states effects of non-registration.",
        source_url="https://www.indiacode.nic.in/handle/123456789/1386",
    ),
    "central_1996_26": EnactmentMetadata(
        act_id="central_1996_26",
        act_number="Act No. 26 of 1996",
        title="The Arbitration and Conciliation Act, 1996",
        year=1996,
        enactment_date="1996-08-16",
        ministry="Ministry of Law and Justice",
        jurisdiction="Central",
        total_sections=86,
        summary="Consolidates and amends laws relating to domestic arbitration, international commercial arbitration and enforcement of foreign arbitral awards.",
        source_url="https://www.indiacode.nic.in/handle/123456789/1978",
    ),
    "state_mh_1999_18": EnactmentMetadata(
        act_id="state_mh_1999_18",
        act_number="Maharashtra Act No. 18 of 2000",
        title="The Maharashtra Rent Control Act, 1999",
        year=1999,
        enactment_date="2000-03-10",
        ministry="Government of Maharashtra",
        jurisdiction="Maharashtra",
        total_sections=60,
        summary="Regulates rent and eviction in Maharashtra. Section 24 provides summary eviction on expiry of leave and license, and Section 55 makes registration of agreements mandatory in writing.",
        source_url="https://www.indiacode.nic.in/handle/123456789/13768",
    ),
    "central_2016_16": EnactmentMetadata(
        act_id="central_2016_16",
        act_number="Act No. 16 of 2016",
        title="Real Estate (Regulation and Development) Act, 2016 (RERA)",
        year=2016,
        enactment_date="2016-03-25",
        ministry="Ministry of Housing and Urban Affairs",
        jurisdiction="Central",
        total_sections=92,
        summary="Protects the interest of consumers in real estate, establishes Real Estate Regulatory Authority (RERA) and Appellate Tribunal for speedy dispute redressal.",
        source_url="https://www.indiacode.nic.in/handle/123456789/2158",
    ),
    "central_2019_35": EnactmentMetadata(
        act_id="central_2019_35",
        act_number="Act No. 35 of 2019",
        title="The Consumer Protection Act, 2019",
        year=2019,
        enactment_date="2019-08-09",
        ministry="Ministry of Consumer Affairs, Food and Public Distribution",
        jurisdiction="Central",
        total_sections=107,
        summary="Protects consumer interests against unfair trade practices, unfair contracts, product liability and establishes Consumer Commissions.",
        source_url="https://www.indiacode.nic.in/handle/123456789/15256",
    ),
    "central_1963_47": EnactmentMetadata(
        act_id="central_1963_47",
        act_number="Act No. 47 of 1963",
        title="The Specific Relief Act, 1963",
        year=1963,
        enactment_date="1963-12-13",
        ministry="Ministry of Law and Justice",
        jurisdiction="Central",
        total_sections=44,
        summary="Defines and amends the law relating to certain kinds of specific relief, specific performance of contracts, injunctions, and declaratory decrees.",
        source_url="https://www.indiacode.nic.in/handle/123456789/1583",
    ),
    "central_2000_21": EnactmentMetadata(
        act_id="central_2000_21",
        act_number="Act No. 21 of 2000",
        title="The Information Technology Act, 2000",
        year=2000,
        enactment_date="2000-06-09",
        ministry="Ministry of Electronics and Information Technology",
        jurisdiction="Central",
        total_sections=94,
        summary="Provides legal recognition for transactions carried out by means of electronic data interchange and electronic commerce, including digital signatures and electronic contracts.",
        source_url="https://www.indiacode.nic.in/handle/123456789/1999",
    ),
    "central_1899_2": EnactmentMetadata(
        act_id="central_1899_2",
        act_number="Act No. 2 of 1899",
        title="The Indian Stamp Act, 1899",
        year=1899,
        enactment_date="1899-01-27",
        ministry="Ministry of Finance",
        jurisdiction="Central",
        total_sections=79,
        summary="Consolidates and amends the law relating to stamps payable on instruments. Section 35 renders unstamped instruments inadmissible in evidence.",
        source_url="https://www.indiacode.nic.in/handle/123456789/2337",
    ),
    "central_2015_4": EnactmentMetadata(
        act_id="central_2015_4",
        act_number="Act No. 4 of 2016",
        title="The Commercial Courts Act, 2015",
        year=2015,
        enactment_date="2015-12-31",
        ministry="Ministry of Law and Justice",
        jurisdiction="Central",
        total_sections=23,
        summary="Provides for the constitution of Commercial Courts, Commercial Appellate Courts for speedy adjudication of commercial disputes of specified value.",
        source_url="https://www.indiacode.nic.in/handle/123456789/2155",
    ),
}

STATUTORY_SECTIONS: tuple[StatutorySection, ...] = (
    # --- Indian Contract Act, 1872 ---
    StatutorySection(
        section_id="ica_sec_10",
        section_number="Section 10",
        title="What agreements are contracts",
        text="All agreements are contracts if they are made by the free consent of parties competent to contract, for a lawful consideration and with a lawful object, and are not hereby expressly declared to be void.",
        act_id="central_1872_9",
        act_name="The Indian Contract Act, 1872",
        year=1872,
        jurisdiction="Central",
        keywords=("contract", "free consent", "competency", "lawful consideration", "validity"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2187",
        gazette_ref="Gazette of India, 1872, Pt. IV, p. 1",
    ),
    StatutorySection(
        section_id="ica_sec_23",
        section_number="Section 23",
        title="What considerations and objects are lawful, and what not",
        text="The consideration or object of an agreement is lawful, unless it is forbidden by law; or is of such a nature that, if permitted, it would defeat the provisions of any law; or is fraudulent; or involves or implies injury to the person or property of another; or the Court regards it as immoral, or opposed to public policy. In each of these cases, the consideration or object of an agreement is said to be unlawful. Every agreement of which the object or consideration is unlawful is void.",
        act_id="central_1872_9",
        act_name="The Indian Contract Act, 1872",
        year=1872,
        jurisdiction="Central",
        keywords=("public policy", "unlawful consideration", "forbidden by law", "void agreement", "fraudulent"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2187",
        gazette_ref="Gazette of India, 1872, Pt. IV, p. 1",
    ),
    StatutorySection(
        section_id="ica_sec_27",
        section_number="Section 27",
        title="Agreement in restraint of trade, void",
        text="Every agreement by which any one is restrained from exercising a lawful profession, trade or business of any kind, is to that extent void. Exception 1: One who sells the goodwill of a business may agree with the buyer to refrain from carrying on a similar business, within specified local limits, so long as the buyer, or any person deriving title to the goodwill from him, carries on a like business therein, provided that such limits appear to the Court reasonable.",
        act_id="central_1872_9",
        act_name="The Indian Contract Act, 1872",
        year=1872,
        jurisdiction="Central",
        keywords=("non-compete", "restraint of trade", "void", "exclusivity", "post-termination"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2187",
        gazette_ref="Gazette of India, 1872, Pt. IV, p. 1",
    ),
    StatutorySection(
        section_id="ica_sec_28",
        section_number="Section 28",
        title="Agreements in restraint of legal proceedings, void",
        text="Every agreement by which any party thereto is restricted absolutely from enforcing his rights under or in respect of any contract, by the usual legal proceedings in the ordinary tribunals, or which limits the time within which he may thus enforce his rights; or which extinguishes the rights of any party thereto, or discharges any party thereto, from any liability, under or in respect of any contract on the expiry of a specified period so as to restrict any party from enforcing his rights, is void to that extent. Exception: Saving of contract to refer to arbitration dispute that may arise.",
        act_id="central_1872_9",
        act_name="The Indian Contract Act, 1872",
        year=1872,
        jurisdiction="Central",
        keywords=("covenant not to sue", "restraint of legal proceedings", "limitation period", "arbitration exception"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2187",
        gazette_ref="Gazette of India, 1872, Pt. IV, p. 1",
    ),
    StatutorySection(
        section_id="ica_sec_56",
        section_number="Section 56",
        title="Agreement to do impossible act",
        text="An agreement to do an act impossible in itself is void. A contract to do an act which, after the contract is made, becomes impossible, or, by reason of some event which the promisor could not prevent, unlawful, becomes void when the act becomes impossible or unlawful.",
        act_id="central_1872_9",
        act_name="The Indian Contract Act, 1872",
        year=1872,
        jurisdiction="Central",
        keywords=("force majeure", "doctrine of frustration", "impossibility", "discharge"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2187",
        gazette_ref="Gazette of India, 1872, Pt. IV, p. 1",
    ),
    StatutorySection(
        section_id="ica_sec_73",
        section_number="Section 73",
        title="Compensation for loss or damage caused by breach of contract",
        text="When a contract has been broken, the party who suffers by such breach is entitled to receive, from the party who has broken the contract, compensation for any loss or damage caused to him thereby, which naturally arose in the usual course of things from such breach, or which the parties knew, when they made the contract, to be likely to result from the breach of it. Such compensation is not to be given for any remote and indirect loss or damage sustained by reason of the breach.",
        act_id="central_1872_9",
        act_name="The Indian Contract Act, 1872",
        year=1872,
        jurisdiction="Central",
        keywords=("damages", "breach", "consequential loss", "indirect loss", "remoteness"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2187",
        gazette_ref="Gazette of India, 1872, Pt. IV, p. 1",
    ),
    StatutorySection(
        section_id="ica_sec_74",
        section_number="Section 74",
        title="Compensation for breach of contract where penalty stipulated for",
        text="When a contract has been broken, if a sum is named in the contract as the amount to be paid in case of such breach, or if the contract contains any other stipulation by way of penalty, the party complaining of the breach is entitled, whether or not actual damage or loss is proved to have been caused thereby, to receive from the party who has broken the contract reasonable compensation not exceeding the amount so named or, as the case may be, the penalty stipulated for.",
        act_id="central_1872_9",
        act_name="The Indian Contract Act, 1872",
        year=1872,
        jurisdiction="Central",
        keywords=("liquidated damages", "penalty", "security deposit forfeiture", "lock-in compensation", "cap"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2187",
        gazette_ref="Gazette of India, 1872, Pt. IV, p. 1",
    ),

    # --- Transfer of Property Act, 1882 ---
    StatutorySection(
        section_id="tpa_sec_105",
        section_number="Section 105",
        title="Lease defined",
        text="A lease of immovable property is a transfer of a right to enjoy such property, made for a certain time, express or implied, or in perpetuity, in consideration of a price paid or promised, or of money, a share of crops, service or any other thing of value, to be rendered periodically or on specified occasions to the transferor by the transferee, who accepts the transfer on such terms. The transferor is called the lessor, the transferee is called the lessee, the price is called the premium, and the money, share, service or other thing to be so rendered is called the rent.",
        act_id="central_1882_4",
        act_name="The Transfer of Property Act, 1882",
        year=1882,
        jurisdiction="Central",
        keywords=("lease", "lessor", "lessee", "rent", "premium", "interest in property"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2338",
        gazette_ref="Gazette of India, 1882, Pt. IV, p. 2",
    ),
    StatutorySection(
        section_id="tpa_sec_106",
        section_number="Section 106",
        title="Duration of certain leases in absence of written contract or local usage",
        text="In the absence of a contract or local law or usage to the contrary, a lease of immovable property for agricultural or manufacturing purposes shall be deemed to be a lease from year to year, terminable, on the part of either lessor or lessee, by six months' notice; and a lease of immovable property for any other purpose shall be deemed to be a lease from month to month, terminable, on the part of either lessor or lessee, by fifteen days' notice.",
        act_id="central_1882_4",
        act_name="The Transfer of Property Act, 1882",
        year=1882,
        jurisdiction="Central",
        keywords=("notice period", "termination", "month to month", "fifteen days notice"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2338",
        gazette_ref="Gazette of India, 1882, Pt. IV, p. 2",
    ),
    StatutorySection(
        section_id="tpa_sec_108",
        section_number="Section 108",
        title="Rights and liabilities of lessor and lessee",
        text="In the absence of a contract or local usage to the contrary: Lessor is bound to disclose latent material defects in the property; on request of lessee, lessor is bound to put him in possession; lessor shall be deemed to contract with lessee that if lessee pays rent he may hold property without interruption (quiet enjoyment). Lessee is bound to pay rent; keep property in good repair; not commit waste; restore property on determination.",
        act_id="central_1882_4",
        act_name="The Transfer of Property Act, 1882",
        year=1882,
        jurisdiction="Central",
        keywords=("quiet enjoyment", "repairs", "waste", "possession", "latent defects"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2338",
        gazette_ref="Gazette of India, 1882, Pt. IV, p. 2",
    ),
    StatutorySection(
        section_id="tpa_sec_111",
        section_number="Section 111",
        title="Determination of lease",
        text="A lease of immovable property determines: (a) by efflux of the time limited thereby; (b) where such time is limited conditionally on the happening of some event, by the happening of such event; (c) by express surrender; (d) by implied surrender; (e) by forfeiture for breach of express condition or denial of title; (f) on expiration of a notice to determine the lease, or to quit.",
        act_id="central_1882_4",
        act_name="The Transfer of Property Act, 1882",
        year=1882,
        jurisdiction="Central",
        keywords=("determination", "termination of lease", "surrender", "forfeiture", "expiry"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2338",
        gazette_ref="Gazette of India, 1882, Pt. IV, p. 2",
    ),

    # --- Indian Easements Act, 1882 ---
    StatutorySection(
        section_id="iea_sec_52",
        section_number="Section 52",
        title="License defined",
        text="Where one person grants to another, or to a definite number of other persons, a right to do, or continue to do, in or upon the immovable property of the grantor, something which would, in the absence of such right, be unlawful, and such right does not amount to an easement or an interest in the property, the right is called a license.",
        act_id="central_1882_5",
        act_name="The Indian Easements Act, 1882",
        year=1882,
        jurisdiction="Central",
        keywords=("license", "leave and license", "permissive use", "no interest in land"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2340",
        gazette_ref="Gazette of India, 1882, Pt. IV, p. 3",
    ),
    StatutorySection(
        section_id="iea_sec_60",
        section_number="Section 60",
        title="License when revocable",
        text="A license may be revoked by the grantor, unless: (a) it is coupled with a transfer of property and such transfer is in force; (b) the licensee, acting upon the license, has executed a work of a permanent character and incurred expenses in the execution.",
        act_id="central_1882_5",
        act_name="The Indian Easements Act, 1882",
        year=1882,
        jurisdiction="Central",
        keywords=("irrevocable license", "revocable", "permanent work", "perpetual"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2340",
        gazette_ref="Gazette of India, 1882, Pt. IV, p. 3",
    ),

    # --- Registration Act, 1908 ---
    StatutorySection(
        section_id="reg_sec_17",
        section_number="Section 17",
        title="Documents of which registration is compulsory",
        text="The following documents shall be registered: (d) leases of immovable property from year to year, or for any term exceeding one year, or reserving a yearly rent. Note: Non-testamentary instruments transferring or creating rights in immovable property exceeding Rs. 100 in value must be registered.",
        act_id="central_1908_16",
        act_name="The Registration Act, 1908",
        year=1908,
        jurisdiction="Central",
        keywords=("registration", "compulsory registration", "leases exceeding one year", "11 months"),
        source_url="https://www.indiacode.nic.in/handle/123456789/1386",
        gazette_ref="Gazette of India, 1908, Pt. IV, p. 2",
    ),
    StatutorySection(
        section_id="reg_sec_49",
        section_number="Section 49",
        title="Effect of non-registration of documents required to be registered",
        text="No document required by section 17 or by any provision of the Transfer of Property Act, 1882 to be registered shall: (a) affect any immovable property comprised therein, or (b) confer any power to adopt, or (c) be received as evidence of any transaction affecting such property or conferring such power, unless it has been registered. Proviso: An unregistered document may be received as evidence of a contract in a suit for specific performance or as evidence of any collateral transaction not required to be effected by registered instrument.",
        act_id="central_1908_16",
        act_name="The Registration Act, 1908",
        year=1908,
        jurisdiction="Central",
        keywords=("unregistered", "inadmissible in evidence", "collateral purpose", "unenforceable"),
        source_url="https://www.indiacode.nic.in/handle/123456789/1386",
        gazette_ref="Gazette of India, 1908, Pt. IV, p. 2",
    ),

    # --- Maharashtra Rent Control Act, 1999 ---
    StatutorySection(
        section_id="mrca_sec_24",
        section_number="Section 24",
        title="Landlord entitled to recover possession of premises given on licence on expiry",
        text="Notwithstanding anything contained in this Act, a licensee in possession or occupation of premises given to him on licence for residence shall deliver possession of such premises to the landlord on expiry of the period of licence; and on the failure of the licensee to so deliver the possession of the licensed premises, a landlord shall be entitled to recover possession of such premises by making an application to the Competent Authority; and the Competent Authority, on being satisfied, shall make an order for eviction.",
        act_id="state_mh_1999_18",
        act_name="The Maharashtra Rent Control Act, 1999",
        year=1999,
        jurisdiction="Maharashtra",
        keywords=("eviction", "competent authority", "leave and license", "summary recovery", "damages"),
        source_url="https://bombayhighcourt.nic.in/libweb/acts/2000.18.pdf",
        gazette_ref="Maharashtra Government Gazette, Pt. IV, 2000",
    ),
    StatutorySection(
        section_id="mrca_sec_55",
        section_number="Section 55",
        title="Tenancy agreement to be compulsorily in writing and registered",
        text="Notwithstanding anything contained in this Act or any other law for the time being in force, any agreement for a leave and licence or letting of any premises, entered into between the landlord and the tenant or the licensee, as the case may be, after the commencement of this Act, shall be in writing and shall be registered under the Registration Act, 1908. The responsibility of getting such agreement registered shall be on the landlord.",
        act_id="state_mh_1999_18",
        act_name="The Maharashtra Rent Control Act, 1999",
        year=1999,
        jurisdiction="Maharashtra",
        keywords=("mandatory registration", "leave and license", "landlord duty", "writing requirement"),
        source_url="https://bombayhighcourt.nic.in/libweb/acts/2000.18.pdf",
        gazette_ref="Maharashtra Government Gazette, Pt. IV, 2000",
    ),

    # --- Transfer of Property Act, 1882 (Leases How Made) ---
    StatutorySection(
        section_id="tpa_sec_107",
        section_number="Section 107",
        title="Leases how made",
        text="A lease of immovable property from year to year, or for any term exceeding one year or reserving a yearly rent, can be made only by a registered instrument. All other leases of immovable property may be made either by a registered instrument or by oral agreement accompanied by delivery of possession.",
        act_id="central_1882_4",
        act_name="The Transfer of Property Act, 1882",
        year=1882,
        jurisdiction="Central",
        keywords=("lease execution", "registered instrument", "exceeding one year", "oral agreement"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2338",
        gazette_ref="Gazette of India, 1882, Pt. IV, p. 2",
    ),

    # --- Specific Relief Act, 1963 ---
    StatutorySection(
        section_id="sra_sec_10",
        section_number="Section 10",
        title="Specific performance in respect of contracts",
        text="The specific performance of a contract shall be enforced by the court subject to the provisions contained in sub-section (2) of section 11, section 14 and section 16. (Post-2018 amendment: specific performance is now mandatory rather than discretionary, subject to statutory exceptions).",
        act_id="central_1963_47",
        act_name="The Specific Relief Act, 1963",
        year=1963,
        jurisdiction="Central",
        keywords=("specific performance", "enforcement of contract", "breach", "remedy"),
        source_url="https://www.indiacode.nic.in/handle/123456789/1583",
        gazette_ref="Gazette of India, 1963, Pt. II, Sec. 1, p. 649",
    ),

    # --- Information Technology Act, 2000 ---
    StatutorySection(
        section_id="ita_sec_10a",
        section_number="Section 10A",
        title="Validity of contracts formed through electronic means",
        text="Where in a contract formation, the communication of proposals, the acceptance of proposals, the revocation of proposals and acceptances, as the case may be, are expressed in electronic form or by means of an electronic record, such contract shall not be deemed to be unenforceable solely on the ground that such electronic form or means was used for that purpose.",
        act_id="central_2000_21",
        act_name="The Information Technology Act, 2000",
        year=2000,
        jurisdiction="Central",
        keywords=("electronic contracts", "e-signatures", "validity", "digital agreement"),
        source_url="https://www.indiacode.nic.in/handle/123456789/1999",
        gazette_ref="Gazette of India, 2000, Ext., Pt. II, Sec. 1",
    ),

    # --- Arbitration and Conciliation Act, 1996 ---
    StatutorySection(
        section_id="arb_sec_7",
        section_number="Section 7",
        title="Arbitration agreement",
        text="In this Part, 'arbitration agreement' means an agreement by the parties to submit to arbitration all or certain disputes which have arisen or which may arise between them in respect of a defined legal relationship, whether contractual or not. An arbitration agreement shall be in writing.",
        act_id="central_1996_26",
        act_name="The Arbitration and Conciliation Act, 1996",
        year=1996,
        jurisdiction="Central",
        keywords=("arbitration agreement", "dispute resolution", "in writing", "arbitral tribunal"),
        source_url="https://www.indiacode.nic.in/handle/123456789/1978",
        gazette_ref="Gazette of India, 1996, Ext., Pt. II, Sec. 1",
    ),

    # --- Indian Stamp Act, 1899 ---
    StatutorySection(
        section_id="stamp_sec_35",
        section_number="Section 35",
        title="Instruments not duly stamped inadmissible in evidence, etc.",
        text="No instrument chargeable with duty shall be admitted in evidence for any purpose by any person having by law or consent of parties authority to receive evidence, or shall be acted upon, registered or authenticated by any such person or by any public officer, unless such instrument is duly stamped. Proviso allows impounding and payment of penalty.",
        act_id="central_1899_2",
        act_name="The Indian Stamp Act, 1899",
        year=1899,
        jurisdiction="Central",
        keywords=("stamp duty", "inadmissible in evidence", "impounding", "deficit duty"),
        source_url="https://www.indiacode.nic.in/handle/123456789/2337",
        gazette_ref="Gazette of India, 1899, Pt. IV, p. 1",
    ),
)


# ==============================================================================
# 2. Supreme Court & High Court Precedent Library (Open India Law)
# ==============================================================================

PRECEDENT_JUDGMENTS: tuple[PrecedentJudgment, ...] = (
    PrecedentJudgment(
        judgment_id="sc_2006_zaheer_khan",
        citation="(2006) 4 SCC 227",
        case_name="Percept D'Mark (India) (P) Ltd. v. Zaheer Khan & Anr.",
        court="Supreme Court of India",
        date="2006-03-22",
        bench="Y.K. Sabharwal, C.J., C.K. Thakker, R.V. Raveendran, JJ.",
        relevant_acts=("The Indian Contract Act, 1872",),
        sections_interpreted=("Section 27",),
        issue="Whether a post-contractual restrictive covenant or right of first refusal restraining a player from contracting with others after expiry of contract violates Section 27.",
        holding="Under Section 27 of the Contract Act, any restrictive covenant extending beyond the term of the agreement is void in toto. The doctrine of restraint of trade does not apply during the subsistence of the contract, but post-termination restraints are void and unenforceable.",
        quote="The doctrine of restraint of trade does not apply during the continuance of the contract of employment; it applies only when the contract comes to an end... A post-contractual covenant in restraint of trade is void and of no effect under Section 27.",
        ratio_decidendi="Under Indian law, Section 27 does not permit reasonableness tests for post-contractual non-compete clauses. Any restraint after contract termination is void.",
        source_url="https://main.sci.gov.in/judgment",
    ),
    PrecedentJudgment(
        judgment_id="sc_1967_niranjan_golikari",
        citation="AIR 1967 SC 1098",
        case_name="Niranjan Shankar Golikari v. Century Spg. & Mfg. Co. Ltd.",
        court="Supreme Court of India",
        date="1967-01-17",
        bench="J.M. Shelat, V. Bhargava, C.A. Vaidialingam, JJ.",
        relevant_acts=("The Indian Contract Act, 1872",),
        sections_interpreted=("Section 27",),
        issue="Whether a negative covenant restraining an employee during the period of employment from serving elsewhere violates Section 27.",
        holding="A negative covenant that an employee shall not engage in another business or employment during the period of his employment is valid and does not violate Section 27.",
        quote="Considerations against restrictive covenants are different in cases where the restriction is to apply during the period after the termination of the contract than those in cases where it applies during the period of the contract.",
        ratio_decidendi="Negative covenants operating during the active term of employment are valid to prevent disclosure of trade secrets, but cannot extend past the term.",
        source_url="https://main.sci.gov.in/judgment",
    ),
    PrecedentJudgment(
        judgment_id="sc_2015_kailash_nath",
        citation="(2015) 4 SCC 136",
        case_name="Kailash Nath Associates v. Delhi Development Authority",
        court="Supreme Court of India",
        date="2015-01-09",
        bench="Ranjan Gogoi, R.F. Nariman, JJ.",
        relevant_acts=("The Indian Contract Act, 1872",),
        sections_interpreted=("Section 74", "Section 73"),
        issue="Whether earnest money or security deposits can be automatically forfeited as liquidated damages without proof of actual legal injury or loss.",
        holding="Under Section 74, compensation can only be awarded for damage or loss actually proved to have been caused. Where it is possible to prove actual loss, proof of such loss is not dispensed with. Forfeiture of deposit without proving loss or reasonable estimate is illegal.",
        quote="Where it is possible to prove actual damage or loss, such proof is not dispensed with. It is only in cases where damage or loss is difficult or impossible to prove that the liquidated amount named in the contract may be taken as reasonable measure.",
        ratio_decidendi="Section 74 does not permit a party to make a windfall profit by forfeiting security deposits or demanding penalties without proving actual legal injury.",
        source_url="https://main.sci.gov.in/judgment",
    ),
    PrecedentJudgment(
        judgment_id="sc_1959_associated_hotels",
        citation="AIR 1959 SC 1262",
        case_name="Associated Hotels of India Ltd. v. R.N. Kapoor",
        court="Supreme Court of India",
        date="1959-05-19",
        bench="A.K. Sarkar, K. Subba Rao, J.R. Mudholkar, JJ.",
        relevant_acts=("The Transfer of Property Act, 1882", "The Indian Easements Act, 1882"),
        sections_interpreted=("Section 105 (TPA)", "Section 52 (Easements Act)"),
        issue="Distinction between Lease and Leave & License agreements for commercial and residential premises.",
        holding="If a document gives only a right to use the property in a particular way while legal possession remains with the owner, it is a license. If it transfers an exclusive interest in the property with exclusive possession, it is a lease regardless of what label the parties put on it.",
        quote="The substance of the document must be preferred to the form. If the effect of the instrument is to give the holder an exclusive right of occupation of the land, it is a lease.",
        ratio_decidendi="Exclusive possession is the prima facie test of a lease as opposed to a license. The court looks at the substance, not the drafting label.",
        source_url="https://main.sci.gov.in/judgment",
    ),
    PrecedentJudgment(
        judgment_id="sc_2000_anthony_ittoop",
        citation="(2000) 6 SCC 394",
        case_name="Anthony v. K.C. Ittoop & Sons & Ors.",
        court="Supreme Court of India",
        date="2000-08-18",
        bench="K.T. Thomas, R.P. Sethi, JJ.",
        relevant_acts=("The Registration Act, 1908", "The Transfer of Property Act, 1882"),
        sections_interpreted=("Section 17 (Reg)", "Section 49 (Reg)", "Section 106 (TPA)"),
        issue="What is the legal effect of an unregistered lease deed for more than one year where possession has been given and rent paid?",
        holding="Although an unregistered lease for more than one year cannot create a valid long-term lease under Section 17 & 49 of the Registration Act, acceptance of rent creates a month-to-month tenancy under Section 106 of the Transfer of Property Act, terminable with 15 days' notice.",
        quote="If a lease deed for more than one year is unregistered, it is inadmissible to prove the duration of the lease. However, the jural relationship of landlord and tenant arises and it is treated as a month-to-month tenancy.",
        ratio_decidendi="Unregistered agreements for terms > 11 months cannot enforce lock-ins or multi-year terms; they degenerate into month-to-month tenancies with 15-day termination rights.",
        source_url="https://main.sci.gov.in/judgment",
    ),
    PrecedentJudgment(
        judgment_id="sc_2021_vidya_drolia",
        citation="(2021) 2 SCC 1",
        case_name="Vidya Drolia and Ors. v. Durga Trading Corporation",
        court="Supreme Court of India",
        date="2020-12-14",
        bench="N.V. Ramana, Sanjiv Khanna, Krishna Murari, JJ.",
        relevant_acts=("The Arbitration and Conciliation Act, 1996", "The Transfer of Property Act, 1882"),
        sections_interpreted=("Section 8 (Arb)", "Section 11 (Arb)", "Section 111 (TPA)"),
        issue="Whether landlord-tenant disputes governed by the Transfer of Property Act are arbitrable.",
        holding="Landlord-tenant disputes under the Transfer of Property Act are arbitrable as they deal with rights in personam. However, disputes covered by special Rent Control Acts where exclusive jurisdiction is conferred on special statutory forums (e.g. Rent Controller / Competent Authority) are non-arbitrable.",
        quote="Landlord-tenant disputes are arbitrable as the Transfer of Property Act does not forbid arbitration. But where a specific rent control statute grants exclusive jurisdiction to a rent court, arbitration is barred.",
        ratio_decidendi="Arbitration clauses in lease/license deeds are valid under general law, but cannot bypass statutory tribunals where Rent Control Acts apply.",
        source_url="https://main.sci.gov.in/judgment",
    ),
)


# ==============================================================================
# 3. Statutory Compliance Evaluator (Cross-referencing Contracts with Indian Law)
# ==============================================================================

def audit_contract_compliance(document_text: str) -> list[StatutoryAuditFinding]:
    """Evaluates an uploaded contract against Indian primary law statutes and case law.

    Detects common high-risk clauses in Indian contracts and leave-and-license agreements:
    1. Restraint of trade / Non-compete clauses (Section 27 Contract Act)
    2. Restraint of legal proceedings / Covenant not to sue (Section 28 Contract Act)
    3. Exorbitant liquidated damages / deposit forfeiture (Section 74 Contract Act)
    4. Duration exceeding 11 months without registration (Registration Act Sec 17 & 49)
    5. Irrevocable or perpetual licenses (Easements Act Sec 60)
    6. Jurisdiction & Arbitration clauses (Arbitration Act Sec 7 & Rent Control S.24)
    """
    findings: list[StatutoryAuditFinding] = []

    # 1. Non-compete / Restraint of Trade
    non_compete_match = re.search(
        r"(?:shall\s+not\s+(?:directly\s+or\s+indirectly\s+)?(?:engage\s+in|compete|carry\s+on|solicit)[^.\n]{10,180}\b(?:after\s+(?:the\s+)?termination|post-termination|for\s+a\s+period\s+of\s+\d+\s+(?:months?|years?))\b|"
        r"\b(?:non-compete|restraint\s+of\s+trade)[^.\n]{10,160})",
        document_text,
        re.IGNORECASE,
    )
    if non_compete_match:
        findings.append(
            StatutoryAuditFinding(
                clause_category="Non-Compete / Restraint of Trade",
                contract_quote=non_compete_match.group(0).strip(),
                contract_page=1,
                statute="The Indian Contract Act, 1872",
                section="Section 27",
                legal_rule="Agreements in restraint of trade, profession or business are void in toto under Indian law. Unlike English or US law, no test of reasonableness applies to post-termination non-compete covenants.",
                compliance_status="VOID_UNENFORCEABLE",
                risk_level="HIGH",
                statutory_citation="Section 27, The Indian Contract Act, 1872 (Act No. 9 of 1872)",
                relevant_precedent="Percept D'Mark v. Zaheer Khan, (2006) 4 SCC 227 (Supreme Court of India)",
                explanation="Under Section 27, any covenant restraining an individual from exercising a lawful trade, profession, or business post-termination is void as contrary to Indian public policy.",
            )
        )

    # 2. Covenant Not to Sue / Restraint of Legal Proceedings
    sue_match = re.search(
        r"(?:covenants?\s+not\s+to\s+sue|waives?\s+(?:all\s+)?rights?\s+to\s+(?:sue|initiate\s+litigation|bring\s+claims?)|"
        r"shall\s+not\s+initiate\s+any\s+(?:legal\s+proceedings|litigation)[^.\n]{0,80})",
        document_text,
        re.IGNORECASE,
    )
    if sue_match:
        findings.append(
            StatutoryAuditFinding(
                clause_category="Covenant Not to Sue / Restraint of Proceedings",
                contract_quote=sue_match.group(0).strip(),
                contract_page=1,
                statute="The Indian Contract Act, 1872",
                section="Section 28",
                legal_rule="Agreements restricting absolutely any party from enforcing rights in ordinary tribunals or shortening the statutory limitation period are void.",
                compliance_status="VOID_UNENFORCEABLE",
                risk_level="HIGH",
                statutory_citation="Section 28, The Indian Contract Act, 1872 (Act No. 9 of 1872)",
                relevant_precedent="National Insurance Co. Ltd. v. Sujir Ganesh Nayak & Co., AIR 1997 SC 2049",
                explanation="Section 28 prohibits contracts that extinguish rights or bar legal remedy. An absolute covenant not to sue is unenforceable under Indian law, though arbitration agreements are saved.",
            )
        )

    # 3. Forfeiture of Entire Security Deposit / Penalties
    forfeit_match = re.search(
        r"(?:forfeit\s+(?:the\s+)?(?:entire|all)\s+(?:security\s+)?deposit|"
        r"(?:entire\s+)?deposit\s+(?:of\s+[\w\s.,]+)?shall\s+be\s+forfeited|"
        r"forfeited\s+as\s+penalty|penalty\s+of\s+rs|"
        r"liquidated\s+damages\s+equal\s+to\s+(?:the\s+)?remaining\s+lock-in)",
        document_text,
        re.IGNORECASE,
    )
    if forfeit_match:
        findings.append(
            StatutoryAuditFinding(
                clause_category="Security Deposit Forfeiture / Penalty",
                contract_quote=forfeit_match.group(0).strip(),
                contract_page=1,
                statute="The Indian Contract Act, 1872",
                section="Section 74",
                legal_rule="Stipulations by way of penalty or automatic total forfeiture are restricted to reasonable compensation. A party cannot forfeit a deposit without proving actual loss sustained.",
                compliance_status="CAUTION",
                risk_level="MEDIUM",
                statutory_citation="Section 74, The Indian Contract Act, 1872",
                relevant_precedent="Kailash Nath Associates v. DDA, (2015) 4 SCC 136; Fateh Chand v. Balkishan Dass, AIR 1963 SC 1405",
                explanation="Under Supreme Court precedent, security deposit forfeiture clauses cannot operate as arbitrary penalties. The lessor or party claiming damages is entitled only to reasonable compensation for actual loss proved.",
            )
        )

    # 4. Lease Duration & Compulsory Registration
    term_match = re.search(
        r"\b(?:period\s+(?:of|is|shall\s+be)|(?:lease\s+)?term\s+(?:of|is|shall\s+be(?:\s+for)?|is\s+for)|duration\s+(?:of|is))\s+"
        r"(?:(\d+)\s+(?:months?|years?)|(?:eleven|11|twelve|12|twenty-four|24|thirty-six|36)\s+months?)\b",
        document_text,
        re.IGNORECASE,
    )
    if term_match:
        term_str = term_match.group(0).lower()
        is_over_11_months = any(w in term_str for w in ("year", "12 month", "24 month", "36 month", "two year", "three year"))
        if is_over_11_months:
            findings.append(
                StatutoryAuditFinding(
                    clause_category="Term Exceeding 11 Months / Compulsory Registration",
                    contract_quote=term_match.group(0).strip(),
                    contract_page=1,
                    statute="The Registration Act, 1908",
                    section="Section 17(1)(d)",
                    legal_rule="Leases of immovable property exceeding 11 months (or for any term exceeding one year) must be registered with the sub-registrar. Unregistered multi-year leases are inadmissible in evidence under Section 49.",
                    compliance_status="CAUTION",
                    risk_level="HIGH",
                    statutory_citation="Section 17(1)(d) & Section 49, The Registration Act, 1908 (Act No. 16 of 1908)",
                    relevant_precedent="Anthony v. K.C. Ittoop & Sons, (2000) 6 SCC 394 (Supreme Court of India)",
                    explanation="If this agreement is executed for more than 11 months without payment of stamp duty and registration, the long-term tenure and lock-in covenants are legally unenforceable; the tenancy is reduced to month-to-month under Section 106 TPA.",
                )
            )
        else:
            findings.append(
                StatutoryAuditFinding(
                    clause_category="11-Month Leave & License Tenure",
                    contract_quote=term_match.group(0).strip(),
                    contract_page=1,
                    statute="The Registration Act, 1908 & Maharashtra Rent Control Act, 1999",
                    section="Section 17 (Reg Act) & Section 55 (MRCA)",
                    legal_rule="Tenure under 12 months avoids Section 17(1)(d) central lease registration, but Maharashtra state law (Section 55 MRCA) still mandates registration in writing for all leave & license deeds.",
                    compliance_status="COMPLIANT",
                    risk_level="LOW",
                    statutory_citation="Section 17, Registration Act, 1908 & Section 55, Maharashtra Rent Control Act, 1999",
                    relevant_precedent="Associated Hotels of India v. R.N. Kapoor, AIR 1959 SC 1262",
                    explanation="11-month structures are standard in Indian commercial practice to prevent tenancy creation under Section 105 TPA. In states like Maharashtra, online e-registration is mandatory regardless of duration.",
                )
            )

    # 5. Perpetual or Irrevocable License
    perpetual_match = re.search(
        r"(?:perpetual\s+and\s+irrevocable|irrevocable\s+(?:and\s+)?perpetual|royalty-free,\s*perpetual|perpetual\s+license|license\s+in\s+perpetuity)",
        document_text,
        re.IGNORECASE,
    )
    if perpetual_match:
        findings.append(
            StatutoryAuditFinding(
                clause_category="Perpetual / Irrevocable License Grant",
                contract_quote=perpetual_match.group(0).strip(),
                contract_page=1,
                statute="The Indian Easements Act, 1882",
                section="Section 60",
                legal_rule="Licenses are revocable at will by the grantor under Section 60 unless coupled with transfer of property or substantial permanent works executed with expense.",
                compliance_status="CAUTION",
                risk_level="MEDIUM",
                statutory_citation="Section 60, The Indian Easements Act, 1882 (Act No. 5 of 1882)",
                relevant_precedent="Ram Sarup Gupta v. Bishun Narain Inter College, (1987) 2 SCC 555",
                explanation="A bare perpetual license may be challenged as revocable by the grantor unless protected under Section 60(a) or (b) of the Easements Act.",
            )
        )

    # 6. Governing Law & Jurisdiction Clause
    law_match = re.search(
        r"(?:governed\s+by\s+(?:the\s+)?laws?\s+of\s+([A-Za-z\s]+)|jurisdiction\s+of\s+(?:the\s+)?courts?\s+(?:at|in)\s+([A-Za-z\s]+))",
        document_text,
        re.IGNORECASE,
    )
    if law_match:
        findings.append(
            StatutoryAuditFinding(
                clause_category="Governing Law & Jurisdiction",
                contract_quote=law_match.group(0).strip(),
                contract_page=1,
                statute="Code of Civil Procedure, 1908 & Indian Contract Act, 1872",
                section="Section 20 (CPC) & Section 28 (Contract Act)",
                legal_rule="Parties can agree to confer exclusive jurisdiction on one competent court having territorial/cause-of-action jurisdiction, but cannot confer jurisdiction on a court having no inherent jurisdiction.",
                compliance_status="COMPLIANT",
                risk_level="LOW",
                statutory_citation="Section 20, Code of Civil Procedure, 1908; ABC Laminart v. A.P. Agencies, (1989) 2 SCC 163",
                relevant_precedent="ABC Laminart Pvt. Ltd. v. A.P. Agencies, Salem, AIR 1989 SC 1239",
                explanation="Exclusive jurisdiction clauses are valid in India provided the chosen court has part of the cause of action or location of the property.",
            )
        )

    return findings


# ==============================================================================
# 4. Search & Query Functions for Chatbot & Library Explorer
# ==============================================================================

def search_primary_law(query: str, limit: int = 6) -> dict[str, Any]:
    """Search across Central Enactments, Sections, and Supreme Court Precedents."""
    normalized = query.lower()
    terms = set(re.findall(r"[a-z0-9]{3,}", normalized))

    matching_sections: list[dict[str, Any]] = []
    for sec in STATUTORY_SECTIONS:
        score = 0
        searchable_text = f"{sec.act_name} {sec.section_number} {sec.title} {sec.text} {' '.join(sec.keywords)}".lower()
        for term in terms:
            if term in searchable_text:
                score += 2 if term in sec.title.lower() or term in sec.section_number.lower() else 1
        if score > 0:
            matching_sections.append({"score": score, "section": asdict(sec)})

    matching_sections.sort(key=lambda x: x["score"], reverse=True)

    matching_judgments: list[dict[str, Any]] = []
    for j in PRECEDENT_JUDGMENTS:
        score = 0
        searchable_text = f"{j.case_name} {j.citation} {j.issue} {j.holding} {j.quote} {j.ratio_decidendi} {' '.join(j.sections_interpreted)}".lower()
        for term in terms:
            if term in searchable_text:
                score += 2 if term in j.case_name.lower() or term in j.citation.lower() else 1
        if score > 0:
            matching_judgments.append({"score": score, "judgment": asdict(j)})

    matching_judgments.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": query,
        "sections": [item["section"] for item in matching_sections[:limit]],
        "judgments": [item["judgment"] for item in matching_judgments[:limit]],
        "total_sections_matched": len(matching_sections),
        "total_judgments_matched": len(matching_judgments),
    }


def get_all_enactments() -> list[dict[str, Any]]:
    return [asdict(e) for e in ENACTMENTS.values()]


def get_all_judgments() -> list[dict[str, Any]]:
    return [asdict(j) for j in PRECEDENT_JUDGMENTS]


def get_all_sections() -> list[dict[str, Any]]:
    return [asdict(s) for s in STATUTORY_SECTIONS]
