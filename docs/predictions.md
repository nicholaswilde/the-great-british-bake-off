# The Great British Bake Off Series 17 Empirical Predictions & Accuracy Ledger

This document tracks weekly probabilistic forecasts, baker trajectory shifts, and empirical model accuracy against actual broadcast outcomes for **The Great British Bake Off Series 17**.

Predictions are calculated using an empirical modeling engine calibrated on 16 historical GBBO series: **Cumulative Technical Challenge Percentile (30%)**, **Recent Technical Form (25%)**, **Star Baker Momentum & Callouts (20%)**, **Hollywood Handshakes (15%)**, and **Winner Age Distribution (5%)**.

---

## 🎂 Latest Contender Rankings (After Episode 4)

**Model Context**: Active Bakers: 8/12 | Calibrated Historical Sample: Series 1–16

| Rank | Baker | Age | Avg Tech % | Handshakes | Star Bakers | Next Star Baker | Next Elim Risk | Win Prob | Finale Prob |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **Tom Whittaker** | 25 | 71.1% | 0 | 2 | **26.7%** | 4.4% | **30.6%** | **87.7%** |
| 2 | **Mo Mahir** | 21 | 72.8% | 0 | 1 | **11.7%** | 8.4% | **15.7%** | **52.2%** |
| 3 | **Clara Satchell-Silva** | 24 | 55.5% | 0 | 1 | **14.4%** | 7.1% | **14.1%** | **44.9%** |
| 4 | **Moyin Odeniran** | 22 | 58.8% | 1 | 0 | **12.2%** | 8.5% | **11.0%** | **38.2%** |
| 5 | **Gabe Capes** | 32 | 84.1% | 0 | 0 | **15.6%** | 8.5% | **10.5%** | **42.0%** |
| 6 | **Elizabeth 'Connie' Lewis** | 63 | 63.6% | 0 | 0 | **8.7%** | 13.9% | **6.8%** | **29.0%** |
| 7 | **Dr. Yannis Ali** | 28 | 28.6% | 0 | 0 | **5.9%** | 23.8% | **6.3%** | **20.8%** |
| 8 | **Gary Harding** | 67 | 30.2% | 0 | 0 | **4.9%** | 25.4% | **5.1%** | **18.3%** |

---

## 📈 Weekly Win Probability Trajectory

Progression of calibrated series win probabilities across broadcast episodes:

| Baker | Status | Episode 1 | Episode 2 | Episode 3 | Episode 4 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Tom Whittaker** | Active | 11.9% | 19.9% | 17.0% | 30.6% |
| **Mo Mahir** | Active | 16.5% | 17.3% | 17.5% | 15.7% |
| **Clara Satchell-Silva** | Active | 6.7% | 6.0% | 13.0% | 14.1% |
| **Moyin Odeniran** | Active | 6.0% | 7.1% | 10.5% | 11.0% |
| **Gabe Capes** | Active | 10.8% | 9.3% | 10.1% | 10.5% |
| **Elizabeth 'Connie' Lewis** | Active | 6.7% | 7.8% | 7.2% | 6.8% |
| **Dr. Yannis Ali** | Active | 7.7% | 7.1% | 6.6% | 6.3% |
| **Gary Harding** | Active | 9.1% | 5.9% | 5.6% | 5.1% |
| **Nikki** | Withdrew | 7.6% | 6.2% | 6.6% | 0.0% |
| **Molly Chauhan** | Eliminated | 5.3% | 6.2% | 5.9% | 0.0% |
| **Shannon Amy** | Eliminated | 6.1% | 7.2% | 0.0% | 0.0% |
| **Danni** | Eliminated | 5.4% | 0.0% | 0.0% | 0.0% |

---

## 🎯 Prediction Accuracy vs Actual Broadcast Outcomes

Comparison of model forecasts against actual weekly judging results:

| Episode | Actual Star Baker | Model Top SB Candidate | Actual Elimination | Model Top Elim Risk |
| :---: | :--- | :--- | :--- | :--- |
| Episode 1 | **Mo Mahir** | Mo Mahir (18.1%) | **None** | Molly Chauhan (16.2%) |
| Episode 2 | **Tom Whittaker** | Tom Whittaker (22.8%) | **Danni** | Clara Satchell-Silva (14.1%) |
| Episode 3 | **Clara Satchell-Silva** | Clara Satchell-Silva (16.6%) | **Shannon Amy** | Molly Chauhan (19.6%) |
| Episode 4 | **Tom Whittaker** | Tom Whittaker (26.7%) | **Molly Chauhan** | Gary Harding (25.4%) |

### Elimination & Baker Status Verification
- **Nikki**: Withdrew. Win & Star Baker probability correctly set to **0.0%**.
- **Molly Chauhan**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.
- **Shannon Amy**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.
- **Danni**: Eliminated. Win & Star Baker probability correctly set to **0.0%**.

---

## 🔬 Model Diagnostics & Scoring Methodology
- **Cumulative Technical Rank**: Historical series winners averaged a 60.1% technical percentile rank; finalists averaged 55.5%; early eliminated bakers averaged 40.7%.
- **Judging Momentum**: 36.2% of non-first-episode eliminated bakers were placed *at risk* or in the bottom in the immediately preceding episode.
- **Hollywood Handshakes**: Handshakes strongly correlate with Star Baker performance and series longevity.
- **Peak Winner Age**: Gaussian centered at 32.5 ± 9.9 years.
