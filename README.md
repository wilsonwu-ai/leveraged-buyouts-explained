# Leveraged buyouts, explained

How a small company gets bought mostly with borrowed money, told from the seat of someone searching for one to buy: what to buy, the capital stack, where deals come from, quality of earnings, due diligence, closing, Day 1 cash, the seller's handover, value creation and the exit. Search funds and ETA (entrepreneurship through acquisition), in plain language.

**Read it here:** https://wilsonwu-ai.github.io/leveraged-buyouts-explained/

By Wilson Wu, founder of Dubbs Capital: an operator who studies AI engineering and is searching for a small business to buy.

## The story in three parts

- **Situation.** I want to buy one small, steady company and make it better with what I know about running a business and building AI tools. The part I understood least was the money: how one buyer pays millions for a company with mostly borrowed money, and what can go wrong.
- **Task and action.** I joined a community of searchers, talked with sellers, brokers and bankers, read the SBA's new lending rules, and built a small model of an illustrative company to test the math.
- **Result.** The whole path from finding a deal to selling it: who sells companies and how, the deal team, quality of earnings, a due diligence checklist, closing, the cash a buyer needs on Day 1, how long the seller stays, value creation with AI tools, and an exit after 5 to 7 years. The page ends with what the news and social media say about buyouts, and five lessons.

The page is written for two readers at once. Most sections have a box called "The simple version" for anyone, and several have a deeper panel for searchers and investors. There are 16 diagrams and charts, several of them interactive, and a narrated video of about 90 seconds with captions.

## How the numbers were checked

- **The illustrative company.** Every worked-example number comes from `model/lbo_model.py`: a made-up company with $1.0M of EBITDA on $5.0M of revenue, not a real business. The scenarios are illustrations, not forecasts, and returns count sale proceeds only, before fees and taxes.
- **SBA rules.** The SBA's SOP 50 10 8.1 applies to loans from 1 October 2026. Where the page states a rule, it says it is one reading and that you should confirm it with your lender.
- **Market and industry figures.** Each links to its source, and every source is listed in the page's Sources section.
- **News.** Coverage in The Wall Street Journal, The New York Times, the Financial Times and The Economist was read in full and is paraphrased, never copied.
- **Social media.** Searches on X and Hacker News, read on 7 November 2026, with Reddit read through search results only. The page reports themes; only public figures are named.
- **Before publishing,** a separate pass compared every number, rule and date in the copy against its source.

## What is in this repository

| Path | What it holds |
|---|---|
| `content/` | The copy, one markdown file per part |
| `templates/` | The page template and the 16 figure partials |
| `model/` | The illustrative buyout model, the sourced facts, the source list and `site_data.json`, which feeds every chart |
| `docs/` | The built site that GitHub Pages serves |
| `motion/` | Source for the narrated video (HyperFrames compositions, script and caption builder) |

## Rebuild the page

Python 3 and the `markdown` package are all the build needs.

```bash
pip install markdown
python3 model/lbo_model.py       # the illustrative company -> model/lbo_model.json
python3 model/build_data.py      # model plus sourced facts -> model/site_data.json
python3 build.py                 # copy, figures and data -> docs/index.html
python3 -m http.server --directory docs 8000
```

The charts use D3 and GSAP from cdnjs. Each chart drawn in JavaScript has a data table behind it, so its numbers can still be read if the script fails to load. The video's narration is regenerated with `motion/tts.py`, which needs your own OpenAI API key in the environment.

The first explainer in this series covers the equity side of a purchase: [Buying a business, explained](https://wilsonwu-ai.github.io/buying-a-business-explained/).

Educational only. Not investment, legal or tax advice. The worked example is an illustrative company, not a real deal.
