<div align="center">
  <img width="1200" height="475" alt="AI-PECO Banner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# AI-PECO · AI-Powered Energy Consumption Optimizer

AI-PECO is a Vite + React dashboard that helps households and small facilities understand how their devices draw power in real time. It combines live telemetry, forecast modeling, and a Gemini-powered assistant to surface anomalies, cost trends, and actionable recommendations with a tone that feels human—not robotic.

> **Demo:** https://ai.studio/apps/drive/1lMtIVZ4wAAHFEblJv8BNdZoAD7obCHAY

---

## ✨ Highlights

- Live and historical energy charts with forecast overlays
- Device-by-device diagnostics, statuses, and remote toggles
- AI recommendation feed with contextual savings tips
- Friendly chatbot that understands Markdown responses via Gemini
- Dark/light theming and fully responsive layout

---

## 🧱 Tech Stack

- **Frontend:** React 18, TypeScript, TailwindCSS, Recharts, Vite
- **AI:** Google Gemini (chat + analysis endpoints)
- **Tooling:** ESLint, npm scripts, Vite build pipeline

---

## 🚀 Getting Started

### 1. Prerequisites

- Node.js 18+
- npm 9+ (bundled with newer Node installers)

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

Create `.env.local` (never commit this file) and add your Gemini key:

```
GEMINI_API_KEY=your-key-here
```

> The project reads `process.env.GEMINI_API_KEY` inside `services/geminiService.ts`. Without it, smart analysis and the chatbot fall back to friendly error messages.

### 4. Run the development server

```bash
npm run dev
```

Visit `http://localhost:5173` (or the port Vite prints) to explore the dashboard.

---

## 🔧 Scripts

| Command         | Description                              |
|-----------------|------------------------------------------|
| `npm run dev`   | Start Vite in dev mode with hot reload    |
| `npm run build` | Create a production build in `dist/`      |
| `npm run preview` | Serve the production build locally     |

---

## 🗂 Project Layout

```
AIPECO/
├── components/          # Reusable UI building blocks
├── contexts/            # Theme + global providers
├── hooks/               # Custom hooks (mock data, chat, notifications)
├── services/            # Gemini client + analysis helpers
├── App.tsx              # Root layout and view switching
├── types.ts             # Shared TypeScript contracts
└── vite.config.ts
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-idea`
3. Commit with context-rich messages
4. Push and open a Pull Request

Please lint before pushing and avoid checking in `.env.local` or API keys.

---

## 📄 License

This project is distributed under the MIT License. Feel free to adapt it for your own dashboards, and let us know what you build!

---

Made with care by the AI-PECO team. If something feels off or you have a feature idea, open an issue—we actually read them. 💡
