# AI Placement Interview — restructured

## Files

| File | Responsibility |
|---|---|
| `app.py` | Entry point. Sets page config, loads CSS, routes between home and interview screens. ~20 lines. |
| `config.py` | Env vars, the cached Groq client, and every constant (model names, question count, interview modes). |
| `prompts.py` | Every prompt template as its own function. Tune the interviewer's behavior here without touching logic. |
| `ai_service.py` | All Groq calls (chat + speech-to-text). No Streamlit/session-state code. |
| `resume_service.py` | PDF → text extraction. |
| `state.py` | The shape of `st.session_state` and every transition (start, submit answer, reveal answer, advance, reset). |
| `components.py` | All rendering: hero, cards, progress bar, chat bubbles, forms. |
| `styles.css` | Visual design (see below). |

Run it the same way as before:

```
pip install -r requirements.txt
streamlit run app.py
```

## What changed structurally

- **One file → eight.** The original `app.py` mixed config, prompts, API calls, state
  management and rendering in a single 900-line file. Each of those is now its own
  module, so a change to (say) a prompt can't accidentally touch UI code.
- **The Groq client is cached** with `st.cache_resource` instead of being rebuilt
  implicitly on every rerun.
- **Session-state transitions are named functions** (`start_new_interview`,
  `record_answer`, `reveal_correct_answer`, `advance_to_next_question`) instead of
  being inlined inside button `if` blocks — the button handlers in `components.py`
  are now a couple of lines each.
- **Chat-bubble rendering is data-driven**: one `MESSAGE_STYLES` dict plus one loop,
  instead of four near-identical `if/elif` blocks.
- **`get_interview_history()`** builds the transcript from a small label lookup
  table instead of four separate string-concatenation branches.

## What changed visually

The old UI used a purple/indigo gradient with heavy glass-blur cards — a look that's
become the generic default for AI-generated dashboards. The new one:

- A warm paper background with a single accent color (deep teal), plus a muted
  amber used only for the progress fill and the "ideal answer" marker — not a
  five-color gradient.
- A serif (Fraunces) for headings paired with a sans-serif (IBM Plex Sans) for
  body text, instead of one typeface doing every job.
- Flat cards with a hairline border and a soft shadow — no backdrop blur, no
  all-caps tracked labels, no gradient-clipped headline text.
- Motion is restrained to one fade-up entrance per card and direct hover/focus
  feedback on buttons and inputs; nothing animates on its own after load.
  `prefers-reduced-motion` is respected.
- Fixed sizing issues: buttons have a consistent 44px min-height, the textarea
  and mic button line up on the same baseline, and the mic column gets a fixed
  46px width on small screens instead of being squeezed into 9% of a narrow
  viewport.