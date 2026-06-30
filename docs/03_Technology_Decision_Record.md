Phase 2 – Technology Decision Record (TDR)
Objective
Technology Decision Record ka objective project ke liye har important engineering decision ko document karna hai, jisme alternatives, trade-offs aur final rationale clearly defined ho.
________________________________________
Decision Template
Har decision isi format me hoga.
Decision ID

Problem

Possible Options

Evaluation Criteria

Pros

Cons

Final Decision

Reason

Impact on HLD

Impact on LLD

Future Consideration
________________________________________
TDR-01 — Programming Language
Problem
Pipeline kis language me build karein?
________________________________________
Options
●	Python
●	Java
●	Go
●	Node.js
________________________________________
Evaluation Criteria
●	Development Speed
●	Library Ecosystem
●	PDF Parsing Support
●	JSON Handling
●	Type Safety
●	Community
●	Interview Readability
________________________________________
Language	Pros	Cons
Python	Rich ecosystem, rapid development, excellent parsing libraries	Runtime slower than Java/Go
Java	Strong typing, enterprise ready	Verbose for assignment
Go	Fast, lightweight	Limited resume parsing ecosystem
Node.js	Good JSON support	Fewer mature document-processing libraries
________________________________________
Final Decision
Python 3.12+
________________________________________
Reason
●	Excellent ecosystem for parsing and validation.
●	Mature libraries (PyMuPDF, Pydantic, Typer).
●	Faster development under assignment timeline.
●	Readable code for interview discussion.
________________________________________
Impact
HLD and LLD will be Python-centric.
________________________________________
TDR-02 — CLI Framework
Options
●	argparse
●	Click
●	Typer
________________________________________
Framework	Pros	Cons
argparse	Built-in	Verbose
Click	Mature	More boilerplate
Typer	Type hints, modern API, excellent UX	External dependency
________________________________________
Decision
Typer
________________________________________
Reason
Cleaner code, type-safe commands, excellent developer experience.
________________________________________
TDR-03 — Data Model
Options
●	dict
●	dataclass
●	Pydantic
________________________________________
Option	Pros	Cons
dict	Flexible	No validation
dataclass	Lightweight	Manual validation
Pydantic	Validation + serialization + typing	Slight overhead
________________________________________
Decision
Pydantic
________________________________________
Reason
Canonical Model is the heart of the project.
Automatic validation.
JSON serialization.
Strong typing.
________________________________________
TDR-04 — PDF Parsing
Options
●	PyMuPDF
●	pdfplumber
●	pypdf
________________________________________
Library	Pros	Cons
PyMuPDF	Fast, accurate, preserves layout	Slightly larger dependency
pdfplumber	Great for tables	Slower
pypdf	Lightweight	Weak text extraction
________________________________________
Decision
PyMuPDF
________________________________________
TDR-05 — Resume Parsing Strategy
Options
●	Regex
●	NLP
●	LLM
●	Hybrid
________________________________________
Strategy	Pros	Cons
Regex	Deterministic	Limited context
NLP	Better understanding	Model dependency
LLM	Flexible	Non-deterministic
Hybrid	Balanced	Slightly more implementation effort
________________________________________
Decision
Hybrid (Text Extraction + Rule-Based Parsing)
________________________________________
Reason
Meets assignment requirements:
●	Deterministic
●	Explainable
●	Maintainable
________________________________________
TDR-06 — Merge Strategy
Options
●	Source Priority
●	Majority Voting
●	Confidence Based
●	LLM
________________________________________
Decision
Source Priority + Field Rules
________________________________________
Reason
Deterministic.
Easy to explain.
Auditable.
________________________________________
TDR-07 — Confidence Engine
Options
●	ML
●	Statistical
●	Rule Based
________________________________________
Decision
Rule Based
________________________________________
Reason
Assignment emphasizes explainability.
________________________________________
TDR-08 — Configuration Format
Options
●	JSON
●	YAML
●	TOML
________________________________________
Decision
YAML
________________________________________
Reason
Readable.
Supports nested configuration.
Widely used in DevOps and ML projects.
________________________________________
TDR-09 — Testing Framework
Options
●	unittest
●	pytest
________________________________________
Decision
pytest
________________________________________
Reason
Simple syntax.
Powerful fixtures.
Industry standard.
________________________________________
TDR-10 — Logging
Options
●	print()
●	logging
●	structlog
________________________________________
Decision
Python logging
________________________________________
Reason
No unnecessary dependencies.
Enough for assignment.
________________________________________
TDR-11 — Configuration Driven Design
Decision
Pipeline behavior should be driven through configuration instead of hardcoded logic.
Reason
Supports configurable output requirement.
________________________________________
TDR-12 — Project Architecture
Options
●	Monolith
●	Layered
●	Microservices
________________________________________
Decision
Layered Pipeline Architecture
Reason
Small scope.
Easy testing.
Easy extension.
________________________________________
TDR-13 — Parser Design Pattern
Decision
Strategy Pattern
Reason
Easy addition of future parsers.
________________________________________
TDR-14 — Output Format
Decision
JSON
Reason
Machine-readable.
Matches assignment.
________________________________________
TDR-15 — User Interface
Decision
CLI
Reason
Explicit assignment requirement.
No unnecessary UI complexity.
________________________________________
TDR-16 — Error Handling
Decision
Recoverable parser failures should generate warnings.
Fatal schema errors should stop execution.
________________________________________
TDR-17 — Folder Structure
Decision
Feature-based modular structure.
No single-file implementation.
________________________________________
TDR-18 — Dependency Management
Decision
Use uv (or pip if simplicity is preferred) with a pinned requirements.txt (or lockfile if using uv).
Reason
Reproducible builds.
________________________________________
📋 Final Technology Stack
Layer	Technology
Language	Python 3.12+
CLI	Typer
Validation	Pydantic
PDF Parsing	PyMuPDF
Config	YAML
Testing	pytest
Logging	logging
Formatting	Ruff + Black
Architecture	Layered Pipeline
Merge	Rule Based
Confidence	Rule Based
TDR-19 — Dependency Injection Strategy
Problem
Pipeline ke components (Parser, Normalizer, Merge Engine, Validator, etc.) ek dusre ko kaise access karenge?
________________________________________
Options
Option 1 — Global Objects
parser = ResumeParser()

