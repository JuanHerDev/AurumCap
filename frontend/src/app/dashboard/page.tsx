"use client";

import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { useState } from "react";
import { FaBookOpen, FaCalculator, FaBriefcase } from "react-icons/fa";

const data = [
  { name: "Ene", value: 11000 },
  { name: "Feb", value: 11200 },
  { name: "Mar", value: 10900 },
  { name: "Abr", value: 11500 },
  { name: "May", value: 11750 },
  { name: "Jun", value: 12500 },
];

export default function Dashboard() {
  const [period, setPeriod] = useState("1M");

  return (
    <main className="min-h-screen bg-black text-white px-4 py-6 flex flex-col items-center lg:px-20">
      {/* Header */}
      <header className="w-full max-w-5xl mb-6">
        <h1 className="text-xl font-semibold">
          Hola, <span className="text-yellow-400">Alex 👋</span>
        </h1>
      </header>

      {/* Balance Card */}
      <section className="w-full max-w-5xl bg-yellow-900/30 rounded-2xl p-4 flex flex-col justify-between mb-6 lg:flex-row lg:items-center">
        <div>
          <p className="text-sm text-yellow-200">Balance Total</p>
          <h2 className="text-3xl font-bold">$12.500,55</h2>
          <p className="text-gray-400 text-sm">Crecimiento este mes</p>
        </div>
        <div className="text-green-400 text-lg font-semibold mt-2 lg:mt-0">+5,23%</div>
      </section>

      {/* Chart Section */}
      <section className="w-full max-w-5xl bg-zinc-900 rounded-2xl p-4 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">Rendimiento</h3>
          <div className="flex gap-2">
            {["1D", "1S", "1M", "1A"].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1 rounded-lg text-sm ${
                  period === p ? "bg-yellow-500 text-black font-bold" : "bg-zinc-800 text-gray-400"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className="h-52 lg:h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <XAxis dataKey="name" stroke="#888" />
              <YAxis hide />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#facc15" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="w-full max-w-5xl grid grid-cols-2 gap-4 lg:grid-cols-3">
        <ActionCard icon={<FaBriefcase size={28} />} label="Portafolio" />
        <ActionCard icon={<FaCalculator size={28} />} label="Simular inversión" />
        <ActionCard icon={<FaBookOpen size={28} />} label="Aprender" />
      </section>
    </main>
  );
}

function ActionCard({ icon, label }: { icon: JSX.Element; label: string }) {
  return (
    <div className="bg-zinc-900 rounded-2xl p-4 flex flex-col items-center justify-center hover:bg-zinc-800 transition">
      <div className="text-yellow-500 mb-2">{icon}</div>
      <p className="text-sm font-medium">{label}</p>
    </div>
  );
}
