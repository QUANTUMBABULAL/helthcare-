"use client";

import { useState } from "react";

/**
 * HealthProfileForm — collects user medical conditions, allergies, etc.
 * Stored in state and passed along with each API call.
 */

const COMMON_CONDITIONS = [
  "Diabetes",
  "Hypertension",
  "Heart Disease",
  "Asthma",
  "Cholesterol",
  "Obesity",
  "Epilepsy",
  "DVT",
  "Pregnancy",
];

export type HealthData = {
  conditions: string[];
  allergies: string[];
  age: number | null;
  weight_kg: number | null;
  height_cm: number | null;
  medications: string[];
};

const DEFAULT_HEALTH: HealthData = {
  conditions: [],
  allergies: [],
  age: null,
  weight_kg: null,
  height_cm: null,
  medications: [],
};

export default function HealthProfileForm({
  health,
  onChange,
  onClose,
}: {
  health: HealthData;
  onChange: (h: HealthData) => void;
  onClose: () => void;
}) {
  const [local, setLocal] = useState<HealthData>({ ...health });
  const [allergyInput, setAllergyInput] = useState("");
  const [medInput, setMedInput] = useState("");

  const toggleCondition = (c: string) => {
    const lower = c.toLowerCase();
    const next = local.conditions.includes(lower)
      ? local.conditions.filter((x) => x !== lower)
      : [...local.conditions, lower];
    setLocal({ ...local, conditions: next });
  };

  const addAllergy = () => {
    if (!allergyInput.trim()) return;
    setLocal({
      ...local,
      allergies: [...local.allergies, allergyInput.trim().toLowerCase()],
    });
    setAllergyInput("");
  };

  const addMed = () => {
    if (!medInput.trim()) return;
    setLocal({
      ...local,
      medications: [...local.medications, medInput.trim()],
    });
    setMedInput("");
  };

  const save = () => {
    onChange(local);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto border border-gray-700">
        <h2 className="text-xl font-bold mb-4">Your Health Profile</h2>

        {/* Conditions */}
        <p className="text-sm text-gray-400 mb-2">Select your conditions:</p>
        <div className="flex flex-wrap gap-2 mb-4">
          {COMMON_CONDITIONS.map((c) => (
            <button
              key={c}
              onClick={() => toggleCondition(c)}
              className={`px-3 py-1 rounded-full text-sm border transition ${
                local.conditions.includes(c.toLowerCase())
                  ? "bg-emerald-600 border-emerald-500 text-white"
                  : "border-gray-600 text-gray-300 hover:border-gray-400"
              }`}
            >
              {c}
            </button>
          ))}
        </div>

        {/* Allergies */}
        <label className="text-sm text-gray-400">Allergies</label>
        <div className="flex gap-2 mb-2">
          <input
            className="flex-1 bg-gray-800 rounded px-3 py-1.5 text-sm border border-gray-700 focus:outline-none focus:border-emerald-500"
            placeholder="e.g. peanuts"
            value={allergyInput}
            onChange={(e) => setAllergyInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addAllergy()}
          />
          <button onClick={addAllergy} className="text-emerald-400 text-sm">
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-1 mb-4">
          {local.allergies.map((a, i) => (
            <span key={i} className="bg-gray-800 text-xs px-2 py-1 rounded-full">
              {a}{" "}
              <button
                onClick={() =>
                  setLocal({
                    ...local,
                    allergies: local.allergies.filter((_, j) => j !== i),
                  })
                }
                className="text-red-400 ml-1"
              >
                x
              </button>
            </span>
          ))}
        </div>

        {/* Age / Weight / Height */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div>
            <label className="text-xs text-gray-400">Age</label>
            <input
              type="number"
              className="w-full bg-gray-800 rounded px-2 py-1.5 text-sm border border-gray-700 focus:outline-none focus:border-emerald-500"
              value={local.age ?? ""}
              onChange={(e) =>
                setLocal({ ...local, age: e.target.value ? +e.target.value : null })
              }
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Weight (kg)</label>
            <input
              type="number"
              className="w-full bg-gray-800 rounded px-2 py-1.5 text-sm border border-gray-700 focus:outline-none focus:border-emerald-500"
              value={local.weight_kg ?? ""}
              onChange={(e) =>
                setLocal({
                  ...local,
                  weight_kg: e.target.value ? +e.target.value : null,
                })
              }
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Height (cm)</label>
            <input
              type="number"
              className="w-full bg-gray-800 rounded px-2 py-1.5 text-sm border border-gray-700 focus:outline-none focus:border-emerald-500"
              value={local.height_cm ?? ""}
              onChange={(e) =>
                setLocal({
                  ...local,
                  height_cm: e.target.value ? +e.target.value : null,
                })
              }
            />
          </div>
        </div>

        {/* Medications */}
        <label className="text-sm text-gray-400">Medications</label>
        <div className="flex gap-2 mb-2">
          <input
            className="flex-1 bg-gray-800 rounded px-3 py-1.5 text-sm border border-gray-700 focus:outline-none focus:border-emerald-500"
            placeholder="e.g. Metformin"
            value={medInput}
            onChange={(e) => setMedInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addMed()}
          />
          <button onClick={addMed} className="text-emerald-400 text-sm">
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-1 mb-6">
          {local.medications.map((m, i) => (
            <span key={i} className="bg-gray-800 text-xs px-2 py-1 rounded-full">
              {m}{" "}
              <button
                onClick={() =>
                  setLocal({
                    ...local,
                    medications: local.medications.filter((_, j) => j !== i),
                  })
                }
                className="text-red-400 ml-1"
              >
                x
              </button>
            </span>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            onClick={save}
            className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white py-2 rounded-lg font-medium transition"
          >
            Save Profile
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg transition"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export { DEFAULT_HEALTH };
