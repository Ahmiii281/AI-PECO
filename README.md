# AI-PECO · AI-Powered Energy Consumption Optimizer

AI-PECO is a Vite + React dashboard that helps households and small facilities understand how their devices draw power in real time. It combines live telemetry, forecast modeling, and a handcrafted assistant layer to surface anomalies, cost trends, and actionable recommendations with a tone that feels human—not robotic.


---

## ✨ Highlights

- Live + historical energy timelines with forecast overlays
- Device-by-device diagnostics, statuses, and remote toggles
- AI-style recommendation feed with contextual savings tips
- Friendly chatbot that speaks Markdown and references the latest conversation history
- Dark/light theming, keyboard-friendly navigation, and a responsive layout that feels natural on any screen

---

## 🧱 Tech Stack

- **Frontend:** React 18, TypeScript, TailwindCSS, Recharts, Vite
- **Logic:** Custom heuristic chatbot + analysis engine (no hosted AI dependency)
- **Tooling:** ESLint, npm scripts, Vite build pipeline

---

## 🧠 How It Works

- **Mock data loop** — `hooks/useMockData.ts` simulates live draws, forecasts, device statuses, and anomalies so the UI feels alive without wiring up hardware yet.
- **Insight layer** — `hooks/useChatAssistant.ts` and `components/SmartAnalysis.tsx` translate raw numbers into conversational guidance. The logic is deterministic and owned by this repo—no external AI calls.
- **UI composition** — `App.tsx` swaps between views (`Dashboard`, `Chatbot`, `Devices`, `Reports`, `Settings`) while `Sidebar` + `Header` keep navigation predictable.

---

## 🚀 Getting Started

### 1. Prerequisites

- Node.js 18+
- npm 9+ (bundled with newer Node installers)

### 2. Install dependencies

```bash
npm install
```

### 3. Run the development server

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

## 🧪 Testing & Quality

- `npm run build` to ensure the TypeScript + bundler pipeline succeeds.
- Use your browser devtools or Lighthouse against `npm run preview` for performance and accessibility budgets.
- The project ships with TypeScript types across components and hooks, so favor type-safe additions over `any`.

---

## 🗂 Project Layout

```
AIPECO/
├── components/          # Reusable UI building blocks
├── contexts/            # Theme + global providers
├── hooks/               # Custom hooks (mock data, chat, notifications)
├── services/            # Reserved for future API adapters (currently empty)
├── App.tsx              # Root layout and view switching
├── types.ts             # Shared TypeScript contracts
└── vite.config.ts
```

---

## 🔧 Customization Tips

- **Data fidelity**: swap `useMockData` with real telemetry by hooking your API inside the hook; the rest of the app already expects the same shape.
- **Chat voice**: update the `ENERGY_TIPS` array and rules in `useChatAssistant` to match your brand voice or domain expertise.
- **Smart analysis**: extend `buildResponse` in `SmartAnalysis` with richer heuristics or plug in a local ML model if you want deeper insights.

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
