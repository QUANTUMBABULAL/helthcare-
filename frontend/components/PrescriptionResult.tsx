"use client";

type PrescriptionMedicine = {
  name: string;
  dose: string;
  frequency: string;
  duration: string;
  warning_level: "OK" | "CAUTION" | "AVOID";
  warning_reason: string;
  estimated_cost: number;
};

type PrescriptionData = {
  medicines: PrescriptionMedicine[];
  total_estimated_cost: number;
  warnings: string[];
  disclaimer: string;
};

const WARNING_STYLE: Record<string, string> = {
  OK: "bg-emerald-600/20 text-emerald-400 border-emerald-500/40",
  CAUTION: "bg-yellow-600/20 text-yellow-400 border-yellow-500/40",
  AVOID: "bg-red-600/20 text-red-400 border-red-500/40",
};

export default function PrescriptionResult({ data }: { data: PrescriptionData }) {
  return (
    <div className="space-y-3">
      <div className="space-y-2">
        {data.medicines.length === 0 && (
          <p className="text-sm text-gray-400">No medicines detected from this image.</p>
        )}

        {data.medicines.map((med, idx) => (
          <div
            key={idx}
            className="bg-gray-800/60 rounded-lg border border-gray-700/50 p-3 space-y-1"
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium">{med.name}</p>
              <span
                className={`text-[11px] font-bold px-2 py-0.5 rounded border ${
                  WARNING_STYLE[med.warning_level] || WARNING_STYLE.OK
                }`}
              >
                {med.warning_level}
              </span>
            </div>
            <p className="text-xs text-gray-300">Dose: {med.dose}</p>
            <p className="text-xs text-gray-300">Frequency: {med.frequency}</p>
            <p className="text-xs text-gray-300">Duration: {med.duration}</p>
            <p className="text-xs text-gray-300">Estimated cost: ₹{med.estimated_cost.toFixed(2)}</p>
            <p className="text-xs text-gray-400">{med.warning_reason}</p>
          </div>
        ))}
      </div>

      <div className="bg-gray-800/40 rounded-lg p-3 border border-gray-700/40 space-y-1">
        <p className="text-sm font-semibold text-emerald-400">
          Estimated Total Cost: ₹{data.total_estimated_cost.toFixed(2)}
        </p>
        <ul className="text-xs text-gray-300 space-y-1">
          {data.warnings.map((warning, i) => (
            <li key={i}>• {warning}</li>
          ))}
        </ul>
        <p className="text-xs text-yellow-300 mt-2">{data.disclaimer}</p>
      </div>
    </div>
  );
}
