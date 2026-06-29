# Design partner outreach

Copy-paste for DMs, email, or GitHub discussions.

---

## Short DM

Hey — I'm building **Model Alive** (pre-flight check before LLM API calls: retired IDs + optional ghost-drift probe).  

Looking for 2–3 teams to integrate in CI for 15 min feedback. In return I'll add your provider/models to the registry same week.

Repo: https://github.com/Ahaozandaburada/modelalive  
Interested?

---

## Email / longer

**Subject:** 15 min feedback — LLM model ID pre-flight tool

Hi,

I maintain **Model Alive** — an open-source gate that runs before LLM calls:

- **Alive:** block or auto-replace retired/deprecated model IDs (765 models, provider doc sources)
- **Stable:** optional CI probe for silent behavior changes under the same model name

```bash
pip install modelalive
modelalive ensure "$MODEL_ID"
```

I'm looking for 2–3 design partners (startups or OSS maintainers) for a short feedback call. If you share which models/providers you use, I'll prioritize registry coverage for you.

- Repo: https://github.com/Ahaozandaburada/modelalive
- PyPI: https://pypi.org/project/modelalive/
- Examples: https://github.com/Ahaozandaburada/modelalive/tree/main/examples

No sales pitch — project is MIT and free. Just want real integration feedback before wider launch.

Thanks,  
[Your name]

---

## Who to target

- AI startups with hardcoded model lists in env/config
- OSS agent frameworks (LangChain-adjacent, LiteLLM users)
- Teams on Bedrock/Azure with deployment-specific model strings
- r/LocalLLaMA power users running Ollama in production
