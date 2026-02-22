"use client";

import FoodResult from "@/components/FoodResult";
import PrescriptionResult from "@/components/PrescriptionResult";

type AnalyzeData = {
  response_type: "food" | "prescription" | "unknown";
  confidence: number;
  food?: any;
  prescription?: any;
  message?: string;
};

export default function AnalyzeResult({ data }: { data: AnalyzeData }) {
  if (data.response_type === "food" && data.food) {
    return <FoodResult data={data.food} />;
  }

  if (data.response_type === "prescription" && data.prescription) {
    return <PrescriptionResult data={data.prescription} />;
  }

  return (
    <p className="text-sm text-gray-300">
      {data.message || "Could not determine image type. Please try again."}
    </p>
  );
}
