// app/simulator/page.tsx
"use client";

import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Area } from "recharts";
import { FaCalculator, FaChartLine, FaDollarSign, FaExclamationTriangle, FaArrowUp, FaHome, FaBriefcase, FaBookOpen } from "react-icons/fa";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter } from "next/navigation";

// Tipos de activos disponibles
const ASSET_TYPES = [
  { value: "sp500", label: "S&P 500", risk: "Medio", avgReturn: 10.5 },
  { value: "nasdaq", label: "NASDAQ", risk: "Alto", avgReturn: 12.8 },
  { value: "bitcoin", label: "Bitcoin", risk: "Muy Alto", avgReturn: 45.2 },
  { value: "ethereum", label: "Ethereum", risk: "Alto", avgReturn: 32.1 },
  { value: "gold", label: "Oro", risk: "Bajo", avgReturn: 6.2 },
  { value: "bonds", label: "Bonos", risk: "Bajo", avgReturn: 4.5 },
  { value: "reit", label: "REITs", risk: "Medio", avgReturn: 8.7 },
];

// Datos históricos de rendimiento por tipo de activo (anualizado)
const ASSET_PERFORMANCE = {
  sp500: [0, 2.1, 4.8, 7.2, 10.5],
  nasdaq: [0, 3.2, 6.8, 9.5, 12.8],
  bitcoin: [0, 8.5, 18.2, 30.1, 45.2],
  ethereum: [0, 6.8, 14.5, 23.4, 32.1],
  gold: [0, 1.2, 2.8, 4.5, 6.2],
  bonds: [0, 0.9, 2.1, 3.3, 4.5],
  reit: [0, 1.8, 4.2, 6.5, 8.7],
};

