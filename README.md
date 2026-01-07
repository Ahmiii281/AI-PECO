# AI-PECO - Energy Consumption Dashboard

AI-PECO is a web application built with React and TypeScript that helps users monitor and optimize their electricity consumption. The dashboard displays real-time power usage, device status, energy forecasts, and provides recommendations to reduce costs.

---

## Features

- Real-time power consumption monitoring with live charts
- Device management - view and track individual appliances
- Energy consumption forecasts for the next 24 hours
- Smart analysis tool that answers questions about usage patterns
- Chat assistant for energy-saving tips and advice
- Historical data viewing and reports
- Dark and light theme support
- Responsive design for all screen sizes

---

## Technology Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling
- **Marked** - Markdown parsing

---

## Project Structure

```
AIPECO/
├── components/       # React components (charts, views, UI elements)
├── contexts/        # React context providers (theme)
├── hooks/           # Custom React hooks (data, chat, notifications)
├── services/        # API services (for future backend integration)
├── App.tsx          # Main application component
├── types.ts         # TypeScript type definitions
└── vite.config.ts   # Vite configuration
```

---

## Getting Started

### Requirements

- Node.js 18 or higher
- npm 9 or higher

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to the URL shown in the terminal (usually `http://localhost:5173`)

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

---

## How It Works

The application uses mock data to simulate real-time energy monitoring:

- **Data Generation**: The `useMockData` hook generates realistic power consumption data based on time-of-day patterns
- **Device Simulation**: Device statuses and power levels are updated automatically to simulate real devices
- **Chat Assistant**: A rule-based chatbot provides energy-saving advice based on user questions
- **Analysis Engine**: The Smart Analysis component processes consumption data to answer user queries

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Create production build |
| `npm run preview` | Preview the production build locally |

---

## Customization

- **Connect Real Data**: Replace the mock data in `useMockData.ts` with API calls to your backend
- **Modify Chat Responses**: Update the response logic in `useChatAssistant.ts` to change the assistant's behavior
- **Add New Features**: Extend the Smart Analysis component or add new views in the `components/` folder

---

## License

This project is licensed under the MIT License.

---

## Author

Final Year Project - Software Engineering  
University of Mianwali  
2025

---

## Notes

- Currently uses mock data for demonstration purposes
- All analysis and recommendations are generated locally (no external AI services)
- The application is designed to be easily extended with real hardware integration
