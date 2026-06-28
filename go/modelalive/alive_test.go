package modelalive_test

import (
	"testing"
	"time"

	"github.com/Ahaozandaburada/modelalive/go/modelalive"
)

func TestAliveRetired(t *testing.T) {
	res, err := modelalive.Alive("claude-sonnet-4-20250514", time.Date(2026, 6, 28, 0, 0, 0, 0, time.UTC))
	if err != nil {
		t.Fatal(err)
	}
	if res.Status != "retired" {
		t.Fatalf("expected retired, got %s", res.Status)
	}
}

func TestEnsureReplacement(t *testing.T) {
	safe, err := modelalive.Ensure("claude-sonnet-4-20250514", time.Date(2026, 6, 28, 0, 0, 0, 0, time.UTC))
	if err != nil {
		t.Fatal(err)
	}
	if safe != "claude-sonnet-4-6" {
		t.Fatalf("expected claude-sonnet-4-6, got %s", safe)
	}
}

func TestBedrockHost(t *testing.T) {
	res, err := modelalive.Alive("anthropic.claude-sonnet-4-6-v1:0", time.Date(2026, 6, 28, 0, 0, 0, 0, time.UTC))
	if err != nil {
		t.Fatal(err)
	}
	if res.Provider != "bedrock" {
		t.Fatalf("expected bedrock provider, got %s", res.Provider)
	}
}

func TestResolveGemini(t *testing.T) {
	safe, err := modelalive.Resolve("gemini-2.0-flash", time.Date(2026, 6, 28, 0, 0, 0, 0, time.UTC))
	if err != nil {
		t.Fatal(err)
	}
	if safe != "gemini-3.5-flash" {
		t.Fatalf("expected gemini-3.5-flash, got %s", safe)
	}
}
