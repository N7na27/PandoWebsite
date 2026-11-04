#!/usr/bin/env python3
"""Builds the static HTML pages of the Pando Surgical website.

The nav, footer and log in modal are shared by every page, so they live here
once. Edit this file, then run:  python3 tools/build.py
"""
from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "assets" / "icons"
EMAIL = "contact@pandosurgical.com"


def svg(name, cls="", current=True):
    """Inline an icon. White fills/strokes become currentColor so CSS can color them."""
    s = (ICONS / f"{name}.svg").read_text().strip()
    if current:
        s = s.replace('fill="white"', 'fill="currentColor"').replace('stroke="white"', 'stroke="currentColor"')
    attrs = ' aria-hidden="true" focusable="false"'
    if cls:
        attrs += f' class="{cls}"'
    return s.replace("<svg ", f"<svg{attrs} ", 1)


def social(name, label, href):
    s = svg(name, current=False).replace('<circle cx="15" cy="15" r="15" fill="#868686" fill-opacity="0.15"/>',
                                         '<circle class="bg" cx="15" cy="15" r="15"/>')
    ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
    return f'<a class="social" href="{href}" aria-label="{label}"{ext}>{s}</a>'


# Social links for the company
COMPANY_LINKEDIN = "https://www.linkedin.com/company/pandosurgical/posts/?feedView=all"
COMPANY_YOUTUBE = "https://www.youtube.com/@pandosurgical"


def nav(page):
    def cur(*names):
        return " is-current" if page in names else ""
    chev = svg("chevron-down")
    return f"""<header class="nav" id="nav">
  <div class="nav-left glass">
    <a class="nav-logo" href="index.html" aria-label="Pando Surgical home">{svg("pando-mark")}</a>
    <nav class="nav-links" aria-label="Main">
      <div class="dd">
        <button class="nav-link dd-toggle{cur('laprotator', 'ent')}" aria-expanded="false" aria-controls="dd-product">Product {chev}</button>
        <div class="dd-panel glass" id="dd-product">
          <a href="laprotator.html" class="{cur('laprotator').strip()}">LapRotator</a>
          <a href="ent.html" class="{cur('ent').strip()}">ENT Product</a>
        </div>
      </div>
      <a class="nav-link{cur('team')}" href="team.html">Team</a>
      <a class="nav-link{cur('news')}" href="news.html">News</a>
      <div class="dd">
        <button class="nav-link dd-toggle{cur('about', 'investors', 'careers', 'contact')}" aria-expanded="false" aria-controls="dd-about">About {chev}</button>
        <div class="dd-panel glass" id="dd-about">
          <a href="about.html" class="{cur('about').strip()}">Company</a>
          <a href="investors.html" class="{cur('investors').strip()}">Investors</a>
          <a href="careers.html" class="{cur('careers').strip()}">Careers</a>
          <a href="contact.html" class="{cur('contact').strip()}">Contact Us</a>
        </div>
      </div>
    </nav>
    <div class="mobile-extra">
      <div class="row">
        <button class="nav-link" data-modal="login">Log in</button>
        <button class="theme-toggle" data-theme-toggle><span class="swatch"></span><span class="theme-label">Cold</span></button>
      </div>
      <a class="btn btn-primary" href="contact.html">Get in touch</a>
    </div>
    <button class="nav-burger" aria-label="Menu" aria-expanded="false"><span></span></button>
  </div>
  <div class="nav-right">
    <div class="nav-util glass">
      <span class="nav-link" title="Language">EN</span>
      <button class="nav-link" data-modal="login">Log in</button>
      <button class="theme-toggle" data-theme-toggle><span class="swatch"></span><span class="theme-label">Cold</span></button>
    </div>
    <a class="btn btn-primary" href="contact.html">Get in touch</a>
  </div>
</header>"""


