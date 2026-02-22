"use client";

/**
 * PrescriptionResult — Renders the prescription analysis from the AI.
 * Shows detected medicines, dosage, safety warnings, and cost estimate.
 */

type MedicineItem = {
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
};

type PrescriptionData = {
  medicines: MedicineItem[];
  safety_warnings: string[];
  cost_estimate: Record<string, number>;
  ocr_text: string;
  explanation: string;
};

export default function PrescriptionResult({ data }: { data: PrescriptionData }) {
  const totalCost = Object.values(data.cost_estimate).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-3">
      {/* Medicine cards */}
      {data.medicines.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs uppercase text-gray-500 font-semibold tracking-wide">Medicines Prescribed</p>
          {data.medicines.map((med, i) => (
            <div
              key={i}
              className="bg-gray-800/60 rounded-lg px-4 py-2.5 border border-gray-700/50"
            >
              <div className="flex items-center justify-between">
                <p className="font-medium text-sm text-white">{med.name}</p>
                {data.cost_estimate[med.name] !== undefined && (
                  <span className="text-xs text-emerald-400">
                    ~${data.cost_estimate[med.name].toFixed(2)}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                {med.dosage} · {med.frequency} · {med.duration}
              </p>
            </div>
          ))}
          {totalCost > 0 && (
            <p className="text-xs text-gray-400 text-right">
              Estimated total cost: ~${totalCost.toFixed(2)}
            </p>
          )}
        </div>
      )}

      {/* Safety warnings */}
      {data.safety_warnings.length > 0 && (
        <div className="bg-red-900/20 rounded-lg p-3 border border-red-500/30">
          <p className="text-xs uppercase text-red-400 font-semibold tracking-wide mb-2">
            ⚠ Safety Warnings
          </p>
          <ul className="space-y-1">
            {data.safety_warnings.map((w, i) => (
              <li key={i} className="text-sm text-red-300 flex gap-2">
                <span className="mt-0.5">•</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Explanation */}
      <div className="bg-gray-800/40 rounded-lg p-3 border border-gray-700/40">
        <p className="text-sm text-gray-300">{data.explanation}</p>
      </div>

      {/* Raw OCR text (collapsed) */}
      {data.ocr_text && (
        <details className="text-xs text-gray-500">
          <summary className="cursor-pointer hover:text-gray-400 transition">
            View raw prescription text
          </summary>
          <pre className="mt-2 bg-gray-800/40 rounded p-2 whitespace-pre-wrap break-words">
            {data.ocr_text}
          </pre>
        </details>
      )}
    </div>
  );
}
