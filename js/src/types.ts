export interface AliveResult {
  model: string;
  alive: boolean;
  status: "active" | "deprecated" | "retired" | "unknown";
  queried_model?: string;
  canonical_model?: string;
  aliased?: boolean;
  provider?: string;
  deprecated_at?: string;
  retired_at?: string;
  replacement?: string | null;
  breaking_changes?: string[];
  migrate_url?: string;
  days_until_retirement?: number | null;
  message?: string;
  registry_version?: string;
  source_url?: string;
  source_checked_at?: string;
  confidence?: string;
}

export interface Registry {
  version: string;
  schema_version: number;
  sources: Record<string, { url: string; checked_at: string }>;
  aliases: Record<string, string>;
  models: Record<string, RegistryModel>;
}

export interface RegistryModel {
  provider: string;
  status: string;
  deprecated_at?: string;
  retired_at?: string;
  replacement?: string | null;
  breaking_changes?: string[];
  migrate_url?: string;
  source?: string;
}

export class ModelRetiredError extends Error {
  constructor(public readonly result: AliveResult) {
    super(result.message ?? `Model ${result.model} is retired`);
    this.name = "ModelRetiredError";
  }
}

export class ModelUnknownError extends Error {
  constructor(public readonly result: AliveResult) {
    super(result.message ?? `Model ${result.model} is unknown`);
    this.name = "ModelUnknownError";
  }
}