FOOTER = f"""<footer class="footer">
  <div class="footer-glow" aria-hidden="true"><span class="g1"></span><span class="g2"></span><span class="g3"></span></div>
  <div class="footer-top">
    <div class="footer-brand">
      <p>Making surgical tools equitable, efficient, and ergonomic.</p>
    </div>
    <div class="footer-cols">
      <div class="footer-col">
        <h2>Product</h2>
        <ul><li><a href="laprotator.html">LapRotator</a></li><li><a href="ent.html">ENT Product</a></li></ul>
      </div>
      <div class="footer-col">
        <h2>Company</h2>
        <ul><li><a href="about.html">About</a></li><li><a href="team.html">Team</a></li><li><a href="news.html">News</a></li><li><a href="careers.html">Careers</a></li></ul>
      </div>
      <div class="footer-col">
        <h2>Connect</h2>
        <ul><li><a href="investors.html">Investors</a></li><li><a href="contact.html">Contact Us</a></li></ul>
      </div>
    </div>
  </div>
  <div class="footer-bottom">
    <div class="footer-left">
      <a href="index.html" class="footer-wordmark" aria-label="Pando Surgical home">{svg("pando-wordmark").replace('fill="#FFFCF2"', 'fill="currentColor"')}</a>
      <div class="socials">
        {social("linkedin", "Pando Surgical on LinkedIn", COMPANY_LINKEDIN)}
        {social("youtube", "Pando Surgical on YouTube", COMPANY_YOUTUBE)}
      </div>
    </div>
    <div class="footer-right">
      <nav class="footer-legal" aria-label="Legal">
        <a href="privacy.html">Privacy Notice</a>
        <a href="terms.html">Terms of Use</a>
        <a href="accessibility.html">Accessibility Statement</a>
      </nav>
      <small>© 2026 Pando Surgical, Inc. All rights reserved.</small>
    </div>
  </div>
</footer>"""

# Simple footer (Figma "Footer"): used on every page except Home, which keeps the gradient footer
FOOTER_SIMPLE = f"""<footer class="footer-simple">
  <div class="fs-top">
    <div class="fs-brand">
      <p>Making surgical tools equitable, efficient, and ergonomic.</p>
      <div class="socials">
        {social("linkedin", "Pando Surgical on LinkedIn", COMPANY_LINKEDIN)}
        {social("youtube", "Pando Surgical on YouTube", COMPANY_YOUTUBE)}
      </div>
    </div>
    <div class="fs-right">
      <div class="footer-cols">
        <div class="footer-col">
          <h2>Product</h2>
          <ul><li><a href="laprotator.html">LapRotator</a></li><li><a href="ent.html">ENT Product</a></li></ul>
        </div>
        <div class="footer-col">
          <h2>Company</h2>
          <ul><li><a href="about.html">About</a></li><li><a href="team.html">Team</a></li><li><a href="news.html">News</a></li><li><a href="careers.html">Careers</a></li></ul>
        </div>
        <div class="footer-col">
          <h2>Connect</h2>
          <ul><li><a href="investors.html">Investors</a></li><li><a href="contact.html">Contact Us</a></li></ul>
        </div>
      </div>
      <a href="index.html" class="fs-mark" aria-label="Pando Surgical home">{svg("footer-mark")}</a>
    </div>
  </div>
  <div class="fs-bottom">
    <small>© 2026 Pando Surgical, Inc. All rights reserved.</small>
    <nav class="fs-legal" aria-label="Legal">
      <a href="privacy.html">Privacy Notice</a>
      <a href="terms.html">Terms of Use</a>
      <a href="accessibility.html">Accessibility Statement</a>
    </nav>
  </div>
</footer>"""

GOOGLE_G = """<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg>"""

LOGIN = f"""<div class="modal" id="login" role="dialog" aria-modal="true" aria-labelledby="login-title" aria-hidden="true">
  <div class="modal-card login-card">
    <div class="login-head">
      <h2 id="login-title">Welcome back</h2>
      <p>Sign in to access your account</p>
    </div>
    <button class="modal-close" aria-label="Close"><img src="assets/icons/icon-close.svg" alt=""></button>
    <form class="login-body" data-demo="Sign in isn’t connected yet. This is a preview of the design.">
      <button type="button" class="btn btn-google btn-block">{GOOGLE_G} Continue with Google</button>
      <div class="or">or</div>
      <div class="field">
        <label for="login-email">Email address</label>
        <div class="input-icon"><img src="assets/icons/icon-mail.svg" alt=""><input id="login-email" type="email" placeholder="you@example.com" autocomplete="email" required></div>
      </div>
      <div class="field">
        <label for="login-pass">Password</label>
        <div class="input-icon"><img src="assets/icons/icon-lock-field.svg" alt=""><input id="login-pass" type="password" placeholder="Enter your password" autocomplete="current-password" required>
          <button type="button" class="eye" aria-label="Show password"><img src="assets/icons/icon-eye.svg" alt=""></button></div>
      </div>
      <a class="forgot" href="mailto:{EMAIL}?subject=Password%20reset">Forgot password?</a>
      <button class="btn btn-primary btn-block" type="submit">Sign in</button>
      <p class="form-note" role="status"></p>
      <p class="login-foot">Don’t have an account? <a href="mailto:{EMAIL}?subject=Request%20access">Request access</a></p>
    </form>
  </div>
</div>"""


