import Link from "next/link";
import Image from "next/image";
import { FaChartLine, FaEye, FaGraduationCap, FaMobileAlt, FaShieldAlt, FaSync, FaFilter, FaUsers, FaCalculator, FaBook } from "react-icons/fa";

export default function Home() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8 md:py-12">
        
        {/* Logo Section */}
        <div className="flex flex-col items-center gap-4 md:gap-6 mb-6 md:mb-8">
          <Image 
            src="/Logo.png"
            alt="AurumCap Logo"
            width={100}
            height={100}
            className="w-16 h-16 md:w-24 md:h-24 lg:w-32 lg:h-32"
          />
          
          {/* Text: AurumCap */}
          <h2 className="text-[#CCB661] text-2xl md:text-4xl lg:text-5xl font-bold drop-shadow-md">
            AurumCap
          </h2>
        </div>

        {/* Main Text - ENFATIZANDO SEGUIMIENTO UNIFICADO */}
        <section className="text-center mb-6 md:mb-8 max-w-2xl">
          <div className="inline-block bg-[#B59F50]/20 border border-[#B59F50] rounded-full px-3 py-1 mb-3">
            <span className="text-[#B59F50] text-xs font-semibold">VISIÓN UNIFICADA</span>
          </div>
          <h1 className="font-bold text-xl md:text-3xl lg:text-4xl mb-3 md:mb-4 leading-tight">
            Tu portafolio completo en un solo lugar
          </h1>
          <p className="text-gray-300 text-sm md:text-base leading-relaxed mb-3">
            Conecta todas tus inversiones y sigue su rendimiento desde una única plataforma
          </p>
          <div className="bg-gray-900/50 rounded-lg p-3 border border-gray-700 mb-4">
            <p className="text-gray-400 text-xs">
              <strong className="text-[#CCB661]">💡 Ejemplo real:</strong> Hapi: $560 + Binance: $440 = 
              <strong className="text-white"> Total: $1,000 visibles en AurumCap</strong>
            </p>
          </div>

          {/* Action Buttons - COMPACTOS */}
          <div className="w-full max-w-xs md:max-w-sm space-y-2 md:space-y-0 md:flex md:justify-center md:gap-3 mx-auto">
            <Link
              href="/register"
              className="w-full md:w-auto flex items-center justify-center bg-[#B59F50] text-black font-bold text-sm md:text-base py-2 md:py-3 px-6 md:px-8 rounded-lg shadow-lg hover:bg-[#A68F45] transition-all duration-300 hover:scale-105"
            >
              Unificar Mis Inversiones
            </Link>

            <Link
              href="/login"
              className="w-full md:w-auto flex items-center justify-center border border-[#B59F50] text-[#B59F50] font-bold text-sm md:text-base py-2 md:py-3 px-6 md:px-8 rounded-lg hover:bg-[#B59F50] hover:text-black transition-all duration-300"
            >
              Acceder
            </Link>
          </div>
        </section>

        {/* Benefits - MÁS COMPACTO */}
        <section className="w-full max-w-xs md:max-w-2xl">
          <h3 className="text-[#CCB661] font-semibold text-base md:text-xl mb-3 md:mb-4 text-center">
            Control Total de Tus Inversiones
          </h3>
          
          {/* Mobile: Lista vertical más compacta */}
          <div className="block md:hidden space-y-2">
            {[
              { icon: "👁️", text: "Visión Unificada" },
              { icon: "📊", text: "Análisis Detallado" },
              { icon: "🎓", text: "Aprendizaje" }
            ].map((benefit, index) => (
              <div key={index} className="flex items-center gap-2 bg-gray-900/50 rounded-lg p-2">
                <span className="text-base">{benefit.icon}</span>
                <span className="font-medium text-sm">{benefit.text}</span>
              </div>
            ))}
          </div>

          {/* Desktop: Grid más compacto */}
          <div className="hidden md:grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4">
            {[
              { 
                icon: "👁️", 
                text: "Visión Unificada", 
                desc: "Todas tus inversiones en una app" 
              },
              { 
                icon: "📊", 
                text: "Análisis Detallado", 
                desc: "Filtra por tipo de activo" 
              },
              { 
                icon: "🎓", 
                text: "Aprendizaje Integrado", 
                desc: "Mejora tus decisiones" 
              }
            ].map((benefit, index) => (
              <div 
                key={index} 
                className="flex flex-col items-center gap-2 p-3 bg-gray-900/30 rounded-lg hover:bg-gray-900/50 transition-all duration-300"
              >
                <span className="text-xl md:text-2xl">{benefit.icon}</span>
                <div className="text-center">
                  <div className="font-semibold text-sm md:text-base mb-1">{benefit.text}</div>
                  <div className="text-gray-400 text-xs">{benefit.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* El resto del código se mantiene igual */}
      {/* Value Added Sections */}
      
      {/* Sección 1: El Problema que Resolvemos */}
      <section className="py-12 md:py-20 px-4 bg-gray-900/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8 md:mb-16">
            <h2 className="text-2xl md:text-4xl font-bold text-[#CCB661] mb-4">
              ¿Cansado de cambiar entre apps para ver tu portafolio?
            </h2>
            <p className="text-gray-300 text-lg md:text-xl max-w-3xl mx-auto">
              Binance, Hapi, eToro, tu broker... AurumCap <strong>unifica todo</strong> en una sola vista.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            {[
              {
                icon: FaSync,
                title: "Sincronización Central",
                description: "Registra inversiones de todas tus plataformas en un solo lugar"
              },
              {
                icon: FaEye,
                title: "Visión 360°",
                description: "Ve el valor total y el rendimiento de todo tu portafolio"
              },
              {
                icon: FaFilter,
                title: "Filtros Inteligentes",
                description: "Analiza por tipo de activo, plataforma o período de tiempo"
              },
              {
                icon: FaChartLine,
                title: "Tendencias Claras",
                description: "Identifica qué activos y plataformas generan más rentabilidad"
              }
            ].map((feature, index) => (
              <div 
                key={index}
                className="bg-gray-800/50 p-4 md:p-6 rounded-xl hover:bg-gray-800/70 transition-all duration-300 border border-gray-700/50"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-[#B59F50] p-2 rounded-lg">
                    <feature.icon className="text-white text-lg md:text-xl" />
                  </div>
                  <h3 className="font-bold text-white text-base md:text-lg">{feature.title}</h3>
                </div>
                <p className="text-gray-300 text-sm md:text-base leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sección 2: Cómo funciona el Seguimiento Unificado */}
      <section className="py-12 md:py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-4xl font-bold text-center mb-8 md:mb-16 text-[#CCB661]">
            Tu Centro de Control de Inversiones
          </h2>
          
          <div className="space-y-6 md:space-y-8">
            {[
              {
                step: "📥",
                title: "Registra Todas Tus Inversiones",
                description: "Agrega inversiones de cualquier plataforma: cripto, acciones, fondos, etc."
              },
              {
                step: "🔍",
                title: "Analiza con Filtros Avanzados",
                description: "Filtra por tipo de activo para ver qué genera más rentabilidad"
              },
              {
                step: "🏢",
                title: "Compara Plataformas",
                description: "Descubre en qué plataforma tus inversiones rinden mejor"
              },
              {
                step: "📈",
                title: "Toma Decisiones Informadas",
                description: "Usa datos reales de todo tu portafolio para optimizar tus estrategias"
              }
            ].map((step, index) => (
              <div 
                key={index}
                className="flex items-start gap-4 md:gap-6 bg-gray-900/30 p-4 md:p-6 rounded-xl border border-gray-700/30"
              >
                <div className="bg-[#B59F50] text-black font-bold md:text-xl w-12 h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center shrink-0 text-2xl">
                  {step.step}
                </div>
                <div>
                  <h3 className="font-bold text-white text-lg md:text-xl mb-2">
                    {step.title}
                  </h3>
                  <p className="text-gray-300 text-sm md:text-base">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sección 3: Ejemplos de Análisis */}
      <section className="py-12 md:py-20 px-4 bg-gray-900/30">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl md:text-4xl font-bold text-center mb-8 md:mb-16 text-[#CCB661]">
            Descubre Insights que Otras Apps No Te Muestran
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
            {/* Ejemplo 1: Filtro por Tipo de Activo */}
            <div className="bg-gray-800/50 p-6 rounded-xl border border-gray-700/50">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-[#B59F50] p-2 rounded-lg">
                  <FaFilter className="text-white text-lg" />
                </div>
                <h3 className="font-bold text-white text-xl">Por Tipo de Activo</h3>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">🔵 Criptomonedas</span>
                  <span className="text-green-400">+18.5%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">🟢 Acciones</span>
                  <span className="text-green-400">+12.2%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">🟡 ETFs</span>
                  <span className="text-red-400">-2.1%</span>
                </div>
              </div>
              <p className="text-gray-400 text-xs mt-4">
                <strong>Insight:</strong> Tus criptomonedas generan mayor rentabilidad que otros activos
              </p>
            </div>

            {/* Ejemplo 2: Filtro por Plataforma */}
            <div className="bg-gray-800/50 p-6 rounded-xl border border-gray-700/50">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-[#B59F50] p-2 rounded-lg">
                  <FaChartLine className="text-white text-lg" />
                </div>
                <h3 className="font-bold text-white text-xl">Por Plataforma</h3>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">🎯 Binance</span>
                  <span className="text-green-400">+22.3%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">📊 Hapi</span>
                  <span className="text-green-400">+15.8%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">💼 Tu Broker</span>
                  <span className="text-green-400">+8.4%</span>
                </div>
              </div>
              <p className="text-gray-400 text-xs mt-4">
                <strong>Insight:</strong> Binance genera mejor rendimiento para tus estrategias actuales
              </p>
            </div>
          </div>

          {/* Aclaración importante */}
          <div className="mt-12 p-6 bg-blue-500/10 border border-blue-500/30 rounded-xl">
            <div className="flex items-start gap-3">
              <div className="text-blue-400 text-xl">💡</div>
              <div>
                <h4 className="font-bold text-blue-400 text-lg mb-2">Plataforma de Seguimiento</h4>
                <p className="text-blue-300 text-sm md:text-base">
                  <strong>AurumCap es tu centro de control para seguir TODAS tus inversiones.</strong> 
                  No ejecutamos transacciones, pero te damos la visión completa que necesitas para 
                  tomar mejores decisiones en todas tus plataformas.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Sección 4: Educación + Seguimiento */}
      <section className="py-12 md:py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl md:text-4xl font-bold text-center mb-8 md:mb-16 text-[#CCB661]">
            Seguimiento Inteligente + Aprendizaje Continuo
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
            <div className="bg-gray-900/30 p-6 rounded-xl border border-gray-700/30">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-[#B59F50] p-2 rounded-lg">
                  <FaEye className="text-white text-lg" />
                </div>
                <h3 className="font-bold text-white text-xl">Seguimiento en Tiempo Real</h3>
              </div>
              <ul className="space-y-3 text-gray-300">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#B59F50] rounded-full"></div>
                  Valor total de todo tu portafolio
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#B59F50] rounded-full"></div>
                  Rendimiento por activo y plataforma
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#B59F50] rounded-full"></div>
                  Tendencias y análisis comparativos
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#B59F50] rounded-full"></div>
                  Alertas personalizadas de rendimiento
                </li>
              </ul>
            </div>

            <div className="bg-gray-900/30 p-6 rounded-xl border border-gray-700/30">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-[#B59F50] p-2 rounded-lg">
                  <FaGraduationCap className="text-white text-lg" />
                </div>
                <h3 className="font-bold text-white text-xl">Aprendizaje Basado en Datos</h3>
              </div>
              <ul className="space-y-3 text-gray-300">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#B59F50] rounded-full"></div>
                  Simulaciones con tus datos reales
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#B59F50] rounded-full"></div>
                  Análisis de tus patrones de inversión
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#B59F50] rounded-full"></div>
                  Recomendaciones personalizadas
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#B59F50] rounded-full"></div>
                  Cursos basados en tu portafolio real
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Sección 5: Testimonios */}
      <section className="py-12 md:py-20 px-4 bg-gray-900/30">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-4xl font-bold text-center mb-8 md:mb-16 text-[#CCB661]">
            Inversores que Ya Unificaron Su Visión
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
            {[
              {
                name: "Ana M.",
                role: "Inversora en 4 plataformas",
                text: "Por fin veo el rendimiento REAL de todo mi portafolio. AurumCap me mostró que mis cripto en Binance rendían más que todo lo demás."
              },
              {
                name: "David R.",
                role: "Usuario de Hapi y eToro", 
                text: "El filtro por tipo de activo me reveló que mis ETFs no rendían como esperaba. Ahora tomo decisiones basadas en datos reales."
              }
            ].map((testimonial, index) => (
              <div 
                key={index}
                className="bg-gray-800/50 p-6 rounded-xl border border-gray-700/30"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-[#B59F50] rounded-full flex items-center justify-center">
                    <FaUsers className="text-white text-sm" />
                  </div>
                  <div>
                    <div className="font-bold text-white">{testimonial.name}</div>
                    <div className="text-gray-400 text-sm">{testimonial.role}</div>
                  </div>
                </div>
                <p className="text-gray-300 text-sm md:text-base italic">
                  "{testimonial.text}"
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Final */}
      <section className="py-12 md:py-20 px-4 bg-linear-to-br from-[#B59F50] to-[#D4AF37]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl md:text-4xl font-bold text-black mb-4 md:mb-6">
            Deja de Cambiar Entre Apps
          </h2>
          <p className="text-black/80 text-lg md:text-xl mb-6 md:mb-8 max-w-2xl mx-auto">
            Unifica todas tus inversiones y descubre insights que transformarán tu estrategia.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="bg-black text-white font-bold py-3 md:py-4 px-8 md:px-12 rounded-xl hover:bg-gray-900 transition-all duration-300 text-lg"
            >
              Unificar Mis Inversiones
            </Link>
            <Link
              href="/learn"
              className="bg-white/20 text-black font-bold py-3 md:py-4 px-8 md:px-12 rounded-xl hover:bg-white/30 transition-all duration-300 text-lg border border-black/20"
            >
              Ver Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 bg-gray-900">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-center md:text-left">
              <div className="text-[#CCB661] font-bold text-xl mb-2">AurumCap</div>
              <p className="text-gray-400 text-sm">
                Tu centro de control para todas las inversiones
              </p>
            </div>
            
            <div className="flex gap-6 text-sm text-gray-400">
              <Link
                href="/privacy"
                className="hover:text-[#CCB661] transition-colors duration-200"
              >
                Privacidad
              </Link>
              <Link
                href="/support"
                className="hover:text-[#CCB661] transition-colors duration-200"
              >
                Soporte
              </Link>
              <Link
                href="/terms"
                className="hover:text-[#CCB661] transition-colors duration-200"
              >
                Términos
              </Link>
            </div>
          </div>
          
          <div className="text-center mt-6 pt-6 border-t border-gray-700">
            <p className="text-gray-500 text-xs">
              © 2024 AurumCap. Plataforma de seguimiento y educación de inversiones.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}