merge_engine = MergeEngine()
Components globally accessible.
________________________________________
Option 2 — Singleton Pattern
Ek hi instance poore application me use hoga.
________________________________________
Option 3 — Constructor Dependency Injection ⭐
Pipeline(
   ats_parser,
   resume_parser,
   normalizer,
   merge_engine,
   validator,
   projection_engine
)
Dependencies constructor ke through inject hongi.
________________________________________
Evaluation Criteria
●	Testability
●	Loose Coupling
●	Maintainability
●	SOLID Principles
●	Extensibility
________________________________________
Option	Pros	Cons
Global Objects	Simple	Tight coupling, difficult testing
Singleton	Shared instances	Hidden dependencies, hard to mock
Constructor Injection	Explicit dependencies, highly testable	Slightly more boilerplate
________________________________________
Final Decision
Constructor Dependency Injection
________________________________________
Reason
●	Follows Dependency Inversion Principle (DIP).
●	Dependencies become explicit.
●	Easy unit testing with mock implementations.
●	Future parser implementations can be injected without changing pipeline logic.
________________________________________
Example
Pipeline
│
├── ATSParser
├── ResumeParser
├── Normalizer
├── MergeEngine
├── Validator
└── ProjectionEngine
Pipeline sirf interfaces use karega.
Implementation later inject hogi.
________________________________________
Impact on HLD
Pipeline components loosely coupled rahenge.
________________________________________
Impact on LLD
Classes constructor-based dependency injection follow karengi.
________________________________________
Future Consideration
Future me Dependency Injection Container (e.g., dependency-injector) use kiya ja sakta hai agar project microservices ya larger architecture me evolve kare.
________________________________________
TDR-20 — Configuration Validation Strategy
Problem
Configuration file (YAML) invalid hui to kya hoga?
Example
projection:
 include:
   - full_name
   - xyz
