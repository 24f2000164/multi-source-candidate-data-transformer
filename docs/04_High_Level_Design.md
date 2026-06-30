High Level Design (HLD)
Multi-Source Candidate Data Transformer
Version: 1.0
Status: Final
Author: Sahil Kumar
________________________________________
1. Purpose
This document defines the high-level architecture of the Multi-Source Candidate Data Transformer.
The system transforms heterogeneous candidate information collected from multiple sources into a standardized Golden Candidate Record while ensuring deterministic processing, explainability, modularity, and extensibility.
This document serves as the architectural blueprint for implementation.
________________________________________
2. Scope
Supported Input Sources (MVP)
•	ATS JSON (Structured)
•	Resume PDF (Unstructured)
Output
•	Golden Candidate JSON
Interface
•	Command Line Interface (CLI)
________________________________________
3. Architecture Goals
The architecture is designed to achieve:
•	Modular design
•	Deterministic processing
•	Explainable transformations
•	Configuration-driven output
•	High maintainability
•	Independent testing
•	Future extensibility
________________________________________
4. Architecture Style
The system follows a Layered Pipeline Architecture.
Each layer owns a single responsibility and communicates only with adjacent layers.
________________________________________
5. High-Level Architecture
                ATS JSON
                   │
                   │
             Resume PDF
                   │
                   ▼
          Pipeline Orchestrator
                   │
                   ▼
             Parser Layer
                   │
                   ▼
      Canonical Candidate Model
                   │
                   ▼
        Normalization Engine
                   │
                   ▼
            Merge Engine
                   │
                   ▼
        Confidence Engine
                   │
                   ▼
         Validation Layer
                   │
                   ▼
         Projection Engine
                   │
                   ▼
            Output Writer
                   │
                   ▼
      Golden Candidate Record
Supporting Components
•	Configuration
•	Logging
•	Error Handling
Future Extensions
•	GitHub Parser
•	LinkedIn Parser
•	Recruiter Notes Parser
________________________________________
6. Component Responsibilities
CLI
Responsibilities
•	Accept runtime arguments
•	Start pipeline
•	Display execution status
________________________________________
Pipeline Orchestrator
Responsibilities
•	Execute pipeline stages
•	Coordinate workflow
•	Handle failures
•	Produce final result
________________________________________
Parser Layer
Responsibilities
•	Parse ATS JSON
•	Extract Resume information
•	Convert source data into internal representation
________________________________________
Canonical Candidate Model
Responsibilities
•	Unified internal schema
•	Source-independent representation
•	Input to downstream layers
________________________________________
Normalization Engine
Responsibilities
•	Standardize emails
•	Standardize phone numbers
•	Normalize names
•	Normalize dates
•	Deduplicate skills
________________________________________
Merge Engine
Responsibilities
•	Resolve conflicts
•	Apply deterministic merge policy
•	Track provenance
•	Produce Golden Candidate Record
________________________________________
Confidence Engine
Responsibilities
•	Calculate field confidence
•	Calculate overall confidence
•	Preserve explainability
________________________________________
Validation Layer
Responsibilities
•	Validate input
•	Validate canonical model
•	Validate output schema
________________________________________
Projection Engine
Responsibilities
•	Apply runtime configuration
•	Include or exclude fields
•	Generate configurable output
________________________________________
Output Writer
Responsibilities
•	Serialize final object
•	Write JSON output
________________________________________
7. End-to-End Data Flow
ATS JSON
        \
         \
          --> Parser Layer
         /
Resume PDF

↓

Canonical Candidate Model

↓

Normalization

↓

Merge

↓

Confidence

↓

Validation

↓

Projection

↓

Golden Candidate JSON
________________________________________
8. Technology Mapping
Component	Technology
CLI	Typer
Models	Pydantic
PDF Parsing	PyMuPDF
Configuration	PyYAML
Testing	Pytest
Linting	Ruff
Formatting	Black
Type Checking	MyPy
________________________________________
9. Cross-Cutting Concerns
Logging
Structured logging across every pipeline stage.
Configuration
External YAML configuration.
Error Handling
Centralized exception handling.
Explainability
Every merged field retains provenance and confidence.
________________________________________
10. Design Principles
The architecture follows:
•	Single Responsibility Principle
•	Open/Closed Principle
•	Dependency Inversion Principle
•	Composition over Inheritance
•	Configuration Driven Design
•	Deterministic Processing
________________________________________
11. Quality Attributes
The architecture is designed for:
•	Maintainability
•	Testability
•	Reliability
•	Extensibility
•	Explainability
•	Security
•	Performance
________________________________________
12. Future Extension Strategy
The architecture supports future input sources without modifying existing components.
Potential future parsers:
•	GitHub
•	LinkedIn
•	Recruiter Notes
•	Recruiter CSV
•	XML
•	REST API
The Open/Closed Principle is preserved by implementing new parsers through a common parser abstraction.
________________________________________
13. HLD to LLD Mapping
HLD Component	Planned Package
Pipeline Orchestrator	src/core
Parser Layer	src/parsers
Canonical Candidate Model	src/canonical
Normalization Engine	src/normalization
Merge Engine	src/merge
Confidence Engine	src/confidence
Validation Layer	src/validation
Projection Engine	src/projection
Output Writer	src/output
Domain Models	src/models
________________________________________
14. Risks
•	Invalid ATS JSON
•	Corrupted Resume PDF
•	Conflicting candidate information
•	Missing mandatory fields
•	Configuration errors
Mitigation is provided through validation, deterministic merge rules, and graceful error handling.
________________________________________
15. Architecture Validation Checklist
•	Layered architecture
•	Modular components
•	No cyclic dependencies
•	Deterministic processing
•	Configurable output
•	Explainable merge decisions
•	Testable modules
•	Future extensibility
________________________________________
16. Conclusion
The proposed architecture provides a clean, modular, and production-inspired foundation for the Multi-Source Candidate Data Transformer.
The architecture satisfies all functional and non-functional requirements identified during the Software Requirements Analysis and is fully aligned with the Technology Decision Record. It serves as the implementation blueprint for the Low Level Design and subsequent development.
