
import { GoogleGenAI, Chat } from "@google/genai";
import { DataPoint } from '../types';

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  console.warn("API_KEY environment variable not set. Smart Analysis and Chatbot will not work.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY! });
let chatSession: Chat | null = null;

function getChatSession(): Chat {
  if (!API_KEY) {
    throw new Error("Gemini API key is not configured.");
  }
  if (!chatSession) {
    chatSession = ai.chats.create({
      model: 'gemini-2.5-flash',
      config: {
        systemInstruction: 'You are a helpful and friendly AI assistant for the AI-PECO energy management dashboard. Your name is PECO-Bot. Be concise and helpful. You can answer questions about energy consumption, provide energy-saving tips, and explain concepts related to electricity. Keep responses friendly and easy to understand for a non-technical audience. Use markdown for formatting when it improves readability (e.g., lists).',
      }
    });
  }
  return chatSession;
}

export const sendChatMessage = async (message: string): Promise<string> => {
  if (!API_KEY) {
    return "Error: Gemini API key is not configured.";
  }
  try {
    const chat = getChatSession();
    const response = await chat.sendMessage({ message });
    return response.text;
  } catch (error) {
    console.error("Error sending chat message:", error);
    if (error instanceof Error) {
        return `An error occurred while communicating with the AI model: ${error.message}`;
    }
    return "An unknown error occurred while communicating with the AI model.";
  }
};


export const runSmartAnalysis = async (query: string, consumptionHistory: DataPoint[]): Promise<string> => {
  if (!API_KEY) {
    return "Error: Gemini API key is not configured. Please set the API_KEY environment variable.";
  }

  const model = 'gemini-2.5-pro';
  
  const dataSummary = consumptionHistory.slice(-24).map(d => `Time: ${d.time}, Power: ${d.power.toFixed(2)} kW`).join('\n');

  const prompt = `
    System Instruction:
    You are AI-PECO, an advanced AI-powered energy consumption analyst. Your task is to analyze user queries about their energy usage based on the provided data. Provide clear, actionable insights in a well-structured format. Use markdown for formatting. Be concise but thorough.

    Energy Consumption Data (Last 24 hours):
    ${dataSummary}

    User Query:
    "${query}"

    Analysis and Response:
  `;

  try {
    const response = await ai.models.generateContent({
      model: model,
      contents: prompt,
      config: {
        thinkingConfig: { thinkingBudget: 32768 }
      }
    });
    return response.text;
  } catch (error) {
    console.error("Error calling Gemini API:", error);
    if (error instanceof Error) {
        return `An error occurred while communicating with the AI model: ${error.message}`;
    }
    return "An unknown error occurred while communicating with the AI model.";
  }
};
