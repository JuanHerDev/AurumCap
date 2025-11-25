"use client";

import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { FaBookOpen, FaCalculator, FaBriefcase, FaHome } from "react-icons/fa";
import { JSX, useState } from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter } from "next/navigation";

const data = [
  { name: "Ene", value: 4000 },
  { name: "Feb", value: 7000 },
  { name: "Mar", value: 11000 },
  { name: "Abr", value: 9000 },
  { name: "May", value: 12000 },
  { name: "Jun", value: 12500 },
];

export default function Dashboard() {
  const [period, setPeriod] = useState("1M");
  const { user } = useAuth();
  const router = useRouter();

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900">
      {/* Header */}
      <header className="bg-white px-6 py-4 border-b border-gray-200">
        <h1 className="text-2xl font-bold">
          Hola, <span className="text-[#B59F50]">{user?.full_name || "Alex"}</span>
        </h1>
      </header>

      {/* Main Content */}
      <div className="p-6 max-w-6xl mx-auto">
        {/* Balance Card */}
        <section className="bg-white rounded-2xl p-6 shadow-sm mb-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-500 text-sm mb-1">Balance Total</p>
              <h2 className="text-4xl font-bold mb-2">$12.500,55</h2>
              <div className="flex items-center gap-2">
                <span className="text-green-500 font-semibold">+5,23%</span>
                <span className="text-gray-500 text-sm">Crecimiento este mes</span>
              </div>
            </div>
          </div>
        </section>

        {/* Chart Section */}
        <section className="bg-white rounded-2xl p-6 shadow-sm mb-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-semibold text-lg">Rendimiento</h3>
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
              {["1D", "1S", "1M", "1A"].map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    period === p 
                      ? "bg-[#B59F50] text-white" 
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <XAxis 
                  dataKey="name" 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  domain={[0, 14000]}
                  ticks={[0, 4000, 7000, 11000, 14000]}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none',
                    borderRadius: '8px',
                    color: 'white'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#B59F50" 
                  strokeWidth={3} 
                  dot={false}
                  activeDot={{ r: 6, fill: "#B59F50" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Quick Actions */}
        <section className="grid grid-cols-2 gap-4 mb-20">
          <ActionCard 
            icon={<FaBriefcase className="text-[#B59F50]" size={24} />} 
            label="Portafolio" 
            href="/portfolio" 
          />
          <ActionCard 
            icon={<FaCalculator className="text-[#B59F50]" size={24} />} 
            label="Simular inversión" 
            href="/simulator" 
          />
          <ActionCard 
            icon={<FaBookOpen className="text-[#B59F50]" size={24} />} 
            label="Aprender" 
            href="/learn" 
          />
        </section>
      </div>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-3 px-8">
        <div className="flex justify-between items-center">
          <NavItem icon={<FaHome size={20} />} label="Inicio" active={true} />
          <NavItem icon={<FaBriefcase size={20} />} label="Portafolio" href="/portfolio" />
          <NavItem icon={<FaCalculator size={20} />} label="Simulador" href="/simulator" />
          <NavItem icon={<FaBookOpen size={20} />} label="Perfil" href="/profile" />
        </div>
      </nav>
    </main>
  );
}

function ActionCard({ icon, label, href }: { icon: JSX.Element; label: string; href?: string }) {
  const router = useRouter();

  const handleClick = () => {
    if (href) router.push(href);
  };

  return (
    <div
      onClick={handleClick}
      className="cursor-pointer bg-white rounded-2xl p-6 flex flex-col items-center justify-center hover:shadow-md transition-shadow border border-gray-100"
    >
      <div className="mb-3">{icon}</div>
      <p className="font-medium text-gray-900 text-center">{label}</p>
    </div>
  );
}

function NavItem({ 
  icon, 
  label, 
  href, 
  active = false 
}: { 
  icon: JSX.Element; 
  label: string; 
  href?: string;
  active?: boolean;
}) {
  const router = useRouter();

  const handleClick = () => {
    if (href) router.push(href);
  };

  return (
    <button
      onClick={handleClick}
      className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-colors ${
        active ? 'text-[#B59F50]' : 'text-gray-500 hover:text-gray-700'
      }`}
    >
      {icon}
      <span className="text-xs font-medium">{label}</span>
    </button>
  );
}