def page(filename, title, description, page_id, main, light=False, extra=""):
    body_cls = "page-light" if light else "page-dark"
    full_title = "Pando Surgical" if page_id == "home" else f"{title} | Pando Surgical"
    out = f"""<!doctype html>
<html lang="en" data-theme="cold">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{html.escape(description)}">
<script>try{{var t=localStorage.getItem("pando-theme");if(t==="warm"||t==="cold")document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>
<link rel="icon" href="assets/icons/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
<noscript><style>body{{opacity:1}}.reveal{{opacity:1;transform:none}}</style></noscript>
</head>
<body class="{body_cls}">
<a class="skip-link" href="#main">Skip to content</a>
{nav(page_id)}
<main id="main">
{main}
</main>
{FOOTER if page_id == "home" else FOOTER_SIMPLE}
{LOGIN}
{extra}
<script src="js/main.js"></script>
</body>
</html>
"""
    (ROOT / filename).write_text(out)


def btn(text, href, kind="primary"):
    return f'<a class="btn btn-{kind}" href="{href}">{text}</a>'


# ---------------------------------------------------------------- Landing
# three.js for the LapRotator 3D model (js/model.js). Pinned version from jsDelivr.
THREE = "https://cdn.jsdelivr.net/npm/three@0.160.0"
MODEL_SCRIPTS = f"""<script type="importmap">{{"imports":{{"three":"{THREE}/build/three.module.min.js","three/addons/":"{THREE}/examples/jsm/"}}}}</script>
<script type="module" src="js/model.js"></script>"""
LOGOS = [("logo-iowa", "University of Iowa", 138), ("logo-uthealth", "UTHealth Houston", 191),
         ("logo-keck", "Keck Medicine of USC", 189), ("logo-17", "University medical center", 224),
         ("logo-18", "University medical center", 108), ("logo-1", "University medical center", 225)]
logo_imgs = "".join(f'<img src="assets/icons/{f}.svg" alt="{a}" width="{w}">' for f, a, w in LOGOS)
logo_imgs_dup = "".join(f'<img src="assets/icons/{f}.svg" alt="" aria-hidden="true" width="{w}">' for f, a, w in LOGOS)
WORDS = ["supported.", "considered.", "included.", "understood.", "heard."]

page("index.html", "Home", "Pando Surgical makes ergonomic surgical tools that adapt to the surgeon, not the other way around.", "home", f"""
<section class="hero">
  <div class="hero-fade"></div>
  <div class="hero-content">
    <h1>Every surgeon,<span class="rolling" aria-label="supported."><span class="rolling-track" aria-hidden="true">{"".join(f"<span>{w}</span>" for w in WORDS + WORDS[:1])}</span></span></h1>
    <p class="hero-sub">Pando Surgical makes tools that adapt to the surgeon, not the other way around.</p>
    <a class="btn btn-primary" href="#mission">Learn more</a>
  </div>
  <div class="trust">
    <p>Demand from top university medical centers</p>
    <div class="marquee"><div class="marquee-track">{logo_imgs}{logo_imgs_dup}</div></div>
  </div>
</section>

<section class="mission" id="mission">
  <p class="label reveal">Mission</p>
  <h2 class="reveal">To make surgery more<br> <em>equitable, efficient, and ergonomic</em><br> by developing tools that empower<br> surgeons worldwide.</h2>
</section>

<section class="why on-dark">
  <div class="why-text reveal">
    <p class="label">Why Pando</p>
    <h2>Surgical tools are not built for every hand.</h2>
    <p class="body">Many tools were designed solely around the male anatomy and failed to adapt for every surgeon. Surgical tools should be equitable, efficient and ergonomic: for every surgeon.</p>
  </div>
  <div class="stat">
    <span class="stat-num" data-count="78" data-suffix="%">78%</span>
    <p class="stat-text">of surgeons report work-related pain or injury</p>
    <p class="stat-src">[Source / citation placeholder]</p>
  </div>
</section>

<section class="product">
  <div class="reveal">
    <h2>Built for surgical needs.<br>Introducing LapRotator</h2>
    {btn("Learn more about LapRotator", "laprotator.html", "dark")}
    <div class="proof">
      <div class="proof-item"><img src="assets/icons/icon-link.svg" alt=""><span>Compatible with<br>Stryker laparoscopes</span></div>
      <div class="proof-item"><img src="assets/icons/icon-rotate.svg" alt=""><span>One-handed<br>scope rotation</span></div>
      <div class="proof-item"><img src="assets/icons/icon-hand.svg" alt=""><span>Designed around<br>surgeon ergonomics</span></div>
    </div>
  </div>
  <div class="lr-model reveal" tabindex="0" role="img" aria-label="3D model of the LapRotator on a laparoscope, turning around the scope. Hover or focus to stop it; drag or use the left and right arrow keys to turn it.">
    <img class="lr-model-poster" src="assets/model/laprotator-poster.webp" alt="" width="848" height="540">
  </div>
</section>

<section class="grove">
  <div class="grove-text reveal">
    <p class="label">Why “Pando”</p>
    <h2>One root.<br>Every surgeon.</h2>
    <p class="body">Pando is one of the largest living organisms on Earth: a single aspen with one shared root system and tens of thousands of trunks. Pando Surgical works the same way. Our commitment to ergonomics runs underneath every tool, supporting every surgeon with all body types and specialties.</p>
  </div>
  <img class="grove-img reveal" src="assets/img/grove.jpg" alt="Aspen grove with white trunks and golden autumn undergrowth" width="640" height="520" loading="lazy">
</section>

<section class="cta on-dark">
  <h2 class="reveal">Built for the hands that heal.</h2>
  <p>Surgeon, hospital or partner? We’d love to hear from you.</p>
  <div class="btn-row">
    {btn("Get in touch", "contact.html")}
    {btn("Press inquiries", f"mailto:{EMAIL}?subject=Press%20inquiry", "outline")}
  </div>
</section>
""", extra=MODEL_SCRIPTS)

