---
{
  "name": "MOD1 Frontend",
  "description": "Account, projects, and backlog interface following the shared Module 6 visual guide.",
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
    "text-muted-dark": "#9AA0B4",
    "brand-accent": "#C8102E"
  },
  "typography": {
    "headline": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "28px",
      "fontWeight": 600,
      "lineHeight": 1.2,
      "letterSpacing": "-.035em"
    },
    "title": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "28px",
      "fontWeight": 600,
      "lineHeight": 1.2,
      "letterSpacing": "-.035em"
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
      "fontSize": "14px",
      "fontWeight": 600,
      "lineHeight": 1.4
    },
    "value": {
      "fontFamily": "Inter, system-ui, sans-serif",
      "fontSize": "14px",
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
      "backgroundColor": "{colors.surface}",
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
      "padding": "36px",
      "width": "min(480px, 100%)"
    },
    "message": {
      "backgroundColor": "{colors.bg}",
      "textColor": "{colors.text}",
      "typography": "{typography.body}",
      "rounded": "{rounded.control}",
      "padding": "12px 16px"
    },
    "workspace-tab": {
      "backgroundColor": "transparent",
      "textColor": "{colors.text-muted}",
      "typography": "{typography.body}",
      "rounded": "{rounded.control}",
      "padding": "10px 14px"
    },
    "board-item": {
      "backgroundColor": "{colors.surface}",
      "textColor": "{colors.text}",
      "typography": "{typography.body}",
      "rounded": "{rounded.control}",
      "padding": "16px"
    }
  }
}
---

# Design System: MOD1 Frontend

## Overview

**Creative North Star: "Guide neutrals, navy actions, and precise outlines"**

The shared Module 6 guide provides the visual authority: cool neutral surfaces, navy actions, Inter typography, and precise outlines. Calm spacing and clear text hierarchy support authentication, account management, projects, and backlog work. The editorial greeting direction refines this existing identity through composition and density; it does not replace the brand.

Light and dark themes change neutral surfaces, borders, and text while keeping the action palette stable. Depth comes from surface contrast and borders. The module is identified through text; its lock symbol is a functional identifier rather than an official logo.

**Key Characteristics:**

- Cool neutral surfaces with navy primary actions.
- Inter at weights 400, 500, and 600.
- Outlined controls, gently curved panels, and visible keyboard focus.
- Theme-aware neutrals and text-supported status feedback.

Recorded from `public/styles/tokens.css`, `public/styles/app.css`, `public/styles/workspace.css`, `public/styles/premium.css`, and `public/index.html`. The premium stylesheet is loaded last and supplies the effective presentation refinements. The approved specification and `PRODUCT.md` establish durable identity commitments. Frontmatter is normative and uses JSON notation, which is valid YAML. The sidecar records extensions and component previews.

## Colors

The palette combines a stable navy action color with cool neutrals that adapt to light and dark themes.

### Primary

- **Navy action** (`primary`): primary buttons, module lock tile, account avatar, and selection backgrounds.
- **Navy hover** (`primary-hover`): enabled primary-button hover.
- **Brand accent** (`brand-accent`): the small corner detail on the existing module tile; it does not color actions or semantic states.
- **White on navy** (`on-primary`): text and icons on navy, including selection. It stays white in both themes.

### Neutral

- **Cool canvas** (`bg`, `bg-dark`): page background and secondary-button hover fill.
- **Panel surface** (`surface`, `surface-dark`): panels, inputs, password control, and theme-control hover fill.
- **Quiet outline** (`border`, `border-dark`): panels, theme-control borders, and account-row dividers.
- **Main ink** (`text`, `text-dark`): text, account values, secondary actions, caret, and keyboard focus.
- **Supporting ink** (`text-muted`, `text-muted-dark`): instructions, account-data labels, placeholders, input borders, and secondary-action hover outlines.

Critical red (`priority-critical`) outlines errors. Success green (`success`) accompanies the active-account icon; its text remains in main ink. Other shared priority and chart tokens retain their source values and semantic roles; this refinement introduces no replacement palette.

Dark frontmatter keys record dark counterparts. At runtime `[data-theme="dark"]` overrides the existing neutral CSS properties; components retain semantic property names.

**The Action Color Rule.** Use navy for primary actions. Reserve critical red for error outlines; never use red for action buttons.

**The Stable Contrast Rule.** Keep on-primary white in both themes; theme switches change neutral tokens, not navy-button foregrounds.

## Typography

**Interface Font:** Inter, with `system-ui, sans-serif` fallback. The official variable font is served locally.

**Technical Font:** JetBrains Mono, with `ui-monospace, monospace` fallback. Its official regular font is available locally for code and technical identifiers; the current screens do not render it. Provenance and licenses are recorded in `docs/font-sources.md`.

Inter supplies a plain interface voice. Weight changes establish hierarchy without decorative display lettering.

### Hierarchy

- **Headline:** `headline` for authentication and workspace headings; compact screens use 24px.
- **Title:** `title` for the authenticated greeting; compact screens use 24px.
- **Body:** `body` for instructions, input content, and messages.
- **Label:** `label` for field labels and small interactive text.
- **Control:** `control` for main action buttons.
- **Value:** `value` for account values.
- **Supporting:** `supporting` for descriptions, notes, footer, and account-data labels.

