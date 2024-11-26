# System Architecture

This document describes the high-level architecture of the Production Control application.

## Components

The system consists of the following main components:

### Production Control App

- **Web Application**: The main user interface
- **SQLModel Layer**: Data persistence and ORM
- **Spacing Pages**: UI components for spacing management
- **Spacing Model**: Domain model for spacing operations
- **OpTech Client**: Integration with OpTech API

### Data Sources

- **Dremio Instance**: Data warehouse
- **registratie_controle view**: View for registration control

### Spacing Control

- **Technison Application**: External spacing control system
- **OpTech API**: API for spacing operations

## Component Diagram

```mermaid
graph TD
    subgraph Production Control App
        WebApp[Web Application]
        SQLModel[SQLModel Layer]
        SpacingPages[Spacing Pages]
        SpacingModel[Spacing Model]
        OpTechClient[OpTech Client]
    end
    
    subgraph Data Sources
        Dremio[Dremio Instance]
        DremioView[registratie_controle view]
    end
    
    subgraph Spacing Control
        Technison[Technison Application]
        OpTech[OpTech API]
    end

    WebApp --> SpacingPages
    SpacingPages --> SpacingModel
    SpacingPages --> OpTechClient
    SpacingModel --> SQLModel
    OpTechClient --> OpTech
    SQLModel --> DremioView
    DremioView --> Dremio
    OpTech --> Technison

    style WebApp fill:#f9f,stroke:#333
    style SQLModel fill:#bbf,stroke:#333
    style SpacingPages fill:#f9f,stroke:#333
    style SpacingModel fill:#bbf,stroke:#333
    style OpTechClient fill:#fbf,stroke:#333
    style Dremio fill:#bfb,stroke:#333
    style Technison fill:#fbb,stroke:#333
    style OpTech fill:#fbf,stroke:#333
```
