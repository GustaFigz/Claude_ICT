# Next Steps — Start Here

> **You are here:** Configuration ready, CLAUDE.md configured, structure in place.
> **Next:** Complete Phase 0, then begin Phase 1.

---

## What Was Just Done

✅ **CLAUDE.md** — Claude's instructions configured (compact, references JSON only)

✅ **Configuration templates** — Account, symbols, risk rules prepared

✅ **Rules & definitions** — execution_policy.md, ict_definitions.md, report_template.md all prepared

✅ **README.md** — Complete project guide with phases, structure, workflow

✅ **PHASE_0_CHECKLIST.md** — Systematic checklist for all decisions

✅ **Project structure** — Folders created: config/, rules/, data_pipeline/, ict_engine/, context/, reports/, logs/

✅ **.gitignore** — Protects credentials, generated files, account data

---

## Your Task: Complete Phase 0 (3-5 hours)

### Step 1: Make Your Decisions (Take Your Time)

Open **PHASE_0_CHECKLIST.md** and answer every question:

1. **Account parameters** — FTMO type, capital, loss limits
2. **Trading assets** — Choose 1-3 symbols (recommend: EURUSD)
3. **Session** — Choose primary trading window (recommend: NY AM 13:00-16:00 CEST)
4. **Risk rules** — Position size, R:R ratio, max consecutive losses
5. **Data sources** — MT5 account, OANDA credentials
6. **ICT model** — Choose first model (recommend: Silver Bullet)
7. **Validation rules** — Define all blockers (data quality, news, session, risk)
8. **Logging** — Confirm report structure and trade logging location

**Critical:** Don't rush this. These decisions determine everything that follows.

### Step 2: Update Configuration Files

Once you've answered the checklist, update:

```bash
# Copy and edit these:
config/account.yaml          ← Fill in YOUR account details
config/symbols.yaml          ← Enable only symbols you'll trade
.env                         ← Add MT5 + OANDA credentials
```

### Step 3: Verify You Can Answer These Questions

Before moving to Phase 1:

- "What's the daily loss limit I won't exceed?"
- "What's my riskd per trade in %?"
- "When can I trade (session window)?"
- "What's the first ICT model I'll implement?"
- "How many confluency factors minimum?"
- "What stops me from trading (blockers)?"

**If you can't answer all these, go back to the checklist.**

### Step 4: Commit Your Decisions

Once complete, tell me:

```
Phase 0 Complete!

Account: FTMO [Type], $[Capital]
Symbol: [Your symbol]
Session: [NY AM / Other]
Risk per trade: [%]
First model: [Silver Bullet / Other]
```

I'll then validate everything is aligned before Phase 1.

---

## Phase 1: When You're Ready (Week 1-2)

Phase 1 builds the **data contracts** — all the structures the system will use.

You'll create:

```
data_pipeline/
  schemas.py       ← Pydantic models for: Candle, Event, Account, Level, Setup
  
ict_engine/
  (empty, ready for Phase 2)
```

The goal: define what valid data looks like so nothing bad can get through.

**You don't start this until Phase 0 is 100% done and verified.**

---

## What NOT to Do Yet

❌ Don't write Python code (Phase 0 first)
❌ Don't open the FTMO challenge account (Phase 6+)
❌ Don't trade any real account (Phase 8+ at earliest)
❌ Don't assume your edge is proven (it needs 50+ trades first)
❌ Don't change CLAUDE.md (it's configured correctly)

---

## Files You Need to Read

In this order:

1. ✅ **README.md** — Complete overview (read once)
2. ✅ **CLAUDE.md** — How Claude behaves (re-read if unsure)
3. ✅ **PHASE_0_CHECKLIST.md** — Your todo list (fill in completely)
4. ⏭️ **rules/execution_policy.md** — FTMO rules (reference, understand deeply)
5. ⏭️ **rules/ict_definitions.md** — ICT definitions (reference for Phase 1+)
6. ⏭️ **rules/report_template.md** — Report structure (reference)

---

## When Phase 0 is Done

You will have defined:

✅ What the system trades (symbol, timeframes)
✅ When it trades (session, hours, Kill Zones)
✅ How much risk (% per trade, max per day, max total)
✅ When it stops (blockers: drawdown, news, confluency, etc.)
✅ How it logs (report format, trade metadata)
✅ How it validates (data sources, agreementt checks)

Everything after Phase 0 builds on these decisions. Changing them later is expensive (rebuilding code).

---

## Communication Going Forward

Once you complete Phase 0:

1. **Tell me you're done** — Share your answers from the checklist
2. **I'll validate** — Make sure everything is internally consistent
3. **Phase 1 begins** — We'll start building the data schemas
4. **Iterative development** — Each phase 1-2 weeks, fully testable before next

---

## Questions to Ask Before Proceeding

If you're unsure about anything in the checklist:

- "What does 'risk per trade 0.50%' actually mean in position sizing?"
- "Why NY AM Silver Bullet and not [other model]?"
- "What happens if data from MT5 and OANDA disagree?"
- "How do I know when to stop trading for the day?"

**Better to ask now than build wrong for weeks.**

---

## Emergency: If You Get Stuck

1. **Re-read PHASE_0_CHECKLIST.md** — Most questions are answered there
2. **Check ANALISE_CRITICA_E_PLANO.md** — Deep context for why we're doing this
3. **Review README.md phases** — Understand the flow
4. **Ask me** — I'm here to clarify

---

## Your Decision Point

**Today (Phase 0):**
- [ ] Read PHASE_0_CHECKLIST.md completely
- [ ] Answer all questions
- [ ] Update config/*.yaml and .env
- [ ] Come back and tell me you're done

**Result:** System is defined, ready to build.

---

**Next message:** "Phase 0 complete! Here are my decisions..."

---

*This is not a shortcut. This is how we reduce FTMO failure from 90% to something manageable.*
