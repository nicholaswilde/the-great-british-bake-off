---
version: alpha
name: The Great British Bake Off Dataset & UI System
description: Visual design system, tokens, and aesthetic specifications for The Great British Bake Off (GBBO) tidy dataset, interactive Streamlit analytics dashboard, and publication assets.
colors:
  primary: "#cba6f7"        # Mauve (accent, branding, prominent highlights)
  secondary: "#89b4fa"      # Blue (interactive links, focus rings, primary action)
  tertiary: "#fab387"       # Peach (warm culinary highlight, Hollywood handshakes)
  neutral: "#1e1e2e"        # Base background fill
  neutral-light: "#cdd6f4"  # Primary foreground text
  surface: "#313244"        # Surface0 (cards, stat panels, container fills)
  surface-hover: "#45475a"  # Surface1 (hover states, borders, divider lines)
  crust: "#11111b"          # Crust (sidebar background, table wells)
  mantle: "#181825"         # Mantle (modal backdrops, tooltip bodies)
  text: "#cdd6f4"           # High-contrast body text
  text-muted: "#a6adc8"     # Subtext0 (secondary metadata, captions)
  success: "#a6e3a1"        # Green (Star Baker, survival, passed tests)
  warning: "#f9e2af"        # Yellow (technical rank risk, cautions)
  error: "#f38ba8"          # Red (eliminations, withdrawals, pipeline failures)
  info: "#74c7ec"           # Sapphire (general metrics, informational notices)
  lavender: "#b4befe"       # Lavender (baker demographic comparisons)
  teal: "#94e2d5"           # Teal (technical challenge scores and percentiles)
  tent-powder-blue: "#5c94b3" # Tent heritage powder blue (publication assets)
  tent-raspberry: "#c74163"   # Tent heritage raspberry (publication accents)
  tent-gold: "#d48c2e"        # Tent heritage caramel/gold
  tent-sage: "#4a7c59"        # Tent heritage sage green
typography:
  h1:
    fontFamily: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: -0.01em
  h3:
    fontFamily: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.4
  body-lg:
    fontFamily: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  body-md:
    fontFamily: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  caption:
    fontFamily: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.4
  mono:
    fontFamily: "JetBrains Mono", "Fira Code", SFMono-Regular, Menlo, Monaco, Consolas, monospace
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.4
rounded:
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    borderRadius: "{rounded.lg}"
    padding: "{spacing.lg}"
  button:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.neutral}"
    borderRadius: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
  badge:
    backgroundColor: "{colors.surface-hover}"
    textColor: "{colors.primary}"
    borderRadius: "{rounded.full}"
    padding: "{spacing.xs} {spacing.sm}"
  metric:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    borderRadius: "{rounded.md}"
    padding: "{spacing.md}"
---

# Design System: The Great British Bake Off

## Overview

The Great British Bake Off (GBBO) Dataset & Analytics platform pairs the warm, quintessential nostalgia of the British baking tent with a high-density, modern computational analytics interface.

The design identity balances two core modes:
1. **Interactive Exploratory Analytics (Catppuccin Mocha)**: An ergonomic, low-eyestrain dark interface powering the Streamlit web dashboard, interactive Altair/Vega charts, predictive modeling displays, and baker archetype inspectors.
2. **Tent Heritage Publication Assets**: Warm, pastel-rich visual themes used in publication-ready social cards, hex badges, R package vignettes, and research figures.

### Core Principles
- **Clarity Over Clutter**: Complex performance matrices, Kaplan-Meier curves, and probability trajectories are legible at a glance with strict visual hierarchy.
- **Accessible Color Semantics**: Results (Star Baker, Safe, Eliminated, Handshake) maintain unmistakable semantic color mappings across every table, chart, and card.
- **Rhythmic Geometry**: 8px spatial rhythm and softened geometric rounding (`8px` to `12px`) ensure containers feel friendly rather than clinical.

---

## Colors

### Catppuccin Mocha Interface Palette (Default)

The interactive dashboard uses the **Catppuccin Mocha** dark palette to maximize readability and focus during long exploratory sessions:

