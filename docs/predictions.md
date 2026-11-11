# The Great British Bake Off Series 17 Empirical Predictions & Accuracy Ledger

This document tracks weekly probabilistic forecasts, baker trajectory shifts, and empirical model accuracy against actual broadcast outcomes for **The Great British Bake Off Series 17**.

Predictions are calculated using an empirical modeling engine calibrated on 16 historical GBBO series: **Cumulative Technical Challenge Percentile (30%)**, **Recent Technical Form (25%)**, **Star Baker Momentum & Callouts (20%)**, **Hollywood Handshakes (15%)**, and **Winner Age Distribution (5%)**.

---

## 🎂 Latest Contender Rankings (After Episode 8)

**Model Context**: Active Bakers: 4/12 | Calibrated Historical Sample: Series 1–16

| Rank | Baker | Age | Avg Tech % | Handshakes | Star Bakers | Next Star Baker | Next Elim Risk | Win Prob | Finale Prob |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **Tom Whittaker** | 25 | 76.3% | 0 | 3 | **40.4%** | 11.4% | **54.0%** | **95.0%** |
| 2 | **Moyin Odeniran** | 22 | 58.8% | 1 | 1 | **31.1%** | 17.6% | **18.4%** | **55.9%** |
| 3 | **Gabe Capes** | 32 | 73.8% | 0 | 1 | **18.1%** | 26.3% | **16.1%** | **53.4%** |
| 4 | **Mo Mahir** | 21 | 49.1% | 0 | 1 | **10.4%** | 44.6% | **11.5%** | **37.4%** |

---

## 📈 Weekly Win Probability Trajectory

Progression of calibrated series win probabilities across broadcast episodes:

| Baker | Status | Episode 1 | Episode 2 | Episode 3 | Episode 4 | Episode 5 | Episode 6 | Episode 7 | Episode 8 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tom Whittaker** | Active | 11.9% | 19.9% | 17.0% | 30.6% | 30.0% | 30.0% | 51.8% | 54.0% |
| **Moyin Odeniran** | Active | 6.0% | 7.1% | 10.5% | 11.0% | 10.2% | 10.2% | 9.6% | 18.4% |
| **Gabe Capes** | Active | 10.8% | 9.3% | 10.1% | 10.5% | 10.3% | 10.3% | 16.4% | 16.1% |
| **Mo Mahir** | Active | 16.5% | 17.3% | 17.5% | 15.7% | 14.9% | 14.9% | 12.1% | 11.5% |
| **Elizabeth "Connie" Lewis** | Eliminated | 6.7% | 7.8% | 7.2% | 6.8% | 13.7% | 13.7% | 10.2% | 0.0% |
| **Gary Harding** | Eliminated | 9.1% | 5.9% | 5.6% | 5.1% | 5.9% | 5.9% | 0.0% | 0.0% |
| **Clara Satchell-Silva** | Eliminated | 6.7% | 6.0% | 13.0% | 14.1% | 14.9% | 14.9% | 0.0% | 0.0% |
| **Yannis Ali** | Eliminated | 7.7% | 7.1% | 6.6% | 6.3% | 0.0% | 0.0% | 0.0% | 0.0% |
| **Nikki Porter** | Withdrew | 7.6% | 6.2% | 6.6% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| **Molly Chauhan** | Eliminated | 5.3% | 6.2% | 5.9% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| **Shannon Amy** | Eliminated | 6.1% | 7.2% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| **Danni Noke** | Eliminated | 5.4% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |

---

## 🎯 Prediction Accuracy vs Actual Broadcast Outcomes

Comparison of model forecasts against actual weekly judging results:

| Episode | Actual Star Baker | Model Top SB Candidate | Actual Elimination | Model Top Elim Risk |
| :---: | :--- | :--- | :--- | :--- |
| Episode 1 | **Mo Mahir** | Mo Mahir (18.1%) | **—** | Molly Chauhan (16.2%) |
| Episode 2 | **Tom Whittaker** | Tom Whittaker (22.8%) | **Danni Noke** | Clara Satchell-Silva (14.1%) |
| Episode 3 | **Clara Satchell-Silva** | Clara Satchell-Silva (16.6%) | **Shannon Amy** | Molly Chauhan (19.6%) |
| Episode 4 | **Tom Whittaker** | Tom Whittaker (26.7%) | **Molly Chauhan (Elim), Nikki Porter (Withdrew)** | Gary Harding (25.4%) |
| Episode 5 | **Elizabeth "Connie" Lewis** | Elizabeth 'Connie' Lewis (24.1%) | **Yannis Ali** | Moyin Odeniran (22.3%) |
| Episode 6 | **Tom Whittaker** | Tom Whittaker (18.5%) | **Clara Satchell-Silva** | Moyin Odeniran (22.3%) |
| Episode 7 | **Gabe Capes** | Tom Whittaker (35.4%) | **Gary Harding** | Elizabeth 'Connie' Lewis (30.9%) |
| Episode 8 | **Moyin Odeniran** | Tom Whittaker (40.4%) | **Elizabeth "Connie" Lewis** | Mo Mahir (44.6%) |

### Elimination & Baker Status Verification
- **Elizabeth "Connie" Lewis**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.
- **Gary Harding**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.
- **Clara Satchell-Silva**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.
- **Yannis Ali**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.
- **Nikki Porter**: Withdrew. Win & Star Baker probability correctly set to **0.0%**.
- **Molly Chauhan**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.
- **Shannon Amy**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.
- **Danni Noke**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.

---

## 🔬 Model Diagnostics & Scoring Methodology
- **Cumulative Technical Rank**: Historical series winners averaged a 60.1% technical percentile rank; finalists averaged 55.5%; early eliminated bakers averaged 40.7%.
- **Judging Momentum**: 36.2% of non-first-episode eliminated bakers were placed *at risk* or in the bottom in the immediately preceding episode.
- **Hollywood Handshakes**: Handshakes strongly correlate with Star Baker performance and series longevity.
- **Peak Winner Age**: Gaussian centered at 32.5 ± 9.9 years.