# ---------------------------------------------------------------- LapRotator
# Tab content from the Figma "LapRotator Tabs" component (Wireframe Components)
FEATURES = [
    "Compatible with existing laparoscopic systems",
    "One-handed rotation for enhanced control",
    "Compact and lightweight frame",
    "Simple user interface",
    "Designed to help reduce surgeon fatigue during procedures",
]
SPECS = [
    ("Laparoscopes (Standard Autoclavable, 30 cm)", "502-555-010/030/045 (5.0 mm); 502-457-010/030/045 (10.0 mm)"),
    ("IDEAL EYES™ HD (30 cm)", "502-539-010/030/045 (5.0 mm); 502-859-010/030/045 (10.0 mm)"),
    ("Bariatric (45 cm)", "502-205-010/030/045 (5.0 mm)"),
    ("Pediatric", "502-543-010/030 (2.7 mm); 502-290-010/030 (2.9 mm, IDEAL EYES™)"),
    ("Camera coupler", "Stryker 1488 HD Camera Head Coupler, 18 mm (P/N 1488-020-122)"),
]
FEATURE_ITEMS = "\n".join(f'      <li><span class="check"><img src="assets/icons/icon-check.svg" alt="" width="16" height="16"></span>{f}</li>' for f in FEATURES)
# Keep each part number on one line, so phones never break it at a hyphen
def _pn(text):
    return re.sub(r"\d+(?:-\d+)+(?:/\d+)*", lambda m: f'<span class="pn">{m.group(0)}</span>', text)