| Token | Hex | Role | Contrast vs `#1E1E2E` |
| :--- | :--- | :--- | :--- |
| `colors.neutral` (Base) | `#1E1E2E` | Primary app canvas and background fill | Canvas |
| `colors.mantle` (Mantle) | `#181825` | Tooltip bodies, dialog wells, sunken panels | Structural |
| `colors.crust` (Crust) | `#11111B` | Sidebar background, secondary wells | Structural |
| `colors.surface` (Surface0) | `#313244` | Stat cards, metric tiles, table headers | 1.3:1 (Container) |
| `colors.surface-hover` (Surface1) | `#45475A` | Interactive hover states, borders | 1.8:1 (Border) |
| `colors.text` (Text) | `#CDD6F4` | Primary high-contrast body & header typography | **13.5:1 (AAA)** |
| `colors.text-muted` (Subtext0) | `#A6ADC8` | Captions, subtitles, secondary metadata | **8.6:1 (AAA)** |
| `colors.primary` (Mauve) | `#CBA6F7` | Branding accent, hero titles, primary selections | **9.2:1 (AAA)** |
| `colors.secondary` (Blue) | `#89B4FA` | Interactive links, tab underlines, action focus | **9.1:1 (AAA)** |
| `colors.tertiary` (Peach) | `#FAB387` | Warm culinary callouts, handshake honors | **9.4:1 (AAA)** |

### Semantic Outcome Mappings

Never use arbitrary colors for competition states. Always use these standardized mappings:

| Competition State | Token | Hex | Meaning / Application |
| :--- | :--- | :--- | :--- |
| **STAR_BAKER / WINNER** | `colors.success` | `#A6E3A1` | Star Baker honor, series champion, top technical rank |
| **SAFE / RUNNER_UP** | `colors.info` | `#74C7EC` | Progressed to next week, finale finalist |
| **HOLLYWOOD_HANDSHAKE** | `colors.tertiary` | `#FAB387` | Hollywood handshake accolade, flavor master |
| **LOW / AT_RISK** | `colors.warning` | `#F9E2AF` | Bottom technical tier, judges' elimination warning |
| **ELIMINATED / WITHDREW** | `colors.error` | `#F38BA8` | Baker departure, challenge failure, withdrawal |
| **TECHNICAL_CHALLENGE** | `colors.teal` | `#94E2D5` | Blind technical judging and ranking stats |

### Tent Heritage Publication Palette

For static plots, paper figures (`dev/images/`), and R hex badges, use the editorial tent palette:
- **Powder Blue**: `#5C94B3` (Tent exterior canopy and workbench linoleum)
- **Raspberry**: `#C74163` (Summer pudding, jam layers, showstopper berry accents)
- **Gold Caramel**: `#D48C2E` (Choux pastry, spun sugar, gingerbread structures)
- **Sage Green**: `#4A7C59` (English estate lawn, pasture backdrop)
- **Dark Plum**: `#2B2038` (High-contrast title text on light canvases)

---

## Typography

### Font Families
- **Primary Interface**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `sans-serif`
- **Code & Identifiers**: `"JetBrains Mono"`, `"Fira Code"`, `SFMono-Regular`, `Consolas`, `monospace`
- **Editorial Publication**: `"DejaVu Sans"`, `"Liberation Sans"`, `sans-serif` (in `matplotlib` visualizers)

### Hierarchy

```
H1 (32px / 700 / 1.2)   — Page Titles ("The Great British Bake Off Explorer")
  H2 (24px / 600 / 1.3) — Section Headers ("Series Inspector", "Contender Trajectories")
    H3 (18px / 600 / 1.4) — Card Headers & Sub-analyses ("Episode 4: Bread Week")
      Body-LG (16px / 400 / 1.6) — Introductory copy & summaries
      Body-MD (14px / 400 / 1.5) — Standard data rows, table contents, explanations
      Caption (12px / 400 / 1.4) — Metadata, timestamps, footnote legends
      Mono (13px / 400 / 1.4)    — Relational keys (`baker_id`, `s17e05_s17_clara`)
```

---

## Layout & Spacing

### 8px Spatial Grid
All container padding, chart margins, and component alignments derive from an 8-point system:
- `xs` (4px): Inline pill padding, badge vertical offset
- `sm` (8px): Button padding, icon spacing, table cell padding
- `md` (16px): Card interior spacing, input margins, small gap
- `lg` (24px): Standard card container padding, grid column gaps
- `xl` (32px): Major section separation
- `xxl` (48px): Top-level view dividers

