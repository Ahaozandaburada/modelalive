package modelalive

import (
	_ "embed"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"math"
	"strings"
	"time"
)

//go:embed stable_prompts.json
var stablePromptsJSON []byte

type StablePrompt struct {
	ID      string `json:"id"`
	Message string `json:"message"`
}

type PromptFingerprint struct {
	ID        string   `json:"id"`
	Prompt    string   `json:"prompt"`
	Responses []string `json:"responses"`
	Digest    string   `json:"digest"`
}

type Fingerprint struct {
	Version          int                 `json:"version"`
	Kind             string              `json:"kind"`
	Model            string              `json:"model"`
	Endpoint         *string             `json:"endpoint,omitempty"`
	CreatedAt        string              `json:"created_at"`
	SamplesPerPrompt int                 `json:"samples_per_prompt"`
	Prompts          []PromptFingerprint `json:"prompts"`
}

type PromptShift struct {
	PromptID        string  `json:"prompt_id"`
	Distance        float64 `json:"distance"`
	BaselineDigest  string  `json:"baseline_digest"`
	CurrentDigest   string  `json:"current_digest"`
}

type StabilityReport struct {
	Model              string        `json:"model"`
	Stable             bool          `json:"stable"`
	MeanDistance       float64       `json:"mean_distance"`
	MaxDistance        float64       `json:"max_distance"`
	Threshold          float64       `json:"threshold"`
	BaselineCreatedAt  *string       `json:"baseline_created_at,omitempty"`
	PromptShifts       []PromptShift `json:"prompt_shifts"`
}

type StableShiftError struct {
	Message string
}

func (e *StableShiftError) Error() string { return e.Message }

func ListStablePrompts() ([]StablePrompt, error) {
	var payload struct {
		Prompts []StablePrompt `json:"prompts"`
	}
	if err := json.Unmarshal(stablePromptsJSON, &payload); err != nil {
		return nil, err
	}
	return payload.Prompts, nil
}

func trigramDistribution(text string) map[string]float64 {
	normalized := strings.Join(strings.Fields(strings.ToLower(text)), " ")
	out := map[string]float64{}
	if len(normalized) < 3 {
		if normalized == "" {
			normalized = "∅"
		}
		out[normalized] = 1
		return out
	}
	for i := 0; i < len(normalized)-2; i++ {
		tri := normalized[i : i+3]
		out[tri]++
	}
	var total float64
	for _, v := range out {
		total += v
	}
	for k, v := range out {
		out[k] = v / total
	}
	return out
}

func distributionDistance(a, b map[string]float64) float64 {
	keys := map[string]struct{}{}
	for k := range a {
		keys[k] = struct{}{}
	}
	for k := range b {
		keys[k] = struct{}{}
	}
	var sum float64
	for k := range keys {
		av, bv := a[k], b[k]
		diff := av - bv
		if diff < 0 {
			diff = -diff
		}
		sum += diff
	}
	return sum / 2
}

func ResponseDistance(left, right string) float64 {
	if left == right {
		return 0
	}
	return distributionDistance(trigramDistribution(left), trigramDistribution(right))
}

func digestResponses(responses []string) string {
	payload := strings.Join(responses, "\n---\n")
	sum := sha256.Sum256([]byte(payload))
	return fmt.Sprintf("%x", sum[:8])
}

func FingerprintFromResponses(model string, responsesByID map[string][]string, endpoint *string, samples int) (*Fingerprint, error) {
	prompts, err := ListStablePrompts()
	if err != nil {
		return nil, err
	}
	out := make([]PromptFingerprint, 0, len(prompts))
	for _, spec := range prompts {
		responses := responsesByID[spec.ID]
		if responses == nil {
			responses = []string{}
		}
		out = append(out, PromptFingerprint{
			ID:        spec.ID,
			Prompt:    spec.Message,
			Responses: append([]string(nil), responses...),
			Digest:    digestResponses(responses),
		})
	}
	if samples < 1 {
		samples = 1
	}
	return &Fingerprint{
		Version:          1,
		Kind:             "modelalive-stable-fingerprint",
		Model:            model,
		Endpoint:         endpoint,
		CreatedAt:        time.Now().UTC().Format(time.RFC3339),
		SamplesPerPrompt: samples,
		Prompts:          out,
	}, nil
}

func CompareFingerprints(baseline, current *Fingerprint, threshold float64) StabilityReport {
	byID := map[string]PromptFingerprint{}
	for _, p := range current.Prompts {
		byID[p.ID] = p
	}
	var shifts []PromptShift
	var distances []float64

	for _, base := range baseline.Prompts {
		cur, ok := byID[base.ID]
		if !ok || len(base.Responses) == 0 || len(cur.Responses) == 0 {
			curDigest := "missing"
			if ok {
				curDigest = cur.Digest
			}
			shifts = append(shifts, PromptShift{
				PromptID: base.ID, Distance: 1, BaselineDigest: base.Digest, CurrentDigest: curDigest,
			})
			distances = append(distances, 1)
			continue
		}
		min := 1.0
		for _, br := range base.Responses {
			for _, cr := range cur.Responses {
				min = math.Min(min, ResponseDistance(br, cr))
			}
		}
		distances = append(distances, min)
		if min > threshold {
			shifts = append(shifts, PromptShift{
				PromptID: base.ID, Distance: min, BaselineDigest: base.Digest, CurrentDigest: cur.Digest,
			})
		}
	}

	mean := 1.0
	max := 1.0
	if len(distances) > 0 {
		var sum float64
		max = distances[0]
		for _, d := range distances {
			sum += d
			if d > max {
				max = d
			}
		}
		mean = sum / float64(len(distances))
	}

	var baselineCreated *string
	if baseline.CreatedAt != "" {
		baselineCreated = &baseline.CreatedAt
	}
	return StabilityReport{
		Model:             current.Model,
		Stable:            mean <= threshold,
		MeanDistance:      mean,
		MaxDistance:       max,
		Threshold:         threshold,
		BaselineCreatedAt: baselineCreated,
		PromptShifts:      shifts,
	}
}

func AssertStable(baseline, current *Fingerprint, threshold float64) (*StabilityReport, error) {
	report := CompareFingerprints(baseline, current, threshold)
	if !report.Stable {
		return &report, &StableShiftError{
			Message: fmt.Sprintf("behavioral drift detected for %s (mean %.3f > %.3f)", current.Model, report.MeanDistance, threshold),
		}
	}
	return &report, nil
}
