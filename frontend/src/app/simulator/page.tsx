// app/simulator/page.tsx
"use client";

import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Area } from "recharts";
import { FaCalculator, FaChartLine, FaDollarSign, FaExclamationTriangle, FaArrowUp, FaHome, FaBriefcase, FaBookOpen, FaInfoCircle, FaCrown } from "react-icons/fa";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter } from "next/navigation";

// Tipos de activos disponibles con datos realistas
const ASSET_TYPES = [
  { 
    value: "sp500", 
    label: "S&P 500", 
    risk: "Medio", 
    avgReturn: 10.5,
    description: "Índice de las 500 mayores empresas de EE.UU.",
    volatility: 15.2
  },
  { 
    value: "nasdaq", 
    label: "NASDAQ", 
    risk: "Alto", 
    avgReturn: 12.8,
    description: "Índice tecnológico con empresas innovadoras",
    volatility: 22.5
  },
  { 
    value: "bitcoin", 
    label: "Bitcoin", 
    risk: "Muy Alto", 
    avgReturn: 45.2,
    description: "Criptomoneda líder con alto potencial de crecimiento",
    volatility: 75.8
  },
  { 
    value: "ethereum", 
    label: "Ethereum", 
    risk: "Alto", 
    avgReturn: 32.1,
    description: "Plataforma blockchain para aplicaciones descentralizadas",
    volatility: 68.3
  },
  { 
    value: "gold", 
    label: "Oro", 
    risk: "Bajo", 
    avgReturn: 6.2,
    description: "Activo refugio tradicional contra la inflación",
    volatility: 12.4
  },
  { 
    value: "bonds", 
    label: "Bonos Corporativos", 
    risk: "Bajo", 
    avgReturn: 4.5,
    description: "Deuda corporativa con rendimientos estables",
    volatility: 8.7
  },
  { 
    value: "reit", 
    label: "REITs", 
    risk: "Medio", 
    avgReturn: 8.7,
    description: "Fondos de inversión en bienes raíces",
    volatility: 18.9
  },
];

