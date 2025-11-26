"use client";

import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Area, ComposedChart } from "recharts";
import { FaBookOpen, FaCalculator, FaBriefcase, FaHome, FaChartLine, FaArrowUp, FaArrowDown } from "react-icons/fa";
import { JSX, useState, useEffect } from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter } from "next/navigation";

// Servicio para obtener datos del portafolio (debes crear este servicio)
interface PortfolioHistory {
  date: string;
  total_value: number;
  return_percentage: number;
}

interface PortfolioSummary {
  total_balance: number;
  total_invested: number;
  total_profit: number;
  monthly_growth: number;
  annual_return: number;
  asset_count: number;
}

export default function Dashboard() {
  const [period, setPeriod] = useState("6M");
  const [portfolioHistory, setPortfolioHistory] = useState<PortfolioHistory[]>([]);
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();
  const router = useRouter();

  // Obtener el nombre del usuario - priorizando diferentes campos posibles
  const getUserName = () => {
    if (!user) return "Inversionista";
    
    // Prioridad de campos de nombre
    return user.full_name || user.name || user.username || user.email?.split('@')[0] || "Inversionista";
  };

  // Simular obtención de datos del portafolio
  useEffect(() => {
    const fetchPortfolioData = async () => {
      setIsLoading(true);
      try {
        // En producción, reemplazar con llamada real a tu API
        const historyData = await getPortfolioHistory(period);
        const summaryData = await getPortfolioSummary();
        
        setPortfolioHistory(historyData);
        setPortfolioSummary(summaryData);
      } catch (error) {
        console.error("Error fetching portfolio data:", error);
        // Datos de ejemplo como fallback
        setPortfolioHistory(generateSampleData(period));
        setPortfolioSummary(generateSampleSummary());
      } finally {
        setIsLoading(false);
      }
    };

    fetchPortfolioData();
  }, [period]);

  // Función para obtener histórico del portafolio
  const getPortfolioHistory = async (period: string): Promise<PortfolioHistory[]> => {
    // Aquí debes conectar con tu endpoint real de FastAPI
    // Ejemplo: const response = await fetch(`/api/portfolio/history?period=${period}`);
    
    // Simulación de datos basados en el período
    return generateSampleData(period);
  };

  // Función para obtener resumen del portafolio
  const getPortfolioSummary = async (): Promise<PortfolioSummary> => {
    // Conectar con tu endpoint real de FastAPI
    // Ejemplo: const response = await fetch('/api/portfolio/summary');
    
    return generateSampleSummary();
  };

  const calculateGrowth = () => {
    if (portfolioHistory.length < 2) return { value: 5.23, isPositive: true };
    
    const current = portfolioHistory[portfolioHistory.length - 1]?.total_value || 0;
    const previous = portfolioHistory[portfolioHistory.length - 2]?.total_value || 0;
    
    if (previous === 0) return { value: 0, isPositive: true };
    
    const growthValue = ((current - previous) / previous * 100);
    return {
      value: Math.abs(growthValue).toFixed(2),
      isPositive: growthValue >= 0
    };
  };

  const growth = calculateGrowth();
  const totalBalance = portfolioSummary?.total_balance || 0;
  const userName = getUserName();

  // Formatear datos para el gráfico
  const chartData = portfolioHistory.map(item => ({
    name: formatDateLabel(item.date, period),
    value: item.total_value,
    return: item.return_percentage
  }));

  if (isLoading) {
    return (
      <main className="min-h-screen bg-gray-50 text-gray-900">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-[#B59F50] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-500 text-sm">Cargando datos del portafolio...</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 pb-20">
      {/* Header */}
      <header className="bg-white px-4 py-4 border-b border-gray-200 sticky top-0 z-10">
        <div className="flex justify-between items-center max-w-6xl mx-auto">
          <h1 className="text-xl font-bold">
            Hola, <span className="text-[#B59F50]">{userName}</span>
          </h1>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="hidden xs:inline">Mercado abierto</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-4 max-w-6xl mx-auto">
        {/* Balance Card */}
        <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
          <div className="flex flex-col xs:flex-row justify-between items-start gap-3">
            <div className="flex-1">
              <p className="text-gray-500 text-xs mb-1">Balance Total</p>
              <h2 className="text-2xl sm:text-3xl font-bold mb-2">
                ${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </h2>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`${growth.isPositive ? 'text-green-500' : 'text-red-500'} font-semibold flex items-center gap-1 text-sm`}>
                  {growth.isPositive ? <FaArrowUp size={10} /> : <FaArrowDown size={10} />}
                  {growth.value}%
                </span>
                <span className="text-gray-500 text-xs">Crecimiento este mes</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-gray-500 text-xs">Rendimiento Anual</p>
              <p className="text-lg sm:text-xl font-bold text-green-500">
                +{portfolioSummary?.annual_return?.toFixed(1) || '18.7'}%
              </p>
            </div>
          </div>
        </section>

        {/* Chart Section */}
        <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
            <h3 className="font-semibold text-base sm:text-lg">Rendimiento del Portafolio</h3>
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1 self-start">
              {["1M", "3M", "6M", "1A"].map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-2 py-1 rounded-md text-xs font-medium transition-colors min-w-10 ${
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

          <div className="h-48 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#B59F50" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#B59F50" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="name" 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 10 }}
                  padding={{ left: 5, right: 5 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 10 }}
                  width={35}
                  tickFormatter={(value) => {
                    if (value >= 1000) return `$${(value/1000).toFixed(0)}k`;
                    return `$${value}`;
                  }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none',
                    borderRadius: '8px',
                    color: 'white',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    fontSize: '12px'
                  }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, 'Valor']}
                  labelFormatter={(label) => `Fecha: ${label}`}
                />
                <Area 
                  type="monotone" 
                  dataKey="value"
                  stroke="#B59F50"
                  fillOpacity={1}
                  fill="url(#colorValue)"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#B59F50" 
                  strokeWidth={2} 
                  dot={false}
                  activeDot={{ 
                    r: 4, 
                    fill: "#B59F50",
                    stroke: "#fff",
                    strokeWidth: 2
                  }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Portfolio Overview */}
        <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
          <h3 className="font-semibold text-base sm:text-lg mb-3">Resumen del Portafolio</h3>
          <div className="grid grid-cols-2 gap-2 sm:gap-3 sm:grid-cols-4">
            <PortfolioMetric 
              label="Invertido" 
              value={`$${(portfolioSummary?.total_invested || 10250).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} 
              change="+5.2%" 
              positive={true} 
            />
            <PortfolioMetric 
              label="Ganancia" 
              value={`$${(portfolioSummary?.total_profit || 2250.55).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} 
              change="+18.7%" 
              positive={true} 
            />
            <PortfolioMetric 
              label="Mensual" 
              value={`${growth.value}%`} 
              change={growth.isPositive ? `+${growth.value}%` : `${growth.value}%`} 
              positive={growth.isPositive} 
            />
            <PortfolioMetric 
              label="Activos" 
              value={portfolioSummary?.asset_count?.toString() || "8"} 
              change="+2" 
              positive={true} 
            />
          </div>
        </section>

        {/* Quick Actions */}
        <section className="grid grid-cols-2 gap-3 mb-16 sm:grid-cols-4">
          <ActionCard 
            icon={<FaBriefcase className="text-[#B59F50]" size={20} />} 
            label="Portafolio" 
            description="Tus inversiones"
            href="/portfolio" 
          />
          <ActionCard 
            icon={<FaCalculator className="text-[#B59F50]" size={20} />} 
            label="Simular" 
            description="Probar estrategias"
            href="/simulator" 
          />
          <ActionCard 
            icon={<FaChartLine className="text-[#B59F50]" size={20} />} 
            label="Mercados" 
            description="Cotizaciones"
            href="/markets" 
          />
          <ActionCard 
            icon={<FaBookOpen className="text-[#B59F50]" size={20} />} 
            label="Aprender" 
            description="Educación"
            href="/learn" 
          />
        </section>
      </div>

      
    </main>
  );
}

// Componente para métricas del portafolio
function PortfolioMetric({ 
  label, 
  value, 
  change, 
  positive = true 
}: { 
  label: string; 
  value: string; 
  change: string; 
  positive?: boolean;
}) {
  return (
    <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg border border-gray-100">
      <p className="text-gray-500 text-xs mb-1">{label}</p>
      <p className="text-sm sm:text-base font-bold text-gray-900 mb-1 truncate" title={value}>
        {value}
      </p>
      <p className={`text-xs font-medium ${positive ? 'text-green-500' : 'text-red-500'}`}>
        {change}
      </p>
    </div>
  );
}

function ActionCard({ 
  icon, 
  label, 
  description,
  href 
}: { 
  icon: JSX.Element; 
  label: string; 
  description: string;
  href?: string;
}) {
  const router = useRouter();

  const handleClick = () => {
    if (href) router.push(href);
  };

  return (
    <div
      onClick={handleClick}
      className="cursor-pointer bg-white rounded-xl p-3 sm:p-4 flex flex-col items-center justify-center hover:shadow-md transition-all duration-200 border border-gray-100 text-center hover:border-[#B59F50] hover:transform hover:-translate-y-1"
    >
      <div className="mb-2 bg-gray-50 p-2 rounded-full">{icon}</div>
      <p className="font-semibold text-gray-900 text-sm mb-1">{label}</p>
      <p className="text-xs text-gray-500 hidden xs:block">{description}</p>
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
      className={`flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition-all duration-200 min-w-[50px] ${
        active 
          ? 'text-[#B59F50] bg-[#B59F50] bg-opacity-10' 
          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
      }`}
    >
      {icon}
      <span className="text-xs font-medium">{label}</span>
    </button>
  );
}

// Funciones auxiliares para generar datos de ejemplo
function generateSampleData(period: string): PortfolioHistory[] {
  const baseData = [
    { date: "2024-01-01", total_value: 4000, return_percentage: 2.1 },
    { date: "2024-02-01", total_value: 7000, return_percentage: 5.8 },
    { date: "2024-03-01", total_value: 11000, return_percentage: 12.3 },
    { date: "2024-04-01", total_value: 9000, return_percentage: 8.7 },
    { date: "2024-05-01", total_value: 12000, return_percentage: 15.2 },
    { date: "2024-06-01", total_value: 12500, return_percentage: 18.7 },
  ];

  // Filtrar según el período seleccionado
  switch (period) {
    case "1M":
      return baseData.slice(-2);
    case "3M":
      return baseData.slice(-4);
    case "6M":
      return baseData;
    case "1A":
      // Extender datos para 1 año
      return [...baseData, 
        { date: "2024-07-01", total_value: 14000, return_percentage: 22.1 },
        { date: "2024-08-01", total_value: 15500, return_percentage: 25.8 },
        { date: "2024-09-01", total_value: 14800, return_percentage: 23.4 },
        { date: "2024-10-01", total_value: 16200, return_percentage: 28.9 },
        { date: "2024-11-01", total_value: 17500, return_percentage: 32.5 },
        { date: "2024-12-01", total_value: 18500, return_percentage: 35.2 }
      ];
    default:
      return baseData;
  }
}

function generateSampleSummary(): PortfolioSummary {
  return {
    total_balance: 12500.55,
    total_invested: 10250.00,
    total_profit: 2250.55,
    monthly_growth: 5.23,
    annual_return: 18.7,
    asset_count: 8
  };
}

function formatDateLabel(date: string, period: string): string {
  const dateObj = new Date(date);
  
  if (period === "1M" || period === "3M") {
    return dateObj.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
  }
  
  return dateObj.toLocaleDateString('es-ES', { month: 'short' });
}