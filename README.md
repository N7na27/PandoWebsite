# Pando Surgical website

Static website for Pando Surgical, built from the Figma design (Website Ver2 "cold" and Ver1 "warm").

**Preview:** https://n7na27.github.io/PandoWebsite/

## What's here

- `index.html` and the other `*.html` pages: the site (plain HTML, no framework).
- `css/style.css`: all styles. Both color themes are CSS variables at the top.
- `js/main.js`: nav dropdowns, hide-on-scroll nav, theme toggle, rolling word, 78% count-up, tabs, log in and news pop-ups, page fade transitions, form word counters.
- `assets/img`, `assets/icons`: images and icons exported from Figma.
- `tools/build.py`: generates the HTML pages. The nav, footer and log in pop-up are shared, so they live here once.

## Editing

Change the text or pages in `tools/build.py`, then run:

```
python3 tools/build.py
```

Styles and scripts can be edited directly.

## Themes

The theme toggle in the nav switches between **Cold** (Ver2, default) and **Warm** (Ver1, cream). The choice is remembered in the browser.

## Not connected yet

- The contact, careers and log in forms are front end only. They need a form service or backend before they send anything.
- The company LinkedIn and YouTube links in the footer point nowhere (`#`) until the real URLs are added in `tools/build.py`.
- Placeholders from the design (LapRotator 3D model, aspen grove image, stat source, news dates) are kept as is.

## Custom domain

When ready, add the domain under Settings → Pages → Custom domain, and point the domain's DNS at GitHub Pages.