xyz canonical schema me exist hi nahi karta.
Agar validation na ho
↓
Runtime error.
________________________________________
Options
Option 1 — No Validation
Configuration direct use.
________________________________________
Option 2 — Runtime Validation
Execution ke dauran validate.
________________________________________
Option 3 — Pydantic Configuration Model ⭐
Configuration load
↓
Pydantic Validation
↓
Pipeline Execution
________________________________________
Evaluation Criteria
●	Early failure
●	Developer experience
●	Type safety
●	Maintainability
________________________________________
Option	Pros	Cons
No Validation	Very simple	High runtime failure risk
Runtime Validation	Moderate	Errors detected late
Pydantic Config Model	Early validation, strong typing	Small additional model
________________________________________
Final Decision
Validate configuration using a dedicated Pydantic Configuration Model before pipeline execution.
________________________________________
Validation Rules
Configuration should verify:
●	Projection fields exist in Canonical Schema.
●	Duplicate fields are removed.
●	Confidence flag is Boolean.
●	Provenance flag is Boolean.
●	Unknown configuration keys are rejected.
●	Configuration version is supported.
________________________________________
Example
Valid
projection:
 include:
   - full_name
   - skills

confidence: true

provenance: false
Invalid
projection:
 include:
   - random_field
↓
Validation Error
Unknown field 'random_field' in projection configuration.
________________________________________
Impact on HLD
Configuration Validator component add hoga.
________________________________________
Impact on LLD
Separate ConfigModel aur ConfigValidator classes hongi.
________________________________________
Future Consideration
Future versions me configuration hot-reload aur environment-specific profiles support kiye ja sakte hain.
________________________________________
TDR-21 — Canonical Schema Versioning Strategy
Problem
Future me agar naye parsers add hue (GitHub, LinkedIn, Recruiter Notes), to Canonical Schema evolve karega.
Without versioning
↓
Backward compatibility break ho sakti hai.
________________________________________
Options
Option 1 — No Versioning
Simple.
Future risk high.
________________________________________
Option 2 — Git Tag Only
Repository version maintain.
Schema independent nahi.
________________________________________
Option 3 — Internal Schema Version ⭐
Canonical Candidate Model me version maintain.
Example
schema_version: "1.0"
________________________________________
Evaluation Criteria
●	Backward Compatibility
●	Maintainability
●	Extensibility
●	API Evolution
________________________________________
Option	Pros	Cons
No Version	Simple	Difficult future evolution
Git Version	Repository only	Schema not versioned
Internal Schema Version	Clean evolution path	Minor metadata overhead
________________________________________
Final Decision
Maintain an internal Canonical Schema Version (schema_version) as part of the Canonical Candidate Model.
________________________________________
Example
{
 "schema_version": "1.0",
 "candidate_id": "ATS-1001",
 "full_name": "Sahil Kumar"
}
________________________________________
Benefits
●	Backward compatibility.
●	Easier migration to future schema versions.
●	New parsers can map to old or new schema.
●	Downstream consumers know expected contract.
________________________________________
Impact on HLD
Canonical Candidate Model becomes version-aware.
________________________________________
Impact on LLD
Candidate model includes:
schema_version : string
Default
"1.0"
________________________________________
Future Roadmap
Potential versions:
Version	Change
1.0	ATS JSON + Resume PDF
1.1	Recruiter Notes support
1.2	GitHub Parser
2.0	LinkedIn Integration
3.0	Semantic Skill Graph + Embedding Metadata
________________________________________
📌 Final TDR Status (v2.0)
Ab Technology Decision Record me 21 engineering decisions documented hain.
Decision Categories
●	✅ Programming Language
●	✅ Architecture Style
●	✅ Design Patterns
●	✅ Data Model
●	✅ Parser Strategy
●	✅ Merge Strategy
●	✅ Confidence Strategy
●	✅ Validation Strategy
●	✅ Configuration Strategy
●	✅ Dependency Injection
●	✅ Schema Versioning
●	✅ Testing
●	✅ Logging
●	✅ Error Handling
●	✅ Folder Structure
●	✅ Output Format
●	✅ CLI
●	✅ Dependency Management
