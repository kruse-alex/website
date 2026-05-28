# alexknowsdata.com — Portfolio Site

Personal portfolio for **Alex Held**, Lead Data Science at Der Spiegel, Hamburg.

## Repo & Deployment

- **Live site:** https://www.alexknowsdata.com
- **GitHub:** https://github.com/kruse-alex/website (account: `kruse-alex`)
- **Netlify:** auto-deploys on every push to `master`, no build step
- **Deploy:** `git add`, `git commit`, `git push origin master`

## Stack

Plain HTML/CSS/JS — no framework, no build tool. Everything lives in `index.html` with styles inline. Do not introduce Hugo, npm, or any build step.

## File Structure

```
index.html              — entire site (nav, hero, Work, About)
posts/*.html            — 20 subpages (old blog posts + bird viz)
public/post/*/          — images used by subpages
akr.jpg                 — profile photo (About section)
netlify.toml            — publish = ".", command = "" (no build)
```

## Design

- Dark terminal aesthetic: base `#0d1117`, accent `#58a6ff`
- Fonts: JetBrains Mono (mono/headings) + Inter (body)
- Nav brand: `alex@held:~$` — typewriter animation + blinking cursor on page load
- All content uses `.list-block` / `.list-item` rows (no cards)

## Site Sections

**Work** (`#work`)
- Towards Data Science (2 articles, 2024)
- The Audiencers (3 articles, 2023/2024/2025)
- Talks & Webinars (3 talks, 2023)
- Medium (3 visible + 5 in toggle)
- Data Viz (birds 2024, marathon, finedust, stadtrad, ddj, generative art, attribution)
- More older work (collapsible archive)
- Hackathons & competitions (3 visible + 2 in toggle)

**About** (`#about`)
- Bio text (2 paragraphs)
- Profile photo: `akr.jpg` (circular)
- Timeline: Lead DS @ Der Spiegel → Data Analyst @ ZEIT Online → Data Journalist @ Spiegel Online (Google News Fellowship) → Data Analyst @ etracker → M.Sc. Business Analytics @ Uni Duisburg-Essen
- LinkedIn + Medium links at bottom of page

## Key Decisions

- No footer — page ends after About
- No skill tags in About (removed)
- Sub-headings in Work are short publication/venue names, not verbose descriptions
- Old blog post subpages all use `alex@held:~$` nav brand and `← alex held` footer link
- OG/Twitter card meta tags point to `https://www.alexknowsdata.com/akr.jpg`
- Name is **Alex Held** everywhere (not Alexander)