SPEC_ROWS = "\n".join(f'      <div class="spec-row"><dt>{k}</dt><dd>{_pn(v)}</dd></div>' for k, v in SPECS)
page("laprotator.html", "LapRotator", "LapRotator: an attachment for laparoscopes that gives surgeons intuitive, single-handed scope rotation.", "laprotator", f"""
<section class="lr-hero">
  <div class="lr-art"><div class="lr-float"><img src="assets/img/laprotator-device.webp" alt="LapRotator attached to a laparoscope" width="1889" height="832"></div></div>
  <div class="lr-hero-text">
    <h1>LapRotator</h1>
    <p>One-Handed Laparoscope Rotation: an attachment for laparoscopes that gives surgeons intuitive, single-handed control.</p>
    {btn("Request a demo", "contact.html")}
  </div>
</section>

<section class="overview">
  <h2 class="reveal">Overview</h2>
  <div class="overview-body reveal">
    <p>The LapRotator is an attachment on the laparoscope that gives surgeons full one-handed control over scope rotation during minimally invasive procedures.</p>
    <p>By removing the need for a second hand or assistant to reposition the scope, the LapRotator helps surgeons reduce fatigue during long procedures, mitigate safety hazards, and work more efficiently in the OR.</p>
    <p>Compatible with existing laparoscopic systems, the LapRotator attaches in seconds and requires no additional training, so any OR can use it right away.</p>
    <a class="text-link" href="contact.html">Request a demo →</a>
  </div>
</section>

<section class="details">
  <div class="tabs" role="tablist" aria-label="LapRotator details">
    <button class="tab" role="tab" id="tab-diff" aria-controls="panel-diff" aria-selected="true" data-text="See the Difference">See the Difference</button>
    <button class="tab" role="tab" id="tab-feat" aria-controls="panel-feat" aria-selected="false" tabindex="-1" data-text="Features and Advantages">Features and Advantages</button>
    <button class="tab" role="tab" id="tab-spec" aria-controls="panel-spec" aria-selected="false" tabindex="-1" data-text="Specifications">Specifications</button>
  </div>
  <div class="tab-panel" role="tabpanel" id="panel-diff" aria-labelledby="tab-diff">
    <h3>LapRotator – See the Difference</h3>
    <div class="compare">
      <figure><video src="assets/video/compare-1.mp4" poster="assets/video/compare-1.jpg" autoplay muted loop playsinline preload="metadata" aria-label="Surgeon rotating a laparoscope by hand, without LapRotator"></video><figcaption>Without LapRotator</figcaption></figure>
      <figure><video src="assets/video/compare-2.mp4" poster="assets/video/compare-2.jpg" autoplay muted loop playsinline preload="metadata" aria-label="Surgeon rotating a laparoscope one-handed with LapRotator V2 attached"></video><figcaption>With LapRotator V2</figcaption></figure>
    </div>
  </div>
  <div class="tab-panel" role="tabpanel" id="panel-feat" aria-labelledby="tab-feat" hidden>
    <h3>Features and Advantages</h3>
    <ul class="features">
{FEATURE_ITEMS}
    </ul>
  </div>
  <div class="tab-panel" role="tabpanel" id="panel-spec" aria-labelledby="tab-spec" hidden>
    <h3>Specifications</h3>
    <h4 class="spec-head">Compatibility</h4>
    <p class="spec-intro">The LapRotator is compatible with the following Stryker rigid laparoscopes and camera coupler:</p>
    <dl class="spec-table">
{SPEC_ROWS}
    </dl>
  </div>
</section>
""")

# ---------------------------------------------------------------- ENT
page("ent.html", "ENT Product", "Pando Surgical is developing a new ergonomic solution for ENT procedures.", "ent", """
<section class="ent">
  <div class="ent-text reveal">
    <h1>Ergonomic ENT Product</h1>
    <p class="body">We’re developing a new ergonomic solution for ENT procedures. The product is currently in stealth; details are under wraps for now. Check back soon.</p>
  </div>
  <img src="assets/img/ent-stealth.jpg" alt="Blurred preview with a lock: product in stealth">
</section>
""", light=True)

# ---------------------------------------------------------------- Team
FOUNDERS = [
    ("Aiden Pan", "CEO & Co-Founder", "USC Biomedical Engineering", "https://www.linkedin.com/in/aidenpan/"),
    ("Toshi Nagai", "Co-Founder", "USC Biomedical Engineering and Mechanical Engineering", "https://www.linkedin.com/in/toshio-nagai2029/"),
    ("Derek Hua", "Co-Founder and Head of Clinical Development", "USC Biomedical Engineering and Pre-Medicine", "https://www.linkedin.com/in/derekhuausc/"),
    ("Sean Lee", "Manager of Strategic Partners", "Cornell University Biomedical Engineering", "https://www.linkedin.com/in/sean-lee-9bbab8373/"),
]
ADVISORS = [
    ("Noah Pearson", "Advisor", "PhD Mechanical Engineering", "https://www.linkedin.com/in/noah-r-pearson/"),
    ("Arieh Halpern", "Advisor", "Medical Device and Digital Health Executive", None),
    ("Xiaoyang Hua", "Advisor", "MD, PhD, FACS, Otolaryngology (ENT) Surgeon", None),
]


def member(m, img):
    name, role, edu, li = m
    link = social("team-linkedin", f"{name} on LinkedIn", li) if li else ""
    return f"""<article class="member reveal">
      <span class="photo"><img src="assets/img/{img}" alt="{name}" width="300" height="300" loading="lazy"></span>
      <div class="member-info">
        <div class="member-head"><div><h3>{name}</h3><p class="role">{role}</p></div>{link}</div>
        <hr>
        <p class="edu">{edu}</p>
      </div>
    </article>"""


