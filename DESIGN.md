---
{
  "name": "MOD1 Frontend",
  "description": "Authentication interface following the shared Module 6 visual guide.",
  "colors": {
    "primary": "#1E2A5A",
    "primary-hover": "#2F3F7F",
    "on-primary": "#FFFFFF",
    "bg": "#F6F7FA",
    "surface": "#FFFFFF",
    "border": "#E2E5EC",
    "text": "#1A1D29",
    "text-muted": "#5B6275",
    "priority-critical": "#DC2626",
    "success": "#16A34A",
    "bg-dark": "#0F1220",
    "surface-dark": "#181C2E",
    "border-dark": "#2A2F45",
    "text-dark": "#E8EAF2",
    "text-muted-dark": "#9AA0B4"
  },
  "typography": {
    "headline": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "32px",
      "fontWeight": 600,
      "lineHeight": 1.2,
      "letterSpacing": "-.025em"
    },
    "title": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "24px",
      "fontWeight": 600,
      "lineHeight": 1.2,
      "letterSpacing": "-.025em"
    },
    "body": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "14px",
      "fontWeight": 400,
      "lineHeight": 1.6
    },
    "label": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "14px",
      "fontWeight": 500,
      "lineHeight": 1.6
    },
    "control": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "16px",
      "fontWeight": 500,
      "lineHeight": 1.4
    },
    "value": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "16px",
      "fontWeight": 500,
      "lineHeight": 1.6
    },
    "supporting": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "12px",
      "fontWeight": 400,
      "lineHeight": 1.6
    }
  },
  "rounded": {
    "panel": "16px",
    "control": "8px"
  },
  "spacing": {
    "xs": "8px",
    "sm": "16px",
    "md": "24px",
    "lg": "32px",
    "xl": "40px"
  },
  "components": {
    "button-primary": {
      "backgroundColor": "{colors.primary}",
      "textColor": "{colors.on-primary}",
      "typography": "{typography.control}",
      "rounded": "{rounded.control}",
      "padding": "12px 18px"
    },
    "button-primary-hover": {
      "backgroundColor": "{colors.primary-hover}",
      "textColor": "{colors.on-primary}"
    },
    "button-secondary": {
      "backgroundColor": "transparent",
      "textColor": "{colors.text}",
      "typography": "{typography.control}",
      "rounded": "{rounded.control}",
      "padding": "12px 18px"
    },
    "theme-button": {
      "backgroundColor": "transparent",
      "textColor": "{colors.text-muted}",
      "typography": "{typography.label}",
      "rounded": "{rounded.control}",
      "padding": "10px 12px"
    },
    "input": {
      "backgroundColor": "{colors.surface}",
      "textColor": "{colors.text}",
      "typography": "{typography.body}",
      "rounded": "{rounded.control}",
      "padding": "12px 16px",
      "height": "48px"
    },
    "panel": {
      "backgroundColor": "{colors.surface}",
      "textColor": "{colors.text}",
      "typography": "{typography.body}",
      "rounded": "{rounded.panel}",
      "padding": "40px",
      "width": "min(480px, 100%)"
    },
    "message": {
      "backgroundColor": "transparent",
      "textColor": "{colors.text}",
      "typography": "{typography.body}",
      "rounded": "{rounded.control}",
      "padding": "12px 16px"
    }
  }
}
---

# Design System: MOD1 Frontend

## Overview

**Creative North Star: "Guide neutrals, navy actions, and precise outlines"**

The shared Module 6 guide provides the visual authority: cool neutral surfaces, navy actions, Inter typography, and precise outlines. Calm spacing and clear text hierarchy support brief authentication tasks.

Light and dark themes change neutral surfaces, borders, and text while keeping the action palette stable. Depth comes from surface contrast and borders. The module is identified through text; its lock symbol is a functional identifier rather than an official logo.

**Key Characteristics:**

- Cool neutral surfaces with navy primary actions.
- Inter at weights 400, 500, and 600.
- Outlined controls, gently curved panels, and visible keyboard focus.
- Theme-aware neutrals and text-supported status feedback.

Recorded from `public/styles/tokens.css`, `public/styles/app.css`, and `public/index.html`. The approved specification and `PRODUCT.md` establish durable identity commitments. Frontmatter is normative and uses JSON notation, which is valid YAML. The sidecar records extensions and component previews.

## Colors

The palette combines a stable navy action color with cool neutrals that adapt to light and dark themes.

### Primary

- **Navy action** (`primary`): primary buttons, module lock tile, account avatar, and selection backgrounds.
- **Navy hover** (`primary-hover`): enabled primary-button hover.
- **White on navy** (`on-primary`): text and icons on navy, including selection. It stays white in both themes.

### Neutral

- **Cool canvas** (`bg`, `bg-dark`): page background and secondary-button hover fill.
- **Panel surface** (`surface`, `surface-dark`): panels, inputs, password control, and theme-control hover fill.
- **Quiet outline** (`border`, `border-dark`): panels, theme-control borders, and account-row dividers.
- **Main ink** (`text`, `text-dark`): text, account values, secondary actions, caret, and keyboard focus.
- **Supporting ink** (`text-muted`, `text-muted-dark`): instructions, account-data labels, placeholders, input borders, and secondary-action borders.

Critical red (`priority-critical`) outlines errors. Success green (`success`) accompanies the active-account icon; its text remains in main ink. Other shared brand, priority, and chart tokens exist in the source but have no rendered authentication role and are not promoted into component rules here.

