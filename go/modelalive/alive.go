package modelalive

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
	"sync"
	"time"
)

// Registry bundle is copied from registry/models.json via scripts/sync_registry.py.
//go:embed registry.json
var registryJSON []byte

var (
	registryOnce sync.Once
	registryData *Registry
	registryErr  error
)

type Registry struct {
	Version       string                       `json:"version"`
	SchemaVersion int                          `json:"schema_version"`
	Sources       map[string]SourceMeta        `json:"sources"`
	Aliases       map[string]string            `json:"aliases"`
	Models        map[string]ModelEntry        `json:"models"`
}

type SourceMeta struct {
	URL        string `json:"url"`
	CheckedAt  string `json:"checked_at"`
}

type ModelEntry struct {
	Provider         string   `json:"provider"`
	Status           string   `json:"status"`
	DeprecatedAt     string   `json:"deprecated_at,omitempty"`
	RetiredAt        string   `json:"retired_at,omitempty"`
	Replacement      *string  `json:"replacement"`
	BreakingChanges  []string `json:"breaking_changes"`
	MigrateURL       string   `json:"migrate_url,omitempty"`
	Source           string   `json:"source,omitempty"`
}

type AliveResult struct {
	Model                 string   `json:"model"`
	QueriedModel          string   `json:"queried_model"`
	CanonicalModel        string   `json:"canonical_model"`
	Aliased               bool     `json:"aliased"`
	Alive                 bool     `json:"alive"`
	Status                string   `json:"status"`
	Provider              string   `json:"provider,omitempty"`
	Replacement           *string  `json:"replacement,omitempty"`
	BreakingChanges       []string `json:"breaking_changes,omitempty"`
	RegistryVersion       string   `json:"registry_version,omitempty"`
	SourceURL             string   `json:"source_url,omitempty"`
	SourceCheckedAt       string   `json:"source_checked_at,omitempty"`
	Confidence            string   `json:"confidence,omitempty"`
	Message               string   `json:"message,omitempty"`
	DaysUntilRetirement   *int     `json:"days_until_retirement,omitempty"`
}

func LoadRegistry() (*Registry, error) {
	registryOnce.Do(func() {
		var reg Registry
		if err := json.Unmarshal(registryJSON, &reg); err != nil {
			registryErr = err
			return
		}
		registryData = &reg
	})
	return registryData, registryErr
}

var (
	modelIDPattern = regexp.MustCompile(`^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,200}$`)
	fineTuned      = regexp.MustCompile(`^ft:([^:]+(?::[^:]+)*)`)
)

func NormalizeModel(model string) (string, error) {
	cleaned := strings.TrimSpace(model)
	if cleaned == "" {
		return "", fmt.Errorf("model ID cannot be empty")
	}
	if m := fineTuned.FindStringSubmatch(cleaned); len(m) > 1 {
		parts := strings.Split(m[1], ":")
		if parts[0] != "" {
			cleaned = parts[0]
		}
	}
	if !modelIDPattern.MatchString(cleaned) {
		return "", fmt.Errorf("invalid model ID format: %s", model)
	}
	return cleaned, nil
}

func parseDate(value string) (time.Time, bool) {
	if value == "" {
		return time.Time{}, false
	}
	t, err := time.Parse("2006-01-02", value)
	return t, err == nil
}

func effectiveStatus(entry ModelEntry, today time.Time) string {
	if retired, ok := parseDate(entry.RetiredAt); ok && !retired.After(today) {
		return "retired"
	}
	if entry.Status == "legacy" {
		return "deprecated"
	}
	return entry.Status
}

func daysUntil(value string, today time.Time) *int {
	target, ok := parseDate(value)
	if !ok {
		return nil
	}
	d := int(target.Sub(today).Hours() / 24)
	return &d
}

func resolveAlias(model string, reg *Registry) (string, bool) {
	current := model
	chain := []string{model}
	for i := 0; i < 8; i++ {
		next, ok := reg.Aliases[current]
		if !ok {
			return current, len(chain) > 1
		}
		for _, c := range chain {
			if c == next {
				return current, len(chain) > 1
			}
		}
		chain = append(chain, next)
		current = next
	}
	return current, len(chain) > 1
}

func Alive(model string, today time.Time) (AliveResult, error) {
	reg, err := LoadRegistry()
	if err != nil {
		return AliveResult{}, err
	}
	queried, err := NormalizeModel(model)
	if err != nil {
		return AliveResult{}, err
	}
	canonical, aliased := resolveAlias(queried, reg)
	entry, ok := reg.Models[canonical]
	if !ok {
		return AliveResult{
			Model:           canonical,
			QueriedModel:    queried,
			CanonicalModel:  canonical,
			Aliased:         aliased,
			Alive:           true,
			Status:          "unknown",
			Confidence:      "unknown",
			Message:         "Model not in registry — assumed alive.",
			RegistryVersion: reg.Version,
		}, nil
	}

	status := effectiveStatus(entry, today)
	days := daysUntil(entry.RetiredAt, today)
	confidence := "unknown"
	if entry.Source != "" {
		confidence = "verified"
	}
	var sourceURL, sourceChecked string
	if meta, ok := reg.Sources[entry.Source]; ok {
		sourceURL = meta.URL
		sourceChecked = meta.CheckedAt
	}

	result := AliveResult{
		Model:               canonical,
		QueriedModel:        queried,
		CanonicalModel:      canonical,
		Aliased:             aliased,
		Provider:            entry.Provider,
		Replacement:         entry.Replacement,
		BreakingChanges:     entry.BreakingChanges,
		RegistryVersion:     reg.Version,
		SourceURL:           sourceURL,
		SourceCheckedAt:     sourceChecked,
		Confidence:          confidence,
		DaysUntilRetirement: days,
		Status:              status,
		Alive:               status != "retired",
	}
	if status == "retired" {
		msg := fmt.Sprintf("Model '%s' was retired.", canonical)
		if entry.Replacement != nil {
			msg += fmt.Sprintf(" Use '%s' instead.", *entry.Replacement)
		}
		result.Message = msg
	} else if status == "deprecated" {
		result.Message = fmt.Sprintf("Model '%s' is deprecated.", canonical)
	}
	return result, nil
}

const maxDepth = 12

func Resolve(model string, today time.Time) (string, error) {
	current, err := NormalizeModel(model)
	if err != nil {
		return "", err
	}
	visited := map[string]struct{}{}
	for i := 0; i < maxDepth; i++ {
		if _, ok := visited[current]; ok {
			break
		}
		visited[current] = struct{}{}
		res, err := Alive(current, today)
		if err != nil {
			return "", err
		}
		if res.Status == "active" || res.Status == "unknown" {
			if res.CanonicalModel != "" {
				return res.CanonicalModel, nil
			}
			return current, nil
		}
		if res.Replacement == nil || *res.Replacement == "" {
			if res.CanonicalModel != "" {
				return res.CanonicalModel, nil
			}
			return current, nil
		}
		replRes, err := Alive(*res.Replacement, today)
		if err != nil {
			return "", err
		}
		if replRes.Status == "active" {
			return *res.Replacement, nil
		}
		current = *res.Replacement
	}
	return current, nil
}

func Ensure(model string, today time.Time) (string, error) {
	res, err := Alive(model, today)
	if err != nil {
		return "", err
	}
	if res.Status == "retired" && (res.Replacement == nil || *res.Replacement == "") {
		return "", fmt.Errorf("%s", res.Message)
	}
	return Resolve(model, today)
}
