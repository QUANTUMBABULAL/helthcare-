"use client";

/**
 * FoodResult — Renders the food analysis response from the API.
 * Shows each food item with its verdict badge and total calories.
 */

type FoodItem = {
  name: string;
  ingredients: string[];
  estimated_calories: number;
  verdict: "OK" | "LIMIT" | "AVOID";
  reason: string;
};

type FoodData = {
  items: FoodItem[];
  total_calories: number;
  explanation: string;
};

const VERDICT_STYLE: Record<string, string> = {
  OK: "bg-emerald-600/20 text-emerald-400 border-emerald-500/40",
  LIMIT: "bg-yellow-600/20 text-yellow-400 border-yellow-500/40",
  AVOID: "bg-red-600/20 text-red-400 border-red-500/40",
};

export default function FoodResult({ data }: { data: FoodData }) {
  return (
    <div className="space-y-3">
      {/* Item cards */}
      <div className="grid gap-2">
        {data.items.map((item, i) => (
          <div
            key={i}
            className="flex items-center justify-between bg-gray-800/60 rounded-lg px-4 py-2.5 border border-gray-700/50"
          >
            <div>
              <p className="font-medium text-sm">{item.name}</p>
              <p className="text-xs text-gray-300">
                Ingredients: {item.ingredients?.length ? item.ingredients.join(", ") : "Not available"}
              </p>
              <p className="text-xs text-gray-400">{item.reason}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400">
                {item.estimated_calories} kcal
              </span>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded border ${
                  VERDICT_STYLE[item.verdict] || VERDICT_STYLE.OK
                }`}
              >
                {item.verdict}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Total + explanation */}
      <div className="bg-gray-800/40 rounded-lg p-3 border border-gray-700/40">
        <p className="text-sm font-semibold text-emerald-400 mb-1">
          Total: ~{data.total_calories} kcal
        </p>
        <p className="text-sm text-gray-300">{data.explanation}</p>
      </div>
    </div>
  );
}
