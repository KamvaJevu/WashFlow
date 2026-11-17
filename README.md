# WashFlow

### Multi-Tenant Cleaning Business Management System

WashFlow is a business management platform under development, designed for independent cleaning businesses such as mobile car washes and dustbin cleaning services.

The goal is to provide a centralised system for managing customers, vehicles, bookings, services, staff, payments and business operations.

## Project Overview

WashFlow follows a multi-tenant architecture, allowing multiple independent businesses to operate on one platform while keeping their business data logically separated.

The backend is being developed with Python, FastAPI, PostgreSQL and SQLAlchemy, with an emphasis on data integrity, access control, maintainability and secure business operations.

## Implemented Functionality

The following backend components have been implemented:

- Business, user and business membership models.
- Customer and vehicle management models.
- Business-scoped membership and permission checks.
- Owner and Manager archival and restoration permissions.
- Staff restrictions on archival operations.
- Customer archival with associated active vehicle archival.
- Independent vehicle archival and restoration.
- Restoration rules that preserve independently archived vehicles.
- Mandatory archival and restoration reasons.
- Audit logging for important operations.
- PostgreSQL triggers protecting audit logs against ordinary UPDATE, DELETE and TRUNCATE operations.
- Database migrations managed through Alembic.
- Automated tests covering permissions, archival, restoration, audit integrity and database connections.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | REST API framework |
| PostgreSQL | Relational database |
| SQLAlchemy | Database ORM |
| Alembic | Database migrations |
| Pydantic | Data validation and configuration |
| Pytest | Automated testing |
| Git and GitHub | Version control |

## Project Structure

```text
WashFlow/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── docs/
├── migrations/
├── scripts/
│   └── legacy/
├── tests/
├── .env.example
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── README.md
```

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/KamvaJevu/WashFlow.git
cd WashFlow
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a reference.

Configure `DATABASE_URL` with your local PostgreSQL credentials and database name.

Do not commit `.env` or expose database credentials.

### 5. Apply database migrations

```powershell
python -m alembic upgrade head
```

### 6. Run automated tests

```powershell
python -m pytest -v
```

Automated tests use a dedicated test database. Ensure the configured PostgreSQL server has the required test database available before running them.

## Development Status

**Current phase: Backend foundation and core business logic.**

Completed:
- Project and database configuration.
- Initial database models and migrations.
- Business membership and permission logic.
- Archival and restoration services.
- Audit logging and database-level audit protection.
- Automated backend tests.

Planned:
- Authentication and session management.
- FastAPI endpoints.
- Booking and scheduling workflows.
- Service and pricing management.
- Payment and financial management.
- Staff management.
- Reporting and analytics.
- Frontend development.
- Integration testing and deployment.

## Project Objectives

WashFlow aims to demonstrate practical software engineering through:

- Multi-tenant system architecture.
- Relational database design.
- Secure access control.
- Transaction management and data integrity.
- Automated testing.
- Maintainable backend development.
- Practical business problem-solving.

---

**Project:** WashFlow  
**Status:** In Development  
**Primary Language:** Python
**Repository:** [KamvaJevu/WashFlow](https://github.com/KamvaJevu/WashFlow)