import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Mobile First Layout */}
      <div className="block md:hidden">
        {/* Mobile Version */}
        <div className="w-full h-screen flex flex-col items-center justify-center gap-6 px-6">

          {/* Logo Section */}
          <img 
            src="/Logo.png"
            alt="AurumCap Logo"
            className="w-40 h-auto"
          />

          {/* Text: AurumCap */}
          <h2 className="text-[#CCB661] text-3xl font-bold drop-shadow-md">
            AurumCap
          </h2>

          {/* Main Text */}
          <section className="text-center">
            <h1 className="font-bold text-2xl mb-4">
              Maneja tus inversiones desde un mismo lugar.
            </h1>
            <p className="text-gray-300 text-sm">
              Invierte de forma inteligente y haz crecer tu capital
            </p>
          </section>

          {/* Benefits */}
          <section className="w-full max-w-xs mt-4">
            <h3 className="text-[#CCB661] font-semibold text-lg mb-4 text-center">
              Nuestros Beneficios
            </h3>
            <div className="space-y-3">
              {[
                { icon: "📚", text: "Aprende" },
                { icon: "💼", text: "Invierte" },
                { icon: "📈", text: "Crecimiento" }
              ].map((benefit, index) => (
                <div key={index} className="flex items-center gap-3 bg-gray-900/50 rounded-lg p-3">
                  <span className="text-lg">{benefit.icon}</span>
                  <span className="font-medium">{benefit.text}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Action Buttons */}
          <section className="w-full max-w-xs space-y-3 mt-6">
              <Link
                href="/register"
                className="w-full h-12 flex items-center justify-center bg-[B59F50] text-black font-bold text-lg rounded-xl shadow-lg hover:bg-[#A68F45] transition duration-300"
              >
                Crear cuenta
              </Link>

              <Link
                href="/login"
                className="w-full h-12 flex items-center justify-center border-2 border-[#B59F50] text-[#B59F50] font-bold text-lg rounded-xl hover:bg-[#B59F50] hover:text-black transition duration-300"
              >
                Iniciar sesión
              </Link>
          </section>

          {/* Footer links */}
          <footer className="absolute bottom-6 flex gap-6 text-sm text-gray-400">
            <Link
              href="/privacy"
              className="hover:text-[#CCB661] transition"
            >
              Política de Privacidad
            </Link>

            <Link
              href="/support"
              className="hover:text-[#CCB661] transition"
            >
              Soporte
            </Link>
          </footer>
        </div>
      </div>

      {/* Desktop Layout */}
      <div className="hidden md:flex min-h-screen flex-col items-center justify-center px-8">
        <div className="max-w-2xl w-full text-center">
          
          {/* Logo & Name */}
          <div className="flex flex-col items-center gap-8 mb-16">
            <img
              src="/Logo.png"
              alt="AurumCap Logo"
              className="w-42 h-42"
            />
            <h2 className="text-[#CCB661] text-6xl font-bold"> 
              AurumCap
            </h2>
          </div>

          {/* Main Text */}
          <section className="mb-16">
            <h1 className="text-6xl font-bold mb-8 leading-tight">
              Invierte sin complicarte
            </h1>
            <p className="text-lg text-gray-300 leading-relaxed">
              Maneja tus inversiones desde un mismo lugar de forma<br />
              inteligente y segura.
            </p>
          </section>

          {/* Beneficios - CENTRADO EN GRID */}
          <section className="mb-20">
            <h3 className="text-[#CCB661] font-semibold text-3xl mb-12">
              Nuestros Beneficios
            </h3>
            <div className="grid grid-cols-3 gap-8"> {/* Grid de 3 columnas */}
              {[
                { 
                  icon: "🎓", 
                  text: "Aprende", 
                  desc: "Educación financiera accesible" 
                },
                { 
                  icon: "💼", 
                  text: "Invierte", 
                  desc: "Plataforma intuitiva de inversión" 
                },
                { 
                  icon: "📈", 
                  text: "Crecimiento", 
                  desc: "Sigue tu progreso en tiempo real" 
                }
              ].map((benefit, index) => (
                <div 
                  key={index} 
                  className="flex flex-col items-center gap-4 p-6 bg-gray-900/30 rounded-xl hover:bg-gray-900/50 transition-all duration-300 hover:scale-105"
                >
                  <span className="text-4xl">{benefit.icon}</span> {/* Iconos más grandes */}
                  <div>
                    <div className="font-semibold text-xl mb-2">{benefit.text}</div>
                    <div className="text-gray-400 text-sm">{benefit.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Botones de acción - CENTRADOS */}
          <section className="flex justify-center gap-6 mb-16">
            <Link
              href="/register"
              className="px-16 py-5 bg-[#B59F50] text-black font-bold text-xl rounded-xl shadow-lg hover:bg-[#A68F45] transition-all duration-300 hover:scale-105"
            >
              Crear cuenta
            </Link>
            
            <Link
              href="/login"
              className="px-16 py-5 border-2 border-[#B59F50] text-[#B59F50] font-bold text-xl rounded-xl hover:bg-[#B59F50] hover:text-black transition-all duration-300"
            >
              Iniciar sesión
            </Link>
          </section>

          {/* Enlaces footer - CENTRADOS */}
          <footer className="flex justify-center gap-8 text-gray-400 text-sm">
            <Link 
              href="/privacy" 
              className="hover:text-[#CCB661] transition-colors duration-200"
            >
              Política de Privacidad
            </Link>
            <Link 
              href="/support" 
              className="hover:text-[#CCB661] transition-colors duration-200"
            >
              Soporte
            </Link>
          </footer>
        </div>
      </div>

    </div>
  );
}