page("team.html", "Our Team", "Meet the engineers and advisors behind Pando Surgical.", "team", f"""
<section class="team">
  <h1 class="page-title">Our Team</h1>
  <div class="team-grid">
    {"".join(member(m, f"founder-{i+1}.jpg") for i, m in enumerate(FOUNDERS))}
  </div>
  <h2>Advisory Board</h2>
  <div class="team-grid">
    {"".join(member(m, f"advisor-{i+1}.jpg") for i, m in enumerate(ADVISORS))}
  </div>
</section>
""", light=True)

# ---------------------------------------------------------------- News
STORIES = [
    ("Accelerator", "Accepted into USC and Techstars University Catalyst Pre-Accelerator", "August 2026",
     "Pando Surgical has officially been accepted into the USC and Techstars University Catalyst Pre-Accelerator, a high-impact program delivered in partnership with the USC Research and Innovation office. The program officially launched in late August in Los Angeles, bringing together the Pando Surgical leadership team, program directors, and a select cohort of fellow founders for collaborative kickoff sessions. Over the coming weeks, the company will engage in intensive mentorship and strategic development to accelerate its commercialization pathway alongside top-tier, research-backed ventures."),
    ("Award", "2nd Place, USC Viterbi Min Family Challenge", "April 27, 2026",
     "The Min Family Challenge (MFC) is USC Viterbi’s flagship student venture competition, part of tiehub’s annual $150K Awards Night, awarding funding to student-founded startups with the strongest potential for real-world impact. At the 2026 MEPC &amp; MFC Awards Night on April 27, our team placed 2nd overall and was also selected by audience vote as one of three finalists to deliver a live three-minute pitch, which we won, bringing a working prototype of the LapRotator to the stage."),
    ("Funding", "Closed $60K Pre-Seed Round", "[Date]",
     "We closed a $60,000 pre-seed round to fund our patent filing and kick off the FDA regulatory process, including the testing needed to support that submission. Thank you to everyone who believed in what we’re building this early on."),
    ("Patent", "Patent Filed Through the PCT", "[Date]",
     "Pando Surgical has officially filed a patent application for the LapRotator through the international Patent Cooperation Treaty (PCT). The LapRotator is an attachment for laparoscopes that lets surgeons rotate the scope with one hand. It works with standard laparoscope equipment and is compact, lightweight, and intuitive, built for better control, less fatigue, and better ergonomics. This filing is a big milestone for our team. Thank you to everyone who has supported us along the way. More to come soon."),
]
AVATAR = '<span class="avatar"><img src="assets/icons/avatar-mark.svg" alt=""></span>'
cards = []
modals = []
for i, (cat, title, date, text) in enumerate(STORIES, 1):
    cards.append(f"""<button class="card reveal" data-modal="story-{i}" aria-haspopup="dialog">
      <span class="img-wrap"><img src="assets/img/news-{i}.jpg" alt="" loading="lazy"></span>
      <div class="card-text">
        <span class="cat">{cat}</span>
        <h3>{title}</h3>
        <span class="author">{AVATAR}<span><b>Pando Surgical Team</b><time>{date}</time></span></span>
        <span class="excerpt">{text}</span>
        <span class="read-more">Read more →</span>
      </div>
    </button>""")
    modals.append(f"""<div class="modal" id="story-{i}" role="dialog" aria-modal="true" aria-labelledby="story-{i}-title" aria-hidden="true">
  <article class="modal-card story-card">
    <img src="assets/img/news-{i}.jpg" alt="">
    <button class="modal-close" aria-label="Close"><img src="assets/icons/story-close.svg" alt=""></button>
    <div class="story-body">
      <span class="cat">{cat}</span>
      <h2 id="story-{i}-title">{title}</h2>
      <span class="author story-author">{AVATAR}<span><b>Pando Surgical Team</b><time>{date}</time></span></span>
      <p class="body">{text}</p>
    </div>
  </article>
</div>""")

page("news.html", "Latest News", "News and milestones from Pando Surgical.", "news", f"""
<section class="news">
  <div class="news-head"><h1 class="page-title" style="text-align:center">Latest News</h1></div>
  <div class="news-grid">
    {"".join(cards)}
  </div>
</section>
""", light=True, extra="\n".join(modals))

