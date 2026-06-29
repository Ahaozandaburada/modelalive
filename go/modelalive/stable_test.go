package modelalive_test

import (
	"testing"

	"github.com/Ahaozandaburada/modelalive/go/modelalive"
)

func TestStablePrompts(t *testing.T) {
	prompts, err := modelalive.ListStablePrompts()
	if err != nil {
		t.Fatal(err)
	}
	if len(prompts) < 5 {
		t.Fatalf("expected >=5 prompts, got %d", len(prompts))
	}
}

func TestStableCompareIdentical(t *testing.T) {
	prompts, _ := modelalive.ListStablePrompts()
	responses := map[string][]string{}
	for _, p := range prompts {
		responses[p.ID] = []string{"fixture"}
	}
	base, err := modelalive.FingerprintFromResponses("gpt-4o", responses, nil, 1)
	if err != nil {
		t.Fatal(err)
	}
	cur, err := modelalive.FingerprintFromResponses("gpt-4o", responses, nil, 1)
	if err != nil {
		t.Fatal(err)
	}
	report := modelalive.CompareFingerprints(base, cur, 0.25)
	if !report.Stable {
		t.Fatalf("expected stable, mean=%f", report.MeanDistance)
	}
}

func TestStableDetectDrift(t *testing.T) {
	prompts, _ := modelalive.ListStablePrompts()
	baseMap := map[string][]string{}
	for _, p := range prompts {
		baseMap[p.ID] = []string{"alpha beta gamma"}
	}
	shifted := map[string][]string{}
	for k, v := range baseMap {
		shifted[k] = append([]string(nil), v...)
	}
	shifted["math_fixed"] = []string{"totally different output here now"}

	base, _ := modelalive.FingerprintFromResponses("gpt-4o", baseMap, nil, 1)
	cur, _ := modelalive.FingerprintFromResponses("gpt-4o", shifted, nil, 1)
	report := modelalive.CompareFingerprints(base, cur, 0.01)
	if report.Stable {
		t.Fatal("expected drift")
	}
}

func TestResponseDistanceZero(t *testing.T) {
	if modelalive.ResponseDistance("same", "same") != 0 {
		t.Fatal("expected zero distance")
	}
}
