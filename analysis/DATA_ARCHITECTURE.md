# Data Flow Architecture

This architecture documents the implemented analytical pipeline.  The daily and
intraday price feeds are deliberately kept separate after quality control: the
overlap test found material discrepancies, so they must not be spliced.

```mermaid
flowchart LR
    subgraph S[Raw source layer — dataset_start]
        D[01_market_prices_raw.csv<br/>asset × trading day]
        I[01_market_prices_raw_expanded.csv<br/>asset × 10-minute bar]
        M[02_macro_raw.csv<br/>day × macro / FX / regime]
        F[03_fundamentals_raw.csv<br/>issuer × quarter]
        A[04_asset_reference.csv<br/>asset / issuer attributes]
        C[05_client_profiles.csv<br/>client constraints]
        E[06_events.csv<br/>dated asset / sector events]
    end

    Q[01_inventory.py<br/>inventory, schema and integrity audit]
    CL[clean.py<br/>canonical IDs • dates • numeric parsing<br/>deduplication • missing-value repair<br/>OHLC validation]

    D --> Q
    I --> Q
    M --> Q
    F --> Q
    A --> Q
    C --> Q
    E --> Q

    D --> CL
    I --> CL
    M --> CL
    F --> CL
    A --> CL
    C --> CL
    E --> CL

    subgraph P[Clean analytical paths]
        CD[Clean daily prices]
        CI[Clean intraday prices]
        CM[Clean macro / FX / regimes]
        CF[Clean fundamentals]
        DIM[Clean reference, client and event dimensions]
    end

    CL --> CD
    CL --> CI
    CL --> CM
    CL --> CF
    CL --> DIM

    CD --> DA[02_dimensions_and_daily.py<br/>returns • volatility • drawdown • liquidity]
    CI --> IA[04_intraday.py<br/>session structure • volume curve]
    CD --> IA
    CM --> MA[05_macro.py<br/>regimes • factor links • FX]
    CD --> MA
    CF --> FA[06_fundamentals.py<br/>growth • margins • leverage]
    DIM --> DA
    DIM --> FA
```

```mermaid
flowchart TB
    DA[Daily asset statistics<br/>02_daily_asset_stats.csv]
    FA[Fundamental scorecard<br/>06_fundamentals_scorecard.csv]
    MA[Macro / FX / regime evidence]
    EV[Events dimension]
    AS[Asset reference]

    DA --> INT[07_integration.py]
    FA --> INT
    MA --> INT
    EV --> INT
    AS --> INT

    INT --> ES[Event study<br/>07_event_study.csv]
    INT --> VS[Value synthesis<br/>07_value_synthesis.csv]
    INT --> FIG1[Market, macro, fundamental,<br/>event and value figures]

    VS --> CS[08_client_screening.py]
    DA --> CS
    MA --> CS
    AS --> CS
    CP[Client profiles] --> CS

    CS --> BASE[Base portfolios and<br/>constraint checks]
    BASE --> TW[10_twist_analysis.py<br/>rate shock • liquidity call • COP shock]
    TW --> DD[13_client_deep_dive.py<br/>base-currency risk and actions]

    DD --> OUT[Decision outputs<br/>client recommendations • risk watchlist<br/>cash sleeve / rebalancing actions]
```

```mermaid
flowchart LR
    D[Daily price feed] --> R[Daily return / risk analytics]
    I[Intraday price feed] --> X[Intraday microstructure analytics]
    D -. overlap comparison .-> G{Agreement test}
    I -. overlap comparison .-> G
    G -->|Material close and volume gaps| SEP[Source-separation rule]
    SEP --> R
    SEP --> X
    R -. never append or backfill with .-> X

    style SEP fill:#fff3cd,stroke:#b8860b,color:#222
    style G fill:#f8d7da,stroke:#b02a37,color:#222
```

## Controls embedded in the flow

| Control | Applied before | Why it matters |
|---|---|---|
| Canonical asset and issuer IDs | All joins | Preserves reference and fundamentals links |
| Mixed date and numeric parsing | Time series and reporting | Produces consistent temporal and numeric fields |
| Duplicate removal and period resolution | Metrics and LTM calculations | Avoids double-counting observations |
| Missing-value / bad-tick repair | Price-derived returns | Prevents artificial price moves and unusable bars |
| Daily–intraday separation | All price analysis | Avoids invalidly combining inconsistent sources |
| Client base-currency checks | Final recommendations | Tests drawdown tolerance in the client’s actual currency |

## Monetary-data lineage

The pipeline carries two distinct types of money-related data:

```mermaid
flowchart LR
    P[USD price per share] --> TV[Price × volume]
    V[Trading volume in shares] --> TV
    TV --> L[Average daily traded value<br/>liquidity analysis]

    R[Revenue, EBITDA, net income<br/>debt and cash — USD m] --> F[Fundamental scorecard]
    F --> S[Value and leverage synthesis]

    L --> C[Client suitability / liquidity checks]
    S --> C

    N[No client AUM, positions,<br/>shares outstanding or market cap] -. limitation .-> C
```

See [`MONEY_AND_LIQUIDITY.md`](MONEY_AND_LIQUIDITY.md) for the field-level
definitions, issuer amounts and limitations.