# ---------------------------------------------------------------- About – Company
VALUES = [
    ("Equity", "Most surgical tools were designed around one kind of hand. We design for every body and every hand in the OR, because every surgeon deserves to feel supported.", "Surgeon in scrubs and mask during an operation"),
    ("Efficiency", "We streamline surgical workflows, so teams spend less time fighting their tools and more time focused on the patient.", "Surgical team working in the operating room"),
    ("Ergonomics", "We build around how surgeons actually move, so the intersection between human and technology feels seamless.", "Surgeon's hands using an instrument"),
]
page("about.html", "About", "Pando Surgical believes surgery should be equitable, efficient, and ergonomic.", "about", f"""
<section class="about-hero">
  <h1>We believe surgery should be equitable, efficient, and ergonomic.</h1>
</section>

<section class="story">
  <div class="story-text reveal">
    <h2>How Pando Started</h2>
    <p>Pando Surgical started with the mission to improve surgical ergonomics. We are a group of engineers who work closely with physicians, and we noticed that many surgical tools create unnecessary strain on surgeons because they are designed with only one anatomy in mind. As the workforce diversifies, we aim to equip every surgeon with tools that support them.</p>
    <p>The LapRotator is our first product, but it’s only the beginning. From here, Pando Surgical will grow into a multi-product company, building a full suite of ergonomic tools that takes us from laparoscopy into robotics and beyond, so that every surgeon, in every specialty, has tools designed around them.</p>
  </div>
  <img class="reveal" src="assets/img/about-story.jpg" alt="Pando Surgical team at work" loading="lazy">
</section>

<section class="values">
  <div class="values-head reveal">
    <h2>What we value</h2>
    <p>Three principles shape every tool we build, from the first sketch to the operating room.</p>
  </div>
  <div class="values-grid">
    {"".join(f'''<article class="value reveal"><img src="assets/img/value-{i}.jpg" alt="{alt}" loading="lazy"><div class="value-text"><h3>{t}</h3><p class="body">{b}</p></div></article>''' for i, (t, b, alt) in enumerate(VALUES, 1))}
  </div>
</section>

<section class="team-cta on-dark">
  <h2 class="reveal">Meet the people behind Pando Surgical.</h2>
  <p>A team of engineers working side by side with surgeons, building the tools we wish they’d always had.</p>
  <div class="btn-row">
    {btn("Meet the team", "team.html")}
    {btn("Get in touch", "contact.html", "outline")}
  </div>
</section>
""")

# ---------------------------------------------------------------- Investors
RES = [("icon-deck", "Pitch Deck"), ("icon-fin", "Financial Overview"), ("icon-press", "Press Kit")]
rows = "".join(f'<div class="res-row"><img src="assets/icons/{ic}.svg" alt=""><h2>{t}</h2><span class="chip">Coming soon</span><img src="assets/icons/icon-lock.svg" alt="Locked"></div>' for ic, t in RES)
page("investors.html", "Investors & Resources", "Investor materials for Pando Surgical are coming soon.", "investors", f"""
<section class="investors">
  <div class="inv-intro reveal">
    <h1>Investors &amp; Resources</h1>
    <p class="sub">Investor materials are coming soon.</p>
    <p class="body">We’ll be opening up our seed round soon. Check back here for updates, or reach out directly if you’d like to learn more.</p>
    {btn("Reach out to the team", "contact.html", "dark")}
  </div>
  <div class="resources reveal">
    <p class="eyebrow">Resources</p>
    {rows}
  </div>
</section>
""", light=True)

# ---------------------------------------------------------------- Careers
def area(i, label):
    return f"""<div class="field">
        <label for="q{i}">{label} <span class="req">*</span></label>
        <textarea id="q{i}" name="q{i}" required data-words="150" aria-describedby="q{i}-count"></textarea>
        <span class="counter" id="q{i}-count">0/150 words</span>
      </div>"""


page("careers.html", "Careers", "Join Pando Surgical: we're opening an internship spot for an Engineering intern.", "careers", f"""
<section class="careers">
  <div class="head reveal">
    <h1 class="page-title">Careers</h1>
    <p>We’re opening an internship spot for an Engineering intern.</p>
  </div>
  <form class="app-form" data-demo="Thanks! Online applications aren’t connected yet, so please email your answers and resume link to {EMAIL} for now.">
    <p class="intro">We’re looking for an Engineering intern to join our team. Submit your resume and a few short answers below, and we’ll be in touch after reviewing your application. You can also reach us directly at <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
    <div class="row-2">
      <div class="field"><label for="c-name">Full name <span class="req">*</span></label><input id="c-name" name="name" autocomplete="name" required></div>
      <div class="field"><label for="c-email">Email address <span class="req">*</span></label><input id="c-email" name="email" type="email" autocomplete="email" required></div>
    </div>
    <div class="field">
      <label for="c-resume">Resume (Google Drive link) <span class="req">*</span></label>
      <input id="c-resume" name="resume" type="url" placeholder="https://drive.google.com/…" required aria-describedby="c-resume-hint">
      <p class="hint" id="c-resume-hint">Make sure sharing is set to “Anyone with the link can view” so we can open it.</p>
    </div>
    {area(1, "Tell us about yourself")}
    {area(2, "Why Pando Surgical? Why this role?")}
    {area(3, "What skills can you bring to this role?")}
    <button class="btn btn-primary btn-block" type="submit">Submit application</button>
    <p class="form-note" role="status"></p>
  </form>
</section>
""", light=True)

