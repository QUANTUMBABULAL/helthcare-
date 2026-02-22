"use client";

/**
 * TravelResult — Renders the travel/activity risk assessment.
 * Shows risk level badge, advice list, and AI explanation.
 */

type TravelData = {
  activity: string;
  risk_level: "LOW" | "MODERATE" | "HIGH";
  advice: string[];
  explanation: string;
};

const RISK_STYLE: Record<string, string> = {
  LOW: "bg-emerald-600/20 text-emerald-400 border-emerald-500",
  MODERATE: "bg-yellow-600/20 text-yellow-400 border-yellow-500",
  HIGH: "bg-red-600/20 text-red-400 border-red-500",
};

const RISK_ICON: Record<string, string> = {
  LOW: "OK",
  MODERATE: "!",
  HIGH: "!!",
};

export default function TravelResult({ data }: { data: TravelData }) {
  return (
    <div className="space-y-3">
      {/* Risk badge */}
      <div className="flex items-center gap-3">
        <span
          className={`text-lg font-bold px-4 py-1.5 rounded-lg border ${
            RISK_STYLE[data.risk_level] || RISK_STYLE.LOW
          }`}
        >
          {RISK_ICON[data.risk_level]} {data.risk_level} RISK
        </span>
        <span className="text-gray-400 text-sm">for {data.activity}</span>
      </div>

      {/* Advice list */}
      <div className="bg-gray-800/60 rounded-lg p-3 border border-gray-700/50">
        <p className="text-xs uppercase text-gray-500 mb-2 font-semibold tracking-wide">
          Safety Advice
        </p>
        <ul className="space-y-1.5">
          {data.advice.map((tip, i) => (
            <li key={i} className="text-sm text-gray-300 flex gap-2">
              <span className="text-emerald-400 mt-0.5">-</span>
              {tip}
            </li>
          ))}
        </ul>
      </div>

      {/* AI explanation */}
      <div className="bg-gray-800/40 rounded-lg p-3 border border-gray-700/40">
        <p className="text-sm text-gray-300">{data.explanation}</p>
      </div>
    </div>
  );
}
