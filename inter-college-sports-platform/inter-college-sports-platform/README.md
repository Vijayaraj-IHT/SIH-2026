# Campus Arena — Multi-Sport Inter-Collegiate Fixture & Tournament Platform

A full-stack, enterprise-grade sports tournament management and match fixture platform designed specifically for university athletic meets and inter-collegiate championships.

Built with **Next.js 14 (App Router)**, **TypeScript**, **Tailwind CSS**, and **Supabase (PostgreSQL 15+)**, fully compliant with the **v1.3 Attribute-Level Domain Specification**.

---

## 🏆 Key Features

### 1. Multi-Sport & Modular Scoring Engine
* Native support for **Goal Sports** (Football, Basketball, Kabaddi), **Over-based Sports** (Cricket T20/Limited Overs), and **Set-based Sports** (Volleyball, Badminton, Tennis).
* Standardized points tables with auto-calculated **Goal Difference (GD)**, **Net Run Rate (NRR)**, and **Set/Point Ratios**.

### 2. Automated Fixture Generator with Manual Overrides
* **Round Robin (Berger Algorithm):** Generates balanced round-robin leagues and pool stages.
* **Knockout Bracket Tree:** Nearest power-of-2 calculations with automatic seeded **Byes**.
* **Provenance Preservation:** Overridden matches preserve original bracket source lineage in `original_source_snapshot`.

### 3. Real-Time Operational Ground Controls
* **One-Click Cascade Delay:** Shift all remaining matches on a venue by `+30m` with 1 click during rain or delays.
* **60-Second Spot Entry Modal:** Register walk-in visiting teams instantly so bracket draws are not delayed.
* **Offline-Resilient Mobile Scorer Console:** High-contrast, large-button touch UI with Undo guard and local IndexedDB queuing.
* **30-Minute Dispute Window & Jury Logging:** Formal protest submission system with downstream bracket holds (`HELD_FOR_DISPUTE`).
* **Overall Championship Leaderboard:** Dynamic aggregation across sports for the General Institutional Trophy.

---

## 🛠️ Tech Stack & Directory Architecture

```
inter-college-sports-platform/
├── supabase/
│   ├── migrations/
│   │   └── 20260830000000_master_schema_v1.3.sql   # Complete 24-entity DDL, Triggers, RLS, Views
│   └── seed.sql                                     # Realistic Inter-Collegiate test dataset
├── src/
│   ├── app/
│   │   ├── (auth)/login                             # Role-based Supabase Auth
│   │   ├── admin/                                   # Admin Control Desk, Scheduler, Approvals, Disputes
│   │   ├── scorer/                                  # Field Scorer PWA Console
│   │   ├── captain/                                 # Team Representative Hub & Arrival Check-in
│   │   ├── tournaments/[id]/                        # Brackets, Pools & Standings
│   │   ├── matches/[id]/                            # Live Match Center
│   │   └── leaderboard/                             # Overall General Championship Trophy
│   ├── components/                                  # Modular UI primitives, Brackets, Timelines, Tables
│   ├── hooks/                                       # Live WebSockets & Offline Sync hooks
│   └── lib/                                         # Supabase clients, TypeScript types, Fixture algorithms
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

---

## 🚀 Getting Started

### 1. Database Setup (Supabase)
1. Create a new project on [Supabase](https://supabase.com).
2. Open the **SQL Editor** in your Supabase dashboard.
3. Copy and run the entire contents of `supabase/migrations/20260830000000_master_schema_v1.3.sql`.
4. (Optional) Run `supabase/seed.sql` to populate sample colleges, venues, tournaments, and fixtures.

### 2. Application Setup
1. Clone / extract the project folder:
   ```bash
   cd inter-college-sports-platform
   npm install
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env.local
   ```
   Add your Supabase project credentials in `.env.local`:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🛡️ User Roles & Demo Credentials

| Role | Test Email | Access Scope |
| :--- | :--- | :--- |
| **Super Admin** | `admin@gct.ac.in` | Full management, drag-drop scheduler, dispute adjudication, RLS bypass. |
| **Ground Scorer** | `scorer@gct.ac.in` | Assigned match live scorecard, point increments, undo, walkovers. |
| **Team Captain** | `captain@gct.ac.in` | "My Match Day" card, 1-tap ground check-in, lineup submission, protest filing. |
| **Public Spectator** | *No login needed* | Read-only live scores, brackets, points table, and medal leaderboard. |

---

## 📄 License & Compliance
Compliant with Domain Specification v1.3. Released for collegiate sports boards and university athletic meets.
