📄 Software Requirement Analysis (SRA)

Project: Multi-Source Candidate Data Transformer

Version: 1.0

1. Business Problem

Eightfold ko multiple heterogeneous sources se candidate data milta hai.

Ye data

Inconsistent hota hai
Duplicate hota hai
Different formats me hota hai
Missing fields ho sakti hain
Conflicting values ho sakti hain

System ka objective hai:

One clean, canonical, trustworthy candidate profile generate karna with provenance and confidence.

2. Project Scope (Current Assignment Scope)
Structured Source (Selected)

✅ ATS JSON

Unstructured Source (Selected)

✅ Resume (PDF/DOCX)

Future Extension (Not in MVP)
Recruiter Notes
Recruiter CSV
GitHub
LinkedIn
3. Functional Requirements (FR)
FR-01

System should accept at least one structured source.

FR-02

System should accept at least one unstructured source.

FR-03

System should parse both selected sources.

FR-04

System should map heterogeneous schemas into one canonical schema.

FR-05

System should normalize

phone numbers
dates
countries
skills
FR-06

System should deduplicate repeated information.

FR-07

System should merge multiple sources into one profile.

FR-08

System should resolve conflicting values using a defined merge policy.

FR-09

System should calculate field confidence.

FR-10

System should calculate overall profile confidence.

FR-11

System should maintain provenance.

FR-12

System should validate final output.

FR-13

System should support runtime configurable output.

FR-14

System should project only requested fields.

FR-15

System should support field remapping.

FR-16

System should support configurable normalization.

FR-17

System should support configurable missing-value behavior.

FR-18

System should expose CLI.

FR-19

System should produce schema-valid JSON.

FR-20

System should support one default output schema.

FR-21

System should support one custom output schema.

4. Non Functional Requirements (NFR)
NFR-01

Deterministic

Same input

↓

Same output.

NFR-02

Explainable

Every output field explainable.

NFR-03

Traceable

Every value traceable.

NFR-04

Robust

Pipeline should never crash because of one bad source.

NFR-05

Graceful degradation.

NFR-06

Scalable

Reasonable for thousands of candidates.

NFR-07

Maintainable

Easy to modify.

NFR-08

Extensible

New parsers easily added.

NFR-09

Modular

Independent modules.

NFR-10

Reusable

Pipeline reusable.

NFR-11

Configuration driven.

NFR-12

Readable code.

NFR-13

Testable modules.

NFR-14

Professional documentation.

5. Canonical Output Requirements

Canonical profile should contain

candidate_id

full_name

emails[]

phones[]

location

links

headline

years_experience

skills[]

experience[]

education[]

provenance[]

overall_confidence
6. Normalization Requirements

Phones

↓

E.164

Dates

↓

YYYY-MM

Country

↓

ISO-3166 Alpha-2

Skills

↓

Canonical Skill Name

Emails

↓

Validated

Names

↓

Canonical formatting

7. Merge Requirements

System must

Merge

Deduplicate

Resolve conflicts

Assign confidence

Maintain provenance

Never invent data

8. Projection Requirements

Runtime config should support

Select fields

Rename fields

Normalization preferences

Confidence on/off

Provenance on/off

Missing value strategy

9. Validation Requirements

Validate

Input

Intermediate model

Output Schema

Configuration

10. Explicit Constraints

System should be

Deterministic

Explainable

Robust

Scalable

Unknown values

↓

null

Never hallucinate

Missing source

↓

No crash

11. Hidden Functional Requirements

These are not directly written but implied.

HFR-01

Independent parser layer.

HFR-02

Independent normalization layer.

HFR-03

Independent merge engine.

HFR-04

Independent confidence engine.

HFR-05

Independent projection engine.

HFR-06

Independent validation layer.

HFR-07

Internal canonical model.

HFR-08

Output projection after canonical model.

HFR-09

Support multiple emails.

HFR-10

Support multiple phones.

HFR-11

Support multiple skills.

HFR-12

Support multiple education records.

HFR-13

Support multiple experience records.

HFR-14

Parser failures isolated.

HFR-15

Pipeline continues even if one source fails.

12. Hidden Non Functional Requirements
HNFR-01

Separation of Concerns.

HNFR-02

Single Responsibility.

HNFR-03

Loose Coupling.

HNFR-04

High Cohesion.

HNFR-05

Future extensibility.

HNFR-06

Easy testing.

HNFR-07

Easy debugging.

HNFR-08

Professional folder structure.

HNFR-09

Professional README.

HNFR-10

Reproducible repository.

HNFR-11

Every design decision explainable.

HNFR-12

Technology choices justifiable.

13. Edge Cases Identified

Missing Resume

Missing ATS JSON

Malformed JSON

Corrupted PDF

Duplicate emails

Duplicate skills

Conflicting names

Conflicting company

Conflicting phone

Missing experience

Missing education

Unknown country

Invalid phone

Invalid email

Empty file

Empty config

Unknown config field

Duplicate config fields

Partial parser failure

Null values

14. # Resolved Design Decisions

RDD-01

Source Priority

ATS JSON > Resume

RDD-02

Skills Merge

Union of both sources

RDD-03

Phone Priority

ATS wins

RDD-04

Experience

Resume preferred

RDD-05

Confidence

Rule Based

RDD-06

Canonical Schema Version

1.0


15. Deliverables

One Page PDF

Public GitHub Repository

README

Sample Input

Sample Output

Tests

Demo Video

16.  # Risks

R-01
Corrupted Resume PDF

R-02
Malformed ATS JSON

R-03
Conflicting Candidate Information

R-04
Missing Mandatory Fields

R-05
Configuration Errors

R-06
Unexpected Resume Formatting

R-07
Large Resume Files


17. # Acceptance Criteria

AC-01

CLI executes successfully.

AC-02

Golden Candidate JSON generated.

AC-03

Output passes schema validation.

AC-04

Confidence score generated.

AC-05

Provenance generated.

AC-06

Projection configuration works.

AC-07

Pipeline survives parser failures.

AC-08

Unit tests pass.

18. Requirement Traceability Matrix
Ye bahut professional lagta hai.
Requirement	HLD Component	LLD Module	Test
FR-03	Parser Layer	src/parsers	test_parser.py
FR-05	Normalizer	src/normalization	test_normalizer.py
FR-07	Merge Engine	src/merge	test_merge.py
FR-09	Confidence Engine	src/confidence	test_confidence.py
FR-12	Validation	src/validation	test_validation.py
FR-18	CLI	src/main.py	Test_cli.py





19. # Assumptions

A-01
ATS JSON follows valid schema.

A-02
Resume contains machine-readable text.

A-03
Both inputs belong to the same candidate.

A-04
Configuration file is provided before execution.

A-05
Current MVP supports ATS JSON and Resume PDF only.

20. Reverse Engineered Evaluation Criteria

From the assignment, Eightfold is likely evaluating:

Engineering judgment
System design thinking
Pipeline design
Canonical data modeling
Merge/conflict strategy
Normalization quality
Explainability
Edge case handling
Modularity
Code quality
Documentation
Ability to defend design decisions
Scope management
Working core implementation
Configurable output support