export default function SimulatorPage() {
  const [investmentAmount, setInvestmentAmount] = useState<string>("10000");
  const [selectedAsset, setSelectedAsset] = useState<string>("sp500");
  const [months, setMonths] = useState<string>("12");
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();
  const router = useRouter();

  // Simular automáticamente al cargar la página
  useEffect(() => {
    simulateInvestment();
  }, []);

  const simulateInvestment = () => {
    setIsLoading(true);
    
    // Simular procesamiento
    setTimeout(() => {
      const amount = parseFloat(investmentAmount) || 0;
      const monthsNum = parseInt(months) || 12;
      const years = monthsNum / 12;
      
      const selectedAssetData = ASSET_TYPES.find(asset => asset.value === selectedAsset);
      const performance = ASSET_PERFORMANCE[selectedAsset as keyof typeof ASSET_PERFORMANCE];
      
      // Calcular ganancia estimada
      const annualReturn = selectedAssetData?.avgReturn || 0;
      const futureValue = amount * Math.pow(1 + annualReturn / 100, years);
      const estimatedProfit = futureValue - amount;
      
      // Generar datos para el gráfico
      const chartData = generateChartData(amount, annualReturn, monthsNum);
      
      setSimulationResult({
        estimatedProfit,
        futureValue,
        riskLevel: selectedAssetData?.risk || "Medio",
        annualReturn,
        chartData,
      });
      
      setIsLoading(false);
    }, 1000);
  };

  const generateChartData = (amount: number, annualReturn: number, months: number) => {
    const data = [];
    const years = months / 12;
    
    // Puntos clave en el tiempo
    const timePoints = [0, 0.25, 0.5, 0.75, 1].map(t => t * years);
    
    for (let i = 0; i < timePoints.length; i++) {
      const year = timePoints[i];
      const value = amount * Math.pow(1 + annualReturn / 100, year);
      
      let label = "";
      if (year === 0) label = "Inicio";
      else if (year <= 0.25) label = "Mes 1";
      else if (year <= 0.5) label = "Mes 3";
      else if (year <= 0.75) label = "Mes 6";
      else if (year <= 1) label = "Año 1";
      else label = `Año ${Math.ceil(year)}`;
      
      data.push({
        period: label,
        value: Math.round(value),
      });
    }
    
    return data;
  };

  const handleCreateRealInvestment = () => {
    // Redirigir al formulario de creación de inversión con los datos prellenados
    const params = new URLSearchParams({
      amount: investmentAmount,
      asset: selectedAsset,
      simulated: 'true'
    });
    router.push(`/portfolio/new?${params.toString()}`);
  };

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 pb-20">
      {/* Header */}
      <header className="bg-white px-4 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center max-w-6xl mx-auto">
          <h1 className="text-xl font-bold">
            Simulador de <span className="text-[#B59F50]">Inversión</span>
          </h1>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <FaCalculator className="text-[#B59F50]" size={16} />
            <span className="hidden xs:inline">Simulador</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-4 max-w-6xl mx-auto">
        {/* Sección de Parámetros */}
        <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <FaCalculator className="text-[#B59F50]" />
            Parámetros de Simulación
          </h2>
          <p className="text-gray-600 text-sm mb-4">
            Define tus preferencias de inversión.
          </p>

          <div className="space-y-4">
            {/* Cantidad a Invertir */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cantidad a invertir (USD)
              </label>
              <div className="relative">
                <FaDollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                <input
                  type="number"
                  value={investmentAmount}
                  onChange={(e) => setInvestmentAmount(e.target.value)}
                  placeholder="Ej. 10000"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
                />
              </div>
            </div>

            {/* Tipo de Activo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de activo
              </label>
              <select
                value={selectedAsset}
                onChange={(e) => setSelectedAsset(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              >
                <option value="">Selecciona un activo</option>
                {ASSET_TYPES.map((asset) => (
                  <option key={asset.value} value={asset.value}>
                    {asset.label} ({asset.avgReturn}% anual)
                  </option>
                ))}
              </select>
            </div>

            {/* Plazo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Plazo (meses)
              </label>
              <input
                type="number"
                value={months}
                onChange={(e) => setMonths(e.target.value)}
                placeholder="Ej. 12"
                min="1"
                max="60"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              />
            </div>

            {/* Botón Simular */}
            <button
              onClick={simulateInvestment}
              disabled={isLoading || !investmentAmount || !selectedAsset || !months}
              className="w-full bg-[#B59F50] text-white font-semibold py-3 rounded-lg hover:bg-[#A68F45] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Simulando...
                </>
              ) : (
                <>
                  <FaCalculator size={16} />
                  Simular
                </>
              )}
            </button>
          </div>
        </section>

        {/* Resultados de la Simulación */}
        {simulationResult && (
          <>
            <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <FaChartLine className="text-[#B59F50]" />
                Resultados de la Simulación
              </h2>
              <p className="text-gray-600 text-sm mb-4">
                Potencial de tu inversión basada en los parámetros.
              </p>

              <div className="grid grid-cols-2 gap-4">
                {/* Ganancia Estimada */}
                <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-green-600 text-xs font-medium mb-1">Ganancia Estimada</p>
                  <p className="text-lg font-bold text-green-700">
                    ${simulationResult.estimatedProfit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    +{simulationResult.annualReturn}% anual
                  </p>
                </div>

                {/* Nivel de Riesgo */}
                <div className="text-center p-3 bg-orange-50 rounded-lg border border-orange-200">
                  <p className="text-orange-600 text-xs font-medium mb-1 flex items-center justify-center gap-1">
                    <FaExclamationTriangle size={12} />
                    Nivel de Riesgo
                  </p>
                  <p className="text-lg font-bold text-orange-700">
                    {simulationResult.riskLevel}
                  </p>
                  <p className="text-xs text-orange-600 mt-1">
                    {simulationResult.riskLevel === "Bajo" && "Estable"}
                    {simulationResult.riskLevel === "Medio" && "Moderado"}
                    {simulationResult.riskLevel === "Alto" && "Volátil"}
                    {simulationResult.riskLevel === "Muy Alto" && "Muy Volátil"}
                  </p>
                </div>
              </div>

              {/* Valor Futuro */}
              <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-blue-600 text-xs font-medium mb-1">Valor Futuro Estimado</p>
                <p className="text-xl font-bold text-blue-700">
                  ${simulationResult.futureValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Inversión inicial: ${parseFloat(investmentAmount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
            </section>

            {/* Proyección de Crecimiento */}
            <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <FaChartLine className="text-[#B59F50]" />
                Proyección de Crecimiento
              </h2>

              <div className="h-48 sm:h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={simulationResult.chartData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#B59F50" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#B59F50" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis 
                      dataKey="period" 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#6B7280', fontSize: 10 }}
                    />
                    <YAxis 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#6B7280', fontSize: 10 }}
                      width={45}
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
                      labelFormatter={(label) => `Periodo: ${label}`}
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
                      dot={{ fill: "#B59F50", r: 4 }}
                      activeDot={{ r: 6, fill: "#B59F50", stroke: "#fff", strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

            {/* Convertir en inversión real */}
            <section className="bg-white rounded-xl p-4 shadow-sm mb-6 border border-gray-100">
              <div className="text-center">
                <button
                  onClick={handleCreateRealInvestment}
                  className="w-full bg-green-600 text-white font-semibold py-3 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                >
                  <FaArrowUp size={16} />
                  Convertir en inversión real
                </button>
                <p className="text-xs text-gray-500 mt-2">
                  Esta simulación se basará en datos históricos y no garantiza rendimientos futuros
                </p>
              </div>
            </section>
          </>
        )}

        {/* Información Adicional */}
        <section className="bg-white rounded-xl p-4 shadow-sm mb-6 border border-gray-100">
          <h3 className="font-semibold text-sm mb-3">💡 Nota Importante</h3>
          <p className="text-xs text-gray-600">
            Las simulaciones se basan en datos históricos y promedios de rendimiento. 
            Los resultados son estimaciones y no garantizan rendimientos futuros. 
            Todas las inversiones conllevan riesgo, incluyendo la posible pérdida del capital.
          </p>
        </section>
      </div>

      
    </main>
  );
}

// Componente de navegación
function NavItem({ 
  icon, 
  label, 
  href, 
  active = false 
}: { 
  icon: React.ReactNode; 
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