export default function SimulatorPage() {
  const [investmentAmount, setInvestmentAmount] = useState<string>("10000");
  const [selectedAsset, setSelectedAsset] = useState<string>("sp500");
  const [months, setMonths] = useState<string>("60"); // Cambiado a 5 años por defecto
  const [monthlyContribution, setMonthlyContribution] = useState<string>("100");
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { user } = useAuth();
  const router = useRouter();

  // Simular automáticamente al cargar la página
  useEffect(() => {
    simulateInvestment();
  }, []);

  // CALCULADORA MEJORADA CON INTERÉS COMPUESTO MENSUAL
  const simulateInvestment = () => {
    setIsLoading(true);
    
    setTimeout(() => {
      const initialAmount = parseFloat(investmentAmount) || 0;
      const monthsNum = parseInt(months) || 60;
      const monthlyContrib = parseFloat(monthlyContribution) || 0;
      
      const selectedAssetData = ASSET_TYPES.find(asset => asset.value === selectedAsset);
      const annualReturn = selectedAssetData?.avgReturn || 0;
      
      // INTERÉS COMPUESTO MENSUAL
      const monthlyReturn = annualReturn / 12 / 100;
      
      let currentBalance = initialAmount;
      const monthlyData = [];
      const yearlyData = [];
      
      // Simulación mes a mes con interés compuesto
      for (let month = 1; month <= monthsNum; month++) {
        // Aplicar interés compuesto al balance actual
        currentBalance = currentBalance * (1 + monthlyReturn);
        
        // Agregar contribución mensual (si existe)
        currentBalance += monthlyContrib;
        
        monthlyData.push({
          month,
          balance: currentBalance,
          contributions: initialAmount + (monthlyContrib * month)
        });
        
        // Agrupar por años para el gráfico principal
        if (month % 12 === 0 || month === monthsNum) {
          const years = month / 12;
          yearlyData.push({
            period: `Año ${Math.ceil(years)}`,
            value: Math.round(currentBalance),
            contributions: initialAmount + (monthlyContrib * month),
            profit: currentBalance - (initialAmount + (monthlyContrib * month))
          });
        }
      }
      
      const totalInvested = initialAmount + (monthlyContrib * monthsNum);
      const totalProfit = currentBalance - totalInvested;
      const profitPercentage = (totalProfit / totalInvested) * 100;
      
      setSimulationResult({
        totalInvested,
        totalProfit,
        finalBalance: currentBalance,
        profitPercentage,
        riskLevel: selectedAssetData?.risk || "Medio",
        annualReturn,
        monthlyData,
        yearlyData,
        selectedAssetData,
        months: monthsNum
      });
      
      setIsLoading(false);
    }, 800);
  };

  const handleCreateRealInvestment = () => {
    const params = new URLSearchParams({
      amount: investmentAmount,
      asset: selectedAsset,
      months: months,
      simulated: 'true'
    });
    router.push(`/portfolio/new?${params.toString()}`);
  };

  // Calcular el efecto del interés compuesto
  const calculateCompoundEffect = () => {
    const amount = parseFloat(investmentAmount) || 0;
    const annualReturn = ASSET_TYPES.find(a => a.value === selectedAsset)?.avgReturn || 0;
    const years = parseInt(months) / 12;
    
    // Sin interés compuesto (simple)
    const simpleInterest = amount * (annualReturn / 100) * years;
    
    // Con interés compuesto
    const compoundInterest = amount * Math.pow(1 + annualReturn / 100, years) - amount;
    
    return {
      simple: simpleInterest,
      compound: compoundInterest,
      difference: compoundInterest - simpleInterest
    };
  };

  const compoundEffect = calculateCompoundEffect();

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
            <span className="hidden xs:inline">Simulador Inteligente</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-4 max-w-6xl mx-auto">
        {/* Valor Proposición Única */}
        <section className="bg-linear-to-r from-[#B59F50] to-[#D4AF37] rounded-xl p-4 text-white mb-4">
          <div className="flex items-center gap-2 mb-2">
            <FaCrown size={20} />
            <h2 className="text-lg font-bold">Descubre el Poder del Interés Compuesto</h2>
          </div>
          <p className="text-sm opacity-90">
            Tu dinero trabajando para ti. Ve cómo pequeñas inversiones consistentes se transforman en grande patrimonios.
          </p>
        </section>

        {/* Sección de Parámetros */}
        <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <FaCalculator className="text-[#B59F50]" />
            Configura Tu Simulación
          </h2>

          <div className="space-y-4">
            {/* Inversión Inicial */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Inversión Inicial (USD)
              </label>
              <div className="relative">
                <FaDollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                <input
                  type="number"
                  value={investmentAmount}
                  onChange={(e) => setInvestmentAmount(e.target.value)}
                  placeholder="Ej. 10000"
                  min="0"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
                />
              </div>
            </div>

            {/* Tipo de Activo con Descripción */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Activo de Inversión
              </label>
              <select
                value={selectedAsset}
                onChange={(e) => setSelectedAsset(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent mb-2"
              >
                <option value="">Selecciona un activo</option>
                {ASSET_TYPES.map((asset) => (
                  <option key={asset.value} value={asset.value}>
                    {asset.label} ({asset.avgReturn}% anual)
                  </option>
                ))}
              </select>
              {selectedAsset && (
                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded-lg">
                  <strong>{ASSET_TYPES.find(a => a.value === selectedAsset)?.label}:</strong>{" "}
                  {ASSET_TYPES.find(a => a.value === selectedAsset)?.description}
                </div>
              )}
            </div>

            {/* Plazo de Inversión */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Plazo de Inversión (años)
              </label>
              <select
                value={months}
                onChange={(e) => setMonths(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              >
                <option value="12">1 año</option>
                <option value="60">5 años</option>
                <option value="120">10 años</option>
                <option value="180">15 años</option>
                <option value="240">20 años</option>
                <option value="300">25 años</option>
              </select>
            </div>

            {/* Opciones Avanzadas */}
            <div>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-sm text-[#B59F50] font-medium mb-2"
              >
                <FaInfoCircle size={14} />
                {showAdvanced ? 'Ocultar' : 'Mostrar'} opciones avanzadas
              </button>
              
              {showAdvanced && (
                <div className="space-y-3 p-3 bg-gray-50 rounded-lg border">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Aportación Mensual (USD)
                    </label>
                    <input
                      type="number"
                      value={monthlyContribution}
                      onChange={(e) => setMonthlyContribution(e.target.value)}
                      placeholder="Ej. 100"
                      min="0"
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Pequeñas contribuciones mensuales multiplican tu crecimiento
                    </p>
                  </div>
                </div>
              )}
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
                  Calculando...
                </>
              ) : (
                <>
                  <FaCalculator size={16} />
                  Simular Inversión
                </>
              )}
            </button>
          </div>
        </section>

        {/* Resultados de la Simulación */}
        {simulationResult && (
          <>
            {/* Efecto Interés Compuesto */}
            <section className="bg-blue-50 rounded-xl p-4 shadow-sm mb-4 border border-blue-200">
              <h3 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <FaInfoCircle />
                El Poder del Interés Compuesto
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="text-center p-3 bg-white rounded-lg border">
                  <p className="text-gray-600 mb-1">Interés Simple</p>
                  <p className="text-lg font-bold text-gray-700">
                    +${compoundEffect.simple.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </p>
                </div>
                <div className="text-center p-3 bg-green-100 rounded-lg border border-green-300">
                  <p className="text-green-700 mb-1">Interés Compuesto</p>
                  <p className="text-lg font-bold text-green-800">
                    +${compoundEffect.compound.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </p>
                </div>
              </div>
              <p className="text-xs text-blue-700 mt-2 text-center">
                El interés compuesto genera ${compoundEffect.difference.toLocaleString('en-US', { maximumFractionDigits: 0 })} adicional
              </p>
            </section>

            {/* Resultados Principales */}
            <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <FaChartLine className="text-[#B59F50]" />
                Resultados de Tu Inversión
              </h2>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-green-600 text-xs font-medium mb-1">Balance Final</p>
                  <p className="text-lg font-bold text-green-700">
                    ${simulationResult.finalBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>

                <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-blue-600 text-xs font-medium mb-1">Ganancia Total</p>
                  <p className="text-lg font-bold text-blue-700">
                    +${simulationResult.totalProfit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                  <p className="text-xs text-blue-600">
                    {simulationResult.profitPercentage.toFixed(1)}% de retorno
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-gray-600 text-xs font-medium mb-1">Total Invertido</p>
                  <p className="text-sm font-bold text-gray-700">
                    ${simulationResult.totalInvested.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>

                <div className="text-center p-3 bg-orange-50 rounded-lg border border-orange-200">
                  <p className="text-orange-600 text-xs font-medium mb-1 flex items-center justify-center gap-1">
                    <FaExclamationTriangle size={10} />
                    Riesgo
                  </p>
                  <p className="text-sm font-bold text-orange-700">
                    {simulationResult.riskLevel}
                  </p>
                </div>
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
                  <LineChart data={simulationResult.yearlyData}>
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
                      labelFormatter={(label) => `${label}`}
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

            {/* Llamada a la Acción */}
            <section className="bg-gradient-to-r from-green-600 to-green-700 rounded-xl p-4 shadow-sm mb-6 text-white">
              <div className="text-center">
                <h3 className="font-bold text-lg mb-2">¿Listo para hacerlo realidad?</h3>
                <p className="text-sm opacity-90 mb-4">
                  Comienza tu journey de inversión hoy mismo
                </p>
                <button
                  onClick={handleCreateRealInvestment}
                  className="w-full bg-white text-green-700 font-bold py-3 rounded-lg hover:bg-gray-100 transition-colors flex items-center justify-center gap-2"
                >
                  <FaArrowUp size={16} />
                  Comenzar a Invertir
                </button>
              </div>
            </section>
          </>
        )}


        {/* Disclaimer */}
        <section className="bg-yellow-50 rounded-xl p-4 shadow-sm border border-yellow-200">
          <h3 className="font-semibold text-yellow-800 text-sm mb-2 flex items-center gap-2">
            <FaExclamationTriangle size={14} />
            Información Importante
          </h3>
          <p className="text-xs text-yellow-700">
            Las simulaciones se basan en datos históricos y no garantizan rendimientos futuros. 
            Todas las inversiones conllevan riesgo. AurumCap ofrece herramientas educativas 
            y de simulación para ayudar en la toma de decisiones informadas.
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