Dark frontmatter keys record dark counterparts. At runtime `[data-theme="dark"]` overrides the existing neutral CSS properties; components retain semantic property names.

**The Action Color Rule.** Use navy for primary actions. Reserve critical red for error outlines; never use red for action buttons.

**The Stable Contrast Rule.** Keep on-primary white in both themes; theme switches change neutral tokens, not navy-button foregrounds.

## Typography

**Interface Font:** Inter, with `system-ui, sans-serif` fallback. The official variable font is served locally.

**Technical Font:** JetBrains Mono, with `ui-monospace, monospace` fallback. Its official regular font is available locally for code and technical identifiers; the current screens do not render it. Provenance and licenses are recorded in `docs/font-sources.md`.

Inter supplies a plain interface voice. Weight changes establish hierarchy without decorative display lettering.

### Hierarchy

- **Headline:** `headline` for the login heading.
- **Title:** `title` for the authenticated greeting.
- **Body:** `body` for instructions, input content, and messages.
- **Label:** `label` for field labels and small interactive text.
- **Control:** `control` for main action buttons.
- **Value:** `value` for account values.
- **Supporting:** `supporting` for descriptions, notes, footer, and account-data labels.

The source also reserves 20px, which has no rendered role. The existing metrics utility provides tabular numerals when needed; it is not currently rendered.

**The Readable Floor Rule.** Keep visible text at 12px or above and use Inter at weights 400, 500, and 600.

## Layout

Use the five-step spacing scale in frontmatter: `xs` for label gaps, `sm` and `md` for related content, `lg` for section separation, and `xl` for larger panel padding.

This authentication surface centers a panel capped at 480px beneath a header capped at 1120px. Desktop header padding is 32px vertically and 40px horizontally; main padding is 56px top, 16px horizontally, and 64px bottom. These measurements describe this surface rather than a universal page template.

At 600px and below, header padding is 24px vertically and 16px horizontally, main top padding is 24px, and panel padding is 24px. Main side gutters remain 16px. The theme control hides its visible text while retaining its accessible name. Profile actions wrap, and long account values break to avoid horizontal overflow. Main buttons are at least 48px tall; the theme control is at least 44px tall.

## Elevation & Depth

Surfaces use tonal layering and fine outlines, with no box shadows. Panels use surface fill and borders; account rows use dividers. Input and secondary-button outlines use supporting ink for visibility in both themes. Keyboard focus is a 2px main-ink outline with a 4px offset.

**The Outlined Depth Rule.** Use surface contrast and borders for depth; panels and controls do not use box shadows.

## Shapes

Panels use the softly curved `panel` radius. Reusable controls, avatars, and messages use `control`; borders are 1px. The lock tile has local 10px corners, and the inset password control has local 6px corners; neither is promoted into the reusable radius scale.

Inline line icons use current-color strokes, rounded ends, and rounded joins. Standard icons are 20px with 1.8px strokes; the lock tile uses a 24px icon and the explanatory note uses an 18px icon. Preserve SVG geometry rather than substituting text glyphs.

## Components

### Buttons

Primary actions are solid navy with white text and navy hover fill. Secondary actions are transparent with main-ink text and supporting-ink outlines; hover adds canvas fill. Both use the control radius, 12px by 18px padding, and at least 48px height. Disabled action buttons use 0.65 opacity and a waiting cursor.

The theme button is a quieter outlined variant with supporting-ink text and an icon. Hover uses panel fill and main ink. All variants use the visible keyboard-focus outline. The source has no additional pressed-state animation or hover transition.

### Cards / Containers

The authentication panel uses panel fill, quiet outline, panel radius, and responsive padding from Layout. It has no shadow. The authenticated profile reuses this material treatment.

### Inputs / Fields

Fields have persistent visible labels, panel fill, supporting-ink borders, control radius, and 48px height. Hover changes the border to main ink; keyboard focus adds the shared outline. Placeholders use supporting ink at full opacity. The password field reserves 94px right padding for an inset show/hide control, whose accessible pressed state and label track visibility.

Credential controls begin disabled until initialization completes. A supporting instruction remains visible if initialization fails; successful initialization hides it and enables the controls.

### Messages and account status

Messages use main-ink text, critical-red outlines, control radius, and 12px by 16px padding. Informational session notices use quiet outlines. Alert semantics announce changes without relying on red alone.

Account data uses a description list, quiet row dividers, supporting labels, and main-ink values. A green check icon accompanies the word "Ativa". The avatar is a compact navy tile with white initials.

### Keyboard entry and state changes

A skip link appears on keyboard focus and leads to main content. State changes move focus to the corresponding heading. Profile entry uses a 180ms clip reveal with `cubic-bezier(.16,1,.3,1)` only when reduced motion is not requested. Intermediate animation clipping is a transition frame, not a static layout pattern.

## Do's and Don'ts

### Do:

- Do reference the existing CSS custom properties for reusable visual decisions.
- Do preserve white on-primary text and icons in both themes.
- Do preserve visible labels, keyboard focus, and text or icons alongside status colors.
- Do use the established spacing scale, comfortable mobile gutters, and touch-sized controls.
- Do honor reduced-motion preferences and keep motion brief and local to state changes.

### Don't:

- Don't use red for action buttons or communicate status through color alone.
- Don't add box shadows or decorative elevation to these outlined surfaces.
- Don't shrink visible text below 12px or replace Inter with a system display face.
- Don't treat the lock symbol as an official logo or invent additional brand assets.
- Don't turn the authentication panel composition into a mandatory layout for unrelated surfaces.
