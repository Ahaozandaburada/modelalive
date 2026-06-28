const MODEL_ID_PATTERN = /^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,200}$/;
const FINE_TUNED_PREFIX = /^ft:([^:]+(?::[^:]+)*)/;

export function normalizeModel(model: string): string {
  let cleaned = model.trim();
  if (!cleaned) throw new Error("Model ID cannot be empty");

  const ftMatch = FINE_TUNED_PREFIX.exec(cleaned);
  if (ftMatch) {
    const base = ftMatch[1].split(":")[0];
    if (base) cleaned = base;
  }

  if (!MODEL_ID_PATTERN.test(cleaned)) {
    throw new Error(`Invalid model ID format: ${model}`);
  }
  return cleaned;
}