# ---------------------------------------------------------------- Contact
page("contact.html", "Contact Us", "Get in touch with Pando Surgical: surgeons, hospitals, partners and press.", "contact", f"""
<section class="contact">
  <div class="contact-art">
    <div class="contact-motion" aria-hidden="true"><span class="b1"></span><span class="b2"></span><span class="b3"></span></div>
    <h1>Connect with us.</h1>
    <p>From surgeons, to hospitals, to partners and press, we read every message.</p>
  </div>
  <div class="contact-form">
    <form data-demo="Thanks! The form isn’t connected yet, so please email {EMAIL} for now.">
      <div class="field"><label for="f-name">Name</label><input id="f-name" name="name" autocomplete="name" required></div>
      <div class="field"><label for="f-email">Email</label><input id="f-email" name="email" type="email" autocomplete="email" required></div>
      <div class="field"><label for="f-msg">Message</label><textarea id="f-msg" name="message" required></textarea></div>
      <label class="consent"><input type="checkbox" required><span>By clicking “Send message”, you agree to our <a href="terms.html">Terms of Use</a> and <a href="privacy.html">Privacy Notice</a>.</span></label>
      <button class="btn btn-dark" type="submit">Send a Message</button>
      <p class="form-note" role="status"></p>
    </form>
  </div>
</section>
""", light=True)

# ---------------------------------------------------------------- Legal
MAIL = f'<a href="mailto:{EMAIL}">{EMAIL}</a>'
CONTACT_P = f"Questions about this notice can be sent to {MAIL}."


def legal(filename, title, page_id, desc, sections):
    body = "".join(f"<section><h2>{h}</h2><p>{p}</p></section>" for h, p in sections)
    page(filename, title, desc, page_id, f"""
<section class="legal">
  <h1 class="page-title">{title}</h1>
  <p class="updated">Last updated: August 2026</p>
  <div class="legal-body">{body}</div>
</section>
""", light=True)


legal("privacy.html", "Privacy Notice", "privacy", "How Pando Surgical handles information submitted through this website.", [
    ("Information we collect", "When you use our contact form, we collect the name, email address, and message you provide so we can respond to your inquiry. We do not require an account or collect payment information on this site. We use aggregated, anonymous performance data (such as page load metrics) to help us keep the site running smoothly."),
    ("How we use it", "Information submitted through our contact form is used only to respond to your message and is not sold or shared with third parties for marketing purposes."),
    ("Cookies", "This site does not use advertising or tracking cookies. Basic, privacy-preserving analytics may be used to understand overall site usage."),
    ("Contact", CONTACT_P),
])
legal("terms.html", "Terms of Use", "terms", "Terms of use for the Pando Surgical website.", [
    ("Purpose of this site", "This website is provided by Pando Surgical, Inc. for general informational purposes about our company and the devices we are developing, including the LapRotator. Content on this site does not constitute medical advice, and devices described may not yet be commercially available or cleared for sale in all regions."),
    ("Intellectual property", "The Pando Surgical name, logo, and site content are the property of Pando Surgical, Inc. and may not be reproduced without permission."),
    ("No warranty", "This site is provided “as is” without warranties of any kind. We make reasonable efforts to keep information accurate and up to date but do not guarantee completeness or accuracy at all times."),
    ("Contact", CONTACT_P),
])
legal("accessibility.html", "Accessibility Statement", "accessibility", "Pando Surgical's commitment to an accessible website.", [
    ("Our commitment", "Pando Surgical is committed to making our website usable by as many people as possible, including people with disabilities. We aim to follow the Web Content Accessibility Guidelines (WCAG) 2.1 at level AA as a general standard for our site."),
    ("Ongoing work", "As a small, growing team, we are continuously improving the accessibility of this site, including color contrast, keyboard navigation, and screen reader support, as we add new pages and features."),
    ("Feedback", f"If you encounter any accessibility barriers on this site, please let us know at {MAIL} so we can address them."),
])

print("Built pages in", ROOT)
