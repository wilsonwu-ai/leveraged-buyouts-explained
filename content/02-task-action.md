## The task {#task}

**My task had two jobs: find a good company at a fair price, and pay for it without betting everything.** The first is a search problem. The second is math, which turned out to be the friendlier of the two. Here's what I did:

- I joined Searchfunder, an online community for people buying small companies (members only), and swapped notes with other searchers.
- I run a self-funded search, paying my own way instead of raising investor money up front.
- I talked with sellers, business brokers and bankers about how deals really get done.
- I built the illustrative model behind this page; the code is [on GitHub](https://github.com/wilsonwu-ai/leveraged-buyouts-explained), so you can check my math.
- I read the news and a lot of social media, to hear what people think of all this.

Step one was learning that there's more than one way to do it.

## Four ways to buy a company {#models}

**The LBO math is the same at every size; what changes is who pays for the search, who owns what, and who runs the company afterward.**

<!-- FIG:fig-models -->

- **Traditional search fund.** Investors pay for the search, about $400K to $500K, and the searcher ends up owning roughly a quarter to a third of the company after an 18 to 30 month hunt, per one SBA lending marketplace ([GoSBA Loans](https://gosbaloans.com/?p=9640)).
- **Self-funded search.** The searcher spends about $100K to $200K of their own money, buys with an SBA loan plus equity, can keep up to 100% and often buys within 12 to 24 months, per the same source.
- **Independent sponsor.** No fund at all: the sponsor finds and signs a deal first, then raises money for that one deal ([Revision Legal](https://revisionlegal.com/corporate/business-law/what-is-an-independent-sponsor/)).
- **Private equity fund.** Institutions invest in a fund that buys many companies. In GF Data's sample of private equity-backed deals, Q2 2026 buyouts averaged 7.0x the past year's adjusted EBITDA ([ACG](https://www.acg.org/news-trends/news/gf-data-reports-show-steady-middle-market-deal-flow-amid-more-selective)), and funds now hold companies about 7 years on average at exit ([Bain & Company](https://www.bain.com/insights/outlook-gaining-traction-global-private-equity-report-2026/)).

Does it work? Stanford's 2026 Search Fund Study tracked more than 850 US and Canadian search funds through 2025. 58% ever bought a company, typically after about 20 months; the median price of 2024 to 2025 deals was $16M; and pooled returns were a 33.9% IRR and 4.75x the money invested ([Stanford GSB](https://gsb.stanford.edu/insights/search-funds-keep-offering-proven-path-ownership)). IRR, the internal rate of return, is the yearly return on money, counting when it goes in and when it comes out.

Now the honest caveats. Those are traditional search funds, with deals far bigger than the illustrative company, and one law firm's summary says Stanford's 2024 edition did not evaluate self-funded searches ([Fredrikson & Byron](https://www.fredlaw.com/alert-search-funds-the-life-cycle)). Pooled returns add up all the money invested, so a few big winners can pull the average up. It's also getting harder: according to one advisory firm's summary of the Stanford study, 48% of the 2021 to 2024 funds had bought a company, against 86% of the 2007 to 2010 funds. Searchers sign about 2.5 LOIs (letters of intent: written offers that lay out the price and main terms) for every deal that closes ([Calder Group](https://caldergr.com/acquisition-search-is-getting-harder-takeaways-from-stanfords-2026-search-fund-study)). Outside the US and Canada, IESE found that 73% of finished searches bought a company, and of the exits, 38 made money and 11 lost money ([IESE](https://www.iese.edu/insight/articles/search-funds-record-expansion/)).

Whichever path you choose, the money stacks up the same way.

## The capital stack, visualized {#capital-stack}

**The price sets the loan, the loan sets the yearly payment, and the payment has to fit inside the company's cash with room to spare, so the bank's test caps what you can pay.**

A capital stack is every source of money in a deal, drawn as layers from the safest at the bottom to the riskiest on top. Here is the illustrative company at 4.0x, from the bottom up:

1. **SBA 7(a) loan: $3.83M, 90% of the $4.25M total cost.** The 7(a) is the SBA's main loan program: a bank lends, and the SBA guarantees part of it. It's senior debt, meaning it gets repaid first. A single 7(a) loan tops out at $5M ([SBA](https://www.sba.gov/funding-programs/loans/7a-loans)), and since 4 July 2026 a borrower can combine 7(a) and 504 loans for up to $10M ([SBA](https://www.sba.gov/article/2026/05/18/sba-doubles-cumulative-7a-504-loan-limit-10-million)); confirm with your lender. The model assumes 9.75% over 10 years: the prime rate, the benchmark banks use to price many loans, was 7.00% ([Federal Reserve](https://www.federalreserve.gov/releases/h15/)), and the extra 2.75 points are my assumption.
2. **Seller note on full standby: $213K, 5%.** A seller note means the seller lends part of the price; full standby means no payments while the SBA loan is outstanding. In the model it grows at 6% a year and is repaid when the company is sold.
3. **Buyer cash: $213K, 5%.** With the seller note, this forms the equity injection, the money the buyer's side puts in beneath the loan. One law firm, Starfield & Smith, reads the new SBA rulebook (SOP 50 10 8.1) as requiring 10% of total project costs for an initial acquisition ([Starfield & Smith](https://starfieldsmith.com/2026/09/best-practices-change-of-ownership-transactions-under-sop-50-10-8-1-what-sba-lenders-need-to-know/)), and PilieroMazza reads seller notes and other standby debt as capped at half of that minimum ([PilieroMazza](https://pilieromazza.com/five-sba-7a-changes-that-could-reshape-business-acquisitions)). As one SBA loan broker reads the new rules, at least half of the 10% must be the buyer's own money. Confirm with your lender.
4. **Investors: none at this price.** They show up when the price rises.

The top of the stack takes the first loss. When lenders took over Pluralsight in 2024, Vista's roughly $4B of equity was essentially wiped out (The New York Times, DealBook, "Private Equity's Private Credit Problem", 12 March 2026) <!-- src:nyt-dealbook -->. Same physics, smaller numbers.

Now the bank's test. The company makes $800K a year for its lenders and the payment is $600K, so the DSCR is 1.33x: a pass, with $200K to spare.

<!-- FIG:fig-stack -->

Try it: drag the price to 4.5x. The payment climbs to $671K, the DSCR falls to 1.19x, and the test fails. At 5.5x the DSCR is 0.99x, and the $5.18M loan would also go past the $5.0M limit on a 7(a) loan. The highest price that passes is $4.28M, or 4.28x. Then pick 5.0x and switch on investors: $647K of their money brings the DSCR back to 1.25x, and the buyer keeps 74.1%. That split follows the step-up assumption in [my first explainer](https://wilsonwu-ai.github.io/buying-a-business-explained/), which also covers how searchers raise this layer. All illustrative, and the 1.25x test and the 7(a) limit are one reading of the SBA rules; confirm with your lender. The takeaway: a lower price can do the job of outside money.

<details class="deep" markdown="1">
<summary>For searchers and investors: the formulas and the fine print</summary>

- **CFADS** (cash flow available for debt service) = EBITDA x 90% (after cash taxes of 10%) minus upkeep of 2% of revenue = $900K minus $100K = $800K.
- **Project cost** = price + $150K of fees + a $100K cash cushion = $4.25M at 4.0x. Buyer cash = 5% of it, seller note = 5%, SBA loan = the rest, minus any investors.
- **Yearly payment** = 12 x L x r / (1 minus (1 + r) to the power of minus n), with r = 9.75% / 12 and n = 120 months: $600K on a $3.83M loan.
- **DSCR** = CFADS / yearly payment = $800K / $600K = 1.33x. The biggest loan that passes has a payment of CFADS / 1.25 = $640K, about $4.08M of loan; investors fill whatever the price needs above that.
- The model ignores the SBA guaranty fee and any lender fees beyond the $150K of closing costs it assumes. SOP 50 10 8.1 takes effect on 1 October 2026 ([SBA](https://legacy.sba.gov/document/information-notice-5000-880695-issuance-sop-50-10-81)). [PilieroMazza](https://pilieromazza.com/five-sba-7a-changes-that-could-reshape-business-acquisitions) says it applies to loans that get an SBA loan number on or after that date, while [Starfield & Smith](https://starfieldsmith.com/2026/09/best-practices-change-of-ownership-transactions-under-sop-50-10-8-1-what-sba-lenders-need-to-know/) says loans approved on or after it, so ask your lender which rules cover your loan. Starfield & Smith also reads it as capping standby debt, seller debt and small outside investors without control at half of the 10% together. On the loan broker's reading, a seller note counts toward the equity only on full standby, and investor money inside the 10% can receive only tax distributions until the loan is repaid. Confirm with your lender.
- For scale: the SBA approved 56,130 7(a) loans worth $32.4B in fiscal 2026, a year that included a 43-day federal shutdown that halted SBA lending ([SBA](https://legacy.sba.gov/article/2026/11/02/sba-fuels-main-street-growth-100-billion-delivered-fy26)), after 77,600 worth $37B in fiscal 2025 ([SBA](https://legacy.sba.gov/article/2025/09/30/trump-sba-delivers-record-capital-small-businesses-fy25)). In GF Data's sample of private equity-backed deals, new platform buyouts carried total debt of 2.9x EBITDA in Q2 2026, with senior debt priced at 7.8% ([ACG](https://www.acg.org/news-trends/news/gf-data-reports-show-steady-middle-market-deal-flow-amid-more-selective)).

</details>

So the math puts a ceiling on the price. Next question: where do you find a company to put under it?

## Where deals come from {#finding-deals}

**The size of the company decides who sells it: business brokers handle small companies, M&A advisors the middle and investment banks the largest, while marketplaces and direct outreach to owners cut across sizes.**

The sell side is the seller and the advisors working for them; the buy side is the buyer and theirs. A business broker sells small, owner-run companies for a commission. An M&A (mergers and acquisitions) advisor runs a more formal sale for mid-sized companies, and an investment banker advises on the largest, often through auctions. A proprietary deal is one you find yourself, before the owner hires anyone to sell.

<!-- FIG:fig-sellers -->

Size also sets the price. In a Q2 2026 survey of 255 advisors by the IBBA and M&A Source, reported multiples rose from 2.0x SDE for companies worth under $500K to 3.1x at $1M to $2M, then 4.0x EBITDA at $2M to $5M and 5.8x at $5M to $50M ([IBBA](https://www.ibba.org/wp-content/uploads/2026/08/mp-highlights-q2-2026.pdf)). SDE, seller's discretionary earnings, is profit plus the owner's own pay and perks, the usual yardstick for owner-run businesses. The illustrative company, at $4.0M, would sit in the band where the reported multiple was also 4.0x. Sellers pay the advisors: business brokers typically charge 8% to 12% of the price, often with a $25K to $75K minimum, and M&A advisors typically charge less as deals grow, down to 2% to 5% on $25M to $100M, per one 2026 guide ([CT Acquisitions](https://www.ctacquisitions.com/ma-advisor-fees-how-much-do-they-charge/)).

Each channel asks something different of a buyer. Broker listings reward buyers who are prepared and financeable. Advisors run formal processes: 87% of $5M-plus deals drew 3 or more offers ([IBBA and M&A Source](https://www.webull.com/news/15462423712777216)). Marketplaces such as BizBuySell are easy to browse, and BizBuySell's president said buyers are getting more selective ([BizBuySell](https://finviz.com/news/404656/bizbuysell-releases-q3-2026-insight-report)). Direct outreach is slow, but with 70% of owners lacking a formal succession plan or only in early-stage planning (Chase), many owners haven't been asked yet.

Once a seller is ready, the sale runs on a fairly standard track.

## How a sale runs {#process}

**A sale is a funnel that narrows step by step, from a short teaser to the closing, and it usually takes months.** One firm puts a typical sale at 6 to 12 months in all ([BD Emerson](https://www.bdemerson.com/article/sell-side-ma-process)); the IBBA and M&A Source survey found deals averaged 6 to 10 months on Main Street and 11 to 12 in the lower middle market ([press release](https://www.webull.com/news/15462423712777216)).

<!-- FIG:fig-process -->

The steps, with BD Emerson's typical times:

1. **The seller gets ready:** 2 to 4 months.
2. **Teaser, NDA and CIM:** 4 to 8 weeks. The teaser is a short summary, usually one or two pages, without the company's name. Interested buyers sign an NDA, a non-disclosure agreement to keep what they learn private, and receive the CIM, the confidential information memorandum: the seller's detailed booklet on the company.
3. **IOIs and management meetings:** 4 to 8 weeks. An IOI, or indication of interest, is a non-binding price range that earns you time with the owner.
4. **The LOI**, which usually starts exclusivity: a period when the seller agrees not to negotiate with anyone else. Exclusivity plus confirming diligence usually takes 60 to 90 days ([BD Emerson](https://www.bdemerson.com/article/private-equity-due-diligence)), with documents shared in a data room, an online folder for the buyer to check.
5. **Diligence and the purchase agreement:** 6 to 12 weeks. Alongside run the quality of earnings review (an accountant's check that the earnings are real), about 4 to 6 weeks ([BD Emerson](https://www.bdemerson.com/article/quality-of-earnings-report-cost)), and the SBA loan, typically 30 to 90 days from application to closing ([Surge Business Law](https://surge.law/buying-a-business-with-sba-loan/)).
6. **Closing:** 2 to 6 weeks.

Remember those 2.5 signed LOIs for every closed deal: plenty of offers fall out of this funnel after the handshake. That's the map. Part 3 is what it takes to walk it.