The desktop introduction uses a local 42px heading, reduced to 34px at 1000px. Section headings use 18px or the existing 20px scale. Supporting copy is limited to 65ch where applicable. Numeric table cells use tabular numerals and right alignment.

**The Readable Floor Rule.** Keep visible text at 12px or above and use Inter at weights 400, 500, and 600.

## Layout

Use the five-step spacing scale in frontmatter: `xs` for label gaps, `sm` and `md` for related content, `lg` for section separation, and `xl` for larger panel padding.

The entry surface uses a two-column composition: product context on the left and a form capped at 480px on the right. Its main container is capped at 1164px with a desktop 80px column gap, reduced to 32px at 1000px. The context names access, projects, and backlog. At 800px and below it is hidden and the form remains centered. The access check follows the form when applicable.

Account, projects, and workspace surfaces are capped at 1180px. The account opens with two areas: identity data and primary actions beside account/workspace shortcuts. Invitation and profile/preferences content follow. Account data uses two columns until the compact breakpoint; long values wrap. Project lists and forms use a flexible main column and a 320px side column, reduced to 280px at 1000px; they stack at 800px.

Workspace navigation wraps. Desktop item filters align search, type, status, and action in one row; at 800px they use two columns with search and action spanning the row. The board has three columns and stacks at 680px. Tables keep a 640px minimum width inside their own horizontal scroll region, so dense data remains readable without widening the page.

Desktop main gutters are 32px and panel padding is 32px (36px for authentication). At 800px, gutters and workspace/account panel padding become 24px. At 480px, gutters become 16px, panel padding becomes 24px vertically and 20px horizontally, and account data stacks. The theme button hides visible text at 600px while retaining its accessible name. Main actions retain 48px minimum height; compact row/board actions use 36px and supporting controls use 40–44px.

## Elevation & Depth

Surfaces use tonal layering and fine outlines, with no box shadows. Panels use surface fill and borders; account rows use dividers. Input and secondary-button outlines use supporting ink for visibility in both themes. Keyboard focus is a 2px main-ink outline with a 4px offset.

**The Outlined Depth Rule.** Use surface contrast and borders for depth; panels and controls do not use box shadows.

## Shapes

Panels use the softly curved `panel` radius. Reusable controls, avatars, and messages use `control`; borders are 1px. The lock tile uses the control radius with a small 2px-radius accent detail; the inset password control retains local 6px corners. These local details do not introduce a new reusable radius scale.

Inline line icons use current-color strokes, rounded ends, and rounded joins. Standard icons are 20px with 1.8px strokes; the lock tile uses a 24px icon and the explanatory note uses an 18px icon. Preserve SVG geometry rather than substituting text glyphs.

## Components

### Buttons

Primary actions are solid navy with white text and navy hover fill. Secondary actions use panel fill, main-ink text, and quiet outlines; hover adds canvas fill and a supporting-ink outline. Both use the control radius, 12px by 18px padding, and at least 48px height. Disabled action buttons use 0.65 opacity and a not-allowed cursor. Enabled actions shift down 1px while pressed.

The theme button is a quieter variant with a transparent resting border, supporting-ink text, and an icon. Hover uses panel fill and main ink. All variants use the visible keyboard-focus outline. Color and border feedback lasts 160ms only when reduced motion is not requested; layout changes do not animate.

### Cards / Containers

The authentication panel uses panel fill, quiet outline, panel radius, and responsive padding from Layout. It has no shadow. The authenticated profile reuses this material treatment.

### Inputs / Fields

Fields have persistent visible labels, panel fill, supporting-ink borders, control radius, and 48px height. Hover keeps the supporting-ink border; focus changes the border to navy hover and keyboard focus adds the shared outline. Placeholders use supporting ink at full opacity. The password field reserves 94px right padding for an inset show/hide control, whose accessible pressed state and label track visibility.

Credential controls begin disabled until initialization completes. A supporting instruction remains visible if initialization fails; successful initialization hides it and enables the controls.

### Messages and account status

Messages use canvas fill, main-ink text, critical-red outlines, control radius, and 12px by 16px padding. Informational session notices use quiet outlines. Alert semantics announce changes without relying on red alone.

Account data uses a description list, quiet row dividers, supporting labels, and main-ink values. A green check icon accompanies the word "Ativa". The avatar is a compact navy tile with white initials.

### Keyboard entry and state changes

A skip link appears on keyboard focus and leads to main content. State changes move focus to the corresponding heading. The former profile-entry clip reveal is suppressed by the premium stylesheet. Motion is limited to brief local color/border feedback under `prefers-reduced-motion: no-preference`; respect the same rule in new controls.

### Workspace navigation, tables, and board

Tabs use supporting ink at rest and main ink with canvas fill for the current view. Filter groups use canvas fill and the control radius. Tables use quiet horizontal rules, generous row padding, and canvas hover feedback. Board columns use the canvas; each item uses a separately outlined panel surface with 16px padding and the control radius. Titles remain text actions and keyboard focus stays visible.

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
