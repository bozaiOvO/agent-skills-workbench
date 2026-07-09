# Consumer Product Comparisons From Screenshots

Use this reference when the user sends shopping screenshots or asks which product is better, whether an upgrade is worth it, or what two products differ on.

## Session Pattern

In the 2026-06-26 headphone comparison session, the user compared Sony WH-1000XM5 and WH-1000XM6 from JD screenshots. The practical need was not audiophile quality; it was office quietness and concentration. The useful answer combined:

- visible screenshot facts: model, store/self-operated status, subsidy price, delivery/service tags;
- current price delta: compute arithmetic with a tool when stating exact differences;
- official/current specs: verify before naming processor, weight, battery life, Bluetooth, codec, or microphone counts;
- user goal: decide whether the upgrade meaningfully changes the user's use case.

## Recommended Workflow

1. Extract only visible offer facts from the image: model, price, store, rating/sales, promo labels, and whether it is self-operated/official.
2. Ask what the user actually needs only if it is unclear. If they already state a use case, make that the axis of the comparison.
3. Verify specs from official or current reliable pages before using exact claims. If official sites block direct fetch with 403, retry through a text extraction proxy such as:

```text
https://r.jina.ai/http://https://example.com/path
```

4. Separate three layers in the answer:

- Hard facts: visible prices, official spec numbers, supported features.
- Practical inference: which differences matter for the user's scenario.
- Buying verdict: what to buy at the shown price, and when the other option becomes rational.

5. Do arithmetic with a tool when quoting a price gap.
6. Keep the final answer short and human. Avoid turning a buying question into a full review unless the user asks.

## Pitfalls

- Do not say “newer is better” as the conclusion. Say what the newer product improves and whether that improvement maps to the use case.
- Do not overpromise ANC. For headphones, active noise cancelling is strongest for steady low-frequency noise and weaker for sudden speech, keyboard clicks, and sharp sounds.
- Do not treat third-party marketing claims as official specs. If exact details are blocked or uncertain, say “公开资料显示/我能确认的是” or omit the exact number.
- Do not ignore store/channel risk. For marketplace screenshots, official/self-operated store and after-sales terms can matter as much as small price differences.

## Example Verdict Shape

For office concentration:

- Buy the cheaper previous flagship when it already covers the core need and the upgrade price gap is large.
- Buy the newer model when the user is budget-insensitive, often takes calls, travels frequently, needs better portability, or explicitly wants the newest flagship for a multi-year hold.
