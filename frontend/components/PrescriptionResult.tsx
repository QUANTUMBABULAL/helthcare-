"use client";

/**
 * PrescriptionResult — Renders the prescription analysis response from the API.
 * Shows OCR text, parsed medicines, safety notes, and explanation.
 */

type MedicineItem = {
  name: string;
  dosage: string;
  frequency: string;
  estimated_cost: string;
  warnings: string[];
};

type PrescriptionData = {
  raw_text: string;
  medicines: MedicineItem[];
  safety_notes: string[];
  explanation: string;
};

export default function PrescriptionResult({ data }: { data: PrescriptionData }) {
  return (
    <div className="space-y-3">
      {/* Medicine cards */}
      {data.medicines.length > 0 && (
        <div className="grid gap-2">
          {data.medicines.map((med, i) => (
            <div
              key={i}
              className="bg-gray-800/60 rounded-lg px-4 py-3 border border-gray-700/50"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <p className="font-medium text-sm text-white">{med.name}</p>
                  <p className="text-xs text-gray-300">
                    {med.dosage} &middot; {med.frequency}
                  </p>
                  {med.warnings.length > 0 && (
                    <ul className="mt-1 space-y-0.5">
                      {med.warnings.map((w, j) => (
                        <li key={j} className="text-xs text-red-400 flex gap-1">
                          <span>⚠</span> {w}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <span className="text-xs text-emerald-400 whitespace-nowrap">
                  {med.estimated_cost}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Safety notes */}
      {data.safety_notes.length > 0 && (
        <div className="bg-yellow-900/20 rounded-lg p-3 border border-yellow-700/40">
          <p className="text-xs uppercase text-yellow-500 mb-2 font-semibold tracking-wide">
            Safety Notes
          </p>
          <ul className="space-y-1">
            {data.safety_notes.map((note, i) => (
              <li key={i} className="text-sm text-yellow-300 flex gap-2">
                <span className="mt-0.5">-</span> {note}
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
      {data.raw_text && (
        <details className="bg-gray-800/30 rounded-lg border border-gray-700/30">
          <summary className="cursor-pointer px-3 py-2 text-xs text-gray-500 hover:text-gray-400">
            View raw prescription text
          </summary>
          <p className="px-3 pb-3 text-xs text-gray-400 whitespace-pre-wrap">
            {data.raw_text}
          </p>
        </details>
      )}
    </div>
  );
}
