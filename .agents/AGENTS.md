# Workspace Rules

## Architectural Rule: No Domain Knowledge in Code
No domain knowledge may exist in Python source code.
If you need to add a groundwater statistic, a district profile, BIS limits, aquifer descriptions, or water-quality reference values, they must be added to the appropriate data source (database, indexed document, or external service), NOT to the application logic. This prevents the codebase from gradually drifting back toward embedded knowledge.