### Dashboard Anatomy (Streamlit)
- **Sidebar (`width: ~280px`, `background: #11111B`)**:
  - Sticky top brand marker with emoji icon (`🍰 GBBO Explorer`).
  - View navigation radio buttons.
  - Quick filters (Series selection, broadcast era).
  - Footer with repository version and license attribution.
- **Main Canvas (`background: #1E1E2E`)**:
  - Metric Strip: 4-column KPI cards across full width.
  - Two-Column Layout (`col_left: 60%`, `col_right: 40%`): Chart visualization on left, data breakdown on right.
  - Drill-down expanders (`st.expander`) for secondary statistical logs.

---

## Elevation & Depth

To preserve crisp readability in dark mode, avoid heavy drop shadows that muddy dark themes. Instead, communicate elevation through **surface luminance layering** and **fine border delineation**:

1. **Canvas (Lowest)**: `#1E1E2E` (Canvas body)
2. **Sunken/Sidebar**: `#11111B` (Crust)
3. **Card Layer (Level 1)**: `#313244` (Surface0) with `1px solid #45475A` border
4. **Interactive Hover (Level 2)**: `#45475A` (Surface1) with subtle glow
5. **Popover / Tooltip (Level 3)**: `#181825` (Mantle) with `1px solid #89B4FA` border, `z-index: 1000`

---

## Shapes

- **Badges & Pills**: `rounded.full` (9999px) for status indicators (`Star Baker`, `Eliminated`).
- **Cards & Data Panels**: `rounded.lg` (12px) for metric blocks and analytical chart wraps.
- **Buttons & Input Controls**: `rounded.md` (8px) for selectboxes, text search, and radio buttons.
- **Tooltips & Popovers**: `rounded.sm` (4px) for compact hovered data points.

---

## Components

### Metric Tiles (KPI Cards)
- **Container**: `backgroundColor: #313244`, `borderRadius: 12px`, `padding: 16px 20px`.
- **Label**: `fontSize: 13px`, `color: #A6ADC8`, uppercase with tracking.
- **Value**: `fontSize: 28px`, `fontWeight: 700`, `color: #CBA6F7` (or semantic outcome color).
- **Delta / Context**: `fontSize: 12px`, `color: #A6E3A1` (positive) or `#F38BA8` (negative).

### Chart Configurations (Altair / Vega-Lite)
- **Theme**: Dark background (`#1E1E2E` transparent canvas).
- **Axis Lines**: `#45475A`.
- **Grid Lines**: `#313244` dashed (0.8px stroke).
- **Axis Labels**: `#A6ADC8` (11px).
- **Axis Titles**: `#CDD6F4` (12px bold).
- **Color Scale**: Use semantic outcome tokens or Catppuccin accents (`[#89B4FA, #CBA6F7, #FAB387, #A6E3A1, #F38BA8]`).

### Status Badges
- **Star Baker**: Background `#A6E3A122`, text `#A6E3A1`, border `1px solid #A6E3A166`.
- **Eliminated**: Background `#F38BA822`, text `#F38BA8`, border `1px solid #F38BA866`.
- **Safe**: Background `#74C7EC22`, text `#74C7EC`, border `1px solid #74C7EC66`.
- **Handshake**: Background `#FAB38722`, text `#FAB387`, border `1px solid #FAB38766`.

---

## Do's and Don'ts

### Do's
- **DO** use the Catppuccin Mocha tokens (`#1E1E2E`, `#313244`, `#CDD6F4`, `#CBA6F7`) for all Streamlit UI components.
- **DO** strictly reserve `#A6E3A1` for Star Baker/winners and `#F38BA8` for eliminations/failures.
- **DO** verify all text-to-background combinations achieve a minimum **4.5:1 contrast ratio** (WCAG AA).
- **DO** format baker IDs, episode codes, and timestamps in monospace fonts.
- **DO** provide clear hover tooltips for dense charts showing both raw metrics and rank percentiles.

### Don'ts
- **DON'T** use pure black (`#000000`) or pure white (`#FFFFFF`) as canvas fills in dark mode.
- **DON'T** introduce arbitrary hex values outside of the token specification.
- **DON'T** use low-contrast pastel tones for body text against dark backgrounds.
- **DON'T** use harsh square corners (`0px` border-radius) on dashboard cards or badges.
- **DON'T** mix light-theme and dark-theme chart containers within the same dashboard view.
