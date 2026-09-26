# Desmos Companion Pages Design Refresh Guide

## Overview & Direction
This document outlines layout, typography, visual hierarchy, and copy recommendations for the incremental redesign of the companion pages (Activities/Library, Study Assistant, and Web Resources) while preserving the core Desmos scientific calculator and its existing green/white mathematical utility aesthetic.

---

## 1. Document Head & Favicon Updates
- **Document Title**: `Desmos | Testing`
- **Favicon URL**: `https://customer-assets-cm19k8pv.emergentagent.net/job_calc-unblocked/artifacts/izz9rm1p_www.desmos.webp`
- **HTML Meta Tag**: Ensure `<link rel="icon" type="image/webp" href="https://customer-assets-cm19k8pv.emergentagent.net/job_calc-unblocked/artifacts/izz9rm1p_www.desmos.webp" />` is set in `public/index.html`.

---

## 2. Terminology & Word Censorship Matrix
To ensure a human, classroom-aligned feel and eliminate flags from automated network filters, all explicit labels containing blocked terms (`games`, `unblocked`, `proxy`, `ai`) are replaced with subtle educational alternatives:

| Current Label | Blocked Words | Recommended Humanized Label | Context / Location |
| :--- | :--- | :--- | :--- |
| **Games** | `games` | **Activities** or **Interactive Library** | Main header nav, companion sub-nav, page titles |
| **Kentucky Version** | N/A (flagged style) | **Student Portal** or **Kentucky Practice** | Top bar secondary link |
| **AI assistant** / **AI** | `ai` | **Study Notes** or **Assistant** | Top bar link, sub-nav, sidebar |
| **Browser** / **Proxy** | `proxy` | **Web Resources** or **Reference Explorer** | Sub-nav, URL bar, connection status |
| **"Games by creator..."** | `games` | **"Interactive modules by respective creators"** | Footer credit |
| **"Powered by OpenRouter"** | N/A | **"Connected to Study Engine"** | Assistant sidebar footer |

---

## 3. Component & Layout Copy Recommendations

### A. Leave Confirmation Dialog (`LeaveConfirmation.jsx`)
- **Header**: "Are you sure you want to leave?"
- **Description**: *Remove phrase*: `"Your calculations and conversations are saved. A game in progress may be lost."`
- **Updated Description**: `"Any unsaved progress on this page will be reset."` (or leave minimal/empty description).

### B. Header & Sub-Navigation (`Header.jsx`)
- **Header Structure**: Keep exact 50px green bar (`background: #107b3f`) with Desmos inverted brand logo.
- **Top Bar Links**:
  - `desmos-logo-link`: Route to `/` (Calculator) or Assistant.
  - `scientific-calculator-link`: "Scientific Calculator" -> Route to `/browser` or `/`.
  - `kentucky-version-link`: "Kentucky Portal" or "Practice Suite".
- **Companion Sub-Nav**:
  - Tab 1: **Activities** (`/games`) with `Gamepad2` or `Compass` icon.
  - Tab 2: **Web Resources** (`/browser`) with `Globe2` icon.
  - Tab 3: **Assistant** (`/ai`) with `MessageSquare` icon.
  - Tab 4: **Calculator** (`/`) with `Calculator` icon.

### C. Activities / Library Page (`Games.jsx`)
- **Eyebrow**: `KENTUCKY PRACTICE SUITE`
- **Heading**: "Explore interactive modules."
- **Sub-heading**: "Access tools, exercises, and practice challenges."
- **Search Placeholder**: "Search modules…"
- **Category Filter Tabs**: `All`, `Arcade`, `Puzzle`, `Logic`, `Simulation`, `Favorites`
- **Cards**: Clean 1px border (`#e4e8e3`), 6px border-radius, soft hover shadow with green tint (`#107b3f`).

### D. Study Assistant / Notes Page (`Chat.jsx`)
- **Eyebrow**: `STUDY & CONVERSATION NOTES`
- **Heading**: "How can we help with your studies today?"
- **Suggestions**:
  1. "Solve a step-by-step problem" -> Quadratic equation example
  2. "Clarify a core concept" -> Radians vs degrees
  3. "Draft & review ideas" -> Essay outline or creative prompt
- **Model / Provider Label**: "Connected to Study Engine"

### E. Web Resources Explorer Page (`Browser.jsx`)
- **Status Indicator**: "Connected · Resource Node 1" / "Connecting to node…"
- **Heading**: "Explore reference material."
- **Description**: "A direct window for research, documents, and reference lookup."
- **Footer**: "Encrypted connection · Automatic failover"

---

## 4. Visual Language & Color System
- **Brand Primary**: `#107b3f` (Desmos Green)
- **Primary Hover**: `#096432`
- **Accent Blue**: `#2d70d8`
- **Backgrounds**: Pure white `#ffffff` and subtle off-white `#f7f8f7`
- **Borders**: `#dce2dc`
- **Typography**: Open Sans (`'Open Sans', sans-serif`), clean mathematical weight, generous whitespace.
