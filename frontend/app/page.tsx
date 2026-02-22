"use client";

import { useState, useRef, useEffect } from "react";
import HealthProfileForm, {
  HealthData,
  DEFAULT_HEALTH,
} from "@/components/HealthProfileForm";
import FoodResult from "@/components/FoodResult";
import PrescriptionResult from "@/components/PrescriptionResult";
import TravelResult from "@/components/TravelResult";
import { analyzeImage, assessTravelRisk } from "@/lib/api";

// ---------- Message types for the chat ----------
type Message = {
  id: number;
  role: "user" | "assistant";
  text?: string;
  imageUrl?: string;
  analyzeData?: any;   // unified /api/analyze response
  travelData?: any;
};

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      role: "assistant",
      text: "Hi! I'm your AI Health Companion.\n\nUpload any image — food photo or prescription — and I'll analyze it for you. You can also add a message to give me more context.\n\nTap the profile icon to set your health details first.",
    },
  ]);
  const [input, setInput] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthData>(DEFAULT_HEALTH);
  const [showProfile, setShowProfile] = useState(false);
  const [loading, setLoading] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  let nextId = useRef(1);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMsg = (msg: Omit<Message, "id">) => {
    const m = { ...msg, id: nextId.current++ };
    setMessages((prev) => [...prev, m]);
    return m;
  };

  // ---------- Handle image selection ----------
  const onImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileRef.current) fileRef.current.value = "";
  };

  // ---------- Send handler ----------
  const handleSend = async () => {
    if (loading) return;
    if (!input.trim() && !imageFile) return;

    // If an image is attached, use the unified /api/analyze endpoint
    if (imageFile) {
      const userText = input.trim();
      addMsg({ role: "user", text: userText || "Analyze this image", imageUrl: imagePreview! });
      clearImage();
      setInput("");
      setLoading(true);

      try {
        const data = await analyzeImage(imageFile, health, userText || undefined);
        addMsg({ role: "assistant", analyzeData: data });
      } catch (err: any) {
        addMsg({ role: "assistant", text: `Error: ${err.message}` });
      } finally {
        setLoading(false);
      }
      return;
    }

    // Otherwise treat as a travel/activity risk query
    const userText = input.trim();
    addMsg({ role: "user", text: userText });
    setInput("");
    setLoading(true);

    try {
      const data = await assessTravelRisk(userText, "", health);
      addMsg({ role: "assistant", travelData: data });
    } catch (err: any) {
      addMsg({ role: "assistant", text: `Error: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  // ---------- Render assistant message content ----------
  const renderAssistantContent = (msg: Message) => {
    if (msg.analyzeData) {
      const d = msg.analyzeData;
      if (d.type === "food" && d.food_data) {
        return <FoodResult data={d.food_data} />;
      }
      if (d.type === "prescription" && d.prescription_data) {
        return <PrescriptionResult data={d.prescription_data} />;
      }
      // unknown or message-only
      return (
        <p className="text-sm whitespace-pre-wrap">
          {d.message || "I couldn't identify the image clearly. Please try again with a clearer photo."}
        </p>
      );
    }
    if (msg.travelData) return <TravelResult data={msg.travelData} />;
    if (msg.text) return <p className="text-sm whitespace-pre-wrap">{msg.text}</p>;
    return null;
  };

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto">
      {/* ---- Header ---- */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <div>
          <h1 className="text-lg font-bold tracking-tight">AI Health Companion</h1>
          <p className="text-xs text-gray-500">Upload any image · food or prescription</p>
        </div>
        <button
          onClick={() => setShowProfile(true)}
          className="bg-gray-800 hover:bg-gray-700 text-sm px-3 py-1.5 rounded-lg border border-gray-700 transition flex items-center gap-1.5"
        >
          <span className="text-base">&#9881;</span>
          Health Profile
          {health.conditions.length > 0 && (
            <span className="bg-emerald-600 text-white text-[10px] rounded-full w-5 h-5 flex items-center justify-center">
              {health.conditions.length}
            </span>
          )}
        </button>
      </header>

      {/* ---- Chat area ---- */}
      <div className="flex-1 overflow-y-auto chat-scroll px-4 py-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-emerald-700/30 border border-emerald-600/30"
                  : "bg-gray-800/60 border border-gray-700/40"
              }`}
            >
              {/* User image preview */}
              {msg.imageUrl && (
                <img
                  src={msg.imageUrl}
                  alt="uploaded"
                  className="rounded-lg mb-2 max-h-48 object-cover"
                />
              )}
              {msg.role === "user" && msg.text && (
                <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
              )}
              {msg.role === "assistant" && renderAssistantContent(msg)}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl px-4 py-3">
              <p className="text-sm text-gray-400 animate-pulse">Analyzing...</p>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* ---- Image preview bar ---- */}
      {imagePreview && (
        <div className="px-4 py-2 border-t border-gray-800 flex items-center gap-3">
          <img
            src={imagePreview}
            alt="preview"
            className="h-12 w-12 rounded-lg object-cover"
          />
          <span className="text-xs text-gray-400 flex-1">Image attached — AI will identify it</span>
          <button
            onClick={clearImage}
            className="text-red-400 text-xs hover:text-red-300"
          >
            Remove
          </button>
        </div>
      )}

      {/* ---- Input bar ---- */}
      <div className="px-4 py-3 border-t border-gray-800 flex items-center gap-2">
        {/* Hidden file input */}
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={onImageSelect}
        />
        <button
          onClick={() => fileRef.current?.click()}
          className="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg p-2 transition"
          title="Upload image"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </button>

        <input
          className="flex-1 bg-gray-800 rounded-lg px-4 py-2.5 text-sm border border-gray-700 focus:outline-none focus:border-emerald-500 transition"
          placeholder={
            imageFile
              ? "Optional: describe the image or add context..."
              : "Ask about travel safety (e.g. Can I fly?)"
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          disabled={loading}
        />

        <button
          onClick={handleSend}
          disabled={loading || (!input.trim() && !imageFile)}
          className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2.5 text-sm font-medium transition"
        >
          Send
        </button>
      </div>

      {/* ---- Health Profile Modal ---- */}
      {showProfile && (
        <HealthProfileForm
          health={health}
          onChange={setHealth}
          onClose={() => setShowProfile(false)}
        />
      )}
    </div>
  );
}
