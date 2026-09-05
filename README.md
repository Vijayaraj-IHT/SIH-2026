<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:11998e,50:13a4a0,100:38ef7d&height=190&section=header&text=Campus%20Arena&fontSize=54&fontColor=ffffff&animation=fadeIn&desc=Inter-Collegiate%20Sports%20Fixture%20%26%20Tournament%20Platform&descSize=18&descAlignY=58"/>

<div align="center">

A full-stack, multi-sport tournament management and fixture platform built for university athletic meets — started for the college **PET club** and engineered to scale across colleges.

<br/>

![Next.js](https://img.shields.io/badge/Next.js%2014-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React%2018-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

<br/>

![Status](https://img.shields.io/badge/Status-Active%20Development-22C55E?style=flat-square)
![Version](https://img.shields.io/badge/Version-1.3-6366F1?style=flat-square)
![Hackathon](https://img.shields.io/badge/Smart%20India%20Hackathon-2026-F97316?style=flat-square)

</div>

---

## ✨ Feature Highlights

<table>
<tr>
<td width="50%" valign="top">

#### 🏅 Multi-Sport Scoring
Goal sports (Football, Basketball, Kabaddi) · over-based (Cricket T20) · set-based (Volleyball, Badminton, Tennis) — with auto **GD · NRR · Set-Ratio** points tables.

#### 🔁 Automated Fixtures
Round-Robin via the **Berger algorithm** + knockout brackets with seeded byes. Overrides preserve provenance in `original_source_snapshot`.

</td>
<td width="50%" valign="top">

#### 🎛️ Real-Time Ground Controls
One-click **cascade delay** (+30 min) · **60-sec spot entry** · live score ticker · role dashboards for **Admin / Captain / Scorer**.

#### 📶 Offline-First Scorer
High-contrast touch UI with **IndexedDB queueing** for poor-connectivity venues, plus a **30-min dispute window** with jury logging & bracket holds.

</td>
</tr>
</table>

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | Next.js 14 (App Router), React 18 |
| **Language** | TypeScript |
| **Styling** | Tailwind CSS · lucide-react · clsx · tailwind-merge |
| **Backend / DB** | Supabase — PostgreSQL 15+, Auth, Row Level Security, Triggers, Views |
| **Tooling** | npm, ESLint |

---

## 📁 Project Structure

<details>
<summary><b>📂 View directory tree</b></summary>

```
inter-college-sports-platform/
├── src/
│   ├── app/
│   │   ├── (auth)/login        # Role-based Supabase Auth
│   │   ├── admin/              # Control desk, scheduler, approvals, disputes, audit
│   │   ├── captain/            # Team dashboards, lineups, protests
│   │   ├── scorer/             # Live scoring console
│   │   ├── matches/  tournaments/  leaderboard/
│   ├── components/             # Navbar · LiveScoreTicker · PointsTable
│   │                           # TournamentBracket · VenueTimeline · ui/
│   ├── hooks/                  # useLiveMatch · useOfflineScorer
│   └── lib/                    # fixtureGenerator · supabaseClient/Server · types
└── supabase/
    ├── migrations/             # master_schema_v1.3.sql (24-entity DDL, RLS, triggers)
    └── seed.sql                # Inter-collegiate test dataset
```

</details>

---

## 🚀 Getting Started

```bash
# 1. Move into the app
cd inter-college-sports-platform/inter-college-sports-platform

# 2. Install dependencies
npm install

# 3. Configure Supabase in .env.local
#    NEXT_PUBLIC_SUPABASE_URL=...
#    NEXT_PUBLIC_SUPABASE_ANON_KEY=...

# 4. Run
npm run dev        # → http://localhost:3000
```

> Requires **Node 18+** and a **Supabase** project (PostgreSQL 15+). Apply `supabase/migrations/` then `seed.sql`.

<details>
<summary><b>📜 Available scripts</b></summary>

| Command | Action |
|---|---|
| `npm run dev` | Development server |
| `npm run build` | Production build |
| `npm run start` | Production server |
| `npm run lint` | Run ESLint |

</details>

---

## 📌 Roadmap

- [x] Multi-sport scoring engine
- [x] Round-robin & knockout generation
- [x] Offline scorer console
- [ ] Deploy live demo
- [ ] Multi-college tenancy expansion

---

<div align="center">

**Built by [Vijayaraj K P](https://github.com/Vijayaraj-IHT)**

<a href="https://www.linkedin.com/in/vijaya-raj-k-p-9981593a0/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white"/></a>
<a href="mailto:kpvijay3102@gmail.com"><img src="https://img.shields.io/badge/Email-EA4335?style=for-the-badge&logo=gmail&logoColor=white"/></a>

</div>

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:38ef7d,50:13a4a0,100:11998e&height=110&section=footer"/>
