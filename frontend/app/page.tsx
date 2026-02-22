"use client";

import { useState, useRef, useEffect } from "react";
import HealthProfileForm, {
  HealthData,
  DEFAULT_HEALTH,
} from "@/components/HealthProfileForm";
import FoodResult from "@/components/FoodResult";
import TravelResult from "@/components/TravelResult";
import { analyzeFoodImage, assessTravelRisk } from "@/lib/api";

// ---------- Message types for the chat ----------
type Message = {
  id: number;
  role: "user" | "assistant";
  text?: string;
  imageUrl?: string;
  foodData?: any;
  travelData?: any;
};

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      role: "assistant",
      text: "Hi! I'm your AI Health Companion. You can:\n- Upload a food photo for calorie & risk analysis\n- Ask me about travel/activity safety (e.g. \"Can I fly?\", \"Is scuba diving safe?\")\n\nTap the profile icon to set up your health profile first.",
    },
  ]);
  const [input, setInput] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [foodHint, setFoodHint] = useState("");
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
    setFoodHint("");
    if (fileRef.current) fileRef.current.value = "";
  };

  // ---------- Send handler ----------
  const handleSend = async () => {
    if (loading) return;
    if (!input.trim() && !imageFile) return;

    // If an image is attached, do food analysis
    if (imageFile) {
      const hint = foodHint.trim();
      addMsg({ role: "user", text: hint || "Analyze this food", imageUrl: imagePreview! });
      clearImage();
      setInput("");
      setLoading(true);

      try {
        const data = await analyzeFoodImage(imageFile, health, hint);
        addMsg({ role: "assistant", foodData: data });
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

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto">
      {/* ---- Header ---- */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <div>
          <h1 className="text-lg font-bold tracking-tight">AI Health Companion</h1>
          <p className="text-xs text-gray-500">Food analysis & travel risk advisor</p>
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
                  alt="uploaded food"
                  className="rounded-lg mb-2 max-h-48 object-cover"
                />
              )}
              {/* Text */}
              {msg.text && (
                <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
              )}
              {/* Food result */}
              {msg.foodData && <FoodResult data={msg.foodData} />}
              {/* Travel result */}
              {msg.travelData && <TravelResult data={msg.travelData} />}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl px-4 py-3">
              <p className="text-sm text-gray-400 animate-pulse">Thinking...</p>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* ---- Image preview bar ---- */}
      {imagePreview && (
        <div className="px-4 py-2 border-t border-gray-800 space-y-2">
          <div className="flex items-center gap-3">
          <img
            src={imagePreview}
            alt="preview"
            className="h-12 w-12 rounded-lg object-cover"
          />
          <span className="text-xs text-gray-400 flex-1">Image attached</span>
          <button
            onClick={clearImage}
            className="text-red-400 text-xs hover:text-red-300"
          >
            Remove
          </button>
          </div>
          <div>
            <label htmlFor="food-hint" className="block text-xs text-gray-400 mb-1">
              Describe your food (optional)
            </label>
            <input
              id="food-hint"
              className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-emerald-500 transition"
              placeholder="e.g., Homemade chocolate cupcake"
              value={foodHint}
              onChange={(e) => setFoodHint(e.target.value)}
              disabled={loading}
            />
          </div>
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
          title="Upload food image"
        >
          {/* Camera / image icon (inline SVG) */}
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
              ? "Add a note (optional) and send..